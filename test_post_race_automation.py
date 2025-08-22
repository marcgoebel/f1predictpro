#!/usr/bin/env python3
"""
Test Script für Post-Race Automatisierung
Simuliert das Verhalten nach einem echten F1 Rennen
"""

import os
import pandas as pd
import time
from datetime import datetime
from ml.auto_race_evaluator import AutoRaceEvaluator
from ml.bet_simulator import F1BetSimulator

def create_test_race_result():
    """
    Erstellt ein simuliertes Rennresultat für das aktuelle Rennen
    """
    print("🏁 Erstelle simuliertes Rennresultat...")
    
    # Simuliere das Ergebnis des Spanish Grand Prix 2025
    race_result = {
        'Driver': [
            'VER', 'LEC', 'NOR', 'RUS', 'PIA', 'HAM', 'SAI', 'ALO', 'GAS', 'OCO',
            'TSU', 'ALB', 'HUL', 'LAW', 'BOT', 'ZHO', 'MAG', 'STR', 'RIC', 'SAR'
        ],
        'Actual_Position': list(range(1, 21)),
        'Race_Name': ['2025 Spanish Grand Prix'] * 20
    }
    
    # Erstelle das Verzeichnis falls es nicht existiert
    os.makedirs('data/incoming_results', exist_ok=True)
    
    # Speichere das Ergebnis
    result_df = pd.DataFrame(race_result)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f'data/incoming_results/spanish_gp_2025_results_{timestamp}.csv'
    result_df.to_csv(result_file, index=False)
    
    print(f"✅ Rennresultat gespeichert: {result_file}")
    print("📊 Ergebnis:")
    print("   1. VER (Verstappen)")
    print("   2. LEC (Leclerc) - GEWINN! 🎉")
    print("   3. NOR (Norris) - GEWINN! 🎉")
    print("   4. RUS (Russell) - GEWINN! 🎉")
    print("   5. PIA (Piastri)")
    
    return result_file

def update_betting_recommendations():
    """
    Aktualisiert die Betting-Empfehlungen mit dem korrekten Rennnamen
    """
    print("📝 Aktualisiere Betting-Empfehlungen...")
    
    betting_file = 'data/live/value_bets.csv'
    if os.path.exists(betting_file):
        df = pd.read_csv(betting_file)
        # Aktualisiere den Rennnamen für die Zuordnung
        df['Race_Name'] = '2025 Spanish Grand Prix'
        df.to_csv(betting_file, index=False)
        print(f"✅ Betting-Empfehlungen aktualisiert: {betting_file}")
        return True
    else:
        print(f"❌ Betting-Datei nicht gefunden: {betting_file}")
        return False

def test_automated_evaluation():
    """
    Testet die automatisierte Auswertung nach dem Rennen
    """
    print("\n" + "="*60)
    print("🤖 TESTE POST-RACE AUTOMATISIERUNG")
    print("="*60)
    
    # Schritt 1: Aktualisiere Betting-Empfehlungen
    if not update_betting_recommendations():
        print("❌ Kann ohne Betting-Empfehlungen nicht fortfahren")
        return
    
    # Schritt 2: Erstelle simuliertes Rennresultat
    result_file = create_test_race_result()
    
    # Schritt 3: Warte kurz (simuliert Datei-Upload)
    print("\n⏳ Warte 3 Sekunden (simuliert Datei-Upload)...")
    time.sleep(3)
    
    # Schritt 4: Starte automatische Auswertung
    print("\n🔄 Starte automatische Auswertung...")
    
    try:
        # Initialisiere den Auto-Evaluator
        evaluator = AutoRaceEvaluator()
        
        # Führe eine einzelne Überprüfung durch
        processed_count = evaluator.run_single_check()
        
        if processed_count > 0:
            print(f"\n🎉 ERFOLG! {processed_count} Datei(en) verarbeitet")
            
            # Zeige die Ergebnisse
            show_results()
            
        else:
            print("\n⚠️ Keine neuen Dateien zur Verarbeitung gefunden")
            print("Mögliche Gründe:")
            print("- Datei wurde bereits verarbeitet")
            print("- Datei ist zu neu (< 30 Sekunden)")
            print("- Konfigurationsproblem")
            
    except Exception as e:
        print(f"\n❌ Fehler bei der automatischen Auswertung: {e}")
        print("\n🔧 Versuche manuelle Verarbeitung...")
        manual_processing(result_file)

def manual_processing(result_file):
    """
    Manuelle Verarbeitung falls die Automatisierung fehlschlägt
    """
    try:
        print("\n🛠️ Starte manuelle Verarbeitung...")
        
        # Lade die Daten
        betting_file = 'data/live/value_bets.csv'
        
        if not os.path.exists(betting_file):
            print(f"❌ Betting-Datei nicht gefunden: {betting_file}")
            return
            
        # Initialisiere Simulator
        simulator = F1BetSimulator(starting_capital=1000, bet_amount=10)
        
        # Lade Daten
        if simulator.load_betting_recommendations(betting_file):
            print("✅ Betting-Empfehlungen geladen")
        else:
            print("❌ Fehler beim Laden der Betting-Empfehlungen")
            return
            
        if simulator.load_race_results(result_file):
            print("✅ Rennresultate geladen")
        else:
            print("❌ Fehler beim Laden der Rennresultate")
            return
        
        # Führe Simulation durch
        total_profit = simulator.simulate_bets(top_n_success=3)
        
        print(f"\n💰 Gesamtgewinn für dieses Rennen: €{total_profit:.2f}")
        
        # Speichere Ergebnisse
        log_file = 'data/processed/manual_simulation_log.csv'
        simulator.save_simulation_log(log_file)
        print(f"✅ Simulation gespeichert: {log_file}")
        
        # Zeige Details
        show_bet_details(simulator.simulation_log)
        
    except Exception as e:
        print(f"❌ Fehler bei manueller Verarbeitung: {e}")

def show_results():
    """
    Zeigt die Ergebnisse der automatischen Auswertung
    """
    print("\n📊 ERGEBNISSE DER AUTOMATISCHEN AUSWERTUNG")
    print("-" * 50)
    
    # Prüfe ob Log-Dateien existieren
    log_file = 'data/processed/bet_simulation_log.csv'
    summary_file = 'data/processed/bet_simulation_log_summary.csv'
    
    if os.path.exists(log_file):
        df = pd.read_csv(log_file)
        # Zeige nur die neuesten Einträge (letztes Rennen)
        latest_race = df['Race_Name'].iloc[-1]
        race_data = df[df['Race_Name'] == latest_race]
        
        print(f"🏁 Rennen: {latest_race}")
        print(f"🎯 Anzahl Wetten: {len(race_data)}")
        
        wins = race_data[race_data['Outcome'] == 'WIN']
        losses = race_data[race_data['Outcome'] == 'LOSS']
        
        print(f"✅ Gewonnene Wetten: {len(wins)}")
        print(f"❌ Verlorene Wetten: {len(losses)}")
        
        total_profit = race_data['Profit_Loss'].sum()
        print(f"💰 Gesamtgewinn: €{total_profit:.2f}")
        
        if len(wins) > 0:
            print("\n🎉 GEWINNENDE WETTEN:")
            for _, bet in wins.iterrows():
                print(f"   {bet['Driver']}: €{bet['Profit_Loss']:.2f} (Quote: {bet['Quote']})")
    
    if os.path.exists(summary_file):
        summary_df = pd.read_csv(summary_file)
        if not summary_df.empty:
            latest = summary_df.iloc[-1]
            print(f"\n📈 GESAMTSTATISTIK:")
            print(f"   Gesamtkapital: €{latest['Total_Capital']:.2f}")
            print(f"   Kumulativer Gewinn: €{latest['Cumulative_Profit']:.2f}")
            print(f"   Gewinnrate: {latest['Win_Rate']*100:.1f}%")

def show_bet_details(simulation_log):
    """
    Zeigt Details der Wetten
    """
    print("\n📋 WETT-DETAILS:")
    print("-" * 40)
    
    for bet in simulation_log:
        outcome_emoji = "✅" if bet['Outcome'] == 'WIN' else "❌"
        print(f"{outcome_emoji} {bet['Driver']}: Position {bet['Actual_Position']} - €{bet['Profit_Loss']:.2f}")

def main():
    """
    Hauptfunktion für den Test
    """
    print("🏎️ F1 POST-RACE AUTOMATISIERUNG TEST")
    print("Dieser Test simuliert, was nach einem echten Rennen passiert\n")
    
    # Erstelle notwendige Verzeichnisse
    os.makedirs('data/incoming_results', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('data/archive', exist_ok=True)
    os.makedirs('config', exist_ok=True)
    
    # Starte den Test
    test_automated_evaluation()
    
    print("\n" + "="*60)
    print("✅ TEST ABGESCHLOSSEN")
    print("="*60)
    print("\n📁 Überprüfe diese Verzeichnisse für Ergebnisse:")
    print("   - data/processed/ (Logs und Grafiken)")
    print("   - data/archive/ (Archivierte Dateien)")
    print("   - logs/ (System-Logs)")

if __name__ == "__main__":
    main()