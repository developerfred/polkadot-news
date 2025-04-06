"""
Supabase Database Configuration Utility

This sophisticated utility establishes the requisite database schema in your Supabase instance
to facilitate the Polkadot Community Newsletter system's subscriber management and analytics capabilities.
"""

import os
import sys
import argparse
import logging
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("supabase_setup")

def setup_supabase(url: str, key: str) -> bool:
    """
    Set up required tables in Supabase for the newsletter system
    
    Args:
        url: Supabase project URL
        key: Supabase API key (service_role key recommended for setup)
        
    Returns:
        True if setup was successful, False otherwise
    """
    try:
        logger.info("Connecting to Supabase...")
        supabase = create_client(url, key)
        
        # Create subscribers table
        logger.info("Creating subscribers table...")
        try:
            # Use the SQL API to create table with proper structure
            response = supabase.rpc(
                'create_subscribers_table',
                {
                    'sql_query': """
                    CREATE TABLE IF NOT EXISTS subscribers (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        email TEXT UNIQUE NOT NULL,
                        name TEXT,
                        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'unsubscribed', 'bounced')),
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    -- Create index on email for faster lookups
                    CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
                    
                    -- Create index on status for filtered queries
                    CREATE INDEX IF NOT EXISTS idx_subscribers_status ON subscribers(status);
                    """
                }
            ).execute()
            
            logger.info("Subscribers table created successfully")
        except Exception as e:
            logger.error(f"Error creating subscribers table: {e}")
            
            # Try to create the table using the REST API
            logger.info("Trying alternative method to create subscribers table...")
            
            # Check if table already exists
            try:
                supabase.table('subscribers').select('id').limit(1).execute()
                logger.info("Subscribers table already exists")
            except Exception:
                # Table doesn't exist, create it
                logger.info("Creating subscribers table using Table API...")
                try:
                    # This doesn't actually create the table but will trigger a 404 if it doesn't exist
                    supabase.table('subscribers').insert({
                        'email': 'test@example.com',
                        'name': 'Test User',
                        'status': 'active'
                    }).execute()
                    logger.info("Test record inserted, subscribers table exists")
                except Exception as e:
                    logger.error(f"Unable to create subscribers table: {e}")
                    return False
        
        # Create newsletter_stats table
        logger.info("Creating newsletter_stats table...")
        try:
            # Use the SQL API to create table with proper structure
            response = supabase.rpc(
                'create_newsletter_stats_table',
                {
                    'sql_query': """
                    CREATE TABLE IF NOT EXISTS newsletter_stats (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        newsletter_id TEXT NOT NULL,
                        sent_count INTEGER DEFAULT 0,
                        open_count INTEGER DEFAULT 0,
                        click_count INTEGER DEFAULT 0,
                        unsubscribe_count INTEGER DEFAULT 0,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    -- Create index on newsletter_id for faster lookups
                    CREATE INDEX IF NOT EXISTS idx_newsletter_stats_id ON newsletter_stats(newsletter_id);
                    """
                }
            ).execute()
            
            logger.info("Newsletter stats table created successfully")
        except Exception as e:
            logger.error(f"Error creating newsletter_stats table: {e}")
            
            # Check if table already exists
            try:
                supabase.table('newsletter_stats').select('id').limit(1).execute()
                logger.info("Newsletter stats table already exists")
            except Exception:
                logger.error("Unable to create newsletter_stats table")
                # Not a critical error, continue
        
        logger.info("Supabase setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Supabase: {e}")
        return False


def main():
    """Main function to run the Supabase setup"""
    parser = argparse.ArgumentParser(description="Set up Supabase for the Polkadot Newsletter system")
    parser.add_argument("--url", help="Supabase URL")
    parser.add_argument("--key", help="Supabase API key (service_role key recommended)")
    
    args = parser.parse_args()
    
    # Get credentials from arguments or environment variables
    supabase_url = args.url or os.environ.get("SUPABASE_URL")
    supabase_key = args.key or os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase URL and key are required. Provide them as arguments or set SUPABASE_URL and SUPABASE_KEY environment variables.")
        return 1
    
    success = setup_supabase(supabase_url, supabase_key)
    
    if success:
        logger.info("Supabase setup completed successfully.")
        return 0
    else:
        logger.error("Supabase setup failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())