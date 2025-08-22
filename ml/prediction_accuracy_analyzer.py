import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import json
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class PredictionAccuracyAnalyzer:
    """
    Analysiert die Genauigkeit von F1-Vorhersagen und lernt aus Fehlern
    """
    
    def __init__(self, config_file="config/accuracy_analyzer_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.analysis_results = []
        self.learning_insights = []
        
    def load_config(self) -> Dict[str, Any]:
        """Lädt Konfiguration oder erstellt Standard-Konfiguration"""
        default_config = {
            "prediction_files_pattern": "data/live/predicted_probabilities_*_full.csv",
            "results_files_pattern": "data/incoming_results/*.csv",
            "output_directory": "data/analysis",
            "accuracy_threshold": 0.7,
            "learning_log_file": "data/analysis/learning_insights.json",
            "accuracy_history_file": "data/analysis/accuracy_history.csv",
            "error_patterns_file": "data/analysis/error_patterns.json",
            "improvement_suggestions_file": "data/analysis/improvement_suggestions.txt"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge mit Default-Werten
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"⚠️ Fehler beim Laden der Konfiguration: {e}")
                return default_config
        else:
            # Erstelle Standard-Konfiguration
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def analyze_race_predictions(self, prediction_file: str, result_file: str, race_name: str) -> Dict[str, Any]:
        """
        Analysiert Vorhersagen für ein spezifisches Rennen
        """
        print(f"\n🔍 Analysiere Vorhersagen für {race_name}")
        
        try:
            # Lade Vorhersagen
            pred_df = pd.read_csv(prediction_file)
            result_df = pd.read_csv(result_file)
            
            # Bereite Daten vor
            analysis = self._prepare_analysis_data(pred_df, result_df, race_name)
            
            # Führe verschiedene Analysen durch
            position_accuracy = self._analyze_position_accuracy(analysis)
            probability_calibration = self._analyze_probability_calibration(analysis)
            top_predictions = self._analyze_top_predictions(analysis)
            error_patterns = self._identify_error_patterns(analysis)
            
            # Kombiniere Ergebnisse
            race_analysis = {
                'race_name': race_name,
                'timestamp': datetime.now().isoformat(),
                'total_drivers': len(analysis),
                'position_accuracy': position_accuracy,
                'probability_calibration': probability_calibration,
                'top_predictions': top_predictions,
                'error_patterns': error_patterns,
                'overall_score': self._calculate_overall_score(position_accuracy, probability_calibration, top_predictions)
            }
            
            self.analysis_results.append(race_analysis)
            
            # Generiere Lernerkenntnisse
            insights = self._generate_learning_insights(race_analysis)
            self.learning_insights.extend(insights)
            
            print(f"✅ Analyse für {race_name} abgeschlossen")
            return race_analysis
            
        except Exception as e:
            print(f"❌ Fehler bei der Analyse von {race_name}: {e}")
            return None
    
    def _prepare_analysis_data(self, pred_df: pd.DataFrame, result_df: pd.DataFrame, race_name: str) -> pd.DataFrame:
        """Bereitet Daten für die Analyse vor"""
        # Normalisiere Fahrernamen
        pred_df['driver_clean'] = pred_df['driver'].str.upper().str.strip()
        result_df['driver_clean'] = result_df['Driver'].str.upper().str.strip()
        
        # Merge Vorhersagen mit Ergebnissen
        analysis_df = pd.merge(
            pred_df, result_df, 
            left_on='driver_clean', right_on='driver_clean',
            how='inner'
        )
        
        # Berechne Abweichungen
        analysis_df['position_error'] = abs(analysis_df['position'] - analysis_df['Position'])
        analysis_df['probability_vs_result'] = analysis_df.apply(
            lambda row: row['probability'] if row['Position'] == row['position'] else 0, axis=1
        )
        
        return analysis_df
    
    def _analyze_position_accuracy(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analysiert die Genauigkeit der Positionsvorhersagen"""
        total = len(df)
        
        # Exakte Treffer
        exact_hits = (df['position_error'] == 0).sum()
        
        # Treffer innerhalb verschiedener Toleranzen
        within_1 = (df['position_error'] <= 1).sum()
        within_2 = (df['position_error'] <= 2).sum()
        within_3 = (df['position_error'] <= 3).sum()
        
        # Top-Positionen Genauigkeit
        top3_df = df[df['position'] <= 3]
        top3_accuracy = (top3_df['Position'] <= 3).sum() / len(top3_df) if len(top3_df) > 0 else 0
        
        top10_df = df[df['position'] <= 10]
        top10_accuracy = (top10_df['Position'] <= 10).sum() / len(top10_df) if len(top10_df) > 0 else 0
        
        return {
            'exact_accuracy': exact_hits / total,
            'within_1_accuracy': within_1 / total,
            'within_2_accuracy': within_2 / total,
            'within_3_accuracy': within_3 / total,
            'top3_accuracy': top3_accuracy,
            'top10_accuracy': top10_accuracy,
            'mean_position_error': df['position_error'].mean(),
            'median_position_error': df['position_error'].median()
        }
    
    def _analyze_probability_calibration(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analysiert die Kalibrierung der Wahrscheinlichkeiten"""
        # Gruppiere nach Wahrscheinlichkeits-Bins
        df['prob_bin'] = pd.cut(df['probability'], bins=10, labels=False)
        
        calibration_data = []
        for bin_idx in range(10):
            bin_data = df[df['prob_bin'] == bin_idx]
            if len(bin_data) > 0:
                avg_prob = bin_data['probability'].mean()
                actual_success_rate = (bin_data['position_error'] == 0).mean()
                calibration_data.append({
                    'bin': bin_idx,
                    'avg_probability': avg_prob,
                    'actual_success_rate': actual_success_rate,
                    'calibration_error': abs(avg_prob - actual_success_rate)
                })
        
        if calibration_data:
            avg_calibration_error = np.mean([d['calibration_error'] for d in calibration_data])
            max_calibration_error = np.max([d['calibration_error'] for d in calibration_data])
        else:
            avg_calibration_error = 1.0
            max_calibration_error = 1.0
        
        return {
            'average_calibration_error': avg_calibration_error,
            'max_calibration_error': max_calibration_error,
            'calibration_score': 1 - avg_calibration_error,
            'calibration_data': calibration_data
        }
    
    def _analyze_top_predictions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analysiert die Genauigkeit der Top-Vorhersagen"""
        # Sortiere nach Wahrscheinlichkeit
        df_sorted = df.sort_values('probability', ascending=False)
        
        # Top-N Vorhersagen
        results = {}
        for n in [1, 3, 5, 10]:
            top_n = df_sorted.head(n)
            if len(top_n) > 0:
                # Wie viele der Top-N Vorhersagen waren in den Top-N Ergebnissen?
                top_n_actual = set(df.nsmallest(n, 'Position')['driver'].values)
                top_n_predicted = set(top_n['driver'].values)
                overlap = len(top_n_actual.intersection(top_n_predicted))
                
                results[f'top_{n}_precision'] = overlap / n
                results[f'top_{n}_recall'] = overlap / min(n, len(df))
        
        return results
    
    def _identify_error_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identifiziert Muster in den Vorhersagefehlern"""
        # Fahrer mit größten Fehlern
        worst_predictions = df.nlargest(5, 'position_error')[['driver', 'position', 'Position', 'position_error']]
        
        # Systematische Über-/Unterschätzungen
        overestimations = df[df['position'] < df['Position']]  # Vorhergesagt besser als tatsächlich
        underestimations = df[df['position'] > df['Position']]  # Vorhergesagt schlechter als tatsächlich
        
        # Positionsbereiche mit hohen Fehlern
        position_errors = df.groupby('position')['position_error'].agg(['mean', 'count']).reset_index()
        
        return {
            'worst_predictions': worst_predictions.to_dict('records'),
            'overestimation_rate': len(overestimations) / len(df),
            'underestimation_rate': len(underestimations) / len(df),
            'avg_overestimation_error': overestimations['position_error'].mean() if len(overestimations) > 0 else 0,
            'avg_underestimation_error': underestimations['position_error'].mean() if len(underestimations) > 0 else 0,
            'position_error_distribution': position_errors.to_dict('records')
        }
    
    def _calculate_overall_score(self, position_acc: Dict, prob_cal: Dict, top_pred: Dict) -> float:
        """Berechnet einen Gesamt-Genauigkeitsscore"""
        # Gewichtete Kombination verschiedener Metriken
        weights = {
            'exact_accuracy': 0.3,
            'within_3_accuracy': 0.2,
            'top3_accuracy': 0.2,
            'calibration_score': 0.15,
            'top_3_precision': 0.15
        }
        
        score = 0
        for metric, weight in weights.items():
            if metric in position_acc:
                score += position_acc[metric] * weight
            elif metric in prob_cal:
                score += prob_cal[metric] * weight
            elif metric in top_pred:
                score += top_pred[metric] * weight
        
        return min(1.0, max(0.0, score))
    
    def _generate_learning_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generiert Lernerkenntnisse aus der Analyse"""
        insights = []
        race_name = analysis['race_name']
        
        # Genauigkeits-Insights
        exact_acc = analysis['position_accuracy']['exact_accuracy']
        if exact_acc < 0.1:
            insights.append({
                'type': 'accuracy_warning',
                'race': race_name,
                'message': f'Sehr niedrige exakte Genauigkeit ({exact_acc:.1%}). Modell benötigt Überarbeitung.',
                'priority': 'high',
                'suggested_action': 'model_retraining'
            })
        
        # Kalibrierungs-Insights
        cal_error = analysis['probability_calibration']['average_calibration_error']
        if cal_error > 0.2:
            insights.append({
                'type': 'calibration_warning',
                'race': race_name,
                'message': f'Schlechte Wahrscheinlichkeits-Kalibrierung (Fehler: {cal_error:.2f}). Wahrscheinlichkeiten sind unzuverlässig.',
                'priority': 'medium',
                'suggested_action': 'probability_recalibration'
            })
        
        # Fehler-Pattern Insights
        error_patterns = analysis['error_patterns']
        if error_patterns['overestimation_rate'] > 0.7:
            insights.append({
                'type': 'bias_warning',
                'race': race_name,
                'message': f'Systematische Überschätzung der Fahrerleistung ({error_patterns["overestimation_rate"]:.1%}). Modell ist zu optimistisch.',
                'priority': 'medium',
                'suggested_action': 'bias_correction'
            })
        elif error_patterns['underestimation_rate'] > 0.7:
            insights.append({
                'type': 'bias_warning',
                'race': race_name,
                'message': f'Systematische Unterschätzung der Fahrerleistung ({error_patterns["underestimation_rate"]:.1%}). Modell ist zu pessimistisch.',
                'priority': 'medium',
                'suggested_action': 'bias_correction'
            })
        
        # Positive Insights
        overall_score = analysis['overall_score']
        if overall_score > 0.8:
            insights.append({
                'type': 'success',
                'race': race_name,
                'message': f'Ausgezeichnete Vorhersagegenauigkeit ({overall_score:.1%}). Modell funktioniert sehr gut.',
                'priority': 'info',
                'suggested_action': 'maintain_current_approach'
            })
        
        return insights
    
    def generate_comprehensive_report(self, output_file: str = None) -> str:
        """Generiert einen umfassenden Analysebericht"""
        if not self.analysis_results:
            return "Keine Analyseergebnisse verfügbar."
        
        report_lines = []
        report_lines.append("# F1 PREDICTION ACCURACY ANALYSIS REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("\n" + "="*60 + "\n")
        
        # Zusammenfassung
        total_races = len(self.analysis_results)
        avg_score = np.mean([r['overall_score'] for r in self.analysis_results])
        
        report_lines.append(f"## ZUSAMMENFASSUNG")
        report_lines.append(f"- Analysierte Rennen: {total_races}")
        report_lines.append(f"- Durchschnittlicher Genauigkeitsscore: {avg_score:.1%}")
        report_lines.append("")
        
        # Detaillierte Ergebnisse pro Rennen
        report_lines.append("## DETAILLIERTE ERGEBNISSE")
        for result in self.analysis_results:
            race_name = result['race_name']
            score = result['overall_score']
            pos_acc = result['position_accuracy']
            
            report_lines.append(f"\n### {race_name}")
            report_lines.append(f"- Gesamt-Score: {score:.1%}")
            report_lines.append(f"- Exakte Genauigkeit: {pos_acc['exact_accuracy']:.1%}")
            report_lines.append(f"- Genauigkeit ±3 Positionen: {pos_acc['within_3_accuracy']:.1%}")
            report_lines.append(f"- Top-3 Genauigkeit: {pos_acc['top3_accuracy']:.1%}")
            report_lines.append(f"- Durchschnittlicher Positionsfehler: {pos_acc['mean_position_error']:.1f}")
        
        # Lernerkenntnisse
        if self.learning_insights:
            report_lines.append("\n## LERNERKENNTNISSE UND VERBESSERUNGSVORSCHLÄGE")
            
            # Gruppiere nach Priorität
            high_priority = [i for i in self.learning_insights if i['priority'] == 'high']
            medium_priority = [i for i in self.learning_insights if i['priority'] == 'medium']
            
            if high_priority:
                report_lines.append("\n### 🚨 HOHE PRIORITÄT")
                for insight in high_priority:
                    report_lines.append(f"- {insight['message']}")
                    report_lines.append(f"  Empfohlene Aktion: {insight['suggested_action']}")
            
            if medium_priority:
                report_lines.append("\n### ⚠️ MITTLERE PRIORITÄT")
                for insight in medium_priority:
                    report_lines.append(f"- {insight['message']}")
                    report_lines.append(f"  Empfohlene Aktion: {insight['suggested_action']}")
        
        # Verbesserungsempfehlungen
        report_lines.append("\n## KONKRETE VERBESSERUNGSEMPFEHLUNGEN")
        recommendations = self._generate_improvement_recommendations()
        for rec in recommendations:
            report_lines.append(f"- {rec}")
        
        report = "\n".join(report_lines)
        
        # Speichere Bericht
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 Bericht gespeichert: {output_file}")
        
        return report
    
    def _generate_improvement_recommendations(self) -> List[str]:
        """Generiert konkrete Verbesserungsempfehlungen"""
        recommendations = []
        
        if not self.analysis_results:
            return ["Keine Daten für Empfehlungen verfügbar."]
        
        # Analysiere Trends
        avg_exact_acc = np.mean([r['position_accuracy']['exact_accuracy'] for r in self.analysis_results])
        avg_cal_error = np.mean([r['probability_calibration']['average_calibration_error'] for r in self.analysis_results])
        
        if avg_exact_acc < 0.15:
            recommendations.append("Modell-Features überarbeiten: Aktuelle exakte Genauigkeit zu niedrig")
            recommendations.append("Mehr historische Daten für Training verwenden")
            recommendations.append("Feature Engineering verbessern (Wetter, Streckencharakteristika, etc.)")
        
        if avg_cal_error > 0.15:
            recommendations.append("Wahrscheinlichkeits-Kalibrierung implementieren (z.B. Platt Scaling)")
            recommendations.append("Unsicherheitsschätzung in Vorhersagen integrieren")
        
        # Spezifische Empfehlungen basierend auf Insights
        action_counts = {}
        for insight in self.learning_insights:
            action = insight['suggested_action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        if action_counts.get('model_retraining', 0) > 1:
            recommendations.append("Dringendes Model-Retraining erforderlich - mehrere Rennen mit schlechter Performance")
        
        if action_counts.get('bias_correction', 0) > 1:
            recommendations.append("Systematische Bias-Korrektur implementieren")
        
        if not recommendations:
            recommendations.append("Aktuelle Modell-Performance ist zufriedenstellend - weiter überwachen")
        
        return recommendations
    
    def save_analysis_results(self):
        """Speichert alle Analyseergebnisse"""
        output_dir = self.config['output_directory']
        os.makedirs(output_dir, exist_ok=True)
        
        # Speichere Analyseergebnisse
        results_file = os.path.join(output_dir, 'analysis_results.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Speichere Lernerkenntnisse
        insights_file = self.config['learning_log_file']
        os.makedirs(os.path.dirname(insights_file), exist_ok=True)
        with open(insights_file, 'w', encoding='utf-8') as f:
            json.dump(self.learning_insights, f, indent=2, ensure_ascii=False, default=str)
        
        # Speichere Genauigkeits-Historie
        if self.analysis_results:
            history_data = []
            for result in self.analysis_results:
                history_data.append({
                    'race_name': result['race_name'],
                    'timestamp': result['timestamp'],
                    'overall_score': result['overall_score'],
                    'exact_accuracy': result['position_accuracy']['exact_accuracy'],
                    'within_3_accuracy': result['position_accuracy']['within_3_accuracy'],
                    'top3_accuracy': result['position_accuracy']['top3_accuracy'],
                    'calibration_score': result['probability_calibration']['calibration_score']
                })
            
            history_df = pd.DataFrame(history_data)
            history_file = self.config['accuracy_history_file']
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            history_df.to_csv(history_file, index=False)
        
        print(f"💾 Analyseergebnisse gespeichert in {output_dir}")
    
    def create_visualization(self, output_file: str = None):
        """Erstellt Visualisierungen der Analyseergebnisse"""
        if not self.analysis_results:
            print("❌ Keine Daten für Visualisierung verfügbar")
            return
        
        # Bereite Daten vor
        races = [r['race_name'] for r in self.analysis_results]
        overall_scores = [r['overall_score'] for r in self.analysis_results]
        exact_acc = [r['position_accuracy']['exact_accuracy'] for r in self.analysis_results]
        within_3_acc = [r['position_accuracy']['within_3_accuracy'] for r in self.analysis_results]
        cal_scores = [r['probability_calibration']['calibration_score'] for r in self.analysis_results]
        
        # Erstelle Subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('F1 Prediction Accuracy Analysis', fontsize=16, fontweight='bold')
        
        # 1. Gesamt-Scores über Zeit
        axes[0, 0].plot(races, overall_scores, marker='o', linewidth=2, markersize=8)
        axes[0, 0].set_title('Overall Accuracy Score')
        axes[0, 0].set_ylabel('Score')
        axes[0, 0].tick_params(axis='x', rotation=45)
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Verschiedene Genauigkeitsmetriken
        x = np.arange(len(races))
        width = 0.25
        axes[0, 1].bar(x - width, exact_acc, width, label='Exact', alpha=0.8)
        axes[0, 1].bar(x, within_3_acc, width, label='Within ±3', alpha=0.8)
        axes[0, 1].bar(x + width, cal_scores, width, label='Calibration', alpha=0.8)
        axes[0, 1].set_title('Accuracy Metrics Comparison')
        axes[0, 1].set_ylabel('Accuracy')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(races, rotation=45)
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Fehlerverteilung (letztes Rennen)
        if self.analysis_results:
            last_result = self.analysis_results[-1]
            error_dist = last_result['error_patterns']['position_error_distribution']
            if error_dist:
                positions = [d['position'] for d in error_dist]
                errors = [d['mean'] for d in error_dist]
                axes[1, 0].bar(positions, errors, alpha=0.7)
                axes[1, 0].set_title(f'Position Error Distribution - {last_result["race_name"]}')
                axes[1, 0].set_xlabel('Predicted Position')
                axes[1, 0].set_ylabel('Mean Error')
                axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Trend-Analyse
        if len(overall_scores) > 1:
            # Berechne gleitenden Durchschnitt
            window = min(3, len(overall_scores))
            moving_avg = pd.Series(overall_scores).rolling(window=window).mean()
            
            axes[1, 1].plot(races, overall_scores, 'o-', alpha=0.6, label='Actual')
            axes[1, 1].plot(races, moving_avg, 's-', linewidth=2, label=f'Moving Avg ({window})')
            axes[1, 1].set_title('Accuracy Trend')
            axes[1, 1].set_ylabel('Overall Score')
            axes[1, 1].tick_params(axis='x', rotation=45)
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"📊 Visualisierung gespeichert: {output_file}")
        else:
            plt.show()
        
        plt.close()

def main():
    """Hauptfunktion für Tests"""
    print("🔍 F1 PREDICTION ACCURACY ANALYZER")
    print("="*50)
    
    # Initialisiere Analyzer
    analyzer = PredictionAccuracyAnalyzer()
    
    # Beispiel-Analyse (falls Dateien vorhanden)
    prediction_file = "data/live/predicted_probabilities_2025_Spanish_Grand_Prix_full.csv"
    result_file = "data/test_results/spanish_gp_2025_results.csv"
    
    if os.path.exists(prediction_file) and os.path.exists(result_file):
        print("\n📊 Führe Beispiel-Analyse durch...")
        analysis = analyzer.analyze_race_predictions(
            prediction_file, result_file, "2025 Spanish Grand Prix"
        )
        
        if analysis:
            print(f"\n✅ Analyse abgeschlossen:")
            print(f"   Gesamt-Score: {analysis['overall_score']:.1%}")
            print(f"   Exakte Genauigkeit: {analysis['position_accuracy']['exact_accuracy']:.1%}")
            print(f"   Top-3 Genauigkeit: {analysis['position_accuracy']['top3_accuracy']:.1%}")
            
            # Speichere Ergebnisse
            analyzer.save_analysis_results()
            
            # Generiere Bericht
            report_file = "data/analysis/accuracy_report.txt"
            analyzer.generate_comprehensive_report(report_file)
            
            # Erstelle Visualisierung
            viz_file = "data/analysis/accuracy_visualization.png"
            analyzer.create_visualization(viz_file)
            
            print(f"\n📁 Ergebnisse verfügbar in data/analysis/")
    else:
        print("\n⚠️ Keine Beispieldateien gefunden für Analyse")
        print("   Erstelle zuerst Vorhersagen und Rennresultate")
    
    print("\n🎯 Analyzer bereit für automatische Integration!")

if __name__ == "__main__":
    main()