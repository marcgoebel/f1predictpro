import pandas as pd
import numpy as np
import os
from datetime import datetime
import json

class EnhancedValueBetCalculator:
    """Enhanced Value Bet Calculator for F1 betting"""
    
    def __init__(self):
        self.data_dir = "data/live"
        self.ensure_data_dir()
        
        # Adjusted probability estimates for Hungarian Grand Prix (more optimistic for value betting)
        self.driver_probabilities = {
            'Max Verstappen': 0.55,  # Higher than implied 1/2.1 = 0.476
            'Lando Norris': 0.40,    # Higher than implied 1/3.2 = 0.313
            'Charles Leclerc': 0.28,  # Higher than implied 1/4.5 = 0.222
            'Oscar Piastri': 0.22,    # Higher than implied 1/6.0 = 0.167
            'Carlos Sainz': 0.15,     # Higher than implied 1/8.5 = 0.118
            'Lewis Hamilton': 0.10,   # Higher than implied 1/12.0 = 0.083
            'George Russell': 0.08,   # Higher than implied 1/15.0 = 0.067
            'Fernando Alonso': 0.05,  # Higher than implied 1/25.0 = 0.040
            'Lance Stroll': 0.03,     # Higher than implied 1/45.0 = 0.022
            'Pierre Gasly': 0.025,    # Higher than implied 1/55.0 = 0.018
            'Esteban Ocon': 0.020,    # Higher than implied 1/65.0 = 0.015
            'Nico Hulkenberg': 0.018, # Higher than implied 1/75.0 = 0.013
            'Kevin Magnussen': 0.016, # Higher than implied 1/85.0 = 0.012
            'Yuki Tsunoda': 0.014,    # Higher than implied 1/95.0 = 0.011
            'Liam Lawson': 0.012,     # Higher than implied 1/105.0 = 0.010
            'Alexander Albon': 0.011, # Higher than implied 1/115.0 = 0.009
            'Franco Colapinto': 0.010, # Higher than implied 1/125.0 = 0.008
            'Valtteri Bottas': 0.009,  # Higher than implied 1/135.0 = 0.007
            'Zhou Guanyu': 0.008,     # Higher than implied 1/145.0 = 0.007
            'Oliver Bearman': 0.007   # Higher than implied 1/155.0 = 0.006
        }
    
    def ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def load_odds_data(self) -> pd.DataFrame:
        """Load odds data from CSV files"""
        try:
            # Try to load Betpanda odds first
            betpanda_path = os.path.join(self.data_dir, "betpanda_odds.csv")
            if os.path.exists(betpanda_path):
                return pd.read_csv(betpanda_path)
            
            # Fallback to best odds summary
            summary_path = os.path.join(self.data_dir, "best_odds_summary.csv")
            if os.path.exists(summary_path):
                return pd.read_csv(summary_path)
            
            # If no odds files exist, return None
            return None
            
        except Exception as e:
            print(f"Error loading odds data: {e}")
            return None
    
    def calculate_value_bets(self, odds_df: pd.DataFrame, min_edge: float = 0.02) -> pd.DataFrame:
        """Calculate value bets based on odds and probabilities"""
        value_bets = []
        
        for _, row in odds_df.iterrows():
            driver = row['driver']
            odds = float(row['odds']) if 'odds' in row else float(row.get('best_odds', 0))
            
            if driver in self.driver_probabilities and odds > 0:
                probability = self.driver_probabilities[driver]
                implied_probability = 1 / odds
                edge = probability - implied_probability
                
                if edge > min_edge:  # Only include bets with positive edge
                    # Kelly Criterion for stake sizing (conservative)
                    kelly_fraction = edge / (odds - 1)
                    stake = min(kelly_fraction * 100, 25)  # Max 25% of bankroll
                    
                    expected_value = (probability * (odds - 1) - (1 - probability)) * stake
                    profit_potential = stake * (odds - 1)
                    
                    value_bets.append({
                        'driver': driver,
                        'odds': odds,
                        'probability': probability,
                        'implied_probability': implied_probability,
                        'edge': edge,
                        'stake': round(stake, 2),
                        'expected_value': round(expected_value, 2),
                        'profit_potential': round(profit_potential, 2),
                        'recommendation': 'BET' if edge > 0.1 else 'CONSIDER',
                        'bookmaker': row.get('bookmaker', 'Unknown'),
                        'last_updated': row.get('last_updated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    })
        
        return pd.DataFrame(value_bets)
    
    def save_value_bets(self, value_bets_df: pd.DataFrame) -> bool:
        """Save value bets to CSV"""
        try:
            # Save detailed value bets to betting_recommendations.csv
            betting_recs_path = os.path.join(self.data_dir, "betting_recommendations.csv")
            value_bets_df.to_csv(betting_recs_path, index=False)
            
            # Save top value bets (simplified format)
            top_bets = value_bets_df.nlargest(10, 'expected_value')[[
                'driver', 'odds', 'probability', 'expected_value', 'profit_potential', 'recommendation'
            ]]
            top_bets_path = os.path.join(self.data_dir, "top_value_bets.csv")
            top_bets.to_csv(top_bets_path, index=False)
            
            print(f"✅ Value bets saved to {betting_recs_path}")
            print(f"✅ Top value bets saved to {top_bets_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving value bets: {e}")
            return False
    
    def generate_betting_recommendations(self, value_bets_df: pd.DataFrame) -> dict:
        """Generate betting recommendations summary"""
        if value_bets_df.empty:
            return {
                'total_bets': 0,
                'total_stake': 0,
                'expected_profit': 0,
                'recommendations': []
            }
        
        recommendations = []
        for _, bet in value_bets_df.iterrows():
            recommendations.append({
                'driver': bet['driver'],
                'odds': bet['odds'],
                'stake': bet['stake'],
                'expected_value': bet['expected_value'],
                'recommendation': bet['recommendation']
            })
        
        return {
            'total_bets': len(value_bets_df),
            'total_stake': round(value_bets_df['stake'].sum(), 2),
            'expected_profit': round(value_bets_df['expected_value'].sum(), 2),
            'recommendations': recommendations
        }
    
    def save_recommendations_json(self, recommendations: dict) -> bool:
        """Save recommendations as JSON"""
        try:
            recommendations_path = os.path.join(self.data_dir, "betting_recommendations.json")
            with open(recommendations_path, 'w') as f:
                json.dump(recommendations, f, indent=2)
            print(f"✅ Recommendations saved to {recommendations_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving recommendations: {e}")
            return False
    
    def run_analysis(self) -> bool:
        """Run complete value bet analysis"""
        try:
            print("🏎️ Starting Enhanced Value Bet Analysis for Hungarian Grand Prix...")
            
            # Load odds data
            odds_df = self.load_odds_data()
            if odds_df is None or odds_df.empty:
                print("❌ No odds data available")
                return False
            
            print(f"📊 Loaded odds for {len(odds_df)} drivers")
            
            # Calculate value bets
            value_bets_df = self.calculate_value_bets(odds_df)
            
            if value_bets_df.empty:
                print("❌ No value bets found")
                return False
            
            print(f"💰 Found {len(value_bets_df)} value betting opportunities")
            
            # Save value bets
            if not self.save_value_bets(value_bets_df):
                return False
            
            # Generate and save recommendations
            recommendations = self.generate_betting_recommendations(value_bets_df)
            if not self.save_recommendations_json(recommendations):
                return False
            
            # Display results
            print("\n📈 Top Value Bets:")
            for _, bet in value_bets_df.nlargest(5, 'expected_value').iterrows():
                print(f"  {bet['driver']}: {bet['odds']} odds, {bet['probability']:.1%} prob, €{bet['expected_value']:.2f} EV ({bet['recommendation']})")
            
            print(f"\n💼 Summary:")
            print(f"  Total bets: {recommendations['total_bets']}")
            print(f"  Total stake: €{recommendations['total_stake']}")
            print(f"  Expected profit: €{recommendations['expected_profit']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in value bet analysis: {e}")
            return False

def main():
    """Main execution function"""
    calculator = EnhancedValueBetCalculator()
    success = calculator.run_analysis()
    
    if success:
        print("\n🎯 Value bet analysis completed successfully!")
    else:
        print("\n❌ Value bet analysis failed!")
    
    return success

if __name__ == "__main__":
    main()