import os
import json
import time
import schedule
import logging
import pandas as pd
from datetime import datetime, timedelta, timezone
import fastf1
from pathlib import Path

# Import our existing modules
from ml.betting_strategy import generate_betting_recommendations
from ml.auto_race_evaluator import AutoRaceEvaluator
from ml.betpanda_odds_fetcher import BetpandaOddsFetcher
from ml.auto_race_results_fetcher import AutoRaceResultsFetcher

class AutoF1RaceMonitor:
    """
    Fully automated F1 race monitoring and betting system
    - Monitors F1 race schedule
    - Fetches live odds before each race
    - Generates predictions and betting recommendations
    - Processes race results automatically
    - Updates dashboard with latest data
    """
    
    def __init__(self, config_file="config/auto_monitor_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.race_evaluator = AutoRaceEvaluator()
        self.results_fetcher = AutoRaceResultsFetcher()
        
    def load_config(self):
        """Load configuration or create default"""
        default_config = {
            "check_interval_hours": 6,
            "odds_fetch_hours_before_race": [72, 48, 24, 12, 6, 2],
            "prediction_hours_before_race": 24,
            "auto_process_results_hours_after_race": 4,
            "betting_amount": 10,
            "min_expected_value": 0.05,
            "max_bets_per_race": 8,
            "odds_sources": ["stake", "bet365", "pinnacle"],
            "notification_webhook": None,
            "enable_auto_betting": False,
            "data_paths": {
                "live_odds": "data/live/current_odds.csv",
                "predictions": "data/live/next_race_predictions.csv",
                "recommendations": "data/live/betting_recommendations.csv",
                "race_schedule": "data/live/race_schedule.json",
                "processed_races": "data/processed/processed_races.json"
            }
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def setup_logging(self):
        """Setup logging for the monitor"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"auto_monitor_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_current_f1_schedule(self):
        """Get current F1 season schedule"""
        try:
            current_year = datetime.now().year
            schedule = fastf1.get_event_schedule(current_year, include_testing=False)
            
            # Convert to our format
            races = []
            for _, race in schedule.iterrows():
                race_data = {
                    "race_name": race['EventName'],
                    "country": race['Country'],
                    "location": race['Location'],
                    "race_date": race['Session5Date'].isoformat() if pd.notna(race['Session5Date']) else None,
                    "qualifying_date": race['Session4Date'].isoformat() if pd.notna(race['Session4Date']) else None,
                    "practice_dates": {
                        "fp1": race['Session1Date'].isoformat() if pd.notna(race['Session1Date']) else None,
                        "fp2": race['Session2Date'].isoformat() if pd.notna(race['Session2Date']) else None,
                        "fp3": race['Session3Date'].isoformat() if pd.notna(race['Session3Date']) else None
                    },
                    "round_number": race['RoundNumber']
                }
                races.append(race_data)
            
            # Save schedule
            schedule_file = self.config['data_paths']['race_schedule']
            os.makedirs(os.path.dirname(schedule_file), exist_ok=True)
            with open(schedule_file, 'w') as f:
                json.dump(races, f, indent=2)
            
            self.logger.info(f"Updated F1 schedule with {len(races)} races")
            return races
            
        except Exception as e:
            self.logger.error(f"Error fetching F1 schedule: {e}")
            return []
    
    def get_next_race(self):
        """Get the next upcoming race"""
        try:
            schedule_file = self.config['data_paths']['race_schedule']
            if not os.path.exists(schedule_file):
                races = self.get_current_f1_schedule()
            else:
                with open(schedule_file, 'r') as f:
                    races = json.load(f)
            
            now = datetime.now(timezone.utc)
            upcoming_races = []
            
            for race in races:
                if race['race_date']:
                    race_time = datetime.fromisoformat(race['race_date'].replace('Z', '+00:00'))
                    # Convert to UTC for comparison
                    if race_time.tzinfo is None:
                        race_time = race_time.replace(tzinfo=timezone.utc)
                    else:
                        race_time = race_time.astimezone(timezone.utc)
                    
                    if race_time > now:
                        upcoming_races.append((race, race_time))
            
            if upcoming_races:
                # Sort by date and return the next one
                upcoming_races.sort(key=lambda x: x[1])
                return upcoming_races[0][0], upcoming_races[0][1]
            
            return None, None
            
        except Exception as e:
            self.logger.error(f"Error getting next race: {e}")
            return None, None
    
    def should_fetch_odds(self, race_time):
        """Check if we should fetch odds based on time before race"""
        now = datetime.now(timezone.utc)
        # Ensure race_time is timezone-aware
        if race_time.tzinfo is None:
            race_time = race_time.replace(tzinfo=timezone.utc)
        else:
            race_time = race_time.astimezone(timezone.utc)
        hours_until_race = (race_time - now).total_seconds() / 3600
        
        fetch_times = self.config['odds_fetch_hours_before_race']
        
        # Check if we're within any of the fetch windows (±1 hour)
        for fetch_time in fetch_times:
            if abs(hours_until_race - fetch_time) <= 1:
                return True
        
        return False
    
    def should_generate_predictions(self, race_time):
        """Check if we should generate predictions"""
        now = datetime.now(timezone.utc)
        # Ensure race_time is timezone-aware
        if race_time.tzinfo is None:
            race_time = race_time.replace(tzinfo=timezone.utc)
        else:
            race_time = race_time.astimezone(timezone.utc)
        hours_until_race = (race_time - now).total_seconds() / 3600
        
        prediction_time = self.config['prediction_hours_before_race']
        return abs(hours_until_race - prediction_time) <= 1
    
    def should_process_results(self, race_time):
        """Check if we should process race results"""
        now = datetime.now(timezone.utc)
        # Ensure race_time is timezone-aware
        if race_time.tzinfo is None:
            race_time = race_time.replace(tzinfo=timezone.utc)
        else:
            race_time = race_time.astimezone(timezone.utc)
        hours_after_race = (now - race_time).total_seconds() / 3600
        
        process_time = self.config['auto_process_results_hours_after_race']
        return 0 <= hours_after_race <= process_time
    
    def fetch_live_odds_for_race(self, race_name):
        """Fetch live odds for the upcoming race"""
        try:
            self.logger.info(f"Fetching live odds for {race_name}")
            
            # Use our existing odds fetcher
            odds_fetcher = BetpandaOddsFetcher()
            odds_data = odds_fetcher.fetch_odds(use_sample_data=True)
            
            if odds_data is not None and not odds_data.empty:
                odds_file = self.config['data_paths']['live_odds']
                os.makedirs(os.path.dirname(odds_file), exist_ok=True)
                
                # Add timestamp
                odds_data['fetch_timestamp'] = datetime.now().isoformat()
                odds_data['race_name'] = race_name
                
                odds_data.to_csv(odds_file, index=False)
                self.logger.info(f"Saved {len(odds_data)} odds entries for {race_name}")
                return True
            else:
                self.logger.warning(f"No odds data found for {race_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error fetching odds for {race_name}: {e}")
            return False
    
    def generate_race_predictions(self, race_name):
        """Generate predictions for the upcoming race"""
        try:
            self.logger.info(f"Generating predictions for {race_name}")
            
            # Use our existing prediction system
            # Note: predict_live_race.py is a script, not a function
            # We'll need to run it as a subprocess or refactor it
            predictions = None  # Placeholder - needs implementation
            
            if predictions is not None and not predictions.empty:
                pred_file = self.config['data_paths']['predictions']
                os.makedirs(os.path.dirname(pred_file), exist_ok=True)
                
                # Add metadata
                predictions['prediction_timestamp'] = datetime.now().isoformat()
                predictions['race_name'] = race_name
                
                predictions.to_csv(pred_file, index=False)
                self.logger.info(f"Generated {len(predictions)} predictions for {race_name}")
                return True
            else:
                self.logger.warning(f"No predictions generated for {race_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error generating predictions for {race_name}: {e}")
            return False
    
    def generate_betting_recommendations_for_race(self, race_name):
        """Generate betting recommendations combining predictions and odds"""
        try:
            self.logger.info(f"Generating betting recommendations for {race_name}")
            
            odds_file = self.config['data_paths']['live_odds']
            pred_file = self.config['data_paths']['predictions']
            
            if not os.path.exists(odds_file) or not os.path.exists(pred_file):
                self.logger.warning("Missing odds or predictions data")
                return False
            
            # Generate recommendations using our existing system
            recommendations = generate_betting_recommendations(
                predictions_file=pred_file,
                odds_file=odds_file,
                min_ev=self.config['min_expected_value'],
                max_bets=self.config['max_bets_per_race']
            )
            
            if recommendations is not None and not recommendations.empty:
                rec_file = self.config['data_paths']['recommendations']
                os.makedirs(os.path.dirname(rec_file), exist_ok=True)
                
                # Add metadata
                recommendations['recommendation_timestamp'] = datetime.now().isoformat()
                recommendations['race_name'] = race_name
                
                recommendations.to_csv(rec_file, index=False)
                self.logger.info(f"Generated {len(recommendations)} betting recommendations for {race_name}")
                
                # Log top recommendations
                top_bets = recommendations[recommendations['bet_recommendation'] == 'BET'].head(5)
                if not top_bets.empty:
                    self.logger.info("Top betting recommendations:")
                    for _, bet in top_bets.iterrows():
                        self.logger.info(f"  {bet['driver']} @ {bet['odds']:.2f} (EV: {bet['expected_value']:.3f})")
                
                return True
            else:
                self.logger.warning(f"No betting recommendations generated for {race_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error generating betting recommendations for {race_name}: {e}")
            return False
    
    def process_race_results_auto(self, race_name):
        """Automatically process race results after the race"""
        try:
            self.logger.info(f"Auto-processing results for {race_name}")
            
            # First, try to fetch new race results automatically
            new_results = self.results_fetcher.check_for_new_results()
            if new_results > 0:
                self.logger.info(f"Fetched {new_results} new race result files")
            
            # Then process any available results
            processed = self.race_evaluator.run_single_check()
            
            if processed > 0:
                self.logger.info(f"Successfully processed {processed} race result files")
                return True
            else:
                self.logger.info("No new race results to process")
                return False
                
        except Exception as e:
            self.logger.error(f"Error auto-processing results for {race_name}: {e}")
            return False
    
    def send_notification(self, message):
        """Send notification (webhook, email, etc.)"""
        try:
            webhook_url = self.config.get('notification_webhook')
            if webhook_url:
                import requests
                payload = {
                    "text": f"🏎️ F1 Auto Monitor: {message}",
                    "timestamp": datetime.now().isoformat()
                }
                requests.post(webhook_url, json=payload)
                self.logger.info(f"Sent notification: {message}")
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
    
    def check_and_process_past_races(self):
        """Check for past races that haven't been processed yet"""
        try:
            # Load race schedule
            schedule_file = self.config['data_paths']['race_schedule']
            if not os.path.exists(schedule_file):
                return
            
            with open(schedule_file, 'r') as f:
                races = json.load(f)
            
            # Load processed races
            processed_file = self.config['data_paths']['processed_races']
            processed_races = set()
            if os.path.exists(processed_file):
                with open(processed_file, 'r') as f:
                    processed_data = json.load(f)
                    # Extract race names from filenames
                    for filename in processed_data:
                        if 'belgian' in filename.lower():
                            processed_races.add('Belgian Grand Prix')
                        elif 'british' in filename.lower():
                            processed_races.add('British Grand Prix')
                        elif 'spanish' in filename.lower():
                            processed_races.add('Spanish Grand Prix')
                        elif 'monaco' in filename.lower():
                            processed_races.add('Monaco Grand Prix')
                        elif 'canadian' in filename.lower():
                            processed_races.add('Canadian Grand Prix')
                        elif 'austrian' in filename.lower():
                            processed_races.add('Austrian Grand Prix')
                        elif 'hungarian' in filename.lower():
                            processed_races.add('Hungarian Grand Prix')
            
            now = datetime.now(timezone.utc)
            
            # Check each race
            for race in races:
                if race['race_date']:
                    race_time = datetime.fromisoformat(race['race_date'].replace('Z', '+00:00'))
                    if race_time.tzinfo is None:
                        race_time = race_time.replace(tzinfo=timezone.utc)
                    else:
                        race_time = race_time.astimezone(timezone.utc)
                    
                    # Check if race is in the past and not processed
                    hours_after_race = (now - race_time).total_seconds() / 3600
                    race_name = race['race_name']
                    
                    # Process if race finished more than 2 hours ago and not yet processed
                    if hours_after_race > 2 and race_name not in processed_races:
                        self.logger.info(f"Found unprocessed past race: {race_name}")
                        if self.process_race_results_auto(race_name):
                            self.logger.info(f"✅ Successfully processed past race: {race_name}")
                        else:
                            self.logger.warning(f"⚠️ Failed to process past race: {race_name}")
            
        except Exception as e:
            self.logger.error(f"Error checking past races: {e}")
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        try:
            self.logger.info("🔄 Starting monitoring cycle")
            
            # Check for unprocessed past races first
            self.check_and_process_past_races()
            
            # Get next race
            next_race, race_time = self.get_next_race()
            
            if not next_race:
                self.logger.info("No upcoming races found")
                return
            
            race_name = next_race['race_name']
            self.logger.info(f"Next race: {race_name} at {race_time}")
            
            # Check what actions to take
            actions_taken = []
            
            # 1. Fetch odds if needed
            if self.should_fetch_odds(race_time):
                if self.fetch_live_odds_for_race(race_name):
                    actions_taken.append("fetched odds")
            
            # 2. Generate predictions if needed
            if self.should_generate_predictions(race_time):
                if self.generate_race_predictions(race_name):
                    actions_taken.append("generated predictions")
            
            # 3. Generate betting recommendations if we have both odds and predictions
            odds_file = self.config['data_paths']['live_odds']
            pred_file = self.config['data_paths']['predictions']
            
            if os.path.exists(odds_file) and os.path.exists(pred_file):
                # Check if files are recent (within 48 hours)
                odds_age = time.time() - os.path.getmtime(odds_file)
                pred_age = time.time() - os.path.getmtime(pred_file)
                
                if odds_age < 48 * 3600 and pred_age < 48 * 3600:
                    if self.generate_betting_recommendations_for_race(race_name):
                        actions_taken.append("updated betting recommendations")
            
            # 4. Process results if race is over
            if self.should_process_results(race_time):
                if self.process_race_results_auto(race_name):
                    actions_taken.append("processed race results")
            
            # 5. Update race schedule periodically
            schedule_file = self.config['data_paths']['race_schedule']
            if not os.path.exists(schedule_file) or time.time() - os.path.getmtime(schedule_file) > 24 * 3600:
                self.get_current_f1_schedule()
                actions_taken.append("updated race schedule")
            
            if actions_taken:
                message = f"Completed: {', '.join(actions_taken)} for {race_name}"
                self.logger.info(f"✅ {message}")
                self.send_notification(message)
            else:
                self.logger.info("No actions needed this cycle")
            
        except Exception as e:
            error_msg = f"Error in monitoring cycle: {e}"
            self.logger.error(error_msg)
            self.send_notification(f"❌ {error_msg}")
    
    def start_continuous_monitoring(self):
        """Start continuous monitoring with scheduled checks"""
        self.logger.info("🚀 Starting continuous F1 race monitoring")
        
        # Schedule regular checks
        interval_hours = self.config['check_interval_hours']
        schedule.every(interval_hours).hours.do(self.run_monitoring_cycle)
        
        # Also schedule more frequent checks closer to race time
        schedule.every(30).minutes.do(self.run_monitoring_cycle)
        
        # Run initial cycle
        self.run_monitoring_cycle()
        
        self.logger.info(f"Monitoring scheduled every {interval_hours} hours and every 30 minutes")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
            self.send_notification(f"❌ Monitoring stopped due to error: {e}")
    
    def get_status(self):
        """Get current system status"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "next_race": None,
            "files_status": {},
            "last_actions": []
        }
        
        # Get next race info
        next_race, race_time = self.get_next_race()
        if next_race:
            status["next_race"] = {
                "name": next_race['race_name'],
                "date": race_time.isoformat(),
                "hours_until": (race_time - datetime.now()).total_seconds() / 3600
            }
        
        # Check file status
        for key, path in self.config['data_paths'].items():
            if os.path.exists(path):
                stat = os.stat(path)
                status["files_status"][key] = {
                    "exists": True,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "age_hours": (time.time() - stat.st_mtime) / 3600
                }
            else:
                status["files_status"][key] = {"exists": False}
        
        return status


def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="F1 Auto Race Monitor")
    parser.add_argument("command", choices=["start", "check", "status", "setup"], 
                       help="Command to run")
    parser.add_argument("--config", default="config/auto_monitor_config.json",
                       help="Config file path")
    
    args = parser.parse_args()
    
    monitor = AutoF1RaceMonitor(args.config)
    
    if args.command == "setup":
        print("🔧 Setting up Auto F1 Race Monitor...")
        
        # Create directories
        directories = [
            "data/live",
            "data/processed", 
            "data/incoming_results",
            "config",
            "logs"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created directory: {directory}")
        
        # Initialize schedule
        monitor.get_current_f1_schedule()
        
        print("\n✅ Setup completed!")
        print("\nNext steps:")
        print("1. Configure notification webhook in config file (optional)")
        print("2. Run: python auto_race_monitor.py start")
        
    elif args.command == "start":
        monitor.start_continuous_monitoring()
        
    elif args.command == "check":
        monitor.run_monitoring_cycle()
        
    elif args.command == "status":
        status = monitor.get_status()
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()