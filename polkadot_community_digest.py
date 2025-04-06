"""
Polkadot Community Digest

Main script that integrates the Polkadot forum analyzer with the mailing system
to generate periodic reports and send newsletters summarizing important posts.
"""

import os
import sys
import json
import argparse
import logging
import schedule
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("polkadot_digest.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("polkadot_digest")

# Import necessary modules
try:
    from polkadot_community_analyzer import PolkadotCommunityAnalyzer
except ImportError:
    logger.error("Module PolkadotCommunityAnalyzer not found. Ensure the file is in the same directory.")
    sys.exit(1)

try:
    from polkadot_forum_mailer import PolkadotForumMailer
except ImportError:
    logger.error("Module PolkadotForumMailer not found. Ensure the file is in the same directory.")
    sys.exit(1)


class PolkadotCommunityDigest:
    """
    Class that integrates forum analysis with the mailing system
    """
    def __init__(self, config_file="digest_config.json"):
        """Initialize the digest system"""
        self.config_file = config_file
        self.config = self._load_config()
        self.analyzer = None
        self.mailer = None
        
        # Output directory for all files
        self.output_dir = self.config.get("output_directory", "polkadot_digest_output")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _load_config(self):
        """Load configurations from file or create default"""
        default_config = {
            "analysis": {
                "max_categories": 15,
                "max_topics_per_category": 20,
                "max_topics_details": 100,
                "request_delay": 1.0
            },
            "mailing": {
                "frequency": "weekly",  # daily, weekly, monthly
                "send_hour": 8,  # Hour of the day to send (0-23)
                "send_day": 1,  # Day of the week for weekly sending (0=Monday, 6=Sunday)
                "send_date": 1,  # Date of the month for monthly sending (1-28)
                "test_mode": False
            },
            "output_directory": "polkadot_digest_output",
            "last_run": None
        }
        
        if not os.path.exists(self.config_file):
            # Create default configuration file
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Configuration file created: {self.config_file}")
            return default_config
        
        # Load existing configurations
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configurations loaded from {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")
            return default_config
    
    def _save_config(self):
        """Save updated configurations"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configurations saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configurations: {str(e)}")
    
    def run_analysis(self):
        """Run forum analysis"""
        logger.info("Starting Polkadot forum analysis")
        
        # Get analysis configurations
        analysis_config = self.config.get("analysis", {})
        max_categories = analysis_config.get("max_categories", 15)
        max_topics_per_category = analysis_config.get("max_topics_per_category", 20)
        max_topics_details = analysis_config.get("max_topics_details", 100)
        request_delay = analysis_config.get("request_delay", 1.0)
        
        # Initialize the analyzer
        self.analyzer = PolkadotCommunityAnalyzer(delay_between_requests=request_delay)
        
        # Collect data
        logger.info("Collecting forum data...")
        self.analyzer.collect_data(
            max_categories=max_categories,
            max_topics_per_category=max_topics_per_category,
            max_topics_details=max_topics_details
        )
        
        # Analyze data
        logger.info("Analyzing collected data...")
        report = self.analyzer.analyze_data()
        
        if not report:
            logger.error("Data analysis failed")
            return False
        
        # Generate visualizations
        logger.info("Generating visualizations...")
        self.analyzer.generate_visualizations()
        
        # Save report
        report_path = os.path.join(self.output_dir, f"forum_analysis_{datetime.now().strftime('%Y%m%d')}.json")
        self.analyzer.export_report(report, report_path)
        
        # Create governance summary
        governance_path = os.path.join(self.output_dir, f"governance_summary_{datetime.now().strftime('%Y%m%d')}.md")
        self.analyzer.create_governance_summary(report, governance_path)
        
        # Update last run timestamp
        self.config["last_run"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._save_config()
        
        logger.info(f"Analysis completed. Report saved to {report_path}")
        return True
    
    def generate_newsletter(self):
        """Generate newsletter based on the most recent analysis"""
        logger.info("Generating newsletter based on analyzed data")
        
        # Initialize the mailer with the analyzer
        self.mailer = PolkadotForumMailer(self.analyzer)
        
        # Generate newsletter preview
        preview_file = os.path.join(self.output_dir, f"newsletter_preview_{datetime.now().strftime('%Y%m%d')}.html")
        result = self.mailer.preview_newsletter(preview_file)
        
        if not result:
            logger.error("Failed to generate newsletter")
            return False
        
        logger.info(f"Newsletter generated and saved to {preview_file}")
        return True
    
    def send_newsletter(self, test_mode=False):
        """Send newsletter to subscribers"""
        if test_mode:
            logger.info("Sending newsletter in test mode")
        else:
            logger.info("Sending newsletter to subscribers")
        
        # Ensure the mailer is initialized
        if self.mailer is None:
            self.mailer = PolkadotForumMailer(self.analyzer)
        
        # Send newsletter
        if test_mode:
            # Send only to the first subscriber
            self.mailer.load_subscribers()
            active_subscribers = [sub for sub in self.mailer.subscribers if sub.get('status') == 'active']
            
            if not active_subscribers:
                logger.error("No active subscribers found for test sending")
                return False
            
            newsletter_html = self.mailer.generate_newsletter_content()
            if not newsletter_html:
                logger.error("Failed to generate newsletter content")
                return False
            
            current_date = datetime.now().strftime("%d/%m/%Y")
            subject = f"Polkadot Forum Digest - {current_date} [TEST]"
            
            result = self.mailer.send_email(active_subscribers[0]['email'], subject, newsletter_html)
            if result:
                logger.info(f"Test email sent to {active_subscribers[0]['email']}")
                return True
            else:
                logger.error("Failed to send test email")
                return False
        else:
            # Send to all subscribers
            sent_count = self.mailer.send_newsletter()
            
            if sent_count > 0:
                logger.info(f"Newsletter sent to {sent_count} subscribers")
                return True
            else:
                logger.warning("No newsletters sent")
                return False
    
    def run_full_process(self, test_mode=False):
        """Run the full process: analysis, newsletter generation, and sending"""
        logger.info("Starting full Polkadot Digest process")
        
        # 1. Run analysis
        if not self.run_analysis():
            logger.error("Failed to run analysis. Aborting process.")
            return False
        
        # 2. Generate newsletter
        if not self.generate_newsletter():
            logger.error("Failed to generate newsletter. Aborting process.")
            return False
        
        # 3. Send newsletter
        if not self.send_newsletter(test_mode):
            logger.error("Failed to send newsletter.")
            return False
        
        logger.info("Full process executed successfully!")
        return True
    
    def schedule_runs(self):
        """Schedule periodic runs"""
        mailing_config = self.config.get("mailing", {})
        frequency = mailing_config.get("frequency", "weekly")
        send_hour = mailing_config.get("send_hour", 8)
        send_day = mailing_config.get("send_day", 0)  # 0 = Monday
        send_date = mailing_config.get("send_date", 1)
        test_mode = mailing_config.get("test_mode", False)
        
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        if frequency == "daily":
            schedule.every().day.at(f"{send_hour:02d}:00").do(self.run_full_process, test_mode=test_mode)
            logger.info(f"Scheduled for daily execution at {send_hour:02d}:00")
        
        elif frequency == "weekly":
            # The index 0 in days[] corresponds to Monday
            day = days[send_day] if 0 <= send_day < 7 else "monday"
            getattr(schedule.every(), day).at(f"{send_hour:02d}:00").do(self.run_full_process, test_mode=test_mode)
            logger.info(f"Scheduled for weekly execution at {send_hour:02d}:00 on {day}")
        
        elif frequency == "monthly":
            # Schedule for a specific day of the month
            schedule.every().month.at(f"{send_date} {send_hour:02d}:00").do(self.run_full_process, test_mode=test_mode)
            logger.info(f"Scheduled for monthly execution on day {send_date} at {send_hour:02d}:00")
        
        else:
            logger.error(f"Unknown frequency: {frequency}")
            return False
        
        logger.info("Scheduling configured. The process will run as scheduled.")
        return True
    
    def run_scheduler(self):
        """Run the scheduler in a loop"""
        self.schedule_runs()
        
        logger.info("Starting scheduler loop. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
    
    def setup_interactive(self):
        """Set up the system interactively"""
        print("\n===== POLKADOT COMMUNITY DIGEST SETUP =====")
        
        # Analysis settings
        print("\n----- Analysis Settings -----")
        max_categories = input("Maximum number of categories to analyze [15]: ") or 15
        max_topics_per_category = input("Maximum number of topics per category [20]: ") or 20
        max_topics_details = input("Maximum number of topics for detailed analysis [100]: ") or 100
        request_delay = input("Delay between requests in seconds [1.0]: ") or 1.0
        
        # Convert to appropriate types
        self.config["analysis"] = {
            "max_categories": int(max_categories),
            "max_topics_per_category": int(max_topics_per_category),
            "max_topics_details": int(max_topics_details),
            "request_delay": float(request_delay)
        }
        
        # Mailing settings
        print("\n----- Mailing Settings -----")
        
        frequency_options = {'1': 'daily', '2': 'weekly', '3': 'monthly'}
        print("Newsletter frequency:")
        print("1. Daily")
        print("2. Weekly")
        print("3. Monthly")
        freq_choice = input("Choose (1-3) [2]: ") or '2'
        frequency = frequency_options.get(freq_choice, 'weekly')
        
        send_hour = input("Hour of the day to send (0-23) [8]: ") or 8
        
        if frequency == 'weekly':
            day_options = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6}
            print("Day of the week to send:")
            print("1. Monday")
            print("2. Tuesday")
            print("3. Wednesday")
            print("4. Thursday")
            print("5. Friday")
            print("6. Saturday")
            print("7. Sunday")
            day_choice = input("Choose (1-7) [1]: ") or '1'
            send_day = day_options.get(day_choice, 0)
            send_date = 1  # Not used for weekly
        elif frequency == 'monthly':
            send_date = input("Day of the month to send (1-28) [1]: ") or 1
            send_day = 0  # Not used for monthly
        else:
            send_day = 0  # Not used for daily
            send_date = 1  # Not used for daily
        
        test_mode = input("Enable test mode? (y/n) [n]: ").lower() == 'y'
        
        # Convert to appropriate types
        self.config["mailing"] = {
            "frequency": frequency,
            "send_hour": int(send_hour),
            "send_day": int(send_day),
            "send_date": int(send_date),
            "test_mode": test_mode
        }
        
        # Output directory
        print("\n----- Output Settings -----")
        output_dir = input(f"Output directory for files [{self.output_dir}]: ") or self.output_dir
        self.config["output_directory"] = output_dir
        
        # Create directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save configurations
        self._save_config()
        
        print("\nSetup completed and saved successfully!")
        print(f"Configuration file: {self.config_file}")
        
        # Set up mailing system
        if input("\nWould you like to configure the email sending system now? (y/n) [y]: ").lower() != 'n':
            from polkadot_forum_mailer import setup_newsletter_service
            setup_newsletter_service()
        
        return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Polkadot Community Digest - Forum Analysis and Newsletter')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up the system')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run forum analysis')
    
    # Newsletter command
    newsletter_parser = subparsers.add_parser('newsletter', help='Generate newsletter')
    
    # Send command
    send_parser = subparsers.add_parser('send', help='Send newsletter')
    send_parser.add_argument('--test', action='store_true', help='Send only to the first subscriber')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run the full process')
    run_parser.add_argument('--test', action='store_true', help='Send only to the first subscriber')
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser('scheduler', help='Start execution scheduler')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='List current configurations')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize the digest
    digest = PolkadotCommunityDigest()
    
    # Execute corresponding command
    if args.command == 'setup':
        digest.setup_interactive()
    
    elif args.command == 'analyze':
        digest.run_analysis()
    
    elif args.command == 'newsletter':
        digest.run_analysis()
        digest.generate_newsletter()
    
    elif args.command == 'send':
        # Check if we already have a recent analysis
        if digest.config.get("last_run"):
            last_run = datetime.strptime(digest.config.get("last_run"), '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            hours_since_last_run = (now - last_run).total_seconds() / 3600
            
            if hours_since_last_run > 24:
                logger.warning("Last analysis is over 24 hours old. Running a new analysis...")
                digest.run_analysis()
        else:
            logger.warning("No previous analysis found. Running analysis...")
            digest.run_analysis()
            
        digest.generate_newsletter()
        digest.send_newsletter(args.test)
    
    elif args.command == 'run':
        digest.run_full_process(args.test)
    
    elif args.command == 'scheduler':
        digest.run_scheduler()
    
    elif args.command == 'config':
        print("\n===== CURRENT CONFIGURATIONS =====")
        print(json.dumps(digest.config, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
