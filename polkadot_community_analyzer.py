"""
Polkadot Community Analyzer

An advanced tool to analyze the Polkadot forum and extract insights about
the most relevant topics, emerging trends, and matters that are important to the community.
"""

import requests
import json
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import re
from tqdm import tqdm
import numpy as np
from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import os
import logging

# Configure logger
logger = logging.getLogger("polkadot_analyzer.community")

# Configure NLTK for text analysis
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading required NLTK resources...")
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

BASE_URL = "https://forum.polkadot.network"

class PolkadotCommunityAnalyzer:
    def __init__(self, delay_between_requests=1.0):
        self.categories = []
        self.topics = []
        self.posts = []
        self.user_activity = defaultdict(int)
        self.category_topics = defaultdict(list)
        self.tag_counts = Counter()
        self.mentions = Counter()
        self.keywords = Counter()
        self.governance_proposals = []
        self.delay = delay_between_requests
        
        # Create output directory for results if it doesn't exist
        self.output_dir = "polkadot_analysis_results"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    def fetch_categories(self):
        """Fetch all categories from the forum"""
        logger.info("Fetching categories...")
        try:
            response = requests.get(f"{BASE_URL}/categories.json")
            if response.status_code == 200:
                data = response.json()
                self.categories = data.get("category_list", {}).get("categories", [])
                logger.info(f"Found {len(self.categories)} categories")
                return True
            else:
                logger.error(f"Failed to fetch categories: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return False
    
    def fetch_topics_for_category(self, category_id, page=0):
        """Fetch topics for a specific category"""
        try:
            url = f"{BASE_URL}/c/{category_id}.json?page={page}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                topics = data.get("topic_list", {}).get("topics", [])
                self.category_topics[category_id].extend(topics)
                self.topics.extend(topics)
                return len(topics)
            else:
                logger.warning(f"Failed to fetch topics for category {category_id}: {response.status_code}")
                return 0
        except Exception as e:
            logger.error(f"Error fetching topics for category {category_id}: {str(e)}")
            return 0
            
    def fetch_topic_details(self, topic_id):
        """Fetch detailed information about a specific topic, including all posts"""
        try:
            response = requests.get(f"{BASE_URL}/t/{topic_id}.json")
            if response.status_code == 200:
                data = response.json()
                
                # Extract tags if available
                tags = data.get("tags", [])
                for tag in tags:
                    self.tag_counts[tag] += 1
                
                # Extract posts
                posts = data.get("post_stream", {}).get("posts", [])
                if posts:
                    self.posts.extend(posts)
                    
                    # Record user activity
                    for post in posts:
                        username = post.get("username")
                        if username:
                            self.user_activity[username] += 1
                        
                        # Analyze post content
                        self.analyze_post_content(post)
                    
                    # Check if it's a governance proposal
                    title = data.get("title", "").lower()
                    if any(keyword in title for keyword in ["proposal", "referendum", "vote", "governance", "treasury"]):
                        self.governance_proposals.append({
                            "id": topic_id,
                            "title": data.get("title"),
                            "created_at": data.get("created_at"),
                            "views": data.get("views"),
                            "posts_count": data.get("posts_count"),
                            "url": f"{BASE_URL}/t/{topic_id}"
                        })
                
                return len(posts)
            else:
                logger.warning(f"Failed to fetch topic {topic_id}: {response.status_code}")
                return 0
        except Exception as e:
            logger.error(f"Error fetching topic {topic_id}: {str(e)}")
            return 0

    def analyze_post_content(self, post):
        """Analyze the content of a post to extract mentions, keywords, and themes"""
        content = post.get("cooked", "")  # HTML content of the post
        
        # Remove HTML tags to get plain text
        clean_content = re.sub(r'<[^>]+>', ' ', content)
        
        # Extract mentions (@username)
        mentions = re.findall(r'@(\w+)', clean_content)
        for mention in mentions:
            self.mentions[mention] += 1
        
        # Extract meaningful keywords
        self.extract_keywords(clean_content)
        
    def extract_keywords(self, text):
        """Extract meaningful keywords from the text"""
        # Remove special characters and convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Tokenize the text
        tokens = word_tokenize(text)
        
        # Remove English stopwords
        stop_words = set(stopwords.words('english'))
        tokens = [word for word in tokens if word not in stop_words and len(word) > 3]
        
        # Add technical terms related to Polkadot that should not be filtered
        technical_terms = [
            "polkadot", "kusama", "parachain", "parathread", "substrate", "governance", 
            "referendum", "proposal", "validator", "nominator", "collator", "staking",
            "xcm", "opengl", "relay", "ausd", "chain", "wallet", "token", "dotsama",
            "web3", "blockchain"
        ]
        
        # Count frequency of meaningful words
        for word in tokens:
            if word in technical_terms or len(word) > 4:  # Longer words tend to be more meaningful
                self.keywords[word] += 1
    
    def collect_data(self, max_categories=10, max_topics_per_category=20, max_topics_details=50):
        """Collect data from the forum with limits to avoid excessive API calls"""
        
        # 1. Fetch categories
        if not self.fetch_categories():
            return False
            
        # 2. Fetch topics for each category (limited number)
        logger.info("Fetching topics for categories...")
        for i, category in enumerate(self.categories[:max_categories]):
            category_id = category.get("id")
            if not category_id:
                continue
                
            category_name = category.get('name', f'Category {category_id}')
            logger.info(f"  Category: {category_name} (ID: {category_id})")
            
            topics_count = 0
            page = 0
            
            # Fetch multiple pages until the limit is reached
            while topics_count < max_topics_per_category:
                new_topics = self.fetch_topics_for_category(category_id, page)
                if new_topics == 0:
                    break  # No more topics
                    
                topics_count += new_topics
                page += 1
                time.sleep(self.delay)  # Be gentle with the server
            
            logger.info(f"    Found {topics_count} topics")
        
        total_topics = len(self.topics)
        logger.info(f"Fetched {total_topics} topics from {min(max_categories, len(self.categories))} categories")
        
        # 3. Fetch details for a limited number of topics
        if not self.topics:
            logger.warning("No topics found for analysis")
            return False
            
        logger.info("Fetching details for selected topics...")
        
        # Sort by views or date to get the most relevant ones
        topics_to_analyze = sorted(
            self.topics, 
            key=lambda x: x.get('views', 0) + x.get('posts_count', 0) * 5,  # Prioritize engagement
            reverse=True
        )[:max_topics_details]
        
        for topic in tqdm(topics_to_analyze, desc="Analyzing topics"):
            topic_id = topic.get("id")
            if not topic_id:
                continue
                
            self.fetch_topic_details(topic_id)
            time.sleep(self.delay)  # Be gentle with the server
        
        logger.info(f"Fetched details for {len(topics_to_analyze)} topics, including {len(self.posts)} posts")
        return True
    
    def analyze(self):
        """
        Analyze collected data and generate insights.
        This is the main method that should be called after collect_data().
        """
        logger.info("Starting forum data analysis...")
        if not self.topics or not self.posts:
            logger.warning("No data to analyze. Run collect_data() first.")
            return {}
        
        analysis_results = {}
        
        # 1. Most active categories
        category_activity = self._analyze_category_activity()
        analysis_results["category_activity"] = category_activity
        
        # 2. Hot topics (most viewed and discussed)
        hot_topics = self._identify_hot_topics()
        analysis_results["hot_topics"] = hot_topics
        
        # 3. Most active users
        active_users = self._identify_active_users()
        analysis_results["active_users"] = active_users
        
        # 4. Influential users (users who are most mentioned)
        influential_users = self._identify_influential_users()
        analysis_results["influential_users"] = influential_users
        
        # 5. Trending keywords
        trending_keywords = self._analyze_keywords()
        # Convert trending keywords to ensure NumPy types are converted to Python types
        if trending_keywords:
            # If trending_keywords contains tuples with NumPy types, convert them
            converted_keywords = []
            for keyword_item in trending_keywords:
                if isinstance(keyword_item, tuple):
                    # Convert tuple elements to Python native types
                    word = keyword_item[0]
                    count = int(keyword_item[1]) if hasattr(keyword_item[1], 'item') else keyword_item[1]
                    converted_keywords.append((word, count))
                else:
                    # Already a dict or other structure
                    converted_keywords.append(keyword_item)
            trending_keywords = converted_keywords
        
        analysis_results["trending_keywords"] = trending_keywords
        
        # 6. Popular tags
        popular_tags = self._analyze_tags()
        # Convert tags to ensure NumPy types are converted to Python types
        if popular_tags:
            # If popular_tags contains tuples with NumPy types, convert them
            converted_tags = []
            for tag_item in popular_tags:
                if isinstance(tag_item, tuple):
                    # Convert tuple elements to Python native types
                    tag = tag_item[0]
                    count = int(tag_item[1]) if hasattr(tag_item[1], 'item') else tag_item[1]
                    converted_tags.append((tag, count))
                else:
                    # Already a dict or other structure
                    converted_tags.append(tag_item)
            popular_tags = converted_tags
        
        analysis_results["popular_tags"] = popular_tags
        
        # 7. Governance related discussions
        governance_discussions = self._analyze_governance_discussions()
        analysis_results["governance_discussions"] = governance_discussions
        
        # 8. Activity over time (if timestamps are available)
        activity_timeline = self._analyze_activity_timeline()
        if activity_timeline:
            # Ensure any NumPy int64 values in the timeline are converted to Python int
            for item in activity_timeline:
                if 'count' in item and hasattr(item['count'], 'item'):
                    item['count'] = int(item['count'])
            
            analysis_results["activity_timeline"] = activity_timeline
        
        # 9. Overall forum metrics
        analysis_results["metrics"] = {
            "total_categories": len(self.categories),
            "total_topics_analyzed": len(self.topics),
            "total_posts_analyzed": len(self.posts),
            "unique_users": len(self.user_activity),
            "unique_tags": len(self.tag_counts),
            "unique_keywords": len(self.keywords),
            "analysis_date": datetime.now().isoformat()
        }
        
        logger.info("Forum analysis completed successfully.")
        return analysis_results
    
    def _analyze_category_activity(self):
        """Analyze category activity based on topic and post counts"""
        category_activity = []
        
        for category in self.categories:
            category_id = category.get("id")
            if not category_id:
                continue
            
            topics_in_category = self.category_topics.get(category_id, [])
            
            # Count posts in this category
            post_count = 0
            for topic in topics_in_category:
                post_count += topic.get("posts_count", 0)
            
            category_activity.append({
                "id": category_id,
                "name": category.get("name", f"Category {category_id}"),
                "topic_count": len(topics_in_category),
                "post_count": post_count,
                "last_activity": category.get("last_posted_at", "")
            })
        
        # Sort by activity (topic count + post count)
        category_activity.sort(key=lambda x: x["topic_count"] + x["post_count"], reverse=True)
        return category_activity
    
    def _identify_hot_topics(self):
        """Identify hot topics based on views, replies, and recency"""
        if not self.topics:
            return []
        
        hot_topics = []
        for topic in self.topics:
            # Skip pinned topics as they may skew the results
            if topic.get("pinned", False):
                continue
                
            # Calculate a "heat score" based on views, replies, and recency
            views = topic.get("views", 0)
            posts_count = topic.get("posts_count", 0)
            
            # Convert last activity time to a timestamp
            last_posted_at = topic.get("last_posted_at", "")
            try:
                if last_posted_at:
                    last_posted_timestamp = datetime.fromisoformat(last_posted_at.replace("Z", "+00:00")).timestamp()
                    # Newer posts get a boost
                    recency_boost = (datetime.now().timestamp() - last_posted_timestamp) / 86400  # Days since last post
                    recency_boost = max(1, 30 - recency_boost) / 30  # Scale from 0 to 1
                else:
                    recency_boost = 0.5  # Default middle value
            except (ValueError, TypeError):
                recency_boost = 0.5
            
            # Calculate heat score
            heat_score = (views * 0.3) + (posts_count * 5 * 0.5) + (posts_count * recency_boost * 0.2)
            
            hot_topics.append({
                "id": topic.get("id"),
                "title": topic.get("title", "Untitled"),
                "views": views,
                "posts_count": posts_count,
                "last_posted_at": last_posted_at,
                "created_at": topic.get("created_at", ""),
                "heat_score": heat_score,
                "url": f"{BASE_URL}/t/{topic.get('id')}"
            })
        
        # Sort by heat score
        hot_topics.sort(key=lambda x: x["heat_score"], reverse=True)
        return hot_topics[:50]  # Return top 50 hot topics
    
    def _identify_active_users(self):
        """Identify the most active users based on post count"""
        active_users = [{"username": username, "post_count": count} 
                        for username, count in self.user_activity.items()]
        active_users.sort(key=lambda x: x["post_count"], reverse=True)
        return active_users[:50]  # Return top 50 active users
    
    def _identify_influential_users(self):
        """Identify influential users based on mentions and activity"""
        influential_users = []
        
        # Combine mentions and activity
        all_usernames = set(list(self.mentions.keys()) + list(self.user_activity.keys()))
        
        for username in all_usernames:
            mention_count = self.mentions.get(username, 0)
            post_count = self.user_activity.get(username, 0)
            
            # Calculate influence score (weighted combination of mentions and activity)
            influence_score = (mention_count * 3) + post_count
            
            if influence_score > 0:
                influential_users.append({
                    "username": username,
                    "mention_count": mention_count,
                    "post_count": post_count,
                    "influence_score": influence_score
                })
        
        # Sort by influence score
        influential_users.sort(key=lambda x: x["influence_score"], reverse=True)
        return influential_users[:50]  # Return top 50 influential users
    
    def _analyze_keywords(self):
        """Analyze trending keywords from posts"""
        # Convert Counter to list of tuples
        keywords_list = [(word, count) for word, count in self.keywords.most_common(100)]
        return keywords_list
    
    def _analyze_tags(self):
        """Analyze popular tags used in topics"""
        # Convert Counter to list of tuples
        tags_list = [(tag, count) for tag, count in self.tag_counts.most_common(50)]
        return tags_list
    
    def _analyze_governance_discussions(self):
        """Analyze discussions related to governance"""
        return sorted(self.governance_proposals, 
                    key=lambda x: x.get("views", 0) + x.get("posts_count", 0) * 5, 
                    reverse=True)
    
    def _analyze_activity_timeline(self):
        """Analyze activity over time"""
        # This requires timestamp data in posts
        if not self.posts:
            return None
            
        # Try to extract timestamps from posts
        timestamps = []
        for post in self.posts:
            created_at = post.get("created_at")
            if created_at:
                try:
                    # Convert ISO format to datetime
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    timestamps.append(dt)
                except (ValueError, TypeError):
                    continue
        
        if not timestamps:
            return None
            
        # Convert to pandas Series for easier analysis
        series = pd.Series(timestamps)
        
        # Group by day
        daily_counts = series.dt.floor('D').value_counts().sort_index()
        
        # Convert to list of date-count pairs
        timeline = [{"date": str(date), "count": count} 
                   for date, count in zip(daily_counts.index, daily_counts.values)]
        
        return timeline
    
    def generate_visualizations(self):
        """Generate visualizations from the analyzed data"""
        logger.info("Generating visualizations...")
        
        # 1. Create output directory for visualizations
        viz_dir = os.path.join(self.output_dir, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)
        
        try:
            # 2. Category activity visualization
            self._visualize_category_activity(viz_dir)
            
            # 3. Word cloud of keywords
            self._generate_wordcloud(viz_dir)
            
            # 4. Activity timeline
            self._visualize_activity_timeline(viz_dir)
            
            # 5. User activity distribution
            self._visualize_user_activity(viz_dir)
            
            logger.info(f"Visualizations saved to {viz_dir}")
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
    
    def _visualize_category_activity(self, output_dir):
        """Visualize category activity"""
        if not self.categories:
            return
            
        category_activity = self._analyze_category_activity()
        
        if not category_activity:
            return
            
        # Get top 10 categories by activity
        top_categories = category_activity[:10]
        
        # Create DataFrame
        df = pd.DataFrame(top_categories)
        
        # Set up the figure
        plt.figure(figsize=(12, 6))
        
        # Create bar chart
        sns.barplot(x="name", y="post_count", data=df)
        plt.title("Post Count by Category (Top 10)")
        plt.xlabel("Category")
        plt.ylabel("Number of Posts")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(output_dir, "category_activity.png"))
        plt.close()
        
    def _generate_wordcloud(self, output_dir):
        """Generate word cloud of keywords"""
        if not self.keywords:
            return
            
        # Create a dictionary for the wordcloud
        wordcloud_data = {word: count for word, count in self.keywords.items()}
        
        # Generate word cloud
        wordcloud = WordCloud(width=800, height=400, 
                              background_color="white", 
                              colormap="viridis",
                              max_words=100).generate_from_frequencies(wordcloud_data)
        
        # Plot the word cloud
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.title("Trending Keywords in Polkadot Forum")
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(output_dir, "keywords_wordcloud.png"))
        plt.close()
        
    def _visualize_activity_timeline(self, output_dir):
        """Visualize activity over time"""
        timeline_data = self._analyze_activity_timeline()
        
        if not timeline_data:
            return
            
        # Create DataFrame
        df = pd.DataFrame(timeline_data)
        df["date"] = pd.to_datetime(df["date"])
        
        # Sort by date
        df = df.sort_values("date")
        
        # Set up the figure
        plt.figure(figsize=(14, 6))
        
        # Create line chart
        plt.plot(df["date"], df["count"], marker="o", linestyle="-", markersize=4)
        plt.title("Forum Activity Over Time")
        plt.xlabel("Date")
        plt.ylabel("Number of Posts")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(output_dir, "activity_timeline.png"))
        plt.close()
        
    def _visualize_user_activity(self, output_dir):
        """Visualize user activity distribution"""
        if not self.user_activity:
            return
            
        # Get post counts
        post_counts = list(self.user_activity.values())
        
        # Set up the figure
        plt.figure(figsize=(10, 6))
        
        # Create histogram
        plt.hist(post_counts, bins=30, alpha=0.7, edgecolor="black")
        plt.title("Distribution of User Activity")
        plt.xlabel("Number of Posts per User")
        plt.ylabel("Number of Users")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(output_dir, "user_activity_distribution.png"))
        plt.close()
        
        # Also create a visualization of top users
        active_users = self._identify_active_users()
        top_users = active_users[:15]  # Top 15 users
        
        if not top_users:
            return
            
        # Create DataFrame
        df = pd.DataFrame(top_users)
        
        # Set up the figure
        plt.figure(figsize=(12, 6))
        
        # Create bar chart
        sns.barplot(x="username", y="post_count", data=df)
        plt.title("Most Active Users (Top 15)")
        plt.xlabel("Username")
        plt.ylabel("Number of Posts")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(output_dir, "top_users.png"))
        plt.close()