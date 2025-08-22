#!/usr/bin/env python3
"""
Skript zum Beheben der leeren Tabellen in Supabase
Dieses Skript lädt Beispieldaten in die odds_history und predictions Tabellen
"""

import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import random

# Add the ml directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml'))

from database.supabase_client import get_db_client

def create_sample_odds_data():
    """Erstelle Beispiel-Odds-Daten"""
    drivers = [
        'Max Verstappen', 'Sergio Perez', 'Lewis Hamilton', 'George Russell',
        'Charles Leclerc', 'Carlos Sainz', 'Lando Norris', 'Oscar Piastri',
        'Fernando Alonso', 'Lance Stroll', 'Esteban Ocon', 'Pierre Gasly',
        'Alexander Albon', 'Logan Sargeant', 'Nico Hulkenberg', 'Kevin Magnussen',
        'Valtteri Bottas', 'Zhou Guanyu', 'Yuki Tsunoda', 'Daniel Ricciardo'
    ]
    
    odds_data = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i, driver in enumerate(drivers):
        # Simuliere realistische Odds basierend auf Fahrerleistung
        if i < 2:  # Top drivers
            odds = round(random.uniform(2.5, 4.0), 2)
        elif i < 6:  # Good drivers
            odds = round(random.uniform(8.0, 25.0), 2)
        elif i < 12:  # Mid-field
            odds = round(random.uniform(50.0, 150.0), 2)
        else:  # Back markers
            odds = round(random.uniform(200.0, 1000.0), 2)
            
        odds_data.append({
            'driver': driver,
            'odds': odds,
            'bookmaker': 'Bet365',
            'market_type': 'winner',
            'fetch_timestamp': (base_time + timedelta(minutes=i*5)).isoformat()
        })
    
    return pd.DataFrame(odds_data)

def create_sample_predictions_data():
    """Erstelle Beispiel-Predictions-Daten"""
    drivers = [
        'Max Verstappen', 'Sergio Perez', 'Lewis Hamilton', 'George Russell',
        'Charles Leclerc', 'Carlos Sainz', 'Lando Norris', 'Oscar Piastri',
        'Fernando Alonso', 'Lance Stroll', 'Esteban Ocon', 'Pierre Gasly',
        'Alexander Albon', 'Logan Sargeant', 'Nico Hulkenberg', 'Kevin Magnussen',
        'Valtteri Bottas', 'Zhou Guanyu', 'Yuki Tsunoda', 'Daniel Ricciardo'
    ]
    
    predictions_data = []
    
    for i, driver in enumerate(drivers):
        # Simuliere realistische Vorhersagen
        predicted_pos = i + 1 + random.randint(-2, 2)
        predicted_pos = max(1, min(20, predicted_pos))  # Zwischen 1 und 20
        
        # Win probability basierend auf vorhergesagter Position
        if predicted_pos == 1:
            win_prob = random.uniform(0.15, 0.35)
        elif predicted_pos <= 3:
            win_prob = random.uniform(0.05, 0.15)
        elif predicted_pos <= 8:
            win_prob = random.uniform(0.01, 0.05)
        else:
            win_prob = random.uniform(0.001, 0.01)
            
        # Podium probability
        if predicted_pos <= 3:
            podium_prob = random.uniform(0.4, 0.8)
        elif predicted_pos <= 8:
            podium_prob = random.uniform(0.1, 0.4)
        else:
            podium_prob = random.uniform(0.01, 0.1)
            
        # Points probability
        if predicted_pos <= 10:
            points_prob = random.uniform(0.6, 0.95)
        elif predicted_pos <= 15:
            points_prob = random.uniform(0.2, 0.6)
        else:
            points_prob = random.uniform(0.05, 0.2)
        
        predictions_data.append({
            'driver': driver,
            'predicted_position': predicted_pos,
            'win_probability': round(win_prob, 4),
            'podium_probability': round(podium_prob, 4),
            'points_probability': round(points_prob, 4)
        })
    
    return pd.DataFrame(predictions_data)

def main():
    """Hauptfunktion"""
    print("🔧 Behebe leere Tabellen in Supabase...")
    
    # Verbindung zur Datenbank
    try:
        db_client = get_db_client()
        print("✅ Verbindung zu Supabase hergestellt")
    except Exception as e:
        print(f"❌ Fehler bei der Datenbankverbindung: {e}")
        return
    
    # Erstelle und speichere Odds-Daten
    print("\n📊 Erstelle Beispiel-Odds-Daten...")
    try:
        odds_df = create_sample_odds_data()
        result = db_client.store_odds_data(odds_df, "2024_Test_Grand_Prix")
        if result:
            print(f"✅ {len(odds_df)} Odds-Datensätze gespeichert")
        else:
            print("❌ Fehler beim Speichern der Odds-Daten")
    except Exception as e:
        print(f"❌ Fehler bei Odds-Daten: {e}")
    
    # Erstelle und speichere Predictions-Daten
    print("\n🎯 Erstelle Beispiel-Predictions-Daten...")
    try:
        predictions_df = create_sample_predictions_data()
        result = db_client.store_predictions(predictions_df, "2024_Test_Grand_Prix", "test_v1")
        if result:
            print(f"✅ {len(predictions_df)} Predictions-Datensätze gespeichert")
        else:
            print("❌ Fehler beim Speichern der Predictions-Daten")
    except Exception as e:
        print(f"❌ Fehler bei Predictions-Daten: {e}")
    
    # Überprüfe die Tabellen
    print("\n🔍 Überprüfe Tabellenstatus...")
    try:
        # Zähle Datensätze in jeder Tabelle
        odds_count = len(db_client.get_latest_odds())
        predictions_count = len(db_client.get_predictions())
        results_count = len(db_client.get_race_results())
        
        print(f"📈 odds_history: {odds_count} Datensätze")
        print(f"🎯 predictions: {predictions_count} Datensätze")
        print(f"🏁 race_results: {results_count} Datensätze")
        
        if odds_count > 0 and predictions_count > 0:
            print("\n🎉 Alle Tabellen enthalten jetzt Daten!")
            print("\n📋 Nächste Schritte:")
            print("1. Teste den enhanced_odds_fetcher: python ml/enhanced_odds_fetcher.py")
            print("2. Führe weitere Tests durch: python test_supabase_integration.py")
            print("3. Integriere in deine bestehenden Skripte")
        else:
            print("⚠️ Einige Tabellen sind noch leer")
            
    except Exception as e:
        print(f"❌ Fehler bei der Überprüfung: {e}")

if __name__ == "__main__":
    main()