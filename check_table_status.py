#!/usr/bin/env python3
"""
Überprüfe den Status der Supabase-Tabellen
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml'))

from database.supabase_client import get_db_client

def main():
    print("=== SUPABASE TABELLEN STATUS ===")
    
    try:
        db = get_db_client()
        
        # Zähle Datensätze
        odds_count = len(db.get_latest_odds())
        predictions_count = len(db.get_predictions())
        results_count = len(db.get_race_results())
        betting_count = len(db.get_betting_performance())
        
        print(f"📈 odds_history: {odds_count} Datensätze")
        print(f"🎯 predictions: {predictions_count} Datensätze")
        print(f"🏁 race_results: {results_count} Datensätze")
        print(f"💰 betting_performance: {betting_count} Datensätze")
        
        print("\n=== BEISPIEL DATEN ===")
        
        # Zeige Beispiel-Odds
        if odds_count > 0:
            odds = db.get_latest_odds(limit=3)
            print("Neueste Odds:")
            for _, row in odds.iterrows():
                print(f"  {row['driver']}: {row['odds']} ({row['bookmaker']})")
        
        # Zeige Beispiel-Ergebnisse
        if results_count > 0:
            results = db.get_race_results()
            print("\nNeueste Ergebnisse (erste 3):")
            for i, (_, row) in enumerate(results.head(3).iterrows()):
                race_name = row['race_name'][:30] + '...' if len(row['race_name']) > 30 else row['race_name']
                print(f"  {row['driver']}: P{row['final_position']} ({race_name})")
        
        # Zeige Beispiel-Predictions
        if predictions_count > 0:
            predictions = db.get_predictions()
            print("\nNeueste Predictions (erste 3):")
            for i, (_, row) in enumerate(predictions.head(3).iterrows()):
                win_prob = row.get('win_probability', 0) * 100 if row.get('win_probability') else 0
                print(f"  {row['driver']}: P{row.get('predicted_position', 'N/A')} (Win: {win_prob:.1f}%)")
        
        print("\n🎉 Supabase-Integration ist vollständig funktionsfähig!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    main()