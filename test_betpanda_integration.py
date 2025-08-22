#!/usr/bin/env python3
"""
Test-Skript für die neue Betpanda-Integration
"""

import sys
import os
sys.path.append('ml')

from ml.odds_manager import OddsManager, switch_to_betpanda, get_current_odds
import pandas as pd

def test_betpanda_integration():
    """
    Teste die neue Betpanda-Integration
    """
    print("🐼 Betpanda Integration Test")
    print("=" * 50)
    
    # Erstelle Odds Manager
    manager = OddsManager()
    
    # Zeige aktuellen Status
    status = manager.get_status()
    print(f"\n📊 Aktuelle Datenquelle: {status['current_source']}")
    print("\n🔍 Verfügbare Quellen:")
    for source, available in status['available_sources'].items():
        emoji = "✅" if available else "❌"
        print(f"  {source}: {emoji}")
    
    # Teste Betpanda-Verfügbarkeit
    betpanda_available = status['available_sources'].get('betpanda_scraper', False)
    print(f"\n🐼 Betpanda Scraper verfügbar: {'✅' if betpanda_available else '❌'}")
    
    if betpanda_available:
        print("\n🔄 Wechsle zu Betpanda...")
        success = switch_to_betpanda()
        if success:
            print("✅ Erfolgreich zu Betpanda gewechselt!")
            
            # Teste Datenabfrage
            print("\n📊 Lade Testdaten von Betpanda...")
            try:
                df = get_current_odds()
                if not df.empty:
                    print(f"✅ {len(df)} Odds-Einträge erhalten")
                    print("\n📋 Beispieldaten:")
                    print(df.head())
                    
                    # Zeige Bookmaker-Verteilung
                    if 'bookmaker' in df.columns:
                        print("\n📈 Bookmaker-Verteilung:")
                        bookmaker_counts = df['bookmaker'].value_counts()
                        for bookmaker, count in bookmaker_counts.items():
                            print(f"  {bookmaker}: {count} Odds")
                else:
                    print("❌ Keine Daten erhalten")
            except Exception as e:
                print(f"❌ Fehler beim Laden der Daten: {e}")
        else:
            print("❌ Fehler beim Wechseln zu Betpanda")
    else:
        print("❌ Betpanda Scraper nicht verfügbar")
    
    # Teste alle Quellen
    print("\n🔄 Teste alle verfügbaren Quellen...")
    test_results = manager.test_all_sources()
    for source, result in test_results.items():
        success = result.get('success', False)
        emoji = "✅" if success else "❌"
        print(f"  {source}: {emoji}")
        if not success and 'error' in result:
            print(f"    Fehler: {result['error']}")
    
    print("\n🎯 Test abgeschlossen!")

def demo_betpanda_config():
    """
    Zeige Betpanda-Konfiguration
    """
    print("\n🔧 Betpanda-Konfiguration")
    print("=" * 30)
    
    manager = OddsManager()
    config = manager.config.get('betpanda_scraper', {})
    
    print(f"URL: {config.get('url', 'Nicht konfiguriert')}")
    print(f"Aktiviert: {config.get('enabled', False)}")
    print(f"Update-Intervall: {config.get('update_interval_minutes', 'Nicht gesetzt')} Minuten")
    print(f"Max. Wiederholungen: {config.get('max_retries', 'Nicht gesetzt')}")

if __name__ == "__main__":
    try:
        test_betpanda_integration()
        demo_betpanda_config()
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()