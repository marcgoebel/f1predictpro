#!/usr/bin/env python3
"""
Supabase Integration Script
Integriert Supabase-Funktionalität in bestehende Skripte
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add ML directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml'))

try:
    from database.supabase_client import get_db_client
    from enhanced_odds_fetcher import EnhancedOddsFetcher
except ImportError as e:
    print(f"❌ Import-Fehler: {e}")
    print("Bitte stelle sicher, dass alle Abhängigkeiten installiert sind.")
    sys.exit(1)

def integrate_odds_fetcher():
    """
    Integriert Enhanced Odds Fetcher mit Supabase
    """
    print("🔄 Integriere Enhanced Odds Fetcher mit Supabase...")
    
    try:
        # Initialize database client
        db_client = get_db_client()
        print("✅ Supabase-Verbindung hergestellt")
        
        # Initialize odds fetcher
        odds_fetcher = EnhancedOddsFetcher(db_client)
        print("✅ Enhanced Odds Fetcher initialisiert")
        
        # Fetch latest odds
        print("📈 Lade aktuelle F1-Quoten...")
        odds_data = odds_fetcher.fetch_f1_odds()
        
        if odds_data and not odds_data.empty:
            print(f"✅ {len(odds_data)} Odds-Datensätze abgerufen")
            print("📊 Beispiel-Daten:")
            print(odds_data.head())
            
            # Store in database
            success = odds_fetcher.store_odds(odds_data)
            if success:
                print("✅ Odds erfolgreich in Supabase gespeichert")
            else:
                print("❌ Fehler beim Speichern der Odds")
        else:
            print("⚠️ Keine Odds-Daten verfügbar")
            
    except Exception as e:
        print(f"❌ Fehler bei Odds-Integration: {e}")
        return False
    
    return True

def migrate_csv_data():
    """
    Migriert bestehende CSV-Daten zu Supabase
    """
    print("🔄 Migriere CSV-Daten zu Supabase...")
    
    try:
        db_client = get_db_client()
        
        # Define data directories
        data_dirs = {
            'odds': 'data/odds',
            'predictions': 'data/predictions', 
            'results': 'data/race_results'
        }
        
        migration_stats = {
            'odds': 0,
            'predictions': 0,
            'results': 0
        }
        
        # Migrate odds data
        odds_dir = data_dirs['odds']
        if os.path.exists(odds_dir):
            print(f"📈 Migriere Odds aus {odds_dir}...")
            for file in os.listdir(odds_dir):
                if file.endswith('.csv'):
                    file_path = os.path.join(odds_dir, file)
                    try:
                        df = pd.read_csv(file_path)
                        if not df.empty:
                            # Add metadata
                            df['race_name'] = file.replace('.csv', '').replace('_odds', '')
                            df['created_at'] = datetime.now().isoformat()
                            df['fetch_timestamp'] = datetime.now().isoformat()
                            df['market_type'] = 'race_winner'
                            
                            # Store in database
                            success = db_client.store_odds_data(df)
                            if success:
                                migration_stats['odds'] += len(df)
                                print(f"✅ {file}: {len(df)} Datensätze migriert")
                            else:
                                print(f"❌ Fehler bei {file}")
                    except Exception as e:
                        print(f"❌ Fehler bei {file}: {e}")
        
        # Migrate predictions data
        pred_dir = data_dirs['predictions']
        if os.path.exists(pred_dir):
            print(f"🎯 Migriere Predictions aus {pred_dir}...")
            for file in os.listdir(pred_dir):
                if file.endswith('.csv'):
                    file_path = os.path.join(pred_dir, file)
                    try:
                        df = pd.read_csv(file_path)
                        if not df.empty:
                            # Add metadata
                            df['race_name'] = file.replace('.csv', '').replace('_predictions', '')
                            df['created_at'] = datetime.now().isoformat()
                            df['model_version'] = 'v1.0'
                            
                            # Store in database
                            success = db_client.store_predictions(df)
                            if success:
                                migration_stats['predictions'] += len(df)
                                print(f"✅ {file}: {len(df)} Datensätze migriert")
                            else:
                                print(f"❌ Fehler bei {file}")
                    except Exception as e:
                        print(f"❌ Fehler bei {file}: {e}")
        
        # Migrate race results
        results_dir = data_dirs['results']
        if os.path.exists(results_dir):
            print(f"🏁 Migriere Ergebnisse aus {results_dir}...")
            for file in os.listdir(results_dir):
                if file.endswith('.csv'):
                    file_path = os.path.join(results_dir, file)
                    try:
                        df = pd.read_csv(file_path)
                        if not df.empty:
                            # Add metadata
                            df['race_name'] = file.replace('.csv', '').replace('_results', '')
                            df['created_at'] = datetime.now().isoformat()
                            
                            # Store in database
                            success = db_client.store_race_results(df)
                            if success:
                                migration_stats['results'] += len(df)
                                print(f"✅ {file}: {len(df)} Datensätze migriert")
                            else:
                                print(f"❌ Fehler bei {file}")
                    except Exception as e:
                        print(f"❌ Fehler bei {file}: {e}")
        
        # Print migration summary
        print("\n📊 Migrations-Zusammenfassung:")
        print(f"📈 Odds: {migration_stats['odds']} Datensätze")
        print(f"🎯 Predictions: {migration_stats['predictions']} Datensätze")
        print(f"🏁 Ergebnisse: {migration_stats['results']} Datensätze")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei CSV-Migration: {e}")
        return False

def update_existing_scripts():
    """
    Aktualisiert bestehende Skripte für Supabase-Integration
    """
    print("🔄 Aktualisiere bestehende Skripte...")
    
    scripts_to_update = [
        'ml/f1_predictor.py',
        'ml/betting_strategy.py',
        'utils/data_collector.py'
    ]
    
    update_template = '''
# Supabase Integration
try:
    from database.supabase_client import get_db_client
    SUPABASE_AVAILABLE = True
    db_client = get_db_client()
except ImportError:
    SUPABASE_AVAILABLE = False
    db_client = None
'''
    
    updated_files = []
    
    for script_path in scripts_to_update:
        if os.path.exists(script_path):
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if already updated
                if 'SUPABASE_AVAILABLE' not in content:
                    # Add import at the top after existing imports
                    lines = content.split('\n')
                    import_end = 0
                    
                    for i, line in enumerate(lines):
                        if line.strip().startswith('import ') or line.strip().startswith('from '):
                            import_end = i + 1
                    
                    # Insert Supabase integration
                    lines.insert(import_end, '')
                    lines.insert(import_end + 1, update_template)
                    
                    # Write back
                    with open(script_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    
                    updated_files.append(script_path)
                    print(f"✅ {script_path} aktualisiert")
                else:
                    print(f"ℹ️ {script_path} bereits aktualisiert")
                    
            except Exception as e:
                print(f"❌ Fehler bei {script_path}: {e}")
        else:
            print(f"⚠️ {script_path} nicht gefunden")
    
    if updated_files:
        print(f"\n✅ {len(updated_files)} Skripte erfolgreich aktualisiert")
    
    return len(updated_files) > 0

def verify_integration():
    """
    Verifiziert die Supabase-Integration
    """
    print("🔍 Verifiziere Supabase-Integration...")
    
    try:
        db_client = get_db_client()
        
        # Test database connection
        print("🔗 Teste Datenbankverbindung...")
        if db_client.test_connection():
            print("✅ Datenbankverbindung erfolgreich")
        else:
            print("❌ Datenbankverbindung fehlgeschlagen")
            return False
        
        # Check table counts
        print("📊 Überprüfe Tabellen-Inhalte...")
        
        odds_df = db_client.get_latest_odds()
        predictions_df = db_client.get_predictions()
        results_df = db_client.get_race_results()
        betting_df = db_client.get_betting_performance()
        
        print(f"📈 Odds: {len(odds_df)} Datensätze")
        print(f"🎯 Predictions: {len(predictions_df)} Datensätze")
        print(f"🏁 Ergebnisse: {len(results_df)} Datensätze")
        print(f"💰 Betting: {len(betting_df)} Datensätze")
        
        # Test data quality
        if not odds_df.empty:
            print("✅ Odds-Daten verfügbar")
        if not predictions_df.empty:
            print("✅ Predictions-Daten verfügbar")
        if not results_df.empty:
            print("✅ Ergebnis-Daten verfügbar")
        
        print("✅ Integration erfolgreich verifiziert")
        return True
        
    except Exception as e:
        print(f"❌ Verifikation fehlgeschlagen: {e}")
        return False

def main():
    """
    Hauptfunktion für Supabase-Integration
    """
    print("🚀 Starte Supabase-Integration...")
    print("=" * 50)
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Integrate odds fetcher
    print("\n📈 Schritt 1/5: Enhanced Odds Fetcher Integration")
    if integrate_odds_fetcher():
        success_count += 1
    
    # Step 2: Migrate CSV data
    print("\n📁 Schritt 2/5: CSV-Daten Migration")
    if migrate_csv_data():
        success_count += 1
    
    # Step 3: Update existing scripts
    print("\n🔧 Schritt 3/5: Skript-Updates")
    if update_existing_scripts():
        success_count += 1
    
    # Step 4: Verify integration
    print("\n🔍 Schritt 4/5: Integration-Verifikation")
    if verify_integration():
        success_count += 1
    
    # Step 5: Final summary
    print("\n📋 Schritt 5/5: Zusammenfassung")
    print("=" * 50)
    print(f"✅ Erfolgreich: {success_count}/{total_steps} Schritte")
    
    if success_count == total_steps:
        print("🎉 Supabase-Integration vollständig abgeschlossen!")
        print("\n🔗 Nächste Schritte:")
        print("1. 📊 Dashboard öffnen: http://localhost:8503")
        print("2. 📈 Echte Odds abrufen: python ml/enhanced_odds_fetcher.py")
        print("3. 🎯 Predictions erstellen: python ml/f1_predictor.py")
        print("4. 💰 Betting-Strategien testen: python ml/betting_strategy.py")
        success_count += 1
    else:
        print("⚠️ Integration teilweise erfolgreich")
        print("Bitte überprüfe die Fehler und versuche es erneut.")
    
    return success_count == total_steps

if __name__ == "__main__":
    main()