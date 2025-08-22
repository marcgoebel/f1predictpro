#!/usr/bin/env python3
"""
Kompletter System-Test für F1 Analytics Hub
Überprüft alle Verbindungen zwischen Supabase, ML-Features und Dashboards
"""

import os
import sys
import pandas as pd
import json
from datetime import datetime
import subprocess
import time
import requests

# Add ML directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml'))

def test_supabase_connection():
    """
    Teste Supabase-Datenbankverbindung
    """
    print("\n🔗 1. Teste Supabase-Verbindung...")
    try:
        from database.supabase_client import get_db_client
        db_client = get_db_client()
        
        # Test connection
        if db_client.test_connection():
            print("✅ Supabase-Verbindung erfolgreich")
            
            # Check table counts
            odds_df = db_client.get_latest_odds()
            predictions_df = db_client.get_predictions()
            results_df = db_client.get_race_results()
            betting_df = db_client.get_betting_performance()
            
            print(f"📊 Datenbank-Status:")
            print(f"   📈 Odds: {len(odds_df)} Datensätze")
            print(f"   🎯 Predictions: {len(predictions_df)} Datensätze")
            print(f"   🏁 Ergebnisse: {len(results_df)} Datensätze")
            print(f"   💰 Betting: {len(betting_df)} Datensätze")
            
            return True
        else:
            print("❌ Supabase-Verbindung fehlgeschlagen")
            return False
            
    except Exception as e:
        print(f"❌ Supabase-Test fehlgeschlagen: {e}")
        return False

def test_enhanced_odds_fetcher():
    """
    Teste Enhanced Odds Fetcher
    """
    print("\n📈 2. Teste Enhanced Odds Fetcher...")
    try:
        from enhanced_odds_fetcher import EnhancedOddsFetcher
        from database.supabase_client import get_db_client
        
        db_client = get_db_client()
        odds_fetcher = EnhancedOddsFetcher(db_client)
        
        print("✅ Enhanced Odds Fetcher initialisiert")
        
        # Test database integration
        latest_odds = odds_fetcher.get_latest_odds()
        if not latest_odds.empty:
            print(f"✅ {len(latest_odds)} Odds aus Datenbank abgerufen")
        else:
            print("ℹ️ Keine Odds in Datenbank (normal bei ersten Tests)")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Odds Fetcher Test fehlgeschlagen: {e}")
        return False

def test_betting_strategy():
    """
    Teste Betting Strategy Integration
    """
    print("\n💰 3. Teste Betting Strategy...")
    try:
        # Check if betting_strategy.py runs without errors
        result = subprocess.run(
            [sys.executable, 'ml/betting_strategy.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Betting Strategy läuft erfolgreich")
            if "Connected to Supabase" in result.stdout:
                print("✅ Supabase-Integration in Betting Strategy aktiv")
            return True
        else:
            print(f"❌ Betting Strategy Fehler: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Betting Strategy Test fehlgeschlagen: {e}")
        return False

def test_auto_race_monitor():
    """
    Teste Auto Race Monitor
    """
    print("\n🏁 4. Teste Auto Race Monitor...")
    try:
        result = subprocess.run(
            [sys.executable, 'ml/auto_race_monitor.py', 'status'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Auto Race Monitor läuft")
            if "Connected to Supabase" in result.stdout:
                print("✅ Supabase-Integration in Auto Race Monitor aktiv")
            
            # Parse JSON output
            try:
                lines = result.stdout.strip().split('\n')
                json_line = None
                for line in lines:
                    if line.strip().startswith('{'):
                        json_line = line
                        break
                
                if json_line:
                    status = json.loads(json_line)
                    print(f"📊 Monitor Status: {len(status.get('files_status', {}))} Dateien überwacht")
            except:
                pass
            
            return True
        else:
            print(f"❌ Auto Race Monitor Fehler: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Auto Race Monitor Test fehlgeschlagen: {e}")
        return False

def test_dashboards():
    """
    Teste Dashboard-Verfügbarkeit
    """
    print("\n📊 5. Teste Dashboards...")
    
    dashboards = {
        'Supabase Dashboard': 'http://localhost:8503',
        'Original Dashboard': 'http://localhost:8504'
    }
    
    results = {}
    
    for name, url in dashboards.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} verfügbar: {url}")
                results[name] = True
            else:
                print(f"⚠️ {name} antwortet nicht korrekt: {url}")
                results[name] = False
        except requests.exceptions.RequestException:
            print(f"❌ {name} nicht erreichbar: {url}")
            results[name] = False
    
    return any(results.values())

def test_data_files():
    """
    Teste wichtige Datendateien
    """
    print("\n📁 6. Teste Datendateien...")
    
    important_files = {
        'Race Schedule': 'data/live/race_schedule.json',
        'Sample Odds': 'data/live/sample_odds.csv',
        'Betting Recommendations': 'data/live/betting_recommendations.csv',
        'Training Data': 'data/full/full_training_data.csv'
    }
    
    file_status = {}
    
    for name, path in important_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"✅ {name}: {size} bytes")
            file_status[name] = True
        else:
            print(f"❌ {name} nicht gefunden: {path}")
            file_status[name] = False
    
    return sum(file_status.values()) >= len(file_status) // 2

def test_ml_scripts():
    """
    Teste wichtige ML-Skripte
    """
    print("\n🤖 7. Teste ML-Skripte...")
    
    ml_scripts = [
        'ml/enhanced_odds_fetcher.py',
        'ml/betting_strategy.py',
        'ml/auto_race_monitor.py',
        'ml/value_bet_calculator.py'
    ]
    
    working_scripts = 0
    
    for script in ml_scripts:
        if os.path.exists(script):
            print(f"✅ {script} verfügbar")
            working_scripts += 1
        else:
            print(f"❌ {script} nicht gefunden")
    
    print(f"📊 {working_scripts}/{len(ml_scripts)} ML-Skripte verfügbar")
    return working_scripts >= len(ml_scripts) // 2

def test_integration_completeness():
    """
    Teste Vollständigkeit der Integration
    """
    print("\n🔧 8. Teste Integration-Vollständigkeit...")
    
    integration_checks = {
        'Supabase Client': 'ml/database/supabase_client.py',
        'Integration Script': 'integrate_supabase.py',
        'System Test': 'test_supabase_integration.py',
        'Documentation': 'SUPABASE_INTEGRATION.md'
    }
    
    integration_status = {}
    
    for name, path in integration_checks.items():
        if os.path.exists(path):
            print(f"✅ {name} vorhanden")
            integration_status[name] = True
        else:
            print(f"❌ {name} fehlt: {path}")
            integration_status[name] = False
    
    return all(integration_status.values())

def generate_system_report(test_results):
    """
    Generiere System-Report
    """
    print("\n" + "=" * 60)
    print("📋 SYSTEM-REPORT")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"\n📊 Gesamt-Ergebnis: {passed_tests}/{total_tests} Tests bestanden")
    print(f"🎯 Erfolgsrate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📋 Detaillierte Ergebnisse:")
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALLE TESTS BESTANDEN!")
        print("✅ Das System ist vollständig integriert und funktionsfähig")
        
        print("\n🚀 Verfügbare Features:")
        print("   📊 Supabase Dashboard: http://localhost:8503")
        print("   📈 Original Dashboard: http://localhost:8504")
        print("   💰 Betting Strategies mit Supabase-Integration")
        print("   🏁 Auto Race Monitor mit Datenbank-Anbindung")
        print("   📈 Enhanced Odds Fetcher")
        
    elif passed_tests >= total_tests * 0.7:
        print("\n⚠️ SYSTEM WEITGEHEND FUNKTIONSFÄHIG")
        print("Die meisten Features funktionieren, einige benötigen Aufmerksamkeit")
        
    else:
        print("\n❌ SYSTEM BENÖTIGT AUFMERKSAMKEIT")
        print("Mehrere kritische Komponenten funktionieren nicht korrekt")
    
    # Save report
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'success_rate': (passed_tests/total_tests)*100,
        'test_results': test_results
    }
    
    with open('system_test_report.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n💾 Report gespeichert: system_test_report.json")
    
    return passed_tests == total_tests

def main():
    """
    Hauptfunktion für kompletten System-Test
    """
    print("🚀 F1 Analytics Hub - Kompletter System-Test")
    print("=" * 60)
    print(f"🕒 Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Führe alle Tests durch
    test_results = {
        'Supabase Connection': test_supabase_connection(),
        'Enhanced Odds Fetcher': test_enhanced_odds_fetcher(),
        'Betting Strategy': test_betting_strategy(),
        'Auto Race Monitor': test_auto_race_monitor(),
        'Dashboards': test_dashboards(),
        'Data Files': test_data_files(),
        'ML Scripts': test_ml_scripts(),
        'Integration Completeness': test_integration_completeness()
    }
    
    # Generiere Report
    system_healthy = generate_system_report(test_results)
    
    return system_healthy

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)