"""
Polkadot Newsletter Mailer

A sophisticated module for newsletter distribution leveraging the Resend API for email delivery
and Supabase for comprehensive subscriber management.
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import resend
from supabase import create_client, Client

# Configure logger
logger = logging.getLogger("polkadot_mailer")

class NewsletterMailer:
    """Advanced class for orchestrating newsletter distribution via Resend and comprehensive subscriber management via Supabase"""
    
    def __init__(self, 
                 resend_api_key: Optional[str] = None,
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None,
                 from_email: str = "Polkadot Community <newsletter@polkadot-community.org>"):
        """
        Initialize the newsletter distribution system
        
        Args:
            resend_api_key: Authentication token for Resend service (defaults to RESEND_API_KEY environment variable)
            supabase_url: Supabase project URL (defaults to SUPABASE_URL environment variable)
            supabase_key: Supabase authentication key (defaults to SUPABASE_KEY environment variable)
            from_email: Sender's email address and display name
        """
        # Set up Resend
        self.resend_api_key = resend_api_key or os.environ.get("RESEND_API_KEY")
        if not self.resend_api_key:
            logger.warning("Resend API key not provided. Email sending will be disabled.")
        else:
            resend.api_key = self.resend_api_key
        
        # Set up Supabase
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_KEY")
        self.supabase = None
        
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
        else:
            logger.warning("Supabase credentials not provided. Subscriber management will be disabled.")
        
        self.from_email = from_email
    
    def get_subscribers(self) -> List[Dict[str, Any]]:
        """
        Retrieve the comprehensive collection of active subscribers from the Supabase database
        
        Returns:
            Detailed list of subscriber records, each containing at minimum an 'email' identifier
        """
        if not self.supabase:
            logger.warning("Supabase client not initialized. Returning empty subscribers list.")
            return []
        
        try:
            response = self.supabase.table('subscribers').select('*').eq('status', 'active').execute()
            subscribers = response.data
            logger.info(f"Retrieved {len(subscribers)} active subscribers from Supabase")
            return subscribers
        except Exception as e:
            logger.error(f"Failed to retrieve subscribers from Supabase: {e}")
            return []
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Dispatch an individual email communication utilizing the Resend delivery service
        
        Args:
            to_email: Recipient's electronic mail address
            subject: Email subject line that encapsulates the message's purpose
            html_content: Rich HTML-formatted content body of the email
            
        Returns:
            Boolean indicator of transmission success (True) or failure (False)
        """
        if not self.resend_api_key:
            logger.warning("Resend API key not set. Cannot send email.")
            return False
        
        try:
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            
            if response and "id" in response:
                logger.info(f"Email sent successfully to {to_email}, ID: {response['id']}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}, response: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def send_newsletter(self, subject: str, html_content: str, test_mode: bool = False) -> Dict[str, Any]:
        """
        Send newsletter to subscribers
        
        Args:
            subject: Email subject
            html_content: HTML content of the email
            test_mode: If True, send only to the first subscriber
            
        Returns:
            Dict with results: {'sent': count, 'failed': count, 'total': count}
        """
        subscribers = self.get_subscribers()
        
        if not subscribers:
            logger.warning("No subscribers found. Newsletter not sent.")
            return {'sent': 0, 'failed': 0, 'total': 0}
        
        # In test mode, only use the first subscriber
        if test_mode and subscribers:
            subscribers = [subscribers[0]]
            logger.info(f"Test mode enabled. Sending only to: {subscribers[0]['email']}")
        
        sent_count = 0
        failed_count = 0
        
        for subscriber in subscribers:
            if self.send_email(subscriber['email'], subject, html_content):
                sent_count += 1
            else:
                failed_count += 1
        
        results = {
            'sent': sent_count,
            'failed': failed_count,
            'total': len(subscribers)
        }
        
        logger.info(f"Newsletter sending completed. Results: {results}")
        return results
    
    def add_subscriber(self, email: str, name: Optional[str] = None) -> bool:
        """
        Add a new subscriber to the database
        
        Args:
            email: Email address to add
            name: Optional subscriber name
            
        Returns:
            True if successful, False otherwise
        """
        if not self.supabase:
            logger.warning("Supabase client not initialized. Cannot add subscriber.")
            return False
        
        try:
            # Check if email already exists
            response = self.supabase.table('subscribers').select('*').eq('email', email).execute()
            
            if response.data:
                # Email exists, update status to active if needed
                existing = response.data[0]
                if existing['status'] != 'active':
                    update_response = self.supabase.table('subscribers').update(
                        {'status': 'active', 'updated_at': datetime.now().isoformat()}
                    ).eq('id', existing['id']).execute()
                    logger.info(f"Re-activated subscriber: {email}")
                else:
                    logger.info(f"Subscriber already exists and is active: {email}")
                return True
            
            # Insert new subscriber
            data = {
                'email': email,
                'name': name or '',
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            insert_response = self.supabase.table('subscribers').insert(data).execute()
            logger.info(f"Added new subscriber: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add subscriber {email}: {e}")
            return False
    
    def remove_subscriber(self, email: str) -> bool:
        """
        Remove (deactivate) a subscriber from the database
        
        Args:
            email: Email address to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not self.supabase:
            logger.warning("Supabase client not initialized. Cannot remove subscriber.")
            return False
        
        try:
            # Update status to 'unsubscribed'
            update_response = self.supabase.table('subscribers').update(
                {'status': 'unsubscribed', 'updated_at': datetime.now().isoformat()}
            ).eq('email', email).execute()
            
            if update_response.data:
                logger.info(f"Removed subscriber: {email}")
                return True
            else:
                logger.warning(f"No subscriber found with email: {email}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove subscriber {email}: {e}")
            return False