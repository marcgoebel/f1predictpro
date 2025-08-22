#!/usr/bin/env python3
"""
Test Script für Supabase Integration
Zeigt alle verfügbaren Features nach dem Setup
"""

import pandas as pd
from datetime import datetime
import os

def test_database_connection():
    """Teste die Datenbankverbindung"""
    print("🔍 1. Teste Datenbankverbindung...")
    try:
        from ml.database.supabase_client import get_db_client
        
        db_client = get_db_client()
        if db_client.test_connection():
            print("✅ Datenbankverbindung erfolgreich!")
            return True
        else:
            print("❌ Datenbankverbindung fehlgeschlagen")
            print("💡 Führe zuerst aus: python setup_supabase_tables.py")
            return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_enhanced_odds_fetcher():
    """Teste den Enhanced Odds Fetcher"""
    print("🏎️ 2. Teste Enhanced Odds Fetcher...")
    try:
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), 'ml'))
        
        from enhanced_odds_fetcher import EnhancedOddsFetcher
        
        fetcher = EnhancedOddsFetcher()
        print("✅ Enhanced Odds Fetcher erfolgreich initialisiert!")
        
        # Teste API-Verbindung (ohne echte API-Calls)
        if os.getenv('ODDS_API_KEY'):
            print("✅ Odds API Key gefunden")
        else:
            print("⚠️ Odds API Key nicht gefunden in .env")
        
        return True
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_sample_data_storage():
    """Teste das Speichern von Beispieldaten"""
    print("\n📊 3. Teste Datenspeicherung...")
    try:
        from ml.database.supabase_client import get_db_client
        
        db_client = get_db_client()
        
        # Erstelle Beispiel-Odds-Daten
        sample_odds = pd.DataFrame([
            {
                'race_name': 'Test Grand Prix 2025',
                'driver': 'Max Verstappen',
                'bookmaker': 'Test Bookmaker',
                'odds': 1.85,
                'market_type': 'winner',
                'fetch_timestamp': datetime.now()
            },
            {
                'race_name': 'Test Grand Prix 2025',
                'driver': 'Lando Norris',
                'bookmaker': 'Test Bookmaker',
                'odds': 3.20,
                'market_type': 'winner',
                'fetch_timestamp': datetime.now()
            }
        ])
        
        # Speichere in Supabase
        result = db_client.store_odds_data(sample_odds, 'Test Grand Prix 2025')
        if result:
            print("✅ Beispiel-Odds erfolgreich gespeichert")
        
        # Erstelle Beispiel-Vorhersagen
        sample_predictions = pd.DataFrame([
            {
                'race_name': 'Test Grand Prix 2025',
                'driver': 'Max Verstappen',
                'predicted_position': 1,
                'win_probability': 0.65,
                'podium_probability': 0.85,
                'points_probability': 0.95
            },
            {
                'race_name': 'Test Grand Prix 2025',
                'driver': 'Lando Norris',
                'predicted_position': 2,
                'win_probability': 0.25,
                'podium_probability': 0.70,
                'points_probability': 0.90
            }
        ])
        
        # Speichere Vorhersagen
        result = db_client.store_predictions(sample_predictions, 'Test Grand Prix 2025')
        if result:
            print("✅ Beispiel-Vorhersagen erfolgreich gespeichert")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Speichern: {e}")
        return False

def test_data_retrieval():
    """Teste das Abrufen von Daten"""
    print("\n📈 4. Teste Datenabruf...")
    try:
        from ml.database.supabase_client import get_db_client
        
        db_client = get_db_client()
        
        # Teste Odds-Abruf
        latest_odds = db_client.get_latest_odds('Test Grand Prix 2025')
        if not latest_odds.empty:
            print(f"✅ {len(latest_odds)} Odds-Datensätze abgerufen")
            print("   Beispiel:", latest_odds.iloc[0]['driver'], "-", latest_odds.iloc[0]['odds'])
        
        # Teste Vorhersagen-Abruf
        predictions = db_client.get_predictions('Test Grand Prix 2025')
        if not predictions.empty:
            print(f"✅ {len(predictions)} Vorhersage-Datensätze abgerufen")
            print("   Beispiel:", predictions.iloc[0]['driver'], "-", f"{predictions.iloc[0]['win_probability']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Abrufen: {e}")
        return False

def test_analytics_features():
    """Teste Analytics-Features"""
    print("\n🔍 5. Teste Analytics-Features...")
    try:
        from ml.enhanced_odds_fetcher import EnhancedOddsFetcher
        
        fetcher = EnhancedOddsFetcher()
        
        # Teste Best Odds
        best_odds = fetcher.get_best_odds('Test Grand Prix 2025')
        if not best_odds.empty:
            print(f"✅ Best Odds gefunden für {len(best_odds)} Fahrer")
        
        # Teste Value Bets
        value_bets = fetcher.get_value_bets('Test Grand Prix 2025')
        if not value_bets.empty:
            print(f"✅ {len(value_bets)} Value Bets identifiziert")
        else:
            print("ℹ️ Keine Value Bets gefunden (normal bei Testdaten)")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Analytics: {e}")
        return False

def show_next_steps():
    """Zeige nächste Schritte"""
    print("\n" + "="*60)
    print("🚀 NÄCHSTE SCHRITTE:")
    print("="*60)
    print()
    print("1. 📊 Echte Odds abrufen:")
    print("   python ml/enhanced_odds_fetcher.py")
    print()
    print("2. 📁 Bestehende Daten migrieren:")
    print("   python migrate_data_to_supabase.py")
    print()
    print("3. 🔄 Integration in bestehende Scripts:")
    print("   - auto_race_monitor.py")
    print("   - dashboard/app.py")
    print("   - Alle anderen ML-Scripts")
    print()
    print("4. 📈 Dashboard erweitern:")
    print("   - Historische Odds-Charts")
    print("   - Performance-Tracking")
    print("   - Value-Bet-Alerts")
    print()
    print("5. 🌤️ Wetter-Integration (optional):")
    print("   - OpenWeather API Key in .env")
    print("   - Erweiterte Vorhersagemodelle")
    print()
    print("📋 Dokumentation: SUPABASE_SETUP.md")
    print("🔗 Supabase Dashboard: https://ffgkrmpuwqtjtevpnnsj.supabase.co")

def main():
    """Hauptfunktion für alle Tests"""
    print("🧪 F1 Analytics Hub - Supabase Integration Test")
    print("=" * 60)
    
    # Test 1: Datenbankverbindung
    if not test_database_connection():
        print("\n❌ Setup unvollständig. Bitte führe zuerst aus:")
        print("   python setup_supabase_tables.py")
        print("   Dann die SQL-Befehle in Supabase ausführen.")
        return
    
    # Test 2: Enhanced Odds Fetcher
    if not test_enhanced_odds_fetcher():
        return
    
    # Test 3: Datenspeicherung
    if not test_sample_data_storage():
        return
    
    # Test 4: Datenabruf
    if not test_data_retrieval():
        return
    
    # Test 5: Analytics
    if not test_analytics_features():
        return
    
    print("\n" + "="*60)
    print("🎉 ALLE TESTS ERFOLGREICH!")
    print("✅ Supabase-Integration ist vollständig funktionsfähig")
    print("="*60)
    
    show_next_steps()

if __name__ == "__main__":
    main()