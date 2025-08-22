import os
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import json
import logging

load_dotenv()

class F1SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and Service Role Key must be set in environment variables")
        
        try:
            self.supabase: Client = create_client(self.url, self.key)
            self.logger = logging.getLogger(__name__)
            print(f"[OK] Connected to Supabase: {self.url}")
        except Exception as e:
            print(f"[ERROR] Failed to create Supabase client: {e}")
            raise
    
    def store_odds_data(self, odds_df, race_name):
        """Store betting odds with timestamps"""
        try:
            # Convert DataFrame to list of dicts
            odds_records = odds_df.to_dict('records')
            
            # Add metadata and fix data types
            for record in odds_records:
                record['race_name'] = race_name
                record['created_at'] = datetime.now().isoformat()
                
                # Handle timestamp fields
                if 'fetch_timestamp' in record:
                    if hasattr(record['fetch_timestamp'], 'isoformat'):
                        record['fetch_timestamp'] = record['fetch_timestamp'].isoformat()
                    elif record['fetch_timestamp'] is None:
                        record['fetch_timestamp'] = datetime.now().isoformat()
                else:
                    record['fetch_timestamp'] = datetime.now().isoformat()
                    
                if 'market_type' not in record:
                    record['market_type'] = 'winner'
                    
                # Ensure odds is a float
                if 'odds' in record:
                    record['odds'] = float(record['odds'])
            
            # Insert into Supabase
            result = self.supabase.table('odds_history').insert(odds_records).execute()
            self.logger.info(f"[OK] Stored {len(odds_records)} odds records for {race_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error storing odds data: {e}")
            return None
    
    def store_predictions(self, predictions_df, race_name, model_version="v1"):
        """Store model predictions"""
        try:
            predictions_records = predictions_df.to_dict('records')
            
            for record in predictions_records:
                record['race_name'] = race_name
                record['model_version'] = model_version
                record['created_at'] = datetime.now().isoformat()
                
                # Ensure numeric fields are properly formatted
                if 'predicted_position' in record and record['predicted_position'] is not None:
                    record['predicted_position'] = int(float(record['predicted_position']))
                    
                for field in ['win_probability', 'podium_probability', 'points_probability']:
                    if field in record and record[field] is not None:
                        record[field] = float(record[field])
            
            result = self.supabase.table('predictions').insert(predictions_records).execute()
            self.logger.info(f"[OK] Stored {len(predictions_records)} predictions for {race_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error storing predictions: {e}")
            return None
    
    def store_race_results(self, results_df, race_name):
        """Store actual race results"""
        try:
            results_records = results_df.to_dict('records')
            
            for record in results_records:
                record['race_name'] = race_name
                record['created_at'] = datetime.now().isoformat()
                
                # Ensure numeric fields are properly formatted
                if 'final_position' in record:
                    record['final_position'] = int(record['final_position']) if record['final_position'] is not None else None
                if 'points' in record:
                    record['points'] = int(record['points']) if record['points'] is not None else 0
                if 'dnf' not in record:
                    record['dnf'] = False
            
            result = self.supabase.table('race_results').insert(results_records).execute()
            self.logger.info(f"[OK] Stored race results for {race_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error storing race results: {e}")
            return None
    
    def get_latest_odds(self, race_name=None, limit=100):
        """Get latest odds data"""
        try:
            query = self.supabase.table('odds_history').select('*')
            
            if race_name:
                query = query.eq('race_name', race_name)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            return pd.DataFrame(result.data)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error fetching odds: {e}")
            return pd.DataFrame()
    
    def get_predictions(self, race_name=None, model_version=None):
        """Get predictions data"""
        try:
            query = self.supabase.table('predictions').select('*')
            
            if race_name:
                query = query.eq('race_name', race_name)
            if model_version:
                query = query.eq('model_version', model_version)
            
            result = query.order('created_at', desc=True).execute()
            return pd.DataFrame(result.data)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error fetching predictions: {e}")
            return pd.DataFrame()
    
    def get_race_results(self, race_name=None):
        """Get race results"""
        try:
            query = self.supabase.table('race_results').select('*')
            
            if race_name:
                query = query.eq('race_name', race_name)
            
            result = query.order('created_at', desc=True).execute()
            return pd.DataFrame(result.data)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error fetching race results: {e}")
            return pd.DataFrame()
    
    def get_prediction_accuracy(self, race_name=None):
        """Calculate prediction accuracy by comparing predictions with results"""
        try:
            predictions_df = self.get_predictions(race_name)
            results_df = self.get_race_results(race_name)
            
            if predictions_df.empty or results_df.empty:
                return None
            
            # Merge predictions with actual results
            merged = pd.merge(
                predictions_df, 
                results_df, 
                on=['race_name', 'driver'], 
                suffixes=('_pred', '_actual')
            )
            
            # Calculate accuracy metrics
            accuracy_metrics = {
                'total_predictions': len(merged),
                'position_accuracy': 0,
                'win_accuracy': 0,
                'podium_accuracy': 0,
                'points_accuracy': 0
            }
            
            if len(merged) > 0:
                # Position accuracy (exact match)
                position_correct = (merged['predicted_position'] == merged['final_position']).sum()
                accuracy_metrics['position_accuracy'] = position_correct / len(merged)
                
                # Win predictions accuracy
                win_predictions = merged[merged['win_probability'] > 0.5]
                if len(win_predictions) > 0:
                    win_correct = (win_predictions['final_position'] == 1).sum()
                    accuracy_metrics['win_accuracy'] = win_correct / len(win_predictions)
                
                # Podium predictions accuracy
                podium_predictions = merged[merged['podium_probability'] > 0.33]
                if len(podium_predictions) > 0:
                    podium_correct = (podium_predictions['final_position'] <= 3).sum()
                    accuracy_metrics['podium_accuracy'] = podium_correct / len(podium_predictions)
                
                # Points predictions accuracy
                points_predictions = merged[merged['points_probability'] > 0.5]
                if len(points_predictions) > 0:
                    points_correct = (points_predictions['points'] > 0).sum()
                    accuracy_metrics['points_accuracy'] = points_correct / len(points_predictions)
            
            return accuracy_metrics
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error calculating accuracy: {e}")
            return None
    
    def store_betting_performance(self, bet_results):
        """Store betting performance tracking"""
        try:
            if isinstance(bet_results, dict):
                bet_results = [bet_results]
            
            for record in bet_results:
                record['created_at'] = datetime.now().isoformat()
                # Ensure numeric fields are properly formatted
                for field in ['stake', 'odds', 'profit_loss']:
                    if field in record and record[field] is not None:
                        record[field] = float(record[field])
            
            result = self.supabase.table('betting_performance').insert(bet_results).execute()
            self.logger.info(f"[OK] Stored betting performance data")
            return result
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error storing betting performance: {e}")
            return None
    
    def get_betting_performance(self, race_name=None):
        """Get betting performance data"""
        try:
            query = self.supabase.table('betting_performance').select('*')
            
            if race_name:
                query = query.eq('race_name', race_name)
            
            result = query.order('created_at', desc=True).execute()
            return pd.DataFrame(result.data)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error fetching betting performance: {e}")
            return pd.DataFrame()
    
    def get_overall_roi(self):
        """Calculate overall ROI from betting performance"""
        try:
            betting_df = self.get_betting_performance()
            
            if betting_df.empty:
                return None
            
            total_stake = betting_df['stake'].sum()
            total_profit = betting_df['profit_loss'].sum()
            
            roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0
            
            return {
                'total_bets': len(betting_df),
                'total_stake': total_stake,
                'total_profit': total_profit,
                'roi_percentage': roi,
                'win_rate': (betting_df['profit_loss'] > 0).sum() / len(betting_df) * 100
            }
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error calculating ROI: {e}")
            return None
    
    def test_connection(self):
        """Test the Supabase connection"""
        try:
            # Try a simple query to test connection
            result = self.supabase.table('odds_history').select('count').execute()
            return True
        except Exception as e:
            self.logger.error(f"[ERROR] Connection test failed: {e}")
            return False

# Global instance
db_client = None

def get_db_client():
    """Get or create global database client instance"""
    global db_client
    if db_client is None:
        db_client = F1SupabaseClient()
    return db_client

def test_connection():
    """Test the Supabase connection"""
    try:
        client = get_db_client()
        # Try a simple query to test connection
        result = client.supabase.table('odds_history').select('count').execute()
        print("[OK] Supabase connection successful!")
        return True
    except Exception as e:
        print(f"[ERROR] Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()