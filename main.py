"""
Simplified Polkadot Forum Analyzer

A focused version that addresses core functionality in a more reliable way.
"""

import requests
import json
import time
from datetime import datetime
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import sys

BASE_URL = "https://forum.polkadot.network"

class ForumAnalyzer:
    def __init__(self):
        self.categories = []
        self.topics = []
        self.posts = []
        self.user_activity = defaultdict(int)
        self.category_topics = defaultdict(list)
        
    def fetch_categories(self):
        """Fetch all categories from the forum"""
        print("Fetching categories...")
        try:
            response = requests.get(f"{BASE_URL}/categories.json")
            if response.status_code == 200:
                data = response.json()
                self.categories = data.get("category_list", {}).get("categories", [])
                print(f"Fetched {len(self.categories)} categories")
                return True
            else:
                print(f"Failed to fetch categories: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error fetching categories: {str(e)}")
            return False
            
    def fetch_topics_for_category(self, category_id, page=0):
        """Fetch topics from a specific category"""
        try:
            response = requests.get(f"{BASE_URL}/c/{category_id}.json?page={page}")
            if response.status_code == 200:
                data = response.json()
                topics = data.get("topic_list", {}).get("topics", [])
                self.category_topics[category_id].extend(topics)
                self.topics.extend(topics)
                return len(topics)
            else:
                print(f"Failed to fetch topics for category {category_id}: {response.status_code}")
                return 0
        except Exception as e:
            print(f"Error fetching topics for category {category_id}: {str(e)}")
            return 0
            
    def fetch_topic_details(self, topic_id):
        """Fetch detailed information about a specific topic including all posts"""
        try:
            response = requests.get(f"{BASE_URL}/t/{topic_id}.json")
            if response.status_code == 200:
                data = response.json()
                posts = data.get("post_stream", {}).get("posts", [])
                if posts:
                    self.posts.extend(posts)
                    
                    # Record user activity
                    for post in posts:
                        username = post.get("username")
                        if username:
                            self.user_activity[username] += 1
                    
                return len(posts)
            else:
                print(f"Failed to fetch topic {topic_id}: {response.status_code}")
                return 0
        except Exception as e:
            print(f"Error fetching topic {topic_id}: {str(e)}")
            return 0
            
    def collect_data(self, max_categories=5, max_topics_per_category=5, max_topics_details=10):
        """Collect forum data with limits to avoid excessive API calls"""
        
        # 1. Fetch categories
        if not self.fetch_categories():
            return False
            
        # 2. Fetch topics for each category (limited number)
        print("Fetching topics for categories...")
        for i, category in enumerate(self.categories[:max_categories]):
            category_id = category.get("id")
            if not category_id:
                continue
                
            print(f"  Category: {category.get('name')} (ID: {category_id})")
            topics_count = self.fetch_topics_for_category(category_id)
            print(f"    Found {topics_count} topics")
            
            # Be nice to the server
            time.sleep(1)
        
        print(f"Fetched {len(self.topics)} topics across {min(max_categories, len(self.categories))} categories")
        
        # 3. Fetch details for a limited number of topics
        if not self.topics:
            print("No topics found to analyze")
            return False
            
        print("Fetching details for selected topics...")
        topics_to_analyze = self.topics[:max_topics_details]
        for topic in topics_to_analyze:
            topic_id = topic.get("id")
            if not topic_id:
                continue
                
            print(f"  Topic: {topic.get('title')} (ID: {topic_id})")
            posts_count = self.fetch_topic_details(topic_id)
            print(f"    Found {posts_count} posts")
            
            # Be nice to the server
            time.sleep(1)
        
        print(f"Fetched details for {len(topics_to_analyze)} topics, including {len(self.posts)} posts")
        return True
        
    def analyze_data(self):
        """Perform basic analysis on the collected data"""
        if not self.topics or not self.posts:
            print("Not enough data collected for analysis")
            return None
            
        # 1. Basic metrics
        total_categories = len(self.categories)
        total_topics = len(self.topics)
        total_posts = len(self.posts)
        total_users = len(self.user_activity)
        
        # 2. Most active users
        top_users = sorted(self.user_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 3. Most active categories
        category_activity = {}
        for category in self.categories:
            category_id = category.get("id")
            if category_id:
                category_activity[category.get("name", f"Category {category_id}")] = len(self.category_topics.get(category_id, []))
        
        top_categories = sorted(category_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 4. Basic post metrics
        post_length_avg = 0
        if self.posts:
            post_lengths = [len(str(post.get("cooked", ""))) for post in self.posts]
            post_length_avg = sum(post_lengths) / len(post_lengths) if post_lengths else 0
        
        # Create a report
        analysis_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "summary": {
                "analysis_timestamp": analysis_timestamp,
                "total_categories": total_categories,
                "total_topics_analyzed": total_topics,
                "total_posts_analyzed": total_posts,
                "total_users": total_users,
                "average_post_length": round(post_length_avg, 2)
            },
            "top_users": [{"username": user, "post_count": count} for user, count in top_users],
            "top_categories": [{"name": cat, "topic_count": count} for cat, count in top_categories]
        }
        
    def visualize_top_users(self, report, filename="top_users.png"):
        """Create a simple visualization of top users"""
        try:
            if "top_users" not in report or not report["top_users"]:
                print("No user data available for visualization")
                return
                
            # Extract data for top 5 users
            top_5_users = report["top_users"][:5]
            usernames = [item["username"] for item in top_5_users]
            post_counts = [item["post_count"] for item in top_5_users]
            
            plt.figure(figsize=(10, 6))
            plt.bar(usernames, post_counts, color='skyblue')
            plt.title('Top Forum Contributors')
            plt.xlabel('Username')
            plt.ylabel('Post Count')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(filename)
            print(f"Visualization saved to {filename}")
        except Exception as e:
            print(f"Error creating visualization: {str(e)}")
        
    def export_report(self, report, filename="forum_analysis.json"):
        """Save the analysis report to a JSON file"""
        try:
            with open(filename, "w") as f:
                json.dump(report, f, indent=2)
            print(f"Report exported to {filename}")
            return True
        except Exception as e:
            print(f"Error exporting report: {str(e)}")
            return False
            
    def print_summary(self, report):
        """Print a summary of the analysis to the console"""
        if not report:
            print("No report data available")
            return
            
        print("\n===== FORUM ANALYSIS SUMMARY =====")
        print(f"Analysis completed at: {report.get('summary', {}).get('analysis_timestamp', 'unknown')}")
        print(f"Categories analyzed: {report.get('summary', {}).get('total_categories', 0)}")
        print(f"Topics analyzed: {report.get('summary', {}).get('total_topics_analyzed', 0)}")
        print(f"Posts analyzed: {report.get('summary', {}).get('total_posts_analyzed', 0)}")
        print(f"Unique users found: {report.get('summary', {}).get('total_users', 0)}")
        
        if "top_users" in report and report["top_users"]:
            print("\nTop 3 Forum Contributors:")
            for i, user in enumerate(report["top_users"][:3]):
                print(f"  {i+1}. {user.get('username')} ({user.get('post_count')} posts)")
        
        if "top_categories" in report and report["top_categories"]:
            print("\nMost Active Categories:")
            for i, category in enumerate(report["top_categories"][:3]):
                print(f"  {i+1}. {category.get('name')} ({category.get('topic_count')} topics)")
                
        print("\n===================================")


def main():
    print("Polkadot Forum Analyzer")
    print("=======================")
    
    try:
        # Initialize analyzer
        analyzer = ForumAnalyzer()
        
        # Collect data (with conservative limits)
        print("\nCollecting data...")
        if not analyzer.collect_data(max_categories=5, max_topics_per_category=5, max_topics_details=10):
            print("Data collection failed. Exiting.")
            return
        
        # Analyze the collected data
        print("\nAnalyzing data...")
        report = analyzer.analyze_data()
        if not report:
            print("Analysis failed. Exiting.")
            return
        
        # Create visualization
        print("\nCreating visualization...")
        analyzer.visualize_top_users(report)
        
        # Export the report
        print("\nExporting report...")
        analyzer.export_report(report)
        
        # Print summary
        analyzer.print_summary(report)
        
        print("\nAnalysis completed successfully!")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
