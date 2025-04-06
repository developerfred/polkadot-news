"""
Polkadot Forum Mailer

A module to generate and send periodic newsletters with summaries of the most important posts
from the Polkadot forum. Integrates with the community analyzer to identify relevant content.
"""

import os
import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import pandas as pd
import markdown
import requests
from bs4 import BeautifulSoup
import configparser
import logging
from jinja2 import Template
import html2text

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("forum_mailer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("polkadot_mailer")

# Constants
BASE_URL = "https://forum.polkadot.network"
DEFAULT_TEMPLATE_PATH = "templates/newsletter_template.html"
CONFIG_FILE = "mailer_config.ini"

class PolkadotForumMailer:
    def __init__(self, analyzer=None, config_file=CONFIG_FILE):
        """
        Initializes the newsletter generator
        
        Args:
            analyzer: An optional instance of PolkadotCommunityAnalyzer
            config_file: Path to the configuration file
        """
        self.analyzer = analyzer
        self.config_file = config_file
        self.subscribers = []
        self.last_run = None
        self.config = self._load_config()
        self.templates_dir = "templates"
        
        # Ensure the templates directory exists
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            self._create_default_template()
    
    def _load_config(self):
        """Load configurations from the configuration file"""
        config = configparser.ConfigParser()
        
        # Create default configuration if it doesn't exist
        if not os.path.exists(self.config_file):
            logger.info(f"Configuration file not found. Creating {self.config_file}")
            config['Email'] = {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': '587',
                'smtp_username': 'your_email@gmail.com',
                'smtp_password': 'your_app_password',
                'from_name': 'Polkadot Forum Digest',
                'from_email': 'your_email@gmail.com',
            }
            config['Settings'] = {
                'frequency': 'weekly',  # weekly, daily, monthly
                'max_posts': '10',
                'include_proposals': 'true',
                'include_trending': 'true',
                'include_summary': 'true',
            }
            config['Subscribers'] = {
                'subscribers_file': 'subscribers.csv',
            }
            
            with open(self.config_file, 'w') as f:
                config.write(f)
        else:
            config.read(self.config_file)
        
        return config
    
    def _create_default_template(self):
        """Create a default HTML template for the newsletter"""
        default_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #E6007A;
            padding-bottom: 10px;
        }
        .logo {
            max-width: 150px;
        }
        .date {
            color: #666;
            font-style: italic;
        }
        h1 {
            color: #E6007A;
        }
        h2 {
            color: #172026;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
            margin-top: 25px;
        }
        .post {
            margin-bottom: 25px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .post-title {
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 5px;
        }
        .post-meta {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        .post-summary {
            margin-bottom: 10px;
        }
        .post-link {
            display: inline-block;
            margin-top: 10px;
            color: #E6007A;
            text-decoration: none;
            font-weight: bold;
        }
        .post-link:hover {
            text-decoration: underline;
        }
        .section {
            margin-bottom: 30px;
        }
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 14px;
            color: #666;
            text-align: center;
        }
        .unsubscribe {
            color: #999;
            font-size: 12px;
        }
        .trending-keywords {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
        }
        .keyword {
            background-color: #E6007A20;
            color: #E6007A;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 14px;
        }
        .governance-item {
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px dashed #ddd;
        }
        .summary-box {
            background-color: #f0f0f0;
            border-left: 4px solid #E6007A;
            padding: 15px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p class="date">{{ date }}</p>
    </div>

    {% if community_summary %}
    <div class="section">
        <h2>Community Summary</h2>
        <div class="summary-box">
            <p>{{ community_summary }}</p>
        </div>
    </div>
    {% endif %}

    {% if trending_keywords %}
    <div class="section">
        <h2>Trending Topics</h2>
        <div class="trending-keywords">
            {% for keyword in trending_keywords %}
            <span class="keyword">{{ keyword.word }} ({{ keyword.count }})</span>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    {% if important_posts %}
    <div class="section">
        <h2>Important Posts of the Week</h2>
        {% for post in important_posts %}
        <div class="post">
            <div class="post-title">{{ post.title }}</div>
            <div class="post-meta">
                By <strong>{{ post.author }}</strong> on {{ post.date }} | 
                {{ post.views }} views | {{ post.replies }} replies
            </div>
            <div class="post-summary">{{ post.summary }}</div>
            <a href="{{ post.url }}" class="post-link">Read more »</a>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if governance_proposals %}
    <div class="section">
        <h2>Active Governance Proposals</h2>
        {% for proposal in governance_proposals %}
        <div class="governance-item">
            <div class="post-title">{{ proposal.title }}</div>
            <div class="post-meta">Created on {{ proposal.date }} | {{ proposal.views }} views</div>
            <div class="post-summary">{{ proposal.summary }}</div>
            <a href="{{ proposal.url }}" class="post-link">View full proposal »</a>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="footer">
        <p>Polkadot Forum Digest</p>
        <p class="unsubscribe">If you no longer wish to receive these emails, <a href="{{ unsubscribe_link }}">click here to unsubscribe</a>.</p>
    </div>
</body>
</html>
"""
        template_path = os.path.join(self.templates_dir, "newsletter_template.html")
        with open(template_path, 'w') as f:
            f.write(default_template)
        
        logger.info(f"Default template created at {template_path}")
    
