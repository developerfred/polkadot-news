"""
Integration Framework for Polkadot Ecosystem Analysis

A sophisticated orchestration script that synthesizes analyses of the Polkadot forum discourse 
and on-chain governance proposals. The system generates consolidated reports with 
multidimensional community insights and distributes elegantly crafted newsletters.
"""

import os
import sys
import json
import logging
import argparse
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

# Try to import forum analyzer modules
try:
    from polkadot_community_analyzer import PolkadotCommunityAnalyzer
    forum_analyzer_available = True
except ImportError:
    forum_analyzer_available = False

# Try to import governance analyzer
try:
    from polkadot_governance_analyzer import GovernanceAnalyzer
    governance_analyzer_available = True
except ImportError:
    governance_analyzer_available = False

# Try to import newsletter mailer
try:
    from newsletter_mailer import NewsletterMailer
    mailer_available = True
except ImportError:
    mailer_available = False

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("polkadot_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("polkadot_analyzer")

class PolkadotAnalyzerIntegration:
    """Class that integrates Polkadot forum analysis with on-chain governance analysis"""
    
    def __init__(self, 
                 output_dir: str = "polkadot_analysis", 
                 rpc_endpoint: str = "wss://rpc.polkadot.io",
                 subscan_api_key: Optional[str] = None,
                 website_dir: Optional[str] = None,
                 resend_api_key: Optional[str] = None,
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None):
        """
        Initialize the analyzer integration.
        
        Args:
            output_dir: Directory where reports will be saved
            rpc_endpoint: RPC endpoint for connection to Polkadot network
            subscan_api_key: Optional API key for Subscan
            website_dir: Optional directory for website output
            resend_api_key: Optional API key for Resend email service
            supabase_url: Optional URL for Supabase database
            supabase_key: Optional API key for Supabase database
        """
        self.output_dir = output_dir
        self.rpc_endpoint = rpc_endpoint
        self.subscan_api_key = subscan_api_key
        self.website_dir = website_dir
        
        # Create output directories
        try:
            os.makedirs(output_dir, exist_ok=True)
            if governance_analyzer_available:
                os.makedirs(os.path.join(output_dir, "governance"), exist_ok=True)
            if website_dir:
                os.makedirs(website_dir, exist_ok=True)
                os.makedirs(os.path.join(website_dir, "reports"), exist_ok=True)
                os.makedirs(os.path.join(website_dir, "newsletters"), exist_ok=True)
            logger.debug(f"Output directories created in: {output_dir}")
        except Exception as e:
            logger.error(f"Error creating output directories: {str(e)}")
        
        # Initialize analyzers if available
        self.forum_analyzer = None
        self.governance_analyzer = None
        self.newsletter_mailer = None
        
        if forum_analyzer_available:
            try:
                self.forum_analyzer = PolkadotCommunityAnalyzer(delay_between_requests=1.0)
                logger.debug("Forum analyzer initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing forum analyzer: {str(e)}")
        else:
            logger.warning("Forum analyzer not available. Install the polkadot_community_analyzer module.")
        
        if governance_analyzer_available:
            try:
                self.governance_analyzer = GovernanceAnalyzer(rpc_endpoint, subscan_api_key)
                self.governance_analyzer.output_dir = os.path.join(output_dir, "governance")
                logger.debug(f"Governance analyzer initialized with endpoint: {rpc_endpoint}")
            except Exception as e:
                logger.error(f"Error initializing governance analyzer: {str(e)}")
        else:
            logger.warning("Governance analyzer not available. Install the polkadot_governance_analyzer module.")
            
        # Initialize newsletter mailer if available
        if mailer_available:
            try:
                self.newsletter_mailer = NewsletterMailer(
                    resend_api_key=resend_api_key,
                    supabase_url=supabase_url,
                    supabase_key=supabase_key,
                    from_email="Polkadot Newsletter <newsletter@polkadot-community.org>"
                )
                logger.debug("Newsletter mailer initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing newsletter mailer: {str(e)}")
        else:
            logger.warning("Newsletter mailer not available. Install the newsletter_mailer module.")

    # Helper function to safely get values, regardless of format
    def safe_get(self, data, *keys, default=None):
        """
        Tries to get a nested value in a dictionary or complex data structure.
        Accepts multiple keys for deep search and returns a default value if not found.
        """
        current = data
        try:
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, (list, tuple)) and isinstance(key, int) and 0 <= key < len(current):
                    current = current[key]
                else:
                    return default
            return current
        except Exception:
            return default
    
    def save_data(self, data: Dict[str, Any], filename: str, subdir: str = None) -> str:
        """
        Safely saves data to a JSON file, handling NumPy/pandas types.
        
        Args:
            data: Dictionary with data to be saved
            filename: Filename (without .json extension)
            subdir: Optional subdirectory within the output directory
            
        Returns:
            str: Full path to the saved file or None in case of error
        """
        try:
            # Prepare file path
            if subdir:
                save_dir = os.path.join(self.output_dir, subdir)
                os.makedirs(save_dir, exist_ok=True)
            else:
                save_dir = self.output_dir
            
            # Add timestamp and extension to file
            if not filename.endswith('.json'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                full_filename = f"{filename}_{timestamp}.json"
            else:
                full_filename = filename
            
            file_path = os.path.join(save_dir, full_filename)
            
            # Helper function to convert NumPy types to Python native types
            def convert_numpy_types(obj):
                import numpy as np
                
                if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, (dict, dict)):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            
            # Convert data to ensure all NumPy types are converted to native Python types
            data_converted = convert_numpy_types(data)
            
            # Save data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_converted, f, indent=2, default=str)
            
            logger.debug(f"Data successfully saved to: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {str(e)}")
            return None
    
    def _analyze_activity_timeline(self, posts):
        """Analyze activity over time"""
        # This requires timestamp data in posts
        if not posts:
            return None
            
        # Try to extract timestamps from posts
        timestamps = []
        for post in posts:
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
        
        try:
            # Convert to pandas Series for easier analysis
            import pandas as pd
            series = pd.Series(timestamps)
            
            # Group by day
            daily_counts = series.dt.floor('D').value_counts().sort_index()
            
            # Convert to list of date-count pairs
            timeline = []
            for date, count in zip(daily_counts.index, daily_counts.values):
                # Convert pandas Timestamp to string and NumPy values to Python native types
                timeline.append({
                    "date": str(date),
                    "count": int(count)  # Convert numpy.int64 to Python int
                })
            
            return timeline
        except Exception as e:
            logger.error(f"Error analyzing activity timeline: {str(e)}")
            return None

    def run_forum_analysis(self) -> Dict[str, Any]:
        """Runs Polkadot forum analysis"""
        if not self.forum_analyzer:
            logger.error("Forum analyzer not available")
            return {}
        
        logger.info("Starting Polkadot forum analysis...")
        
        try:
            # Collect forum data
            self.forum_analyzer.collect_data(
                max_categories=15,
                max_topics_per_category=20,
                max_topics_details=100
            )
            
            # Analyze data
            report = self.forum_analyzer.analyze()
            
            # Generate visualizations
            self.forum_analyzer.generate_visualizations()
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"forum_analysis_{timestamp}.json")
            
            # Helper function to convert NumPy types to Python native types
            def convert_numpy_types(obj):
                import numpy as np
                
                if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            
            # Convert report to ensure all NumPy types are converted to native Python types
            converted_report = convert_numpy_types(report)
            
            with open(output_path, "w") as f:
                json.dump(converted_report, f, indent=2, default=str)
            
            logger.info(f"Forum analysis completed. Report saved to {output_path}")
            
            # Copy to website directory if available
            if self.website_dir:
                website_path = os.path.join(self.website_dir, "reports", f"forum_analysis_latest.json")
                with open(website_path, "w") as f:
                    json.dump(converted_report, f, indent=2, default=str)
                logger.info(f"Latest forum analysis copied to website: {website_path}")
            
            return converted_report
            
        except Exception as e:
            logger.error(f"Error during forum analysis: {str(e)}")
            traceback.print_exc()
            return {}
    
    def run_governance_analysis(self) -> Dict[str, Any]:
        """Runs on-chain governance analysis"""
        if not self.governance_analyzer:
            logger.error("Governance analyzer not available")
            return {}
        
        logger.info("Starting on-chain governance analysis...")
        
        try:
            # Analyze on-chain proposals
            analysis_results = self.governance_analyzer.analyze_on_chain_proposals()
            
            # Copy to website directory if available
            if self.website_dir and analysis_results:
                website_path = os.path.join(self.website_dir, "reports", "governance_analysis_latest.json")
                with open(website_path, "w") as f:
                    json.dump(analysis_results, f, indent=2, default=str)
                logger.info(f"Latest governance analysis copied to website: {website_path}")
            
            logger.info("Governance analysis completed.")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error during governance analysis: {str(e)}")
            traceback.print_exc()
            return {}
    
    def generate_integrated_report(self, forum_data: Dict[str, Any], governance_data: Dict[str, Any]) -> str:
        """Generates an integrated report with forum and governance data"""
        
        # Helper function to convert NumPy types to Python native types
        def convert_numpy_types(obj):
            try:
                import numpy as np
                
                if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            except ImportError:
                # If numpy is not available, return the object as is
                return obj
                
        forum_data = convert_numpy_types(forum_data)
        governance_data = convert_numpy_types(governance_data)
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # Initialize markdown content
        md_content = f"""
# Polkadot Community Integrated Report - {timestamp}

## Executive Summary

"""
        
        # Add forum information, if available
        if forum_data:
            # Extract some key points from the forum report
            hot_topics = forum_data.get("hot_topics", [])
            trending_keywords = forum_data.get("trending_keywords", [])
            influential_users = forum_data.get("influential_users", [])
            category_activity = forum_data.get("category_activity", [])
            
            # Fix trending keywords formatting, checking if they are dictionaries or tuples
            trending_keywords_text = ""
            if trending_keywords:
                try:
                    if isinstance(trending_keywords[0], dict) and "word" in trending_keywords[0] and "count" in trending_keywords[0]:
                        # Dictionary format with 'word' and 'count' keys
                        trending_keywords_text = ", ".join([f"{kw['word']} ({kw['count']})" for kw in trending_keywords[:5]])
                    elif isinstance(trending_keywords[0], tuple) and len(trending_keywords[0]) >= 2:
                        # Tuple format (word, count)
                        trending_keywords_text = ", ".join([f"{kw[0]} ({kw[1]})" for kw in trending_keywords[:5]])
                    else:
                        # Other format, try to convert to string in the best possible way
                        trending_keywords_text = ", ".join([str(kw) for kw in trending_keywords[:5]])
                except (KeyError, IndexError, TypeError) as e:
                    trending_keywords_text = f"Error processing keywords: {str(e)}"
                    logger.warning(f"Error processing trending_keywords: {str(e)}")
            
            md_content += f"""
### Forum Activity

- **Hot topics**: {len(hot_topics)} high-relevance topics identified
- **Trending keywords**: {trending_keywords_text}
- **Most active categories**: {", ".join([cat["name"] if isinstance(cat, dict) and "name" in cat else str(cat) for cat in category_activity[:3]])}
"""
            
            # Add hot topics
            if hot_topics:
                md_content += "\n#### Hot Topics\n\n"
                for i, topic in enumerate(hot_topics[:5]):
                    md_content += f"{i+1}. **{topic['title']}** - {topic.get('posts_count', 0)} posts, {topic.get('views', 0)} views\n"
            
            # Add influential users
            if influential_users:
                md_content += "\n#### Influential Users\n\n"
                for i, user in enumerate(influential_users[:3]):
                    md_content += f"{i+1}. **{user['username']}** - Influence score: {user['influence_score']}\n"
        
        # Add governance information, if available
        if governance_data:
            referenda = governance_data.get("referenda", [])
            treasury = governance_data.get("treasury", [])
            bounties = governance_data.get("bounties", [])
            
            md_content += f"""
### On-Chain Governance

- **Active referenda**: {len(referenda)}
- **Treasury proposals**: {len(treasury)}
- **Active bounties**: {len(bounties)}
- **High-risk proposals**: {governance_data.get("summary", {}).get("high_risk_count", 0)}
"""
            
            # Add referenda by risk level
            if referenda:
                # Group by risk level
                risk_groups = {}
                for ref in referenda:
                    risk_level = ref["risk_analysis"]["risk_level"]
                    if risk_level not in risk_groups:
                        risk_groups[risk_level] = []
                    risk_groups[risk_level].append(ref)
                
                md_content += "\n#### Referenda by Risk Level\n\n"
                
                for risk_level in ["critical", "high", "medium", "low"]:
                    refs = risk_groups.get(risk_level, [])
                    if refs:
                        md_content += f"**{risk_level.upper()}** ({len(refs)}): "
                        md_content += ", ".join([f"#{ref['data']['index']}" for ref in refs])
                        md_content += "\n\n"
                
                # Add details of high-risk referenda
                high_risk_refs = risk_groups.get("critical", []) + risk_groups.get("high", [])
                if high_risk_refs:
                    md_content += "\n#### High-Risk Referenda\n\n"
                    for ref in high_risk_refs:
                        data = ref["data"]
                        
                        # Extract proposal details
                        proposal_details = "Unable to decode proposal"
                        if "proposal" in data and "decodedCall" in data["proposal"]:
                            decoded = data["proposal"]["decodedCall"]
                            section = decoded.get("section", "Unknown")
                            method = decoded.get("method", "Unknown")
                            proposal_details = f"{section}.{method}"
                        
                        md_content += f"""
##### Referendum #{data['index']} - {proposal_details}

- **Track**: {data['track'].get('name', data['track'].get('id', 'Unknown'))}
- **Risk Level**: {ref['risk_analysis']['risk_level'].upper()}
- **Risk Factors**: {', '.join([f"{f['pattern']}" for f in ref['risk_analysis']['risk_factors']])}
- **Main Recommendations**: 
  - {ref['risk_analysis']['recommendations'][0] if ref['risk_analysis']['recommendations'] else 'N/A'}
  - {ref['risk_analysis']['recommendations'][1] if len(ref['risk_analysis']['recommendations']) > 1 else ''}

"""
        
        # Add correlations and insights, if both data types are available
        if forum_data and governance_data:
            md_content += """
## Correlation between Forum and Governance

### Forum Topics related to Active Referenda
"""
            
            # Check for matches between forum topics and referenda
            forum_referendum_matches = []
            
            for ref in governance_data.get("referenda", []):
                ref_id = ref["data"]["index"]
                if "forum_data" in ref:
                    for forum_topic in ref["forum_data"]:
                        forum_referendum_matches.append({
                            "referendum_id": ref_id,
                            "topic_title": forum_topic["title"],
                            "posts_count": forum_topic.get("posts_count", 0),
                            "views": forum_topic.get("views", 0),
                            "url": forum_topic.get("url", "")
                        })
            
            if forum_referendum_matches:
                for match in forum_referendum_matches:
                    md_content += f"- **Referendum #{match['referendum_id']}**: [{match['topic_title']}]({match['url']}) - {match['posts_count']} posts, {match['views']} views\n"
            else:
                md_content += "No direct match found between forum topics and active referenda.\n"
            
            # Check if trending keywords appear in governance proposals
            # Adapt to work with both dictionaries and tuples
            trending_keywords = []
            if forum_data.get("trending_keywords", []):
                if isinstance(forum_data["trending_keywords"][0], dict):
                    trending_keywords = [kw["word"] for kw in forum_data["trending_keywords"]]
                elif isinstance(forum_data["trending_keywords"][0], tuple):
                    trending_keywords = [kw[0] for kw in forum_data["trending_keywords"]]
            
            md_content += "\n### Trending Keywords found in Proposals\n\n"
            
            keyword_matches = []
            
            for ref in governance_data.get("referenda", []):
                if "proposal" in ref["data"] and "decodedCall" in ref["data"]["proposal"]:
                    decoded = ref["data"]["proposal"]["decodedCall"]
                    proposal_text = f"{decoded.get('section', '')} {decoded.get('method', '')}"
                    
                    # Check arguments
                    args = decoded.get("args", {})
                    if isinstance(args, dict):
                        for key, value in args.items():
                            proposal_text += f" {key} {value}"
                    
                    # Check if any keyword appears in the proposal
                    for keyword in trending_keywords:
                        if keyword.lower() in proposal_text.lower():
                            keyword_matches.append({
                                "keyword": keyword,
                                "referendum_id": ref["data"]["index"],
                                "proposal_text": proposal_text
                            })
            
            if keyword_matches:
                for match in keyword_matches:
                    md_content += f"- **{match['keyword']}** found in Referendum #{match['referendum_id']}: {match['proposal_text']}\n"
            else:
                md_content += "No trending keyword was found in active governance proposals.\n"
        
        # Add recommendations and next steps
        md_content += """
## Recommendations and Next Steps

1. **Closely monitor high-risk referenda** - Ensure detailed technical review
2. **Promote discussion in under-represented topics** - Identify areas with low participation
3. **Engage influential users in governance debates** - Request feedback on critical proposals
4. **Track high-value treasury proposals** - Verify justifications and expected benefits
5. **Observe voting patterns** - Analyze vote distribution across different tracks

"""
        
        # Save markdown report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"integrated_report_{timestamp}.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        # Save to website directory if available
        if self.website_dir:
            website_path = os.path.join(self.website_dir, "reports", "integrated_report_latest.md")
            with open(website_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            
            # Also save as index.md for the website root
            index_path = os.path.join(self.website_dir, "index.md")
            with open(index_path, "w", encoding="utf-8") as f:
                # Add Jekyll front matter for GitHub Pages
                f.write("---\n")
                f.write("layout: default\n")
                f.write(f"title: Polkadot Community Report - {timestamp}\n")
                f.write("---\n\n")
                f.write(md_content)
            
            logger.info(f"Latest integrated report copied to website: {website_path}")
        
        logger.info(f"Integrated report generated at {output_file}")
        return output_file
        
    def _generate_community_summary(self, forum_data: Dict[str, Any], governance_data: Dict[str, Any]) -> str:
        """Generates a community activity summary for the newsletter"""
        summary = ""
        
        if forum_data:
            try:
                # Get most active categories safely
                categories = []
                if "category_activity" in forum_data and forum_data["category_activity"]:
                    for cat in forum_data["category_activity"][:3]:
                        if isinstance(cat, dict) and "name" in cat:
                            categories.append(cat["name"])
                        elif isinstance(cat, (list, tuple)) and len(cat) > 0:
                            categories.append(str(cat[0]))
                        else:
                            categories.append(str(cat))
                
                if categories:
                    summary += f"The Polkadot community had high activity in the categories {', '.join(categories)}. "
                
                total_topics = len(forum_data.get("topics", []))
                total_posts = len(forum_data.get("posts", []))
                unique_users = len(forum_data.get("user_activity", {}))
                
                summary += f"The Polkadot forum had {total_topics} active topics with {total_posts} posts from {unique_users} distinct users. "
                
                hot_topics_count = len(forum_data.get("hot_topics", []))
                summary += f"There are {hot_topics_count} hot topics currently under discussion. "
            except Exception as e:
                logger.warning(f"Error processing forum data for summary: {str(e)}")
        
        if governance_data:
            try:
                referenda_count = len(governance_data.get("referenda", []))
                high_risk_count = self.safe_get(governance_data, "summary", "high_risk_count", default=0)
                
                summary += f"There are {referenda_count} active referenda at the moment, "
                
                if high_risk_count > 0:
                    summary += f"with {high_risk_count} classified as high-risk. "
                else:
                    summary += "all with moderate or low risk levels. "
                
                treasury_count = len(governance_data.get("treasury", []))
                if treasury_count > 0:
                    summary += f"There are also {treasury_count} treasury proposals in progress. "
            except Exception as e:
                logger.warning(f"Error processing governance data for summary: {str(e)}")
        
        if not summary:
            summary = "The Polkadot community maintains regular activity in the forum and on-chain governance proposals."
        
        return summary
    
    def _extract_important_posts(self, forum_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts the most important forum posts for the newsletter"""
        if not forum_data:
            return []
        
        results = []
        hot_topics = forum_data.get("hot_topics", [])
        
        for topic in hot_topics[:10]:
            try:
                post_info = {
                    "title": self.safe_get(topic, "title", default="No title"),
                    "author": self.safe_get(topic, "author", default="Unknown"),
                    "date": self.safe_get(topic, "created_at", default=""),
                    "views": self.safe_get(topic, "views", default=0),
                    "replies": max(0, self.safe_get(topic, "posts_count", default=1) - 1),
                    "url": self.safe_get(topic, "url", default=""),
                    "summary": self.safe_get(topic, "excerpt", default="No summary available")
                }
                results.append(post_info)
            except Exception as e:
                logger.warning(f"Error processing important topic: {str(e)}")
        
        return results
    
    def _extract_governance_proposals(self, governance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts governance proposals for the newsletter"""
        if not governance_data:
            return []
        
        proposals = []
        
        # Add high-risk referenda first
        for ref in governance_data.get("referenda", []):
            try:
                risk_level = self.safe_get(ref, "risk_analysis", "risk_level", default="unknown")
                
                if risk_level in ["high", "critical"]:
                    data = ref.get("data", {})
                    index = self.safe_get(data, "index", default="?")
                    
                    # Extract proposal details safely
                    proposal_details = "Unable to decode proposal"
                    decoded = self.safe_get(data, "proposal", "decodedCall", default={})
                    
                    if decoded:
                        section = self.safe_get(decoded, "section", default="Unknown")
                        method = self.safe_get(decoded, "method", default="Unknown")
                        proposal_details = f"{section}.{method}"
                    
                    track_name = self.safe_get(data, "track", "name", default=self.safe_get(data, "track", "id", default="Unknown"))
                    submitted_at = self.safe_get(data, "status", "submittedAt", default="")
                    
                    proposals.append({
                        "title": f"Referendum #{index} - {proposal_details}",
                        "date": submitted_at,
                        "views": 0,  # Not available for on-chain referenda
                        "url": f"https://polkadot.polkassembly.io/referenda/{index}",
                        "summary": f"Risk Level: {risk_level.upper()}. Track: {track_name}."
                    })
            except Exception as e:
                logger.warning(f"Error processing referendum: {str(e)}")
        
        # Add some high-value treasury proposals
        try:
            # Sort treasury proposals by value, with error handling
            treasury_proposals = []
            for proposal in governance_data.get("treasury", []):
                try:
                    data = proposal.get("data", {})
                    value = self.safe_get(data, "value", default="0")
                    # Convert to int with validation
                    try:
                        value_int = int(value)
                    except (ValueError, TypeError):
                        value_int = 0
                    
                    treasury_proposals.append((proposal, value_int))
                except Exception as e:
                    logger.warning(f"Error processing treasury proposal for sorting: {str(e)}")
            
            # Sort and take top 3
            treasury_proposals.sort(key=lambda x: x[1], reverse=True)
            
            for proposal_tuple in treasury_proposals[:3]:
                proposal = proposal_tuple[0]
                try:
                    data = proposal.get("data", {})
                    proposal_id = self.safe_get(data, "id", default="?")
                    beneficiary = self.safe_get(data, "beneficiary", default="Unknown")
                    value = self.safe_get(data, "value", default="0")
                    risk_level = self.safe_get(proposal, "risk_analysis", "risk_level", default="unknown")
                    
                    # Convert value to DOT for better readability
                    try:
                        value_dot = float(value) / 10**10
                    except (ValueError, TypeError):
                        value_dot = 0
                    
                    proposals.append({
                        "title": f"Treasury Proposal #{proposal_id} - {value_dot:.2f} DOT",
                        "date": "",  # Not directly available
                        "views": 0,  # Not available
                        "url": f"https://polkadot.polkassembly.io/treasury/{proposal_id}",
                        "summary": f"Beneficiary: {beneficiary}. Risk Level: {risk_level.upper()}."
                    })
                except Exception as e:
                    logger.warning(f"Error processing treasury proposal details: {str(e)}")
        except Exception as e:
            logger.warning(f"Error processing treasury proposals: {str(e)}")
        
        return proposals[:5]  # Limit to 5 proposals total
    
    def create_newsletter(self, 
                          forum_data: Dict[str, Any], 
                          governance_data: Dict[str, Any],
                          test_mode: bool = False) -> Optional[str]:
        """
        Creates a newsletter based on analyzed data and sends it to subscribers
        
        Args:
            forum_data: Analyzed forum data
            governance_data: Analyzed governance data
            test_mode: If True, send newsletter only to first subscriber
            
        Returns:
            Path to the generated newsletter HTML file, or None if failed
        """
        if not mailer_available or not self.newsletter_mailer:
            logger.error("Newsletter mailer not available")
            return None
        
        try:
            # Check trending_keywords format and adapt as needed
            trending_keywords = []
            if forum_data and "trending_keywords" in forum_data and forum_data["trending_keywords"]:
                try:
                    sample_kw = forum_data["trending_keywords"][0]
                    
                    if isinstance(sample_kw, dict) and "word" in sample_kw and "count" in sample_kw:
                        # Already in expected dictionary format
                        trending_keywords = forum_data["trending_keywords"][:15]
                    elif isinstance(sample_kw, tuple) and len(sample_kw) >= 2:
                        # Convert from tuples to dictionaries
                        trending_keywords = [{"word": kw[0], "count": kw[1]} 
                                            for kw in forum_data["trending_keywords"][:15]]
                    else:
                        # Other format, try to adapt in the best possible way
                        trending_keywords = [{"word": str(kw), "count": 1} 
                                            for kw in forum_data["trending_keywords"][:15]]
                except Exception as e:
                    logger.warning(f"Error processing trending_keywords for newsletter: {str(e)}")
            
            # Prepare data for newsletter
            today = datetime.now().strftime("%B %d, %Y")
            newsletter_data = {
                "title": f"Polkadot Forum Digest - {today}",
                "date": today,
                "community_summary": self._generate_community_summary(forum_data, governance_data),
                "important_posts": self._extract_important_posts(forum_data),
                "governance_proposals": self._extract_governance_proposals(governance_data),
                "trending_keywords": trending_keywords,
                "unsubscribe_link": "#unsubscribe"
            }
            
            # Generate newsletter HTML using template
            html_content = self._generate_newsletter_html(newsletter_data)
            
            # Save newsletter to output directory
            timestamp = datetime.now().strftime("%Y%m%d")
            newsletter_path = os.path.join(self.output_dir, f"newsletter_{timestamp}.html")
            with open(newsletter_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"Newsletter HTML saved to {newsletter_path}")
            
            # Save to website directory if available
            if self.website_dir:
                website_path = os.path.join(self.website_dir, "newsletters", f"newsletter_{timestamp}.html")
                latest_path = os.path.join(self.website_dir, "newsletters", "newsletter_latest.html")
                
                with open(website_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                # Also save as latest.html
                with open(latest_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                logger.info(f"Newsletter copied to website: {website_path}")
            
            # Send newsletter to subscribers
            subject = f"Polkadot Community Digest - {datetime.now().strftime('%Y-%m-%d')}"
            results = self.newsletter_mailer.send_newsletter(subject, html_content, test_mode)
            
            if results['sent'] > 0:
                logger.info(f"Newsletter sent to {results['sent']} subscribers (failed: {results['failed']})")
            else:
                logger.warning(f"No newsletters were sent to subscribers. Check for errors.")
            
            return newsletter_path
            
        except Exception as e:
            logger.error(f"Error creating or sending newsletter: {str(e)}")
            traceback.print_exc()
            return None
    
    def _generate_newsletter_html(self, data: Dict[str, Any]) -> str:
        """Generates HTML content for the newsletter"""
        # Basic HTML template
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['title']}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #E6007A;
            padding-bottom: 10px;
        }}
        .logo {{
            max-width: 150px;
        }}
        .date {{
            color: #666;
            font-style: italic;
        }}
        h1 {{
            color: #E6007A;
        }}
        h2 {{
            color: #172026;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
            margin-top: 25px;
        }}
        .post {{
            margin-bottom: 25px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
        .post-title {{
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 5px;
        }}
        .post-meta {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }}
        .post-summary {{
            margin-bottom: 10px;
        }}
        .post-link {{
            display: inline-block;
            margin-top: 10px;
            color: #E6007A;
            text-decoration: none;
            font-weight: bold;
        }}
        .post-link:hover {{
            text-decoration: underline;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 14px;
            color: #666;
            text-align: center;
        }}
        .unsubscribe {{
            color: #999;
            font-size: 12px;
        }}
        .trending-keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
        }}
        .keyword {{
            background-color: #E6007A20;
            color: #E6007A;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 14px;
        }}
        .governance-item {{
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px dashed #ddd;
        }}
        .summary-box {{
            background-color: #f0f0f0;
            border-left: 4px solid #E6007A;
            padding: 15px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{data['title']}</h1>
        <p class="date">{data['date']}</p>
    </div>

    {self._render_community_summary_section(data)}
    {self._render_trending_keywords_section(data)}
    {self._render_important_posts_section(data)}
    {self._render_governance_section(data)}

    <div class="footer">
        <p>Polkadot Forum Digest</p>
        <p class="unsubscribe">If you no longer wish to receive these communications, <a href="{data['unsubscribe_link']}">click here to unsubscribe</a>.</p>
    </div>
</body>
</html>"""
        return html
    
    def _render_community_summary_section(self, data: Dict[str, Any]) -> str:
        """Renders the community summary section of the newsletter"""
        if not data.get('community_summary'):
            return ""
            
        return f"""
    <div class="section">
        <h2>Community Summary</h2>
        <div class="summary-box">
            <p>{data['community_summary']}</p>
        </div>
    </div>
    """
    
    def _render_trending_keywords_section(self, data: Dict[str, Any]) -> str:
        """Renders the trending keywords section of the newsletter"""
        if not data.get('trending_keywords'):
            return ""
            
        keywords_html = ""
        for kw in data['trending_keywords']:
            word = kw.get('word', str(kw)) if isinstance(kw, dict) else kw[0] if isinstance(kw, tuple) else str(kw)
            count = kw.get('count', 1) if isinstance(kw, dict) else kw[1] if isinstance(kw, tuple) else 1
            keywords_html += f"""
            <span class="keyword">{word} ({count})</span>
            """
            
        return f"""
    <div class="section">
        <h2>Trending Topics</h2>
        <div class="trending-keywords">
            {keywords_html}
        </div>
    </div>
    """
    
    def _render_important_posts_section(self, data: Dict[str, Any]) -> str:
        """Renders the important posts section of the newsletter"""
        if not data.get('important_posts'):
            return ""
            
        posts_html = ""
        for post in data['important_posts']:
            posts_html += f"""
        <div class="post">
            <div class="post-title">{post['title']}</div>
            <div class="post-meta">
                By <strong>{post['author']}</strong> on {post['date']} | 
                {post['views']} views | {post['replies']} replies
            </div>
            <div class="post-summary">{post['summary']}</div>
            <a href="{post['url']}" class="post-link">Read more »</a>
        </div>
        """
            
        return f"""
    <div class="section">
        <h2>Key Posts of the Week</h2>
        {posts_html}
    </div>
    """
    
    def _render_governance_section(self, data: Dict[str, Any]) -> str:
        """Renders the governance proposals section of the newsletter"""
        if not data.get('governance_proposals'):
            return ""
            
        proposals_html = ""
        for proposal in data['governance_proposals']:
            proposals_html += f"""
        <div class="governance-item">
            <div class="post-title">{proposal['title']}</div>
            <div class="post-meta">Created on {proposal['date']} | {proposal['views']} views</div>
            <div class="post-summary">{proposal['summary']}</div>
            <a href="{proposal['url']}" class="post-link">View complete proposal »</a>
        </div>
        """
            
        return f"""
    <div class="section">
        <h2>Active Governance Proposals</h2>
        {proposals_html}
    </div>
    """
    
    def run_complete_analysis(self, send_newsletter: bool = False, test_mode: bool = False) -> Dict[str, str]:
        """
        Runs complete forum and governance analysis, generating integrated reports and newsletters
        
        Args:
            send_newsletter: Whether to send the newsletter to subscribers
            test_mode: If True, send newsletter only to the first subscriber
            
        Returns:
            Dict with paths to generated reports and newsletters
        """
        results = {}
        
        # Analyze forum data
        forum_data = {}
        if self.forum_analyzer:
            try:
                logger.info("Starting forum analysis...")
                forum_data = self.run_forum_analysis()
                if forum_data:
                    timestamp = datetime.now().strftime("%Y%m%d")
                    results["forum_analysis"] = os.path.join(
                        self.output_dir, 
                        f"forum_analysis_{timestamp}.json"
                    )
                    logger.info(f"Forum analysis completed successfully.")
            except Exception as e:
                logger.error(f"Error during forum analysis: {str(e)}")
                traceback.print_exc()
        else:
            logger.warning("Forum analyzer not available, skipping forum analysis")
        
        # Analyze governance data
        governance_data = {}
        if self.governance_analyzer:
            try:
                logger.info("Starting governance analysis...")
                governance_data = self.run_governance_analysis()
                if governance_data:
                    timestamp = datetime.now().strftime("%Y%m%d")
                    results["governance_analysis"] = os.path.join(
                        self.output_dir, 
                        "governance", 
                        f"governance_analysis_{timestamp}.json"
                    )
                    logger.info(f"Governance analysis completed successfully.")
            except Exception as e:
                logger.error(f"Error during governance analysis: {str(e)}")
                traceback.print_exc()
        else:
            logger.warning("Governance analyzer not available, skipping governance analysis")
        
        # Generate integrated report if data is available
        integrated_report = None
        if forum_data or governance_data:
            try:
                logger.info("Generating integrated report...")
                integrated_report = self.generate_integrated_report(forum_data, governance_data)
                if integrated_report:
                    results["integrated_report"] = integrated_report
                    logger.info(f"Integrated report generated successfully.")
            except Exception as e:
                logger.error(f"Error generating integrated report: {str(e)}")
                traceback.print_exc()
        else:
            logger.warning("No data available to generate integrated report")
        
        # Create and send newsletter, if requested
        if (send_newsletter or test_mode) and (forum_data or governance_data) and mailer_available and self.newsletter_mailer:
            try:
                logger.info(f"Creating newsletter (test mode: {test_mode})...")
                newsletter_path = self.create_newsletter(forum_data, governance_data, test_mode=test_mode)
                if newsletter_path:
                    results["newsletter"] = newsletter_path
                    logger.info(f"Newsletter created and sent successfully.")
            except Exception as e:
                logger.error(f"Error creating or sending newsletter: {str(e)}")
                traceback.print_exc()
        elif send_newsletter and not (mailer_available and self.newsletter_mailer):
            logger.warning("Newsletter mailer not available, skipping newsletter creation")
        
        return results