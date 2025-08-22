#!/usr/bin/env python3
"""
Manueller Test der Post-Race Verarbeitung
Testet die Betting-Simulation direkt ohne Wartezeiten
"""

import os
import pandas as pd
from datetime import datetime
from ml.bet_simulator import F1BetSimulator

def create_test_race_result():
    """
    Erstellt ein simuliertes Rennresultat für das aktuelle Rennen
    """
    print("🏁 Erstelle simuliertes Rennresultat für Spanish GP 2025...")
    
    # Simuliere das Ergebnis basierend auf unseren Wetten
    race_result = {
        'Driver': [
            'VER', 'LEC', 'NOR', 'RUS', 'PIA', 'HAM', 'SAI', 'ALO', 'GAS', 'OCO',
            'TSU', 'ALB', 'HUL', 'LAW', 'BOT', 'ZHO', 'MAG', 'STR', 'RIC', 'SAR'
        ],
        'Actual_Position': list(range(1, 21)),
        'Race_Name': ['2025 Spanish Grand Prix'] * 20
    }
    
    # Erstelle das Verzeichnis falls es nicht existiert
    os.makedirs('data/test_results', exist_ok=True)
    
    # Speichere das Ergebnis
    result_df = pd.DataFrame(race_result)
    result_file = 'data/test_results/spanish_gp_2025_results.csv'
    result_df.to_csv(result_file, index=False)
    
    print(f"✅ Rennresultat gespeichert: {result_file}")
    print("\n📊 Rennresultat:")
    print("   🥇 1. VER (Verstappen)")
    print("   🥈 2. LEC (Leclerc) - UNSERE WETTE! 🎉")
    print("   🥉 3. NOR (Norris) - UNSERE WETTE! 🎉")
    print("   4. RUS (Russell) - UNSERE WETTE! 🎉")
    print("   5. PIA (Piastri)")
    
    return result_file

def update_betting_recommendations():
    """
    Aktualisiert die Betting-Empfehlungen mit dem korrekten Rennnamen
    """
    print("\n📝 Aktualisiere Betting-Empfehlungen...")
    
    betting_file = 'data/live/value_bets.csv'
    if os.path.exists(betting_file):
        df = pd.read_csv(betting_file)
        print(f"📊 Gefunden: {len(df)} Wett-Empfehlungen")
        
        # Zeige die aktuellen Empfehlungen
        recommended_bets = df[df['recommendation'] == 'BET']
        print(f"🎯 Empfohlene Wetten: {len(recommended_bets)}")
        
        if len(recommended_bets) > 0:
            print("\n💰 UNSERE WETTEN:")
            for _, bet in recommended_bets.iterrows():
                print(f"   {bet['driver']} (P{bet['position']}): Quote {bet['odds']:.2f}, EV: €{bet['expected_value']:.2f}")
        
        # Aktualisiere den Rennnamen für die Zuordnung
        df['Race_Name'] = '2025 Spanish Grand Prix'
        
        # Erstelle eine vereinfachte Version für den Simulator
        simulator_df = pd.DataFrame({
            'Driver': df['driver'],
            'Quote': df['odds'],
            'Predicted_Probability': df['probability'],
            'EV': df['expected_value'],
            'Race_Name': df['Race_Name']
        })
        
        # Filtere nur empfohlene Wetten
        simulator_df = simulator_df[df['recommendation'] == 'BET']
        
        simulator_file = 'data/test_results/betting_recommendations_for_simulation.csv'
        simulator_df.to_csv(simulator_file, index=False)
        
        print(f"✅ Simulator-Datei erstellt: {simulator_file}")
        return simulator_file
    else:
        print(f"❌ Betting-Datei nicht gefunden: {betting_file}")
        return None

def run_betting_simulation(betting_file, result_file):
    """
    Führt die Betting-Simulation durch
    """
    print("\n" + "="*60)
    print("🎰 STARTE BETTING-SIMULATION")
    print("="*60)
    
    try:
        # Initialisiere Simulator
        simulator = F1BetSimulator(starting_capital=1000, bet_amount=10)
        
        # Lade Betting-Empfehlungen
        print("📥 Lade Betting-Empfehlungen...")
        if simulator.load_betting_recommendations(betting_file):
            print("✅ Betting-Empfehlungen erfolgreich geladen")
        else:
            print("❌ Fehler beim Laden der Betting-Empfehlungen")
            return
        
        # Lade Rennresultate
        print("📥 Lade Rennresultate...")
        if simulator.load_race_results(result_file):
            print("✅ Rennresultate erfolgreich geladen")
        else:
            print("❌ Fehler beim Laden der Rennresultate")
            return
        
        # Führe Simulation durch
        print("\n🎲 Führe Betting-Simulation durch...")
        total_profit = simulator.simulate_bets(top_n_success=3)
        
        print(f"\n💰 ERGEBNIS: Gesamtgewinn für dieses Rennen: €{total_profit:.2f}")
        
        # Speichere detaillierte Ergebnisse
        os.makedirs('data/processed', exist_ok=True)
        log_file = 'data/processed/test_simulation_log.csv'
        simulator.save_simulation_log(log_file)
        print(f"✅ Detaillierte Ergebnisse gespeichert: {log_file}")
        
        # Zeige Wett-Details
        show_bet_details(simulator.simulation_log)
        
        # Erstelle Gewinn-Grafik
        try:
            graph_file = 'data/processed/test_profit_graph.png'
            simulator.plot_profit_over_time(graph_file)
            print(f"📈 Gewinn-Grafik erstellt: {graph_file}")
        except Exception as e:
            print(f"⚠️ Konnte Grafik nicht erstellen: {e}")
        
        return total_profit
        
    except Exception as e:
        print(f"❌ Fehler bei der Simulation: {e}")
        import traceback
        traceback.print_exc()
        return None

def show_bet_details(simulation_log):
    """
    Zeigt detaillierte Informationen über jede Wette
    """
    print("\n📋 DETAILLIERTE WETT-ERGEBNISSE:")
    print("-" * 60)
    
    total_stake = 0
    total_winnings = 0
    wins = 0
    losses = 0
    
    for bet in simulation_log:
        outcome_emoji = "✅" if bet['Outcome'] == 'WIN' else "❌"
        driver = bet['Driver']
        position = bet['Actual_Position']
        quote = bet['Quote']
        profit = bet['Profit_Loss']
        stake = bet['Bet_Amount']
        
        total_stake += stake
        if bet['Outcome'] == 'WIN':
            wins += 1
            total_winnings += profit + stake
        else:
            losses += 1
        
        print(f"{outcome_emoji} {driver:12} | P{position:2d} | Quote: {quote:5.2f} | Einsatz: €{stake:5.2f} | Gewinn: €{profit:6.2f}")
    
    print("-" * 60)
    print(f"📊 ZUSAMMENFASSUNG:")
    print(f"   Gesamteinsatz: €{total_stake:.2f}")
    print(f"   Gesamtauszahlung: €{total_winnings:.2f}")
    print(f"   Nettogewinn: €{sum(bet['Profit_Loss'] for bet in simulation_log):.2f}")
    print(f"   Gewonnene Wetten: {wins}")
    print(f"   Verlorene Wetten: {losses}")
    print(f"   Gewinnrate: {wins/(wins+losses)*100:.1f}%")

def analyze_our_predictions():
    """
    Analysiert, wie gut unsere Vorhersagen waren
    """
    print("\n" + "="*60)
    print("🔍 ANALYSE UNSERER VORHERSAGEN")
    print("="*60)
    
    # Lade unsere ursprünglichen Vorhersagen
    pred_file = 'data/live/predicted_probabilities_2025_Spanish_Grand_Prix_full.csv'
    if os.path.exists(pred_file):
        pred_df = pd.read_csv(pred_file)
        
        # Zeige Top-Vorhersagen für die ersten 3 Plätze
        for pos in [1, 2, 3]:
            pos_data = pred_df[pred_df['position'] == pos].sort_values('probability', ascending=False)
            if not pos_data.empty:
                top_driver = pos_data.iloc[0]
                print(f"P{pos}: Vorhergesagt {top_driver['driver']} ({top_driver['probability']*100:.1f}%)")
        
        print("\n🎯 Tatsächliches Ergebnis: VER, LEC, NOR")
        print("📊 Unsere Vorhersage-Genauigkeit wird in der Simulation bewertet!")
    
def main():
    """
    Hauptfunktion für den manuellen Test
    """
    print("🏎️ F1 POST-RACE SIMULATION TEST")
    print("Testet die Betting-Simulation nach dem Spanish Grand Prix 2025\n")
    
    # Erstelle notwendige Verzeichnisse
    os.makedirs('data/test_results', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    # Schritt 1: Aktualisiere Betting-Empfehlungen
    betting_file = update_betting_recommendations()
    if not betting_file:
        print("❌ Kann ohne Betting-Empfehlungen nicht fortfahren")
        return
    
    # Schritt 2: Erstelle simuliertes Rennresultat
    result_file = create_test_race_result()
    
    # Schritt 3: Führe Betting-Simulation durch
    profit = run_betting_simulation(betting_file, result_file)
    
    # Schritt 4: Analysiere Vorhersagen
    analyze_our_predictions()
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("✅ SIMULATION ABGESCHLOSSEN")
    print("="*60)
    
    if profit is not None:
        if profit > 0:
            print(f"🎉 GEWINN! Du hast €{profit:.2f} verdient!")
        elif profit == 0:
            print("😐 Ausgeglichen - kein Gewinn, kein Verlust")
        else:
            print(f"😞 Verlust von €{abs(profit):.2f}")
    
    print("\n📁 Überprüfe diese Dateien für Details:")
    print("   - data/processed/test_simulation_log.csv (Detaillierte Ergebnisse)")
    print("   - data/processed/test_profit_graph.png (Gewinn-Grafik)")
    print("   - data/test_results/ (Test-Daten)")
    
    print("\n🔄 Das echte System würde diese Daten automatisch verarbeiten")
    print("   und in die Master-Logs integrieren!")

if __name__ == "__main__":
    main()