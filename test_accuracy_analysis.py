import os
import pandas as pd
from datetime import datetime
import sys
sys.path.append('ml')

from ml.prediction_accuracy_analyzer import PredictionAccuracyAnalyzer
from ml.auto_race_evaluator import AutoRaceEvaluator

def create_test_prediction_file():
    """
    Erstellt eine Test-Vorhersagedatei für die Analyse
    """
    print("📝 Erstelle Test-Vorhersagedatei...")
    
    # Simuliere Vorhersagen für Spanish GP 2025
    drivers_data = [
        {'driver': 'VER', 'position': 1, 'probability': 0.85},
        {'driver': 'LEC', 'position': 3, 'probability': 0.72},  # Vorhergesagt P3, tatsächlich P2
        {'driver': 'NOR', 'position': 2, 'probability': 0.68},  # Vorhergesagt P2, tatsächlich P3
        {'driver': 'PER', 'position': 4, 'probability': 0.55},
        {'driver': 'RUS', 'position': 5, 'probability': 0.48},
        {'driver': 'HAM', 'position': 6, 'probability': 0.42},
        {'driver': 'SAI', 'position': 7, 'probability': 0.38},
        {'driver': 'ALO', 'position': 8, 'probability': 0.35},
        {'driver': 'STR', 'position': 9, 'probability': 0.32},
        {'driver': 'GAS', 'position': 10, 'probability': 0.28},
        {'driver': 'OCO', 'position': 11, 'probability': 0.25},
        {'driver': 'ALB', 'position': 12, 'probability': 0.22},
        {'driver': 'TSU', 'position': 13, 'probability': 0.18},
        {'driver': 'BOT', 'position': 14, 'probability': 0.15},
        {'driver': 'ZHO', 'position': 15, 'probability': 0.12},
        {'driver': 'MAG', 'position': 16, 'probability': 0.10},
        {'driver': 'HUL', 'position': 17, 'probability': 0.08},
        {'driver': 'RIC', 'position': 18, 'probability': 0.06},
        {'driver': 'LAW', 'position': 19, 'probability': 0.04},
        {'driver': 'SAR', 'position': 20, 'probability': 0.02}
    ]
    
    df = pd.DataFrame(drivers_data)
    
    # Erstelle Verzeichnis
    os.makedirs('data/live', exist_ok=True)
    
    # Speichere Vorhersagedatei
    pred_file = 'data/live/predicted_probabilities_2025_Spanish_Grand_Prix_full.csv'
    df.to_csv(pred_file, index=False)
    
    print(f"✅ Test-Vorhersagedatei erstellt: {pred_file}")
    return pred_file

def create_test_result_file():
    """
    Erstellt eine Test-Ergebnisdatei
    """
    print("🏁 Erstelle Test-Ergebnisdatei...")
    
    # Tatsächliche Ergebnisse (mit einigen Abweichungen zu den Vorhersagen)
    results_data = [
        {'Driver': 'VER', 'Position': 1},   # Korrekt vorhergesagt
        {'Driver': 'LEC', 'Position': 2},   # Vorhergesagt P3, tatsächlich P2
        {'Driver': 'NOR', 'Position': 3},   # Vorhergesagt P2, tatsächlich P3
        {'Driver': 'PER', 'Position': 4},   # Korrekt
        {'Driver': 'RUS', 'Position': 6},   # Vorhergesagt P5, tatsächlich P6
        {'Driver': 'HAM', 'Position': 5},   # Vorhergesagt P6, tatsächlich P5
        {'Driver': 'SAI', 'Position': 7},   # Korrekt
        {'Driver': 'ALO', 'Position': 9},   # Vorhergesagt P8, tatsächlich P9
        {'Driver': 'STR', 'Position': 8},   # Vorhergesagt P9, tatsächlich P8
        {'Driver': 'GAS', 'Position': 10},  # Korrekt
        {'Driver': 'OCO', 'Position': 11},  # Korrekt
        {'Driver': 'ALB', 'Position': 13},  # Vorhergesagt P12, tatsächlich P13
        {'Driver': 'TSU', 'Position': 12},  # Vorhergesagt P13, tatsächlich P12
        {'Driver': 'BOT', 'Position': 14},  # Korrekt
        {'Driver': 'ZHO', 'Position': 16},  # Vorhergesagt P15, tatsächlich P16
        {'Driver': 'MAG', 'Position': 15},  # Vorhergesagt P16, tatsächlich P15
        {'Driver': 'HUL', 'Position': 17},  # Korrekt
        {'Driver': 'RIC', 'Position': 19},  # Vorhergesagt P18, tatsächlich P19
        {'Driver': 'LAW', 'Position': 18},  # Vorhergesagt P19, tatsächlich P18
        {'Driver': 'SAR', 'Position': 20}   # Korrekt
    ]
    
    df = pd.DataFrame(results_data)
    
    # Erstelle Verzeichnis
    os.makedirs('data/test_results', exist_ok=True)
    
    # Speichere Ergebnisdatei
    result_file = 'data/test_results/spanish_gp_2025_results_accuracy_test.csv'
    df.to_csv(result_file, index=False)
    
    print(f"✅ Test-Ergebnisdatei erstellt: {result_file}")
    return result_file

def test_standalone_accuracy_analyzer():
    """
    Testet den Accuracy Analyzer als eigenständiges Tool
    """
    print("\n" + "="*60)
    print("🔍 TESTE STANDALONE ACCURACY ANALYZER")
    print("="*60)
    
    # Erstelle Test-Dateien
    pred_file = create_test_prediction_file()
    result_file = create_test_result_file()
    
    # Initialisiere Analyzer
    analyzer = PredictionAccuracyAnalyzer()
    
    # Führe Analyse durch
    analysis_result = analyzer.analyze_race_predictions(
        pred_file, result_file, "2025 Spanish Grand Prix"
    )
    
    if analysis_result:
        print("\n📊 ANALYSEERGEBNISSE:")
        print(f"   Gesamt-Score: {analysis_result['overall_score']:.1%}")
        print(f"   Exakte Genauigkeit: {analysis_result['position_accuracy']['exact_accuracy']:.1%}")
        print(f"   Genauigkeit ±3: {analysis_result['position_accuracy']['within_3_accuracy']:.1%}")
        print(f"   Top-3 Genauigkeit: {analysis_result['position_accuracy']['top3_accuracy']:.1%}")
        print(f"   Kalibrierungs-Score: {analysis_result['probability_calibration']['calibration_score']:.1%}")
        
        # Zeige Fehler-Patterns
        error_patterns = analysis_result['error_patterns']
        print(f"\n🔍 FEHLER-ANALYSE:")
        print(f"   Überschätzungsrate: {error_patterns['overestimation_rate']:.1%}")
        print(f"   Unterschätzungsrate: {error_patterns['underestimation_rate']:.1%}")
        
        # Zeige schlechteste Vorhersagen
        worst = error_patterns['worst_predictions'][:3]
        print(f"\n❌ SCHLECHTESTE VORHERSAGEN:")
        for pred in worst:
            print(f"   {pred['driver']}: Vorhergesagt P{pred['position']}, Tatsächlich P{pred['Position']} (Fehler: {pred['position_error']})")
        
        # Speichere Ergebnisse
        analyzer.save_analysis_results()
        
        # Generiere Bericht
        report_file = "data/analysis/test_accuracy_report.txt"
        report = analyzer.generate_comprehensive_report(report_file)
        
        # Erstelle Visualisierung
        viz_file = "data/analysis/test_accuracy_visualization.png"
        analyzer.create_visualization(viz_file)
        
        print(f"\n📁 ERGEBNISSE GESPEICHERT:")
        print(f"   Bericht: {report_file}")
        print(f"   Visualisierung: {viz_file}")
        print(f"   Rohdaten: data/analysis/analysis_results.json")
        
        return True
    else:
        print("❌ Fehler bei der Analyse")
        return False

def test_integrated_accuracy_analysis():
    """
    Testet die Integration in den AutoRaceEvaluator
    """
    print("\n" + "="*60)
    print("🔗 TESTE INTEGRIERTE ACCURACY-ANALYSE")
    print("="*60)
    
    try:
        # Erstelle Test-Dateien
        pred_file = create_test_prediction_file()
        result_file = create_test_result_file()
        
        # Kopiere Ergebnisdatei ins incoming_results Verzeichnis
        os.makedirs('data/incoming_results', exist_ok=True)
        incoming_file = f'data/incoming_results/spanish_gp_2025_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        import shutil
        shutil.copy2(result_file, incoming_file)
        print(f"📥 Ergebnisdatei kopiert nach: {incoming_file}")
        
        # Initialisiere AutoRaceEvaluator
        evaluator = AutoRaceEvaluator()
        
        # Führe Single Check durch (sollte die neue Datei verarbeiten)
        print("\n🔄 Führe automatische Evaluation durch...")
        processed_count = evaluator.run_single_check()
        
        if processed_count > 0:
            print(f"✅ {processed_count} Rennen verarbeitet mit integrierter Accuracy-Analyse")
            
            # Prüfe ob Accuracy-Analyse-Dateien erstellt wurden
            analysis_files = [
                "data/analysis/analysis_results.json",
                "data/analysis/accuracy_history.csv",
                "data/analysis/learning_insights.json"
            ]
            
            print("\n📁 ERSTELLTE ANALYSE-DATEIEN:")
            for file in analysis_files:
                if os.path.exists(file):
                    print(f"   ✅ {file}")
                else:
                    print(f"   ❌ {file} (nicht gefunden)")
            
            return True
        else:
            print("❌ Keine Dateien verarbeitet")
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei der integrierten Analyse: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_learning_insights():
    """
    Zeigt die generierten Lernerkenntnisse
    """
    print("\n" + "="*60)
    print("🧠 LERNERKENNTNISSE UND VERBESSERUNGSVORSCHLÄGE")
    print("="*60)
    
    insights_file = "data/analysis/learning_insights.json"
    if os.path.exists(insights_file):
        import json
        with open(insights_file, 'r', encoding='utf-8') as f:
            insights = json.load(f)
        
        if insights:
            for insight in insights:
                priority_emoji = {
                    'high': '🚨',
                    'medium': '⚠️',
                    'info': 'ℹ️'
                }.get(insight['priority'], '📝')
                
                print(f"\n{priority_emoji} {insight['type'].upper()}:")
                print(f"   Rennen: {insight['race']}")
                print(f"   Nachricht: {insight['message']}")
                print(f"   Empfohlene Aktion: {insight['suggested_action']}")
        else:
            print("Keine Lernerkenntnisse verfügbar.")
    else:
        print(f"❌ Insights-Datei nicht gefunden: {insights_file}")

def main():
    """
    Hauptfunktion für den Test
    """
    print("🔍 F1 PREDICTION ACCURACY ANALYSIS TEST")
    print("Testet das neue Vorhersagegenauigkeits-Analysesystem\n")
    
    # Erstelle notwendige Verzeichnisse
    os.makedirs('data/analysis', exist_ok=True)
    os.makedirs('config', exist_ok=True)
    
    success_count = 0
    
    # Test 1: Standalone Analyzer
    if test_standalone_accuracy_analyzer():
        success_count += 1
    
    # Test 2: Integrierte Analyse
    if test_integrated_accuracy_analysis():
        success_count += 1
    
    # Zeige Lernerkenntnisse
    show_learning_insights()
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("✅ TEST ABGESCHLOSSEN")
    print("="*60)
    
    print(f"🎯 Erfolgreiche Tests: {success_count}/2")
    
    if success_count == 2:
        print("🎉 Alle Tests erfolgreich! Das Accuracy-Analysesystem ist voll funktionsfähig.")
        print("\n🔄 Das System analysiert jetzt automatisch:")
        print("   ✅ Vorhersagegenauigkeit nach jedem Rennen")
        print("   ✅ Identifiziert Fehler-Patterns und Bias")
        print("   ✅ Generiert Lernerkenntnisse")
        print("   ✅ Erstellt Verbesserungsvorschläge")
        print("   ✅ Visualisiert Genauigkeitstrends")
        print("   ✅ Empfiehlt Modell-Retraining bei Bedarf")
    else:
        print("⚠️ Einige Tests fehlgeschlagen. Überprüfe die Fehlermeldungen.")
    
    print("\n📁 Überprüfe diese Verzeichnisse für Details:")
    print("   - data/analysis/ (Alle Analyseergebnisse)")
    print("   - data/processed/ (Betting-Simulation Logs)")
    print("   - data/archive/ (Archivierte Dateien)")

if __name__ == "__main__":
    main()