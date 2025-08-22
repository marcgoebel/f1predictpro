import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class BetTracker:
    """
    Klasse zum Tracken von getätigten Wetten und deren Ergebnissen.
    Ermöglicht dem System, von Wett-Outcomes zu lernen.
    """
    
    def __init__(self, db_client=None, tracking_file: str = "data/live/placed_bets.json"):
        self.db_client = db_client
        self.tracking_file = tracking_file
        self.bets = self._load_bets()
    
    def _load_bets(self) -> List[Dict]:
        """Lade bestehende Wetten aus der Tracking-Datei"""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Fehler beim Laden der Wetten: {e}")
                return []
        return []
    
    def _save_bets(self):
        """Speichere Wetten in die Tracking-Datei"""
        os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
        try:
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(self.bets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Fehler beim Speichern der Wetten: {e}")
    
    def place_bet(self, driver: str, bet_type: str, odds: float, stake: float, 
                  race_name: str, predicted_probability: float, 
                  reasoning: str = "") -> str:
        """
        Registriere eine getätigte Wette
        
        Args:
            driver: Name des Fahrers
            bet_type: Art der Wette (z.B. "Win", "Podium", "Top5")
            odds: Quote der Wette
            stake: Einsatz
            race_name: Name des Rennens
            predicted_probability: Unsere vorhergesagte Wahrscheinlichkeit
            reasoning: Begründung für die Wette
        
        Returns:
            bet_id: Eindeutige ID der Wette
        """
        bet_id = f"{race_name}_{driver}_{bet_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        bet = {
            "bet_id": bet_id,
            "timestamp": datetime.now().isoformat(),
            "driver": driver,
            "bet_type": bet_type,
            "odds": odds,
            "stake": stake,
            "race_name": race_name,
            "predicted_probability": predicted_probability,
            "reasoning": reasoning,
            "status": "pending",  # pending, won, lost
            "actual_result": None,
            "profit_loss": None,
            "settled_date": None
        }
        
        self.bets.append(bet)
        self._save_bets()
        
        print(f"✅ Wette registriert: {driver} {bet_type} @ {odds} (Einsatz: {stake}€)")
        return bet_id
    
    def settle_bet(self, bet_id: str, won: bool, actual_result: str = ""):
        """
        Setze das Ergebnis einer Wette
        
        Args:
            bet_id: ID der Wette
            won: True wenn gewonnen, False wenn verloren
            actual_result: Tatsächliches Rennergebnis
        """
        for bet in self.bets:
            if bet["bet_id"] == bet_id:
                bet["status"] = "won" if won else "lost"
                bet["actual_result"] = actual_result
                bet["settled_date"] = datetime.now().isoformat()
                
                if won:
                    bet["profit_loss"] = (bet["odds"] - 1) * bet["stake"]
                else:
                    bet["profit_loss"] = -bet["stake"]
                
                self._save_bets()
                print(f"✅ Wette abgerechnet: {bet_id} - {'Gewonnen' if won else 'Verloren'}")
                return
        
        print(f"❌ Wette nicht gefunden: {bet_id}")
    
    def settle_race_bets(self, race_name: str, race_results: Dict[str, int]):
        """
        Rechne alle Wetten für ein Rennen ab
        
        Args:
            race_name: Name des Rennens
            race_results: Dictionary {driver: final_position}
        """
        settled_count = 0
        
        for bet in self.bets:
            if bet["race_name"] == race_name and bet["status"] == "pending":
                driver = bet["driver"]
                bet_type = bet["bet_type"]
                
                if driver in race_results:
                    final_position = race_results[driver]
                    won = self._check_bet_result(bet_type, final_position)
                    
                    self.settle_bet(
                        bet["bet_id"], 
                        won, 
                        f"P{final_position}" if final_position <= 20 else "DNF"
                    )
                    settled_count += 1
        
        print(f"✅ {settled_count} Wetten für {race_name} abgerechnet")
    
    def _check_bet_result(self, bet_type: str, final_position: int) -> bool:
        """Prüfe ob eine Wette gewonnen wurde basierend auf dem Ergebnis"""
        if bet_type.lower() == "win" or bet_type.lower() == "p1":
            return final_position == 1
        elif bet_type.lower() == "podium" or bet_type.lower() in ["p2", "p3"]:
            return final_position <= 3
        elif bet_type.lower() == "top5":
            return final_position <= 5
        elif bet_type.lower() == "top10":
            return final_position <= 10
        elif bet_type.lower() == "points":
            return final_position <= 10
        else:
            # Für spezifische Positionen wie "P2", "P3" etc.
            if bet_type.upper().startswith("P") and bet_type[1:].isdigit():
                target_position = int(bet_type[1:])
                return final_position == target_position
        
        return False
    
    def get_performance_stats(self) -> Dict:
        """Berechne Performance-Statistiken"""
        settled_bets = [bet for bet in self.bets if bet["status"] in ["won", "lost"]]
        
        if not settled_bets:
            return {
                "total_bets": 0,
                "won_bets": 0,
                "lost_bets": 0,
                "win_rate": 0,
                "total_stake": 0,
                "total_profit": 0,
                "roi": 0
            }
        
        won_bets = [bet for bet in settled_bets if bet["status"] == "won"]
        total_stake = sum(bet["stake"] for bet in settled_bets)
        total_profit = sum(bet["profit_loss"] for bet in settled_bets)
        
        return {
            "total_bets": len(settled_bets),
            "won_bets": len(won_bets),
            "lost_bets": len(settled_bets) - len(won_bets),
            "win_rate": len(won_bets) / len(settled_bets) * 100,
            "total_stake": total_stake,
            "total_profit": total_profit,
            "roi": (total_profit / total_stake * 100) if total_stake > 0 else 0
        }
    
    def get_learning_insights(self) -> Dict:
        """Analysiere Wetten für Lernzwecke"""
        settled_bets = [bet for bet in self.bets if bet["status"] in ["won", "lost"]]
        
        if not settled_bets:
            return {"message": "Keine abgerechneten Wetten für Analyse verfügbar"}
        
        insights = {
            "probability_accuracy": [],
            "odds_analysis": [],
            "driver_performance": {},
            "bet_type_performance": {},
            "prediction_accuracy": self._analyze_prediction_accuracy(settled_bets),
            "learning_recommendations": self._generate_learning_recommendations(settled_bets)
        }
        
        for bet in settled_bets:
            # Wahrscheinlichkeits-Genauigkeit
            predicted_prob = bet["predicted_probability"]
            actual_outcome = 1 if bet["status"] == "won" else 0
            insights["probability_accuracy"].append({
                "predicted": predicted_prob,
                "actual": actual_outcome,
                "difference": abs(predicted_prob - actual_outcome)
            })
            
            # Odds-Analyse
            implied_prob = 1 / bet["odds"]
            insights["odds_analysis"].append({
                "our_prob": predicted_prob,
                "implied_prob": implied_prob,
                "edge": predicted_prob - implied_prob,
                "won": bet["status"] == "won"
            })
            
            # Driver-Performance
            driver = bet["driver"]
            if driver not in insights["driver_performance"]:
                insights["driver_performance"][driver] = {"bets": 0, "wins": 0, "total_stake": 0, "total_profit": 0}
            
            insights["driver_performance"][driver]["bets"] += 1
            insights["driver_performance"][driver]["total_stake"] += bet["stake"]
            insights["driver_performance"][driver]["total_profit"] += bet.get("profit_loss", 0)
            if bet["status"] == "won":
                insights["driver_performance"][driver]["wins"] += 1
            
            # Bet-Type-Performance
            bet_type = bet["bet_type"]
            if bet_type not in insights["bet_type_performance"]:
                insights["bet_type_performance"][bet_type] = {"bets": 0, "wins": 0, "total_stake": 0, "total_profit": 0}
            
            insights["bet_type_performance"][bet_type]["bets"] += 1
            insights["bet_type_performance"][bet_type]["total_stake"] += bet["stake"]
            insights["bet_type_performance"][bet_type]["total_profit"] += bet.get("profit_loss", 0)
            if bet["status"] == "won":
                insights["bet_type_performance"][bet_type]["wins"] += 1
        
        # Berechne ROI für Driver und Bet-Type Performance
        for driver_stats in insights["driver_performance"].values():
            driver_stats["win_rate"] = driver_stats["wins"] / driver_stats["bets"] if driver_stats["bets"] > 0 else 0
            driver_stats["roi"] = driver_stats["total_profit"] / driver_stats["total_stake"] if driver_stats["total_stake"] > 0 else 0
        
        for type_stats in insights["bet_type_performance"].values():
            type_stats["win_rate"] = type_stats["wins"] / type_stats["bets"] if type_stats["bets"] > 0 else 0
            type_stats["roi"] = type_stats["total_profit"] / type_stats["total_stake"] if type_stats["total_stake"] > 0 else 0
        
        return insights
    
    def _analyze_prediction_accuracy(self, settled_bets: List[Dict]) -> Dict:
        """Analysiere die Genauigkeit unserer Vorhersagen"""
        if not settled_bets:
            return {}
        
        accuracy_data = {}
        
        # Analysiere Expected Value vs tatsächliche Ergebnisse
        ev_bets = [bet for bet in settled_bets if "expected_value" in bet and bet["expected_value"] is not None]
        if ev_bets:
            positive_ev_bets = [bet for bet in ev_bets if bet["expected_value"] > 0]
            negative_ev_bets = [bet for bet in ev_bets if bet["expected_value"] <= 0]
            
            if positive_ev_bets:
                pos_wins = sum(1 for bet in positive_ev_bets if bet["status"] == "won")
                pos_stakes = sum(bet["stake"] for bet in positive_ev_bets)
                pos_profit = sum(bet.get("profit_loss", 0) for bet in positive_ev_bets)
                
                accuracy_data["positive_ev_accuracy"] = {
                    "count": len(positive_ev_bets),
                    "win_rate": pos_wins / len(positive_ev_bets),
                    "actual_roi": pos_profit / pos_stakes if pos_stakes > 0 else 0
                }
            
            if negative_ev_bets:
                neg_wins = sum(1 for bet in negative_ev_bets if bet["status"] == "won")
                neg_stakes = sum(bet["stake"] for bet in negative_ev_bets)
                neg_profit = sum(bet.get("profit_loss", 0) for bet in negative_ev_bets)
                
                accuracy_data["negative_ev_accuracy"] = {
                    "count": len(negative_ev_bets),
                    "win_rate": neg_wins / len(negative_ev_bets),
                    "actual_roi": neg_profit / neg_stakes if neg_stakes > 0 else 0
                }
        
        # Analysiere Wahrscheinlichkeits-Vorhersagen vs tatsächliche Ergebnisse
        prob_ranges = [
            (0.0, 0.2, "Sehr niedrig (0-20%)"),
            (0.2, 0.4, "Niedrig (20-40%)"),
            (0.4, 0.6, "Mittel (40-60%)"),
            (0.6, 0.8, "Hoch (60-80%)"),
            (0.8, 1.0, "Sehr hoch (80-100%)")
        ]
        
        prob_accuracy = {}
        for min_prob, max_prob, label in prob_ranges:
            range_bets = [bet for bet in settled_bets if min_prob <= bet["predicted_probability"] < max_prob]
            if range_bets:
                wins = sum(1 for bet in range_bets if bet["status"] == "won")
                avg_predicted = sum(bet["predicted_probability"] for bet in range_bets) / len(range_bets)
                actual_win_rate = wins / len(range_bets)
                
                prob_accuracy[label] = {
                    "count": len(range_bets),
                    "predicted_win_rate": avg_predicted,
                    "actual_win_rate": actual_win_rate,
                    "accuracy_diff": abs(avg_predicted - actual_win_rate)
                }
        
        accuracy_data["probability_accuracy"] = prob_accuracy
        return accuracy_data
    
    def _generate_learning_recommendations(self, settled_bets: List[Dict]) -> List[Dict]:
        """Generiere Empfehlungen zur Verbesserung des ML-Modells"""
        if not settled_bets:
            return []
        
        recommendations = []
        
        # Überprüfe Gesamtperformance
        total_stakes = sum(bet["stake"] for bet in settled_bets)
        total_profit = sum(bet.get("profit_loss", 0) for bet in settled_bets)
        overall_roi = total_profit / total_stakes if total_stakes > 0 else 0
        overall_win_rate = sum(1 for bet in settled_bets if bet["status"] == "won") / len(settled_bets)
        
        if overall_roi < -0.1:  # Verlust von mehr als 10%
            recommendations.append({
                "type": "critical",
                "message": f"Negativer ROI erkannt ({overall_roi:.1%}). Wettstrategie überdenken.",
                "action": "Mindest-Expected-Value-Schwelle erhöhen oder Einsätze reduzieren."
            })
        
        if overall_win_rate < 0.3:  # Weniger als 30% Gewinnrate
            recommendations.append({
                "type": "warning",
                "message": f"Niedrige Gewinnrate ({overall_win_rate:.1%}). Modell-Vorhersagen benötigen Kalibrierung.",
                "action": "Wahrscheinlichkeitsberechnungen überprüfen und zusätzliche Features berücksichtigen."
            })
        
        # Analysiere nach Wett-Typ
        if len(settled_bets) >= 5:  # Nur bei ausreichend Daten
            bet_types = {}
            for bet in settled_bets:
                bet_type = bet["bet_type"]
                if bet_type not in bet_types:
                    bet_types[bet_type] = {"bets": 0, "wins": 0, "stakes": 0, "profit": 0}
                
                bet_types[bet_type]["bets"] += 1
                bet_types[bet_type]["stakes"] += bet["stake"]
                bet_types[bet_type]["profit"] += bet.get("profit_loss", 0)
                if bet["status"] == "won":
                    bet_types[bet_type]["wins"] += 1
            
            for bet_type, stats in bet_types.items():
                type_roi = stats["profit"] / stats["stakes"] if stats["stakes"] > 0 else 0
                if type_roi < -0.2:  # Verlust von mehr als 20% bei diesem Wett-Typ
                    recommendations.append({
                        "type": "warning",
                        "message": f'Wett-Typ "{bet_type}" zeigt schlechte Performance (ROI: {type_roi:.1%}).',
                        "action": f"{bet_type}-Wetten vermeiden oder Einsätze reduzieren."
                    })
        
        # Erfolgs-Empfehlungen
        if overall_roi > 0.1:  # Gewinn von mehr als 10%
            recommendations.append({
                "type": "success",
                "message": f"Starke Performance erkannt (ROI: {overall_roi:.1%}). Aktuelle Strategie funktioniert gut.",
                "action": "Mit aktueller Herangehensweise fortfahren und Einsätze schrittweise erhöhen."
            })
        
        return recommendations
    
    def update_ml_model_feedback(self) -> Optional[Dict]:
        """Aktualisiere ML-Modell mit Wett-Ergebnissen für kontinuierliches Lernen"""
        settled_bets = [bet for bet in self.bets if bet["status"] in ["won", "lost"]]
        
        if not settled_bets:
            return None
        
        # Bereite Feedback-Daten für ML-Modell vor
        feedback_data = []
        
        for bet in settled_bets:
            feedback_entry = {
                "driver": bet["driver"],
                "bet_type": bet["bet_type"],
                "race_name": bet["race_name"],
                "predicted_probability": bet["predicted_probability"],
                "actual_result": 1 if bet["status"] == "won" else 0,
                "odds": bet["odds"],
                "expected_value": bet.get("expected_value"),
                "confidence": bet.get("confidence", 3),
                "timestamp": bet.get("timestamp", bet.get("bet_date"))
            }
            feedback_data.append(feedback_entry)
        
        # Speichere Feedback-Daten für ML-Modell-Retraining
        if feedback_data:
            feedback_df = pd.DataFrame(feedback_data)
            feedback_file = "data/ml_feedback/betting_feedback.csv"
            
            # Erstelle Verzeichnis falls es nicht existiert
            os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
            
            # Hänge an bestehende Feedback-Datei an oder erstelle neue
            if os.path.exists(feedback_file):
                existing_feedback = pd.read_csv(feedback_file)
                combined_feedback = pd.concat([existing_feedback, feedback_df], ignore_index=True)
                combined_feedback.drop_duplicates(subset=["driver", "bet_type", "race_name", "timestamp"], keep="last", inplace=True)
            else:
                combined_feedback = feedback_df
            
            combined_feedback.to_csv(feedback_file, index=False)
            
            return {
                "feedback_entries": len(feedback_data),
                "total_feedback_entries": len(combined_feedback),
                "feedback_file": feedback_file
            }
        
        return None
    
    def add_bet(self, bet_type: str, driver: str, race_name: str, odds: float, 
                stake: float, bookmaker: str = "", confidence: int = 3, notes: str = "") -> str:
        """Füge eine neue Wette hinzu"""
        import uuid
        
        bet_id = str(uuid.uuid4())
        bet_data = {
            "id": bet_id,
            "bet_type": bet_type,
            "driver": driver,
            "race_name": race_name,
            "odds": odds,
            "stake": stake,
            "bookmaker": bookmaker,
            "confidence": confidence,
            "notes": notes,
            "status": "pending",
            "bet_date": datetime.now().isoformat(),
            "profit_loss": 0.0
        }
        
        # Speichere in Supabase wenn verfügbar
        if self.db_client:
            try:
                self.db_client.supabase.table('betting_performance').insert(bet_data).execute()
            except Exception as e:
                print(f"Fehler beim Speichern in Supabase: {e}")
        
        # Speichere auch lokal
        self.bets.append(bet_data)
        self._save_bets()
        
        return bet_id
    
    def get_active_bets(self) -> pd.DataFrame:
        """Hole alle aktiven Wetten"""
        if self.db_client:
            try:
                result = self.db_client.supabase.table('betting_performance').select('*').eq('result', 'pending').execute()
                if result.data:
                    df = pd.DataFrame(result.data)
                    df['bet_date'] = pd.to_datetime(df['bet_date'])
                    return df
            except Exception as e:
                print(f"Fehler beim Laden aus Supabase: {e}")
        
        # Fallback zu lokalen Daten
        active_bets = [bet for bet in self.bets if bet.get('status') == 'pending']
        if active_bets:
            df = pd.DataFrame(active_bets)
            df['bet_date'] = pd.to_datetime(df['bet_date'])
            return df
        return pd.DataFrame()
    
    def get_all_bets(self) -> pd.DataFrame:
        """Hole alle Wetten"""
        if self.db_client:
            try:
                result = self.db_client.supabase.table('betting_performance').select('*').execute()
                if result.data:
                    df = pd.DataFrame(result.data)
                    df['bet_date'] = pd.to_datetime(df['bet_date'])
                    return df
            except Exception as e:
                print(f"Fehler beim Laden aus Supabase: {e}")
        
        # Fallback zu lokalen Daten
        if self.bets:
            df = pd.DataFrame(self.bets)
            df['bet_date'] = pd.to_datetime(df['bet_date'])
            return df
        return pd.DataFrame()
    
    def update_bet_result(self, bet_id: str, result: str):
        """Aktualisiere das Ergebnis einer Wette"""
        if self.db_client:
            try:
                # Hole die Wette um Profit/Loss zu berechnen
                bet_result = self.db_client.supabase.table('betting_performance').select('*').eq('id', bet_id).execute()
                
                if bet_result.data:
                    bet = bet_result.data[0]
                    profit_loss = 0.0
                    
                    if result == 'win':
                        profit_loss = (bet['odds'] - 1) * bet['stake']
                    elif result == 'loss':
                        profit_loss = -bet['stake']
                    
                    # Aktualisiere in Supabase
                    self.db_client.supabase.table('betting_performance').update({
                        'status': result,
                        'profit_loss': profit_loss,
                        'settled_date': datetime.now().isoformat()
                    }).eq('id', bet_id).execute()
                    
            except Exception as e:
                print(f"Fehler beim Aktualisieren in Supabase: {e}")
        
        # Aktualisiere auch lokal
        for bet in self.bets:
            if bet.get('id') == bet_id:
                bet['status'] = result
                if result == 'win':
                    bet['profit_loss'] = (bet['odds'] - 1) * bet['stake']
                elif result == 'loss':
                    bet['profit_loss'] = -bet['stake']
                bet['settled_date'] = datetime.now().isoformat()
                break
        
        self._save_bets()
    
    def get_performance_stats(self) -> Dict:
        """Berechne Performance-Statistiken"""
        if self.db_client:
            try:
                result = self.db_client.supabase.table('betting_performance').select('*').neq('result', 'pending').execute()
                if result.data:
                    df = pd.DataFrame(result.data)
                    
                    total_stakes = df['stake'].sum()
                    total_profit = df['profit_loss'].sum()
                    win_count = len(df[df['result'] == 'win'])
                    total_bets = len(df)
                    
                    return {
                        'total_stakes': total_stakes,
                        'total_profit': total_profit,
                        'roi': (total_profit / total_stakes * 100) if total_stakes > 0 else 0,
                        'win_rate': (win_count / total_bets * 100) if total_bets > 0 else 0,
                        'total_bets': total_bets,
                        'wins': win_count
                    }
            except Exception as e:
                print(f"Fehler beim Laden der Performance: {e}")
        
        # Fallback zu lokalen Daten
        settled_bets = [bet for bet in self.bets if bet.get('status') in ['win', 'loss']]
        
        if not settled_bets:
            return {
                'total_stakes': 0,
                'total_profit': 0,
                'roi': 0,
                'win_rate': 0,
                'total_bets': 0,
                'wins': 0
            }
        
        total_stakes = sum(bet['stake'] for bet in settled_bets)
        total_profit = sum(bet.get('profit_loss', 0) for bet in settled_bets)
        win_count = len([bet for bet in settled_bets if bet['status'] == 'win'])
        
        return {
            'total_stakes': total_stakes,
            'total_profit': total_profit,
            'roi': (total_profit / total_stakes * 100) if total_stakes > 0 else 0,
            'win_rate': (win_count / len(settled_bets) * 100) if settled_bets else 0,
            'total_bets': len(settled_bets),
            'wins': win_count
        }
    
    def get_performance_by_bet_type(self) -> pd.DataFrame:
        """Analysiere Performance nach Wett-Typ"""
        if self.db_client:
            try:
                result = self.db_client.supabase.table('betting_performance').select('*').neq('result', 'pending').execute()
                if result.data:
                    df = pd.DataFrame(result.data)
                    
                    stats = df.groupby('bet_type').agg({
                        'stake': 'sum',
                        'profit_loss': 'sum',
                        'id': 'count'
                    }).reset_index()
                    
                    stats.columns = ['bet_type', 'total_stakes', 'total_profit', 'total_bets']
                    stats['roi'] = (stats['total_profit'] / stats['total_stakes'] * 100).round(2)
                    
                    return stats
            except Exception as e:
                print(f"Fehler beim Laden der Bet-Type-Performance: {e}")
        
        return pd.DataFrame()
    
    def export_to_supabase(self, db_client):
        """Exportiere Wetten zur Supabase-Datenbank"""
        try:
            for bet in self.bets:
                # Konvertiere zu Supabase-Format
                supabase_bet = {
                    "bet_id": bet.get("bet_id", bet.get("id")),
                    "driver": bet["driver"],
                    "bet_type": bet["bet_type"],
                    "odds": bet["odds"],
                    "stake": bet["stake"],
                    "race_name": bet["race_name"],
                    "predicted_probability": bet.get("predicted_probability", 0),
                    "result": bet["status"],
                    "profit_loss": bet.get("profit_loss", 0),
                    "bet_date": bet.get("timestamp", bet.get("bet_date")),
                    "settled_date": bet.get("settled_date")
                }
                
                # Prüfe ob Wette bereits existiert
                existing = db_client.supabase.table('betting_performance').select('bet_id').eq('bet_id', supabase_bet["bet_id"]).execute()
                
                if not existing.data:
                    # Neue Wette einfügen
                    db_client.supabase.table('betting_performance').insert(supabase_bet).execute()
                else:
                    # Bestehende Wette aktualisieren
                    db_client.supabase.table('betting_performance').update(supabase_bet).eq('bet_id', supabase_bet["bet_id"]).execute()
            
            print(f"✅ {len(self.bets)} Wetten zu Supabase exportiert")
            
        except Exception as e:
            print(f"❌ Fehler beim Export zu Supabase: {e}")


def simulate_placed_bets():
    """Simuliere einige getätigte Wetten für Demo-Zwecke"""
    tracker = BetTracker()
    
    # Simuliere einige Wetten
    demo_bets = [
        {
            "driver": "VER", "bet_type": "Win", "odds": 2.5, "stake": 10,
            "race_name": "Spanish Grand Prix", "predicted_probability": 0.45,
            "reasoning": "Starke Qualifying-Performance und gute Streckenhistorie"
        },
        {
            "driver": "LEC", "bet_type": "Podium", "odds": 1.8, "stake": 15,
            "race_name": "Spanish Grand Prix", "predicted_probability": 0.65,
            "reasoning": "Hohe Podium-Wahrscheinlichkeit bei guten Odds"
        },
        {
            "driver": "NOR", "bet_type": "Top5", "odds": 1.4, "stake": 20,
            "race_name": "Spanish Grand Prix", "predicted_probability": 0.80,
            "reasoning": "Sehr sichere Wette mit gutem Value"
        }
    ]
    
    for bet in demo_bets:
        tracker.place_bet(**bet)
    
    print(f"\n📊 Demo-Wetten erstellt: {len(demo_bets)} Wetten registriert")
    return tracker


if __name__ == "__main__":
    # Demo-Modus
    print("🎲 Bet Tracker Demo")
    tracker = simulate_placed_bets()
    
    # Zeige Performance-Stats
    stats = tracker.get_performance_stats()
    print(f"\n📈 Performance Stats: {stats}")
    
    # Simuliere Rennergebnis
    race_results = {
        "VER": 1,  # Gewonnen
        "LEC": 3,  # Podium
        "NOR": 4   # Top5
    }
    
    tracker.settle_race_bets("Spanish Grand Prix", race_results)
    
    # Aktualisierte Stats
    updated_stats = tracker.get_performance_stats()
    print(f"\n📊 Aktualisierte Stats: {updated_stats}")
    
    # Lern-Insights
    insights = tracker.get_learning_insights()
    print(f"\n🧠 Lern-Insights: {insights}")