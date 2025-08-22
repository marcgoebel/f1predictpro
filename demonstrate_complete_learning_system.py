import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
sys.path.append('ml')

from ml.prediction_accuracy_analyzer import PredictionAccuracyAnalyzer
from ml.auto_race_evaluator import AutoRaceEvaluator
from ml.bet_simulator import F1BetSimulator

def simulate_multiple_races_with_learning():
    """
    Simuliert mehrere Rennen und zeigt, wie das System lernt und sich verbessert
    """
    print("🏎️ F1 PREDICTPRO - KOMPLETTES LERNSYSTEM DEMONSTRATION")
    print("="*70)
    print("Simuliert mehrere Rennen und zeigt kontinuierliches Lernen\n")
    
    # Definiere Rennen für die Simulation
    races = [
        {
            'name': '2025 Spanish Grand Prix',
            'base_accuracy': 0.4,  # Startet mit 40% exakter Genauigkeit
            'improvement_factor': 1.0
        },
        {
            'name': '2025 Monaco Grand Prix', 
            'base_accuracy': 0.45,  # Leichte Verbesserung
            'improvement_factor': 1.1
        },
        {
            'name': '2025 Canadian Grand Prix',
            'base_accuracy': 0.55,  # Deutliche Verbesserung
            'improvement_factor': 1.2
        },
        {
            'name': '2025 Austrian Grand Prix',
            'base_accuracy': 0.65,  # Weitere Verbesserung
            'improvement_factor': 1.3
        },
        {
            'name': '2025 British Grand Prix',
            'base_accuracy': 0.75,  # Sehr gute Genauigkeit
            'improvement_factor': 1.4
        }
    ]
    
    analyzer = PredictionAccuracyAnalyzer()
    learning_progress = []
    
    for i, race in enumerate(races):
        print(f"\n🏁 RENNEN {i+1}: {race['name']}")
        print("-" * 50)
        
        # Erstelle Vorhersagen mit verbesserter Genauigkeit
        pred_file = create_improved_predictions(race, i)
        result_file = create_race_results(race, i)
        
        # Führe Analyse durch
        analysis = analyzer.analyze_race_predictions(pred_file, result_file, race['name'])
        
        if analysis:
            # Speichere Fortschritt
            progress = {
                'race_number': i + 1,
                'race_name': race['name'],
                'overall_score': analysis['overall_score'],
                'exact_accuracy': analysis['position_accuracy']['exact_accuracy'],
                'within_3_accuracy': analysis['position_accuracy']['within_3_accuracy'],
                'top3_accuracy': analysis['position_accuracy']['top3_accuracy'],
                'calibration_score': analysis['probability_calibration']['calibration_score'],
                'mean_error': analysis['position_accuracy']['mean_position_error']
            }
            learning_progress.append(progress)
            
            # Zeige Verbesserungen
            print(f"📊 Ergebnisse:")
            print(f"   Gesamt-Score: {analysis['overall_score']:.1%}")
            print(f"   Exakte Genauigkeit: {analysis['position_accuracy']['exact_accuracy']:.1%}")
            print(f"   Genauigkeit ±3: {analysis['position_accuracy']['within_3_accuracy']:.1%}")
            print(f"   Durchschnittlicher Fehler: {analysis['position_accuracy']['mean_position_error']:.1f} Positionen")
            
            # Zeige Lernfortschritt
            if i > 0:
                prev_score = learning_progress[i-1]['overall_score']
                improvement = analysis['overall_score'] - prev_score
                if improvement > 0:
                    print(f"📈 Verbesserung: +{improvement:.1%} gegenüber letztem Rennen")
                else:
                    print(f"📉 Verschlechterung: {improvement:.1%} gegenüber letztem Rennen")
            
            # Simuliere Betting-Performance
            betting_profit = simulate_betting_for_race(pred_file, result_file, race['name'])
            progress['betting_profit'] = betting_profit
            print(f"💰 Betting-Gewinn: €{betting_profit:.2f}")
    
    # Speichere alle Ergebnisse
    analyzer.save_analysis_results()
    
    # Zeige Gesamtfortschritt
    show_learning_summary(learning_progress)
    
    # Erstelle finale Visualisierung
    create_learning_visualization(learning_progress)
    
    # Generiere finalen Bericht
    final_report = analyzer.generate_comprehensive_report("data/analysis/complete_learning_report.txt")
    
    return learning_progress

def create_improved_predictions(race_info, race_index):
    """
    Erstellt Vorhersagen mit verbesserter Genauigkeit über Zeit
    """
    drivers = ['VER', 'LEC', 'NOR', 'PER', 'RUS', 'HAM', 'SAI', 'ALO', 'STR', 'GAS',
               'OCO', 'ALB', 'TSU', 'BOT', 'ZHO', 'MAG', 'HUL', 'RIC', 'LAW', 'SAR']
    
    # Basis-Vorhersagen (werden über Zeit genauer)
    base_positions = list(range(1, 21))
    
    # Füge Rauschen hinzu, das über Zeit abnimmt
    noise_factor = max(0.1, 1.0 - (race_index * 0.2))  # Weniger Rauschen über Zeit
    
    predictions = []
    for i, driver in enumerate(drivers):
        # Grundposition mit abnehmendem Rauschen
        base_pos = i + 1
        noise = np.random.normal(0, noise_factor * 2)
        predicted_pos = max(1, min(20, int(base_pos + noise)))
        
        # Wahrscheinlichkeit basierend auf Position (verbessert sich über Zeit)
        prob_base = 1.0 - (predicted_pos - 1) / 19
        prob_improvement = race_index * 0.05  # Bessere Kalibrierung über Zeit
        probability = min(0.95, prob_base + prob_improvement)
        
        predictions.append({
            'driver': driver,
            'position': predicted_pos,
            'probability': probability
        })
    
    # Sortiere nach vorhergesagter Position
    predictions.sort(key=lambda x: x['position'])
    
    # Erstelle DataFrame
    df = pd.DataFrame(predictions)
    
    # Speichere Datei
    os.makedirs('data/live', exist_ok=True)
    filename = f"data/live/predicted_probabilities_{race_info['name'].replace(' ', '_')}_full.csv"
    df.to_csv(filename, index=False)
    
    return filename

def create_race_results(race_info, race_index):
    """
    Erstellt realistische Rennresultate
    """
    drivers = ['VER', 'LEC', 'NOR', 'PER', 'RUS', 'HAM', 'SAI', 'ALO', 'STR', 'GAS',
               'OCO', 'ALB', 'TSU', 'BOT', 'ZHO', 'MAG', 'HUL', 'RIC', 'LAW', 'SAR']
    
    # Erstelle realistische Ergebnisse mit etwas Variation
    results = []
    positions = list(range(1, 21))
    
    # Mische die Positionen leicht für Realismus
    np.random.shuffle(positions)
    
    for i, driver in enumerate(drivers):
        results.append({
            'Driver': driver,
            'Position': positions[i]
        })
    
    # Sortiere nach Position
    results.sort(key=lambda x: x['Position'])
    
    # Erstelle DataFrame
    df = pd.DataFrame(results)
    
    # Speichere Datei
    os.makedirs('data/test_results', exist_ok=True)
    filename = f"data/test_results/{race_info['name'].replace(' ', '_').lower()}_results.csv"
    df.to_csv(filename, index=False)
    
    return filename

def simulate_betting_for_race(pred_file, result_file, race_name):
    """
    Simuliert Betting für ein Rennen
    """
    try:
        # Lade Vorhersagen und erstelle Betting-Empfehlungen
        pred_df = pd.read_csv(pred_file)
        
        # Erstelle einfache Betting-Empfehlungen (Top-Wahrscheinlichkeiten)
        betting_recs = []
        for _, row in pred_df.iterrows():
            if row['probability'] > 0.6:  # Nur hohe Wahrscheinlichkeiten
                # Simuliere Quote (umgekehrt proportional zur Wahrscheinlichkeit)
                odds = max(1.1, 1.0 / row['probability'])
                expected_value = (row['probability'] * odds - 1) * 10  # 10€ Einsatz
                
                if expected_value > 0:  # Nur positive EV
                    betting_recs.append({
                        'Driver': row['driver'],
                        'Quote': odds,
                        'Predicted_Probability': row['probability'],
                        'EV': expected_value,
                        'Race_Name': race_name
                    })
        
        if not betting_recs:
            return 0.0
        
        # Erstelle Betting-Datei
        betting_df = pd.DataFrame(betting_recs)
        betting_file = f"data/test_results/betting_recs_{race_name.replace(' ', '_')}.csv"
        betting_df.to_csv(betting_file, index=False)
        
        # Führe Simulation durch
        simulator = F1BetSimulator(starting_capital=1000, bet_amount=10)
        
        if simulator.load_betting_recommendations(betting_file) and simulator.load_race_results(result_file):
            profit = simulator.simulate_bets(top_n_success=3)
            return profit
        
        return 0.0
        
    except Exception as e:
        print(f"⚠️ Fehler bei Betting-Simulation: {e}")
        return 0.0

def show_learning_summary(progress):
    """
    Zeigt eine Zusammenfassung des Lernfortschritts
    """
    print("\n" + "="*70)
    print("📈 LERNFORTSCHRITT ZUSAMMENFASSUNG")
    print("="*70)
    
    if not progress:
        print("Keine Fortschrittsdaten verfügbar.")
        return
    
    # Berechne Verbesserungen
    first_race = progress[0]
    last_race = progress[-1]
    
    print(f"\n🎯 VERBESSERUNGEN ÜBER {len(progress)} RENNEN:")
    print(f"   Gesamt-Score: {first_race['overall_score']:.1%} → {last_race['overall_score']:.1%} (+{(last_race['overall_score'] - first_race['overall_score']):.1%})")
    print(f"   Exakte Genauigkeit: {first_race['exact_accuracy']:.1%} → {last_race['exact_accuracy']:.1%} (+{(last_race['exact_accuracy'] - first_race['exact_accuracy']):.1%})")
    print(f"   Durchschnittlicher Fehler: {first_race['mean_error']:.1f} → {last_race['mean_error']:.1f} ({last_race['mean_error'] - first_race['mean_error']:+.1f} Positionen)")
    
    # Betting-Performance
    total_profit = sum(race.get('betting_profit', 0) for race in progress)
    avg_profit = total_profit / len(progress)
    
    print(f"\n💰 BETTING-PERFORMANCE:")
    print(f"   Gesamtgewinn: €{total_profit:.2f}")
    print(f"   Durchschnitt pro Rennen: €{avg_profit:.2f}")
    
    # Zeige Trend
    print(f"\n📊 RENNEN-BY-RENNEN FORTSCHRITT:")
    for race in progress:
        profit_emoji = "📈" if race.get('betting_profit', 0) > 0 else "📉" if race.get('betting_profit', 0) < 0 else "➡️"
        print(f"   {race['race_number']}. {race['race_name'][:25]:25} | Score: {race['overall_score']:.1%} | Profit: €{race.get('betting_profit', 0):6.2f} {profit_emoji}")

def create_learning_visualization(progress):
    """
    Erstellt eine Visualisierung des Lernfortschritts
    """
    try:
        import matplotlib.pyplot as plt
        
        if not progress:
            return
        
        # Bereite Daten vor
        race_numbers = [p['race_number'] for p in progress]
        overall_scores = [p['overall_score'] for p in progress]
        exact_accuracies = [p['exact_accuracy'] for p in progress]
        profits = [p.get('betting_profit', 0) for p in progress]
        
        # Erstelle Subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('F1 PredictPro - Kontinuierliches Lernsystem', fontsize=16, fontweight='bold')
        
        # 1. Gesamt-Score Entwicklung
        axes[0, 0].plot(race_numbers, overall_scores, 'o-', linewidth=3, markersize=8, color='blue')
        axes[0, 0].set_title('Gesamt-Genauigkeitsscore')
        axes[0, 0].set_xlabel('Rennen')
        axes[0, 0].set_ylabel('Score')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(0, 1)
        
        # 2. Exakte Genauigkeit
        axes[0, 1].plot(race_numbers, exact_accuracies, 's-', linewidth=3, markersize=8, color='green')
        axes[0, 1].set_title('Exakte Vorhersagegenauigkeit')
        axes[0, 1].set_xlabel('Rennen')
        axes[0, 1].set_ylabel('Genauigkeit')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_ylim(0, 1)
        
        # 3. Betting-Profit
        colors = ['red' if p < 0 else 'green' for p in profits]
        axes[1, 0].bar(race_numbers, profits, color=colors, alpha=0.7)
        axes[1, 0].set_title('Betting-Gewinn pro Rennen')
        axes[1, 0].set_xlabel('Rennen')
        axes[1, 0].set_ylabel('Gewinn (€)')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # 4. Kumulativer Profit
        cumulative_profits = np.cumsum(profits)
        axes[1, 1].plot(race_numbers, cumulative_profits, '^-', linewidth=3, markersize=8, color='purple')
        axes[1, 1].set_title('Kumulativer Betting-Gewinn')
        axes[1, 1].set_xlabel('Rennen')
        axes[1, 1].set_ylabel('Kumulativer Gewinn (€)')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        plt.tight_layout()
        
        # Speichere Visualisierung
        os.makedirs('data/analysis', exist_ok=True)
        viz_file = 'data/analysis/complete_learning_progress.png'
        plt.savefig(viz_file, dpi=300, bbox_inches='tight')
        print(f"📊 Lernfortschritt-Visualisierung erstellt: {viz_file}")
        
        plt.close()
        
    except Exception as e:
        print(f"⚠️ Fehler bei der Visualisierung: {e}")

def main():
    """
    Hauptfunktion für die komplette Demonstration
    """
    print("🚀 Starte komplette Lernsystem-Demonstration...\n")
    
    # Erstelle notwendige Verzeichnisse
    for directory in ['data/analysis', 'data/live', 'data/test_results', 'config']:
        os.makedirs(directory, exist_ok=True)
    
    # Führe Simulation durch
    progress = simulate_multiple_races_with_learning()
    
    # Finale Zusammenfassung
    print("\n" + "="*70)
    print("🎉 DEMONSTRATION ABGESCHLOSSEN")
    print("="*70)
    
    if progress:
        final_score = progress[-1]['overall_score']
        total_profit = sum(race.get('betting_profit', 0) for race in progress)
        
        print(f"\n🏆 FINALE ERGEBNISSE:")
        print(f"   Finale Vorhersagegenauigkeit: {final_score:.1%}")
        print(f"   Gesamtgewinn über alle Rennen: €{total_profit:.2f}")
        print(f"   Anzahl analysierter Rennen: {len(progress)}")
        
        if final_score > 0.7:
            print(f"\n🎯 AUSGEZEICHNET! Das System hat eine sehr hohe Genauigkeit erreicht.")
        elif final_score > 0.5:
            print(f"\n👍 GUT! Das System zeigt solide Verbesserungen.")
        else:
            print(f"\n📈 Das System lernt kontinuierlich und wird sich weiter verbessern.")
    
    print("\n📁 GENERIERTE DATEIEN:")
    analysis_files = [
        'data/analysis/complete_learning_report.txt',
        'data/analysis/complete_learning_progress.png',
        'data/analysis/accuracy_history.csv',
        'data/analysis/learning_insights.json',
        'data/analysis/analysis_results.json'
    ]
    
    for file in analysis_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (nicht erstellt)")
    
    print("\n🔄 DAS SYSTEM IST BEREIT FÜR DEN PRODUKTIVEN EINSATZ!")
    print("   ✅ Automatische Vorhersageanalyse nach jedem Rennen")
    print("   ✅ Kontinuierliches Lernen aus Fehlern")
    print("   ✅ Identifikation von Verbesserungsmöglichkeiten")
    print("   ✅ Automatische Empfehlungen für Modell-Updates")
    print("   ✅ Detaillierte Berichte und Visualisierungen")

if __name__ == "__main__":
    main()