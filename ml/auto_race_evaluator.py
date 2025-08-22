import pandas as pd
import os
import glob
import shutil
from datetime import datetime, timedelta
import time
import argparse
import logging
from pathlib import Path
import json
from ml.bet_simulator import F1BetSimulator
from ml.prediction_accuracy_analyzer import PredictionAccuracyAnalyzer
import matplotlib.pyplot as plt
import numpy as np

class AutoRaceEvaluator:
    """
    Automated F1 Post-Race Evaluation System
    Monitors for new race results and updates betting simulation automatically
    """
    
    def __init__(self, config_path="config/auto_evaluator_config.json"):
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.processed_races = self.load_processed_races()
        
    def load_config(self, config_path):
        """
        Load configuration from JSON file or create default config
        """
        default_config = {
            "watch_directory": "data/incoming_results",
            "betting_recommendations_file": "data/live/betting_recommendations.csv",
            "master_log_file": "data/processed/bet_simulation_log.csv",
            "profit_graph_file": "data/processed/profit_over_time.png",
            "processed_races_file": "data/processed/processed_races.json",
            "archive_directory": "data/archive",
            "bet_amount": 10,
            "starting_capital": 1000,
            "success_threshold": 3,
            "file_patterns": ["*results*.csv", "*race_results*.csv", "*actual*.csv"],
            "min_file_age_seconds": 30,
            "enable_model_retraining": False,
            "model_retrain_threshold": 5,
            "notification_enabled": True
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"⚠️ Error loading config, using defaults: {e}")
                return default_config
        else:
            # Create default config file
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"📝 Created default config at {config_path}")
            return default_config
    
    def setup_logging(self):
        """
        Setup logging configuration
        """
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"auto_evaluator_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_processed_races(self):
        """
        Load list of already processed races
        """
        processed_file = self.config["processed_races_file"]
        if os.path.exists(processed_file):
            try:
                with open(processed_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Error loading processed races: {e}")
                return []
        return []
    
    def save_processed_races(self):
        """
        Save list of processed races
        """
        processed_file = self.config["processed_races_file"]
        os.makedirs(os.path.dirname(processed_file), exist_ok=True)
        
        with open(processed_file, 'w') as f:
            json.dump(self.processed_races, f, indent=2)
    
    def detect_new_race_files(self):
        """
        Detect new race result files in the watch directory
        """
        watch_dir = self.config["watch_directory"]
        if not os.path.exists(watch_dir):
            os.makedirs(watch_dir, exist_ok=True)
            self.logger.info(f"Created watch directory: {watch_dir}")
            return []
        
        new_files = []
        patterns = self.config["file_patterns"]
        min_age = self.config["min_file_age_seconds"]
        
        for pattern in patterns:
            files = glob.glob(os.path.join(watch_dir, pattern))
            for file_path in files:
                # Check if file is old enough (to ensure it's fully written)
                file_age = time.time() - os.path.getmtime(file_path)
                if file_age >= min_age:
                    file_name = os.path.basename(file_path)
                    if file_name not in self.processed_races:
                        new_files.append(file_path)
        
        return new_files
    
    def extract_race_name_from_file(self, file_path):
        """
        Extract race name from file path or content
        """
        file_name = os.path.basename(file_path)
        
        # Try to extract race name from filename
        race_indicators = [
            'bahrain', 'saudi', 'australia', 'japan', 'china', 'miami', 'spain', 
            'monaco', 'canada', 'austria', 'britain', 'hungary', 'belgium', 
            'netherlands', 'italy', 'singapore', 'russia', 'turkey', 'usa', 
            'mexico', 'brazil', 'qatar', 'abu_dhabi'
        ]
        
        for indicator in race_indicators:
            if indicator.lower() in file_name.lower():
                return f"{indicator.title()} GP"
        
        # Try to read race name from file content
        try:
            df = pd.read_csv(file_path)
            if 'Race_Name' in df.columns:
                race_names = df['Race_Name'].unique()
                if len(race_names) == 1:
                    return race_names[0]
        except Exception as e:
            self.logger.warning(f"Could not read race name from file content: {e}")
        
        # Fallback: use timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"Race_{timestamp}"
    
    def validate_race_results_file(self, file_path):
        """
        Validate that the race results file has the required format
        """
        try:
            df = pd.read_csv(file_path)
            required_columns = ['Driver', 'Actual_Position']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns in {file_path}: {missing_columns}")
                return False, f"Missing columns: {missing_columns}"
            
            # Check for valid position data
            if df['Actual_Position'].isna().any():
                self.logger.warning(f"File {file_path} contains missing position data")
            
            return True, "Valid"
            
        except Exception as e:
            self.logger.error(f"Error validating file {file_path}: {e}")
            return False, str(e)
    
    def process_new_race_results(self, file_path):
        """
        Process a new race results file
        """
        self.logger.info(f"Processing new race results: {file_path}")
        
        # Validate file
        is_valid, message = self.validate_race_results_file(file_path)
        if not is_valid:
            self.logger.error(f"Invalid race results file: {message}")
            return False
        
        # Extract race name
        race_name = self.extract_race_name_from_file(file_path)
        
        # Load race results and add race name if missing
        results_df = pd.read_csv(file_path)
        if 'Race_Name' not in results_df.columns:
            results_df['Race_Name'] = race_name
        
        # Load betting recommendations
        betting_file = self.config["betting_recommendations_file"]
        if not os.path.exists(betting_file):
            self.logger.error(f"Betting recommendations file not found: {betting_file}")
            return False
        
        betting_df = pd.read_csv(betting_file)
        
        # Filter betting recommendations for this race
        race_bets = betting_df[betting_df['Race_Name'] == race_name]
        if race_bets.empty:
            self.logger.warning(f"No betting recommendations found for race: {race_name}")
            # Still process to update logs
        
        # Run simulation for this race
        simulator = F1BetSimulator(
            starting_capital=self.config["starting_capital"],
            bet_amount=self.config["bet_amount"]
        )
        
        # Create temporary files for this race only
        temp_betting_file = f"temp_betting_{race_name.replace(' ', '_')}.csv"
        temp_results_file = f"temp_results_{race_name.replace(' ', '_')}.csv"
        
        race_bets.to_csv(temp_betting_file, index=False)
        results_df.to_csv(temp_results_file, index=False)
        
        try:
            # Load data into simulator
            if not simulator.load_betting_recommendations(temp_betting_file):
                return False
            
            if not simulator.load_race_results(temp_results_file):
                return False
            
            # Run simulation
            race_profit = simulator.simulate_bets(top_n_success=self.config["success_threshold"])
            
            # Update master log
            self.update_master_log(simulator.simulation_log)
            
            # Update profit graph
            self.update_profit_graph()
            
            # Archive processed file
            self.archive_processed_file(file_path, race_name)
            
            # Mark race as processed
            file_name = os.path.basename(file_path)
            self.processed_races.append(file_name)
            self.save_processed_races()
            
            # Send notification
            if self.config["notification_enabled"]:
                self.send_notification(race_name, race_profit, len(simulator.simulation_log))
            
            self.logger.info(f"✅ Successfully processed race: {race_name} (Profit: €{race_profit:.2f})")
            
            # Führe Vorhersagegenauigkeits-Analyse durch
            self.run_prediction_accuracy_analysis(race_name, temp_results_file)
            
            # Trigger model retraining if enabled
            if self.config["enable_model_retraining"]:
                self.check_model_retraining()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing race {race_name}: {e}")
            return False
            
        finally:
            # Clean up temporary files
            for temp_file in [temp_betting_file, temp_results_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
    
    def update_master_log(self, new_simulation_data):
        """
        Update the master simulation log with new race data
        """
        master_log_file = self.config["master_log_file"]
        
        # Load existing log or create new one
        if os.path.exists(master_log_file):
            existing_log = pd.read_csv(master_log_file)
        else:
            existing_log = pd.DataFrame()
        
        # Append new data
        new_data = pd.DataFrame(new_simulation_data)
        updated_log = pd.concat([existing_log, new_data], ignore_index=True)
        
        # Remove duplicates (in case of reprocessing)
        updated_log = updated_log.drop_duplicates(
            subset=['Race_Name', 'Driver'], 
            keep='last'
        )
        
        # Save updated log
        os.makedirs(os.path.dirname(master_log_file), exist_ok=True)
        updated_log.to_csv(master_log_file, index=False)
        
        self.logger.info(f"Updated master log with {len(new_data)} new entries")
    
    def update_profit_graph(self):
        """
        Regenerate and save the profit graph with all data
        """
        master_log_file = self.config["master_log_file"]
        graph_file = self.config["profit_graph_file"]
        
        if not os.path.exists(master_log_file):
            self.logger.warning("No master log file found for graph generation")
            return
        
        try:
            # Load all simulation data
            log_df = pd.read_csv(master_log_file)
            
            # Calculate cumulative profits by race
            race_profits = log_df.groupby('Race_Name')['Profit_Loss'].sum().cumsum()
            total_capitals = race_profits + self.config["starting_capital"]
            
            # Create updated graph
            plt.figure(figsize=(14, 8))
            
            races = race_profits.index.tolist()
            capitals = total_capitals.tolist()
            
            plt.plot(races, capitals, marker='o', linewidth=2, markersize=6, color='#2E86AB')
            plt.axhline(y=self.config["starting_capital"], color='red', linestyle='--', 
                       alpha=0.7, label=f'Starting Capital (€{self.config["starting_capital"]})')
            
            plt.title('F1 Betting Simulation - Total Capital Over Time (Auto-Updated)', 
                     fontsize=16, fontweight='bold')
            plt.ylabel('Total Capital (€)', fontsize=12)
            plt.xlabel('Race', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.xticks(rotation=45)
            
            # Add timestamp
            plt.figtext(0.02, 0.02, f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 
                       fontsize=8, alpha=0.7)
            
            plt.tight_layout()
            
            # Save graph
            os.makedirs(os.path.dirname(graph_file), exist_ok=True)
            plt.savefig(graph_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Updated profit graph: {graph_file}")
            
        except Exception as e:
            self.logger.error(f"Error updating profit graph: {e}")
    
    def archive_processed_file(self, file_path, race_name):
        """
        Move processed file to archive directory
        """
        archive_dir = self.config["archive_directory"]
        os.makedirs(archive_dir, exist_ok=True)
        
        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived_name = f"{timestamp}_{race_name.replace(' ', '_')}_{file_name}"
        archived_path = os.path.join(archive_dir, archived_name)
        
        try:
            shutil.move(file_path, archived_path)
            self.logger.info(f"Archived processed file: {archived_path}")
        except Exception as e:
            self.logger.error(f"Error archiving file: {e}")
    
    def send_notification(self, race_name, profit, bet_count):
        """
        Send notification about processed race (can be extended for email/Slack)
        """
        message = f"🏁 Race Processed: {race_name}\n"
        message += f"💰 Race Profit: €{profit:.2f}\n"
        message += f"🎯 Bets Placed: {bet_count}\n"
        message += f"⏰ Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print("\n" + "="*50)
        print("📧 NOTIFICATION")
        print("="*50)
        print(message)
        print("="*50 + "\n")
        
        # Here you could add email/Slack integration
        # self.send_email_notification(message)
        # self.send_slack_notification(message)
    
    def run_prediction_accuracy_analysis(self, race_name: str, result_file: str):
        """
        Führt detaillierte Vorhersagegenauigkeits-Analyse durch
        """
        try:
            self.logger.info(f"Starte Vorhersagegenauigkeits-Analyse für {race_name}...")
            
            # Initialisiere Accuracy Analyzer
            analyzer = PredictionAccuracyAnalyzer()
            
            # Finde entsprechende Vorhersagedatei
            prediction_file = self.find_prediction_file(race_name)
            
            if prediction_file and os.path.exists(prediction_file):
                # Führe Analyse durch
                analysis_result = analyzer.analyze_race_predictions(
                    prediction_file, result_file, race_name
                )
                
                if analysis_result:
                    # Speichere Analyseergebnisse
                    analyzer.save_analysis_results()
                    
                    # Generiere Bericht
                    report_file = f"data/analysis/accuracy_report_{race_name.replace(' ', '_')}.txt"
                    analyzer.generate_comprehensive_report(report_file)
                    
                    # Erstelle Visualisierung
                    viz_file = f"data/analysis/accuracy_viz_{race_name.replace(' ', '_')}.png"
                    analyzer.create_visualization(viz_file)
                    
                    # Zeige wichtige Metriken
                    overall_score = analysis_result['overall_score']
                    exact_acc = analysis_result['position_accuracy']['exact_accuracy']
                    
                    self.logger.info(f"Vorhersagegenauigkeit für {race_name}:")
                    self.logger.info(f"   Gesamt-Score: {overall_score:.1%}")
                    self.logger.info(f"   Exakte Genauigkeit: {exact_acc:.1%}")
                    self.logger.info(f"   Bericht: {report_file}")
                    self.logger.info(f"   Visualisierung: {viz_file}")
                    
                    # Prüfe ob Modell-Verbesserung nötig ist
                    if overall_score < 0.5:
                        self.logger.warning(f"Niedrige Vorhersagegenauigkeit ({overall_score:.1%}) - Modell-Überarbeitung empfohlen")
                    elif overall_score > 0.8:
                        self.logger.info(f"Ausgezeichnete Vorhersagegenauigkeit ({overall_score:.1%})!")
                    
                else:
                    self.logger.error(f"Fehler bei der Vorhersageanalyse für {race_name}")
            else:
                self.logger.warning(f"Keine Vorhersagedatei gefunden für {race_name}")
                
        except Exception as e:
            self.logger.error(f"Fehler bei der Vorhersageanalyse: {e}")
    
    def find_prediction_file(self, race_name: str) -> str:
        """
        Findet die entsprechende Vorhersagedatei für ein Rennen
        """
        # Normalisiere Rennnamen für Dateisuche
        race_name_clean = race_name.replace(' ', '_').replace('Grand_Prix', 'Grand_Prix')
        
        # Suche in verschiedenen Verzeichnissen
        search_patterns = [
            f"data/live/predicted_probabilities_*{race_name_clean}*_full.csv",
            f"data/live/predicted_probabilities_{race_name_clean}_full.csv",
            f"data/processed/predicted_probabilities_*{race_name_clean}*.csv",
            f"data/live/*{race_name_clean}*probabilities*.csv"
        ]
        
        for pattern in search_patterns:
            files = glob.glob(pattern)
            if files:
                # Nimm die neueste Datei
                latest_file = max(files, key=os.path.getmtime)
                self.logger.info(f"Gefundene Vorhersagedatei: {latest_file}")
                return latest_file
        
        return None
    
    def check_model_retraining(self):
        """
        Check if model retraining should be triggered
        """
        threshold = self.config["model_retrain_threshold"]
        
        if len(self.processed_races) % threshold == 0:
            self.logger.info(f"Triggering model retraining after {len(self.processed_races)} races")
            # Here you would call your model retraining script
            # self.trigger_model_retraining()
            
        # Zusätzlich: Prüfe Accuracy Analyzer Ergebnisse
        try:
            accuracy_history_file = "data/analysis/accuracy_history.csv"
            if os.path.exists(accuracy_history_file):
                acc_df = pd.read_csv(accuracy_history_file)
                if len(acc_df) >= 3:
                    recent_overall_scores = acc_df.tail(3)['overall_score'].mean()
                    if recent_overall_scores < 0.5:
                        self.logger.warning(f"Vorhersagegenauigkeit kritisch niedrig ({recent_overall_scores:.1%}). Dringendes Retraining erforderlich!")
        except Exception as e:
            self.logger.error(f"Error checking accuracy history: {e}")
    
    def run_single_check(self):
        """
        Run a single check for new race files
        """
        self.logger.info("🔍 Checking for new race result files...")
        
        new_files = self.detect_new_race_files()
        
        if not new_files:
            self.logger.info("No new race files found")
            return 0
        
        processed_count = 0
        for file_path in new_files:
            if self.process_new_race_results(file_path):
                processed_count += 1
            else:
                self.logger.error(f"Failed to process: {file_path}")
        
        self.logger.info(f"Processed {processed_count}/{len(new_files)} new race files")
        return processed_count
    
    def run_continuous_monitoring(self, check_interval_minutes=5):
        """
        Run continuous monitoring for new race files
        """
        self.logger.info(f"🚀 Starting continuous monitoring (checking every {check_interval_minutes} minutes)")
        
        try:
            while True:
                self.run_single_check()
                time.sleep(check_interval_minutes * 60)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Error in continuous monitoring: {e}")

def main():
    parser = argparse.ArgumentParser(description='F1 Auto Race Evaluator')
    parser.add_argument('--mode', choices=['single', 'continuous'], default='single',
                       help='Run mode: single check or continuous monitoring')
    parser.add_argument('--interval', type=int, default=5,
                       help='Check interval in minutes for continuous mode')
    parser.add_argument('--config', default='config/auto_evaluator_config.json',
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Initialize evaluator
    evaluator = AutoRaceEvaluator(args.config)
    
    if args.mode == 'single':
        processed = evaluator.run_single_check()
        print(f"\n✅ Single check completed. Processed {processed} files.")
    else:
        evaluator.run_continuous_monitoring(args.interval)

if __name__ == "__main__":
    main()