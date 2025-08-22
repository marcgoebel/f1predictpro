import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import os

def apply_betting_strategy(probabilities_df: pd.DataFrame, odds_dict: Dict[str, float],
                          min_ev: float = 0.0, min_probability: float = 15.0, 
                          min_odds: float = 2.5, stake: float = 10.0) -> pd.DataFrame:
    """
    Wendet Wettstrategie-Kriterien an und entscheidet über Wetten.
    
    Kriterien:
    - EV > min_ev
    - Wahrscheinlichkeit > min_probability %
    - Quote > min_odds
    
    Args:
        probabilities_df: DataFrame mit ['driver', 'position', 'probability']
        odds_dict: Dictionary mit {driver: odds}
        min_ev: Mindest Expected Value
        min_probability: Mindestwahrscheinlichkeit in %
        min_odds: Mindestquote
        stake: Einsatz pro Wette
    
    Returns:
        DataFrame mit Wettempfehlungen
    """
    from ml.enhanced_value_bet_calculator import EnhancedValueBetCalculator

def calculate_expected_value(probability: float, odds: float, stake: float = 1.0) -> float:
    """Calculate Expected Value (EV) of a bet"""
    win_amount = odds * stake
    lose_amount = stake
    ev = (probability * win_amount) - ((1 - probability) * lose_amount)
    return ev
    
    results = []
    
    # Fokus auf P1, P2, P3 Positionen
    top_positions = probabilities_df[probabilities_df['position'].isin([1, 2, 3])].copy()
    
    for _, row in top_positions.iterrows():
        driver = row['driver']
        position = row['position']
        probability_pct = row['probability']
        probability_decimal = probability_pct / 100.0
        
        if driver in odds_dict:
            odds = odds_dict[driver]
            ev = calculate_expected_value(probability_decimal, odds, stake)
            
            # Prüfe alle Kriterien
            meets_ev = ev > min_ev
            meets_probability = probability_pct > min_probability
            meets_odds = odds > min_odds
            
            should_bet = meets_ev and meets_probability and meets_odds
            
            results.append({
                'driver': driver,
                'position': f'P{position}',
                'odds': odds,
                'probability_pct': probability_pct,
                'expected_value': round(ev, 2),
                'meets_ev_criteria': meets_ev,
                'meets_prob_criteria': meets_probability,
                'meets_odds_criteria': meets_odds,
                'bet_recommendation': 'Ja' if should_bet else 'Nein',
                'stake': stake if should_bet else 0,
                'potential_profit': round((odds - 1) * stake, 2) if should_bet else 0
            })
    
    df_results = pd.DataFrame(results)
    
    # Sortiere nach Expected Value (absteigend)
    df_results = df_results.sort_values('expected_value', ascending=False)
    
    return df_results

def generate_betting_recommendations(probabilities_file: str, odds_file: str,
                                   output_file: str = "data/live/betting_recommendations.csv",
                                   strategy_params: Dict = None) -> pd.DataFrame:
    """
    Generiert Wettempfehlungen basierend auf Strategie-Parametern.
    
    Args:
        probabilities_file: Pfad zur Wahrscheinlichkeits-CSV
        odds_file: Pfad zur Quoten-CSV
        output_file: Pfad für Ausgabe-CSV
        strategy_params: Dictionary mit Strategie-Parametern
    
    Returns:
        DataFrame mit Wettempfehlungen
    """
    # Standard-Parameter
    if strategy_params is None:
        strategy_params = {
            'min_ev': 0.0,
            'min_probability': 15.0,
            'min_odds': 2.5,
            'stake': 10.0
        }
    
    # Lade Daten
    if not os.path.exists(probabilities_file):
        raise FileNotFoundError(f"Wahrscheinlichkeits-Datei nicht gefunden: {probabilities_file}")
    
    if not os.path.exists(odds_file):
        raise FileNotFoundError(f"Quoten-Datei nicht gefunden: {odds_file}")
    
    prob_df = pd.read_csv(probabilities_file)
    odds_df = pd.read_csv(odds_file)
    odds_dict = dict(zip(odds_df['driver'], odds_df['odds']))
    
    # Wende Strategie an
    recommendations = apply_betting_strategy(prob_df, odds_dict, **strategy_params)
    
    # Speichere Ergebnisse
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    recommendations.to_csv(output_file, index=False)
    
    # Statistiken
    total_bets = len(recommendations[recommendations['bet_recommendation'] == 'Ja'])
    total_stake = recommendations[recommendations['bet_recommendation'] == 'Ja']['stake'].sum()
    avg_ev = recommendations[recommendations['bet_recommendation'] == 'Ja']['expected_value'].mean()
    
    print(f"✅ Wettempfehlungen gespeichert: {output_file}")
    print(f"📊 Empfohlene Wetten: {total_bets}")
    print(f"💰 Gesamteinsatz: {total_stake}€")
    print(f"📈 Durchschnittlicher EV: {avg_ev:.2f}€" if not pd.isna(avg_ev) else "📈 Kein positiver EV gefunden")
    
    return recommendations

def create_strategy_summary(recommendations_df: pd.DataFrame) -> Dict:
    """
    Erstellt eine Zusammenfassung der Wettstrategie-Ergebnisse.
    
    Args:
        recommendations_df: DataFrame mit Wettempfehlungen
    
    Returns:
        Dictionary mit Zusammenfassung
    """
    recommended_bets = recommendations_df[recommendations_df['bet_recommendation'] == 'Ja']
    
    summary = {
        'total_opportunities': len(recommendations_df),
        'recommended_bets': len(recommended_bets),
        'total_stake': recommended_bets['stake'].sum(),
        'potential_profit': recommended_bets['potential_profit'].sum(),
        'average_odds': recommended_bets['odds'].mean() if len(recommended_bets) > 0 else 0,
        'average_probability': recommended_bets['probability_pct'].mean() if len(recommended_bets) > 0 else 0,
        'total_expected_value': recommended_bets['expected_value'].sum(),
        'best_bet': None
    }
    
    if len(recommended_bets) > 0:
        best_bet_idx = recommended_bets['expected_value'].idxmax()
        summary['best_bet'] = {
            'driver': recommended_bets.loc[best_bet_idx, 'driver'],
            'position': recommended_bets.loc[best_bet_idx, 'position'],
            'odds': recommended_bets.loc[best_bet_idx, 'odds'],
            'probability': recommended_bets.loc[best_bet_idx, 'probability_pct'],
            'expected_value': recommended_bets.loc[best_bet_idx, 'expected_value']
        }
    
    return summary

def print_strategy_report(recommendations_df: pd.DataFrame):
    """
    Druckt einen detaillierten Bericht der Wettstrategie.
    """
    summary = create_strategy_summary(recommendations_df)
    
    print("\n" + "="*50)
    print("🎯 WETTSTRATEGIE BERICHT")
    print("="*50)
    print(f"📊 Gesamte Gelegenheiten: {summary['total_opportunities']}")
    print(f"✅ Empfohlene Wetten: {summary['recommended_bets']}")
    print(f"💰 Gesamteinsatz: {summary['total_stake']:.2f}€")
    print(f"🎁 Potentieller Gewinn: {summary['potential_profit']:.2f}€")
    print(f"📈 Gesamter Expected Value: {summary['total_expected_value']:.2f}€")
    
    if summary['recommended_bets'] > 0:
        print(f"📊 Durchschnittliche Quote: {summary['average_odds']:.2f}")
        print(f"🎯 Durchschnittliche Wahrscheinlichkeit: {summary['average_probability']:.1f}%")
        
        if summary['best_bet']:
            best = summary['best_bet']
            print(f"\n🏆 BESTE WETTE:")
            print(f"   Fahrer: {best['driver']} ({best['position']})")
            print(f"   Quote: {best['odds']:.2f}")
            print(f"   Wahrscheinlichkeit: {best['probability']:.1f}%")
            print(f"   Expected Value: {best['expected_value']:.2f}€")
    else:
        print("\n❌ Keine profitablen Wetten gefunden")
    
    print("="*50)

if __name__ == "__main__":
    # Beispiel-Verwendung
    YEAR = 2025
    RACE = "Spanish_Grand_Prix_full"
    
    prob_file = f"data/live/predicted_probabilities_{YEAR}_{RACE}.csv"
    odds_file = "data/live/betpanda_odds.csv"
    
    # Erstelle Beispiel-Quoten falls nicht vorhanden
    if not os.path.exists(odds_file):
        # from ml.value_bet_calculator import create_sample_odds_file  # Deprecated
        pass

# Supabase Integration
try:
    from database.supabase_client import get_db_client
    SUPABASE_AVAILABLE = True
    db_client = get_db_client()
except ImportError:
    SUPABASE_AVAILABLE = False
    db_client = None

    # Define odds_file for fallback
    odds_file = "data/live/sample_odds.csv"
    if not os.path.exists(odds_file):
        # from ml.value_bet_calculator import create_sample_odds_file  # Deprecated
        create_sample_odds_file(odds_file)
    
    # Verschiedene Strategien testen
    strategies = {
        'Conservative': {'min_ev': 1.0, 'min_probability': 20.0, 'min_odds': 3.0, 'stake': 5.0},
        'Moderate': {'min_ev': 0.5, 'min_probability': 15.0, 'min_odds': 2.5, 'stake': 10.0},
        'Aggressive': {'min_ev': 0.0, 'min_probability': 10.0, 'min_odds': 2.0, 'stake': 15.0}
    }
    
    try:
        for strategy_name, params in strategies.items():
            print(f"\n🎯 Testing {strategy_name} Strategy:")
            output_file = f"data/live/betting_recommendations_{strategy_name.lower()}.csv"
            
            recommendations = generate_betting_recommendations(
                prob_file, odds_file, output_file, params
            )
            
            print_strategy_report(recommendations)
            
    except FileNotFoundError as e:
        print(f"❌ Fehler: {e}")