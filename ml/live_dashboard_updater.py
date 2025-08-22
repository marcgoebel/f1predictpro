import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import threading
import logging

# Import our modules
from auto_race_monitor import AutoF1RaceMonitor
from betting_strategy import generate_betting_recommendations
from enhanced_value_bet_calculator import EnhancedValueBetCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'live_dashboard.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('live_dashboard')

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

class LiveDashboardUpdater:
    """
    Real-time dashboard updater that keeps the Streamlit dashboard
    synchronized with the latest race data, odds, and recommendations
    """
    
    def __init__(self, update_interval_minutes=15):
        self.update_interval = update_interval_minutes * 60  # Convert to seconds
        self.monitor = AutoF1RaceMonitor()
        self.running = False
        self.update_thread = None
        
        # Dashboard data paths
        self.dashboard_data = {
            "next_race_info": "data/live/next_race_info.json",
            "live_recommendations": "data/live/betting_recommendations.csv",
            "best_odds": "data/live/best_odds_summary.csv",
            "value_bets": "data/live/betting_recommendations.csv",
            "race_countdown": "data/live/race_countdown.json"
        }
    
    def get_next_race_info(self):
        """Get comprehensive next race information"""
        try:
            next_race, race_time = self.monitor.get_next_race()
            
            if not next_race:
                return None
            
            now = datetime.now()
            time_until_race = race_time - now
            
            race_info = {
                "race_name": next_race['race_name'],
                "country": next_race['country'],
                "location": next_race['location'],
                "race_date": race_time.isoformat(),
                "race_date_formatted": race_time.strftime("%A, %B %d, %Y at %H:%M"),
                "days_until": time_until_race.days,
                "hours_until": int(time_until_race.total_seconds() // 3600),
                "minutes_until": int((time_until_race.total_seconds() % 3600) // 60),
                "is_race_weekend": time_until_race.total_seconds() < 72 * 3600,  # Within 3 days
                "is_race_day": time_until_race.total_seconds() < 24 * 3600,  # Within 1 day
                "qualifying_date": next_race.get('qualifying_date'),
                "round_number": next_race.get('round_number'),
                "last_updated": datetime.now().isoformat()
            }
            
            return race_info
            
        except Exception as e:
            print(f"Error getting next race info: {e}")
            return None
    
    def get_best_odds_summary(self):
        """Get summary of best available odds for top drivers"""
        try:
            odds_file = self.monitor.config['data_paths']['live_odds']
            
            if not os.path.exists(odds_file):
                return pd.DataFrame()
            
            odds_df = pd.read_csv(odds_file)
            
            if odds_df.empty:
                return pd.DataFrame()
            
            # Get best odds for each driver (highest odds = best value)
            best_odds = odds_df.groupby('driver').agg({
                'odds': 'max',
                'bookmaker': 'first',
                'fetch_timestamp': 'max'
            }).reset_index()
            
            # Sort by odds (best value first)
            best_odds = best_odds.sort_values('odds', ascending=False)
            
            # Add some formatting
            best_odds['odds_formatted'] = best_odds['odds'].apply(lambda x: f"{x:.2f}")
            best_odds['last_updated'] = pd.to_datetime(best_odds['fetch_timestamp']).dt.strftime('%H:%M')
            
            return best_odds.head(10)  # Top 10 drivers
            
        except Exception as e:
            print(f"Error getting best odds summary: {e}")
            return pd.DataFrame()
    
    def get_top_value_bets(self):
        """Get top value betting opportunities"""
        try:
            rec_file = self.monitor.config['data_paths']['recommendations']
            
            if not os.path.exists(rec_file):
                return pd.DataFrame()
            
            recommendations = pd.read_csv(rec_file)
            
            if recommendations.empty:
                return pd.DataFrame()
            
            # Filter for actual betting recommendations
            value_bets = recommendations[recommendations['bet_recommendation'] == 'BET'].copy()
            
            if value_bets.empty:
                return pd.DataFrame()
            
            # Sort by expected value
            value_bets = value_bets.sort_values('expected_value', ascending=False)
            
            # Add formatting
            value_bets['ev_formatted'] = value_bets['expected_value'].apply(lambda x: f"{x:.3f}")
            value_bets['odds_formatted'] = value_bets['odds'].apply(lambda x: f"{x:.2f}")
            value_bets['probability_formatted'] = value_bets['probability_pct'].apply(lambda x: f"{x:.1f}%")
            
            # Calculate potential profit for €10 bet
            value_bets['potential_profit'] = (value_bets['odds'] * 10 - 10).round(2)
            value_bets['potential_profit_formatted'] = value_bets['potential_profit'].apply(lambda x: f"€{x:.2f}")
            
            return value_bets.head(8)  # Top 8 value bets
            
        except Exception as e:
            print(f"Error getting top value bets: {e}")
            return pd.DataFrame()
    
    def update_dashboard_data(self):
        """Update all dashboard data files"""
        try:
            print(f"🔄 Updating dashboard data at {datetime.now().strftime('%H:%M:%S')}")
            
            # Ensure directories exist
            for file_path in self.dashboard_data.values():
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 1. Update next race info
            race_info = self.get_next_race_info()
            if race_info:
                with open(self.dashboard_data["next_race_info"], 'w') as f:
                    json.dump(race_info, f, indent=2)
                print(f"✅ Updated next race info: {race_info['race_name']}")
            
            # 2. Update best odds summary
            best_odds = self.get_best_odds_summary()
            if not best_odds.empty:
                best_odds.to_csv(self.dashboard_data["best_odds"], index=False)
                print(f"✅ Updated best odds for {len(best_odds)} drivers")
            
            # 3. Update top value bets
            value_bets = self.get_top_value_bets()
            if not value_bets.empty:
                value_bets.to_csv(self.dashboard_data["value_bets"], index=False)
                print(f"✅ Updated {len(value_bets)} top value bets")
            
            # 4. Copy latest recommendations to dashboard location
            rec_file = self.monitor.config['data_paths']['recommendations']
            if os.path.exists(rec_file):
                recommendations = pd.read_csv(rec_file)
                recommendations.to_csv(self.dashboard_data["live_recommendations"], index=False)
                print(f"✅ Updated live recommendations ({len(recommendations)} entries)")
            
            # 5. Create race countdown data
            if race_info:
                countdown_data = {
                    "race_name": race_info['race_name'],
                    "days": race_info['days_until'],
                    "hours": race_info['hours_until'] % 24,
                    "minutes": race_info['minutes_until'],
                    "total_hours": race_info['hours_until'],
                    "is_race_weekend": race_info['is_race_weekend'],
                    "is_race_day": race_info['is_race_day'],
                    "last_updated": datetime.now().isoformat()
                }
                
                with open(self.dashboard_data["race_countdown"], 'w') as f:
                    json.dump(countdown_data, f, indent=2)
                print(f"✅ Updated race countdown")
            
            print(f"🎯 Dashboard data update completed successfully")
            
        except Exception as e:
            print(f"❌ Error updating dashboard data: {e}")
    
    def start_background_updates(self):
        """Start background thread for continuous updates"""
        if self.running:
            print("Background updates already running")
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        print(f"🚀 Started background dashboard updates (every {self.update_interval//60} minutes)")
    
    def stop_background_updates(self):
        """Stop background updates"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        print("🛑 Stopped background dashboard updates")
    
    def _update_loop(self):
        """Background update loop"""
        while self.running:
            try:
                self.update_dashboard_data()
                
                # Sleep in small intervals to allow for quick shutdown
                for _ in range(int(self.update_interval)):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Error in update loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def force_update(self):
        """Force an immediate update"""
        self.update_dashboard_data()
    
    def get_dashboard_status(self):
        """Get status of dashboard data files"""
        status = {
            "last_check": datetime.now().isoformat(),
            "files": {},
            "next_race": None
        }
        
        # Check file status
        for name, path in self.dashboard_data.items():
            if os.path.exists(path):
                stat = os.stat(path)
                status["files"][name] = {
                    "exists": True,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "age_minutes": (time.time() - stat.st_mtime) / 60
                }
            else:
                status["files"][name] = {"exists": False}
        
        # Get next race info
        race_info = self.get_next_race_info()
        if race_info:
            status["next_race"] = race_info
        
        return status


# Streamlit integration functions
def load_next_race_info():
    """Load next race info for Streamlit dashboard"""
    try:
        info_file = "data/live/next_race_info.json"
        if os.path.exists(info_file):
            with open(info_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading race info: {e}")
    return None

def load_best_odds():
    """Load best odds for Streamlit dashboard"""
    try:
        odds_file = "data/live/best_odds_summary.csv"
        if os.path.exists(odds_file):
            return pd.read_csv(odds_file)
    except Exception as e:
        st.error(f"Error loading odds: {e}")
    return pd.DataFrame()

def load_top_value_bets():
    """Load top value bets for Streamlit dashboard"""
    try:
        bets_file = "data/live/betting_recommendations.csv"
        if os.path.exists(bets_file):
            return pd.read_csv(bets_file)
    except Exception as e:
        st.error(f"Error loading value bets: {e}")
    return pd.DataFrame()

def load_race_countdown():
    """Load race countdown for Streamlit dashboard"""
    try:
        countdown_file = "data/live/race_countdown.json"
        if os.path.exists(countdown_file):
            with open(countdown_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading countdown: {e}")
    return None


def main():
    """CLI interface for the dashboard updater"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Live Dashboard Updater")
    parser.add_argument("command", choices=["start", "update", "status", "stop"],
                       help="Command to run")
    parser.add_argument("--interval", type=int, default=15,
                       help="Update interval in minutes")
    
    args = parser.parse_args()
    
    updater = LiveDashboardUpdater(args.interval)
    
    if args.command == "start":
        print("🚀 Starting live dashboard updater...")
        updater.start_background_updates()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping dashboard updater...")
            updater.stop_background_updates()
    
    elif args.command == "update":
        print("🔄 Running single update...")
        updater.force_update()
    
    elif args.command == "status":
        status = updater.get_dashboard_status()
        print(json.dumps(status, indent=2))
    
    elif args.command == "stop":
        # This would need a process management system in production
        print("Use Ctrl+C to stop the running updater")


if __name__ == "__main__":
    main()