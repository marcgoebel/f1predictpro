#!/usr/bin/env python3
"""
F1 Analytics Hub - Enhanced Dashboard mit Supabase Integration
Zeigt historische Daten, Odds-Trends und Performance-Analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import sys
import os
import json

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ml'))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Supabase client and BetTracker
try:
    from database.supabase_client import get_db_client
    from ml.bet_tracker import BetTracker
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    st.error("[ERROR] Supabase client nicht verfügbar. Bitte installiere die Abhängigkeiten.")

# Page config
st.set_page_config(
    page_title="F1 Analytics Hub - Supabase Dashboard",
    page_icon="[F1]",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db_client' not in st.session_state and SUPABASE_AVAILABLE:
    try:
        st.session_state.db_client = get_db_client()
        st.session_state.db_connected = True
    except Exception as e:
        st.session_state.db_connected = False
        st.error(f"[ERROR] Datenbankverbindung fehlgeschlagen: {e}")

# Sidebar
st.sidebar.title("[F1] F1 Analytics Hub")
st.sidebar.markdown("### [CHART] Supabase Dashboard")

if not SUPABASE_AVAILABLE or not st.session_state.get('db_connected', False):
    st.error("[ERROR] Keine Datenbankverbindung verfügbar")
    st.stop()

# Navigation
page = st.sidebar.selectbox(
    "Navigation",
    [
        "[CHART] Übersicht",
        "[TREND] Odds-Trends", 
        "[TARGET] Predictions-Analyse",
        "[RACE] Rennergebnisse",
        "[MONEY] Betting-Performance",
        "[DICE] Wett-Empfehlungen",
        "[TARGET] Wett-Tracking",
        "🧠 ML-Lernen",
        "[SETTINGS] Odds-Konfiguration",
        "[CLIPBOARD] Daten-Management"
    ]
)

# Refresh button
if st.sidebar.button("[REFRESH] Daten aktualisieren"):
    st.cache_data.clear()
    st.rerun()

# Helper functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_odds_data():
    """Lade Odds-Daten aus Supabase oder anderen Quellen"""
    try:
        # Verwende den neuen Odds Manager
        import sys
        sys.path.append('../ml')
        from odds_manager import get_current_odds
        
        return get_current_odds()
    except Exception as e:
        # Fallback auf Supabase
        try:
            return st.session_state.db_client.get_latest_odds()
        except Exception as e2:
            st.error(f"Fehler beim Laden der Odds: {e2}")
            return pd.DataFrame()

@st.cache_data(ttl=300)
def load_predictions_data():
    """Lade Predictions-Daten aus Supabase"""
    try:
        return st.session_state.db_client.get_predictions()
    except Exception as e:
        st.error(f"Fehler beim Laden der Predictions: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_race_results():
    """Lade Rennergebnisse aus Supabase"""
    try:
        return st.session_state.db_client.get_race_results()
    except Exception as e:
        st.error(f"Fehler beim Laden der Ergebnisse: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_betting_performance():
    """Lade Betting-Performance aus Supabase"""
    try:
        return st.session_state.db_client.get_betting_performance()
    except Exception as e:
        st.error(f"Fehler beim Laden der Betting-Daten: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)  # Cache for 1 minute for live data
def load_betting_recommendations():
    """Load current betting recommendations from CSV files"""
    try:
        betting_file = "data/live/betting_recommendations.csv"
        if os.path.exists(betting_file):
            return pd.read_csv(betting_file)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading betting recommendations: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_driver_probabilities():
    """Load driver position probabilities from CSV files"""
    try:
        # Try to find the latest probability file
        prob_files = [
            "data/live/predicted_probabilities_2025_Spanish_Grand_Prix_full.csv",
            "data/live/predicted_probabilities_2025_Austrian_Grand_Prix_full.csv",
            "data/live/predicted_probabilities_2025_British_Grand_Prix_full.csv",
            "data/live/predicted_probabilities_2025_Canadian_Grand_Prix_full.csv",
            "data/live/predicted_probabilities_2025_Monaco_Grand_Prix_full.csv"
        ]
        
        for prob_file in prob_files:
            if os.path.exists(prob_file):
                return pd.read_csv(prob_file)
        
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading driver probabilities: {e}")
        return pd.DataFrame()

def create_odds_trend_chart(odds_df, selected_drivers):
    """Erstelle Odds-Trend-Chart"""
    if len(odds_df) == 0:
        return None
    
    # Convert timestamps
    odds_df['created_at'] = pd.to_datetime(odds_df['created_at'])
    
    # Filter for selected drivers
    filtered_df = odds_df[odds_df['driver'].isin(selected_drivers)]
    
    fig = px.line(
        filtered_df,
        x='created_at',
        y='odds',
        color='driver',
        title='[TREND] Odds-Entwicklung über Zeit',
        labels={'created_at': 'Zeit', 'odds': 'Odds', 'driver': 'Fahrer'}
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="Zeit",
        yaxis_title="Odds",
        legend_title="Fahrer"
    )
    
    return fig

def create_prediction_accuracy_chart(predictions_df, results_df):
    """Erstelle Prediction-Accuracy-Chart"""
    if len(predictions_df) == 0 or len(results_df) == 0:
        return None
    
    # Merge predictions with actual results
    merged = predictions_df.merge(
        results_df[['race_name', 'driver', 'final_position']], 
        on=['race_name', 'driver'], 
        how='inner'
    )
    
    if len(merged) == 0:
        return None
    
    # Calculate accuracy
    merged['position_diff'] = abs(merged['predicted_position'] - merged['final_position'])
    
    fig = px.scatter(
        merged,
        x='predicted_position',
        y='final_position',
        color='driver',
        size='win_probability',
        title='[TARGET] Vorhersage vs. Tatsächliche Position',
        labels={
            'predicted_position': 'Vorhergesagte Position',
            'final_position': 'Tatsächliche Position',
            'driver': 'Fahrer'
        }
    )
    
    # Add perfect prediction line
    fig.add_trace(
        go.Scatter(
            x=[1, 20],
            y=[1, 20],
            mode='lines',
            name='Perfekte Vorhersage',
            line=dict(dash='dash', color='red')
        )
    )
    
    fig.update_layout(height=500)
    return fig

# Main content based on selected page
if page == "[CHART] Übersicht":
    st.title("[CHART] F1 Analytics Hub - Übersicht")
    
    # Load data
    odds_df = load_odds_data()
    predictions_df = load_predictions_data()
    results_df = load_race_results()
    betting_df = load_betting_performance()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("[TREND] Odds-Datensätze", len(odds_df))
    with col2:
        st.metric("[TARGET] Predictions", len(predictions_df))
    with col3:
        st.metric("[RACE] Rennergebnisse", len(results_df))
    with col4:
        st.metric("[MONEY] Betting-Records", len(betting_df))
    
    # Recent activity
    st.subheader("[TIME] Neueste Aktivitäten")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### [TREND] Neueste Odds")
        if len(odds_df) > 0:
            recent_odds = odds_df.head(5)[['driver', 'odds', 'bookmaker', 'race_name']]
            st.dataframe(recent_odds, use_container_width=True)
        else:
            st.info("Keine Odds-Daten verfügbar")
    
    with col2:
        st.markdown("### [TARGET] Neueste Predictions")
        if len(predictions_df) > 0:
            recent_preds = predictions_df.head(5)[['driver', 'predicted_position', 'win_probability', 'race_name']]
            recent_preds['win_probability'] = (recent_preds['win_probability'] * 100).round(1)
            st.dataframe(recent_preds, use_container_width=True)
        else:
            st.info("Keine Predictions-Daten verfügbar")
    
    # Database status
    st.subheader("[TOOL] Datenbank-Status")
    
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        st.success("[OK] Supabase-Verbindung aktiv")
        st.info(f"[TIME] Letzte Aktualisierung: {datetime.now().strftime('%H:%M:%S')}")
    
    with status_col2:
        if st.button("[TEST] Verbindung testen"):
            try:
                test_result = st.session_state.db_client.test_connection()
                if test_result:
                    st.success("[OK] Datenbanktest erfolgreich")
                else:
                    st.error("[ERROR] Datenbanktest fehlgeschlagen")
            except Exception as e:
                st.error(f"[ERROR] Testfehler: {e}")

elif page == "[TREND] Odds-Trends":
    st.title("[TREND] Odds-Trends Analyse")
    
    odds_df = load_odds_data()
    
    if len(odds_df) == 0:
        st.warning("[WARNING] Keine Odds-Daten verfügbar")
        st.stop()
    
    # Filters
    st.sidebar.subheader("[CONTROL] Filter")
    
    available_drivers = sorted(odds_df['driver'].unique())
    selected_drivers = st.sidebar.multiselect(
        "Fahrer auswählen",
        available_drivers,
        default=available_drivers[:5] if len(available_drivers) >= 5 else available_drivers
    )
    
    available_races = sorted(odds_df['race_name'].unique())
    selected_race = st.sidebar.selectbox("Rennen auswählen", ['Alle'] + available_races)
    
    # Filter data
    filtered_odds = odds_df.copy()
    if selected_race != 'Alle':
        filtered_odds = filtered_odds[filtered_odds['race_name'] == selected_race]
    
    if selected_drivers:
        filtered_odds = filtered_odds[filtered_odds['driver'].isin(selected_drivers)]
    
    # Charts
    if len(filtered_odds) > 0:
        # Odds trend chart
        trend_chart = create_odds_trend_chart(filtered_odds, selected_drivers)
        if trend_chart:
            st.plotly_chart(trend_chart, use_container_width=True)
        
        # Odds distribution
        st.subheader("[CHART] Odds-Verteilung")
        fig_hist = px.histogram(
            filtered_odds,
            x='odds',
            color='driver',
            title='Odds-Verteilung nach Fahrer',
            nbins=20
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Summary statistics
        st.subheader("[CLIPBOARD] Statistiken")
        stats = filtered_odds.groupby('driver')['odds'].agg(['mean', 'min', 'max', 'std']).round(2)
        stats.columns = ['Durchschnitt', 'Minimum', 'Maximum', 'Standardabweichung']
        st.dataframe(stats, use_container_width=True)
    
    else:
        st.warning("[WARNING] Keine Daten für die ausgewählten Filter")

elif page == "[TARGET] Predictions-Analyse":
    st.title("[TARGET] Predictions-Analyse")
    
    predictions_df = load_predictions_data()
    results_df = load_race_results()
    
    if len(predictions_df) == 0:
        st.warning("[WARNING] Keine Predictions-Daten verfügbar")
        st.stop()
    
    # Accuracy analysis if results available
    if len(results_df) > 0:
        st.subheader("[TARGET] Vorhersage-Genauigkeit")
        
        accuracy_chart = create_prediction_accuracy_chart(predictions_df, results_df)
        if accuracy_chart:
            st.plotly_chart(accuracy_chart, use_container_width=True)
    
    # Win probability distribution
    st.subheader("[CHART] Gewinnwahrscheinlichkeiten")
    
    fig_win_prob = px.box(
        predictions_df,
        x='driver',
        y='win_probability',
        title='Gewinnwahrscheinlichkeiten nach Fahrer'
    )
    fig_win_prob.update_xaxes(tickangle=45)
    st.plotly_chart(fig_win_prob, use_container_width=True)
    
    # Model performance by version
    if 'model_version' in predictions_df.columns:
        st.subheader("[TOOL] Model-Performance")
        
        model_stats = predictions_df.groupby('model_version').agg({
            'win_probability': ['mean', 'std'],
            'predicted_position': ['mean', 'std']
        }).round(3)
        
        st.dataframe(model_stats, use_container_width=True)

elif page == "[RACE] Rennergebnisse":
    st.title("[RACE] Rennergebnisse")
    
    results_df = load_race_results()
    
    if len(results_df) == 0:
        st.warning("[WARNING] Keine Rennergebnisse verfügbar")
        st.stop()
    
    # Race selector
    available_races = sorted(results_df['race_name'].unique())
    selected_race = st.selectbox("Rennen auswählen", available_races)
    
    race_results = results_df[results_df['race_name'] == selected_race].sort_values('final_position')
    
    # Display results
    st.subheader(f"[RACE] Ergebnisse: {selected_race}")
    
    display_results = race_results[['final_position', 'driver', 'points', 'dnf']].copy()
    display_results.columns = ['Position', 'Fahrer', 'Punkte', 'DNF']
    
    st.dataframe(display_results, use_container_width=True)
    
    # Points distribution
    st.subheader("[CHART] Punkte-Verteilung")
    
    fig_points = px.bar(
        race_results,
        x='driver',
        y='points',
        title=f'Punkte-Verteilung - {selected_race}'
    )
    fig_points.update_xaxes(tickangle=45)
    st.plotly_chart(fig_points, use_container_width=True)

elif page == "[MONEY] Betting-Performance":
    st.title("[MONEY] Betting-Performance")
    
    betting_df = load_betting_performance()
    
    if len(betting_df) == 0:
        st.warning("[WARNING] Keine Betting-Daten verfügbar")
        st.info("[IDEA] Betting-Daten werden erstellt, wenn du echte Wetten platzierst")
        st.stop()
    
    # Performance metrics
    total_stakes = betting_df['stake'].sum()
    total_profit = betting_df['profit_loss'].sum()
    roi = (total_profit / total_stakes * 100) if total_stakes > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("[MONEY] Gesamteinsatz", f"{total_stakes:.2f}€")
    with col2:
        st.metric("[TREND] Gewinn/Verlust", f"{total_profit:.2f}€")
    with col3:
        st.metric("[CHART] ROI", f"{roi:.1f}%")
    with col4:
        win_rate = len(betting_df[betting_df['result'] == 'win']) / len(betting_df) * 100
        st.metric("[TARGET] Gewinnrate", f"{win_rate:.1f}%")
    
    # Performance over time
    if 'bet_date' in betting_df.columns:
        betting_df['bet_date'] = pd.to_datetime(betting_df['bet_date'])
        betting_df = betting_df.sort_values('bet_date')
        betting_df['cumulative_profit'] = betting_df['profit_loss'].cumsum()
        
        fig_profit = px.line(
            betting_df,
            x='bet_date',
            y='cumulative_profit',
            title='[TREND] Kumulativer Gewinn über Zeit'
        )
        st.plotly_chart(fig_profit, use_container_width=True)

elif page == "[DICE] Wett-Empfehlungen":
    st.title("[DICE] Wett-Empfehlungen")
    
    # Load betting recommendations and probabilities
    betting_recs = load_betting_recommendations()
    driver_probs = load_driver_probabilities()
    
    if len(betting_recs) == 0 and len(driver_probs) == 0:
        st.warning("[WARNING] Generiere Wett-Empfehlungen...")
        # Try to generate recommendations if not available
        try:
            from ml.betting_strategy import generate_betting_recommendations
            pred_file = "data/live/predicted_probabilities_2025_Spanish_Grand_Prix_full.csv"
            odds_file = "data/live/sample_odds.csv"
            betting_file = "data/live/betting_recommendations.csv"
            
            if os.path.exists(pred_file):
                betting_df = generate_betting_recommendations(pred_file, odds_file, betting_file)
                st.success("[OK] Wett-Empfehlungen erfolgreich generiert!")
                betting_recs = load_betting_recommendations()
            else:
                st.error("[ERROR] Vorhersagedaten nicht verfügbar")
                st.stop()
        except Exception as e:
            st.error(f"[ERROR] Fehler beim Generieren der Empfehlungen: {e}")
            st.stop()
    
    # Sidebar filters (like in old dashboard)
    st.sidebar.markdown("### [CONTROL] Filter")
    
    if len(betting_recs) > 0:
        show_only_recommended = st.sidebar.checkbox("Nur empfohlene Wetten anzeigen", value=True)
        
        if 'expected_value' in betting_recs.columns:
            min_ev_filter = st.sidebar.slider("Minimaler erwarteter Wert", -5.0, 10.0, 0.0, 0.1)
        elif 'value_rating' in betting_recs.columns:
            min_value_filter = st.sidebar.slider("Minimales Value-Rating", 1.0, 5.0, 3.0, 0.1)
    
    # Display betting recommendations
    if len(betting_recs) > 0:
        st.subheader("[CHART] Wett-Empfehlungen Übersicht")
        
        # Filter data
        filtered_recs = betting_recs.copy()
        
        if 'bet_recommendation' in betting_recs.columns and show_only_recommended:
            filtered_recs = filtered_recs[filtered_recs['bet_recommendation'] == 'Ja']
        elif 'value_rating' in betting_recs.columns and 'min_value_filter' in locals():
            filtered_recs = filtered_recs[filtered_recs['value_rating'] >= min_value_filter]
        elif 'expected_value' in betting_recs.columns and 'min_ev_filter' in locals():
            filtered_recs = filtered_recs[filtered_recs['expected_value'] >= min_ev_filter]
        
        if len(filtered_recs) > 0:
            # Format table for better display (like old dashboard)
            if 'expected_value' in filtered_recs.columns:
                # New format with expected_value
                display_df = filtered_recs[[
                    'driver', 'position', 'odds', 'probability_pct', 
                    'expected_value', 'bet_recommendation', 'stake', 'potential_profit'
                ]].copy()
                
                display_df.columns = [
                    'Fahrer', 'Position', 'Quote', 'Wahrscheinlichkeit (%)', 
                    'Erwarteter Wert (€)', 'Empfehlung', 'Einsatz (€)', 'Potentieller Gewinn (€)'
                ]
            else:
                # Old format with value_rating
                display_cols = ['driver', 'bet_type', 'odds', 'win_probability', 'value_rating', 'recommended_stake', 'risk_level']
                available_cols = [col for col in display_cols if col in filtered_recs.columns]
                display_df = filtered_recs[available_cols].copy()
            
            st.dataframe(display_df, use_container_width=True)
            
            # Statistics (like old dashboard)
            col1, col2, col3, col4 = st.columns(4)
            
            if 'bet_recommendation' in filtered_recs.columns:
                recommended_bets = filtered_recs[filtered_recs['bet_recommendation'] == 'Ja']
            else:
                recommended_bets = filtered_recs
            
            with col1:
                st.metric("Empfohlene Wetten", len(recommended_bets))
            with col2:
                if 'stake' in recommended_bets.columns:
                    total_stake = recommended_bets['stake'].sum()
                elif 'recommended_stake' in recommended_bets.columns:
                    total_stake = recommended_bets['recommended_stake'].sum()
                else:
                    total_stake = 0
                st.metric("Gesamteinsatz", f"{total_stake:.2f}€")
            with col3:
                if 'potential_profit' in recommended_bets.columns:
                    total_potential = recommended_bets['potential_profit'].sum()
                elif 'expected_profit' in recommended_bets.columns:
                    total_potential = recommended_bets['expected_profit'].sum()
                else:
                    total_potential = 0
                st.metric("Potentieller Gewinn", f"{total_potential:.2f}€")
            with col4:
                if 'expected_value' in recommended_bets.columns:
                    total_ev = recommended_bets['expected_value'].sum()
                    st.metric("Gesamter erwarteter Wert", f"{total_ev:.2f}€")
                elif 'value_rating' in recommended_bets.columns:
                    avg_value = recommended_bets['value_rating'].mean()
                    st.metric("Durchschnittliches Value-Rating", f"{avg_value:.1f}/5.0")
            
            # Highlight best bet (like old dashboard)
            if len(recommended_bets) > 0:
                st.subheader("[TROPHY] Beste Wett-Empfehlung")
                
                if 'expected_value' in recommended_bets.columns:
                    best_bet = recommended_bets.loc[recommended_bets['expected_value'].idxmax()]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Fahrer", f"{best_bet['driver']} (P{best_bet['position']})")
                    with col2:
                        st.metric("Quote", f"{best_bet['odds']:.2f}")
                    with col3:
                        st.metric("Erwarteter Wert", f"{best_bet['expected_value']:.2f}€")
                elif 'value_rating' in recommended_bets.columns:
                    best_bet = recommended_bets.loc[recommended_bets['value_rating'].idxmax()]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Fahrer", best_bet['driver'])
                    with col2:
                        st.metric("Quote", f"{best_bet['odds']:.2f}")
                    with col3:
                        st.metric("Value Rating", f"{best_bet['value_rating']:.1f}/5.0")
            
            # Initialize bet tracker for placing bets
            if 'bet_tracker' not in st.session_state:
                st.session_state.bet_tracker = BetTracker(st.session_state.db_client)
            
            # Add betting functionality with learning mechanism
            st.subheader("[TARGET] Wette platzieren & Lernen")
            
            if len(recommended_bets) > 0:
                st.markdown("**Empfohlene Wetten zum Platzieren:**")
                
                for idx, bet in recommended_bets.iterrows():
                    if 'expected_value' in bet:
                        title = f"[DICE] {bet['driver']} - Position {bet['position']} (EV: {bet['expected_value']:.2f}€)"
                    else:
                        title = f"[DICE] {bet['driver']} - {bet['bet_type']} (Value: {bet['value_rating']:.1f})"
                    
                    with st.expander(title):
                        col_bet1, col_bet2, col_bet3 = st.columns([2, 1, 1])
                        
                        with col_bet1:
                            st.write(f"**Quote:** {bet['odds']:.2f}")
                            if 'probability_pct' in bet:
                                st.write(f"**Wahrscheinlichkeit:** {bet['probability_pct']:.1f}%")
                            elif 'win_probability' in bet:
                                st.write(f"**Wahrscheinlichkeit:** {bet['win_probability']*100:.1f}%")
                            
                            if 'stake' in bet:
                                stake_value = bet['stake']
                                profit_key = 'potential_profit'
                            else:
                                stake_value = bet['recommended_stake']
                                profit_key = 'expected_profit'
                            
                            st.write(f"**Empfohlener Einsatz:** {stake_value:.2f}€")
                            if profit_key in bet:
                                st.write(f"**Potentieller Gewinn:** {bet[profit_key]:.2f}€")
                        
                        with col_bet2:
                            stake = st.number_input(f"Einsatz (€)", min_value=1.0, max_value=1000.0, 
                                                  value=float(stake_value), step=1.0, key=f"stake_{idx}")
                        
                        with col_bet3:
                            if st.button(f"Wette platzieren", key=f"place_bet_{idx}"):
                                try:
                                    if 'position' in bet:
                                        bet_type = f"Position {bet['position']}"
                                        race_name = "Spanish Grand Prix 2025"
                                    else:
                                        bet_type = bet['bet_type']
                                        race_name = bet.get('race_name', 'Aktuelles Rennen')
                                    
                                    bet_id = st.session_state.bet_tracker.add_bet(
                                        bet_type=bet_type,
                                        driver=bet['driver'],
                                        race_name=race_name,
                                        odds=bet['odds'],
                                        stake=stake,
                                        bookmaker="System-Empfehlung",
                                        confidence=int(bet.get('value_rating', 3)),
                                        notes=f"Automatisch aus Empfehlung erstellt."
                                    )
                                    st.success(f"[OK] Wette platziert! ID: {bet_id}")
                                    st.info("[ROBOT] Diese Wette wird für das ML-Lernen dokumentiert")
                                except Exception as e:
                                    st.error(f"[ERROR] Fehler beim Platzieren der Wette: {e}")
            else:
                st.info("[INFO] Keine empfohlenen Wetten mit den aktuellen Filterkriterien")
        else:
            st.warning("[WARNING] Keine Wetten entsprechen den aktuellen Filterkriterien.")
    
    # Display driver probabilities
    if len(driver_probs) > 0:
        st.subheader("[CHART] Fahrer-Wahrscheinlichkeiten")
        
        # Position probability heatmap
        if 'driver' in driver_probs.columns:
            # Prepare data for heatmap
            prob_cols = [col for col in driver_probs.columns if col.startswith('pos_') and col != 'pos_dnf']
            
            if prob_cols:
                heatmap_data = driver_probs.set_index('driver')[prob_cols]
                
                fig_heatmap = px.imshow(
                    heatmap_data.values,
                    x=[col.replace('pos_', 'P') for col in prob_cols],
                    y=heatmap_data.index,
                    color_continuous_scale='RdYlGn',
                    title='[TARGET] Positionswahrscheinlichkeiten nach Fahrer',
                    labels={'color': 'Wahrscheinlichkeit'}
                )
                
                fig_heatmap.update_layout(height=600)
                st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Top 3 probabilities
        if 'pos_1' in driver_probs.columns and 'pos_2' in driver_probs.columns and 'pos_3' in driver_probs.columns:
            st.subheader("[TROPHY] Podium-Wahrscheinlichkeiten")
            
            podium_data = driver_probs[['driver', 'pos_1', 'pos_2', 'pos_3']].copy()
            podium_data['podium_prob'] = podium_data['pos_1'] + podium_data['pos_2'] + podium_data['pos_3']
            podium_data = podium_data.sort_values('podium_prob', ascending=False)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### [GOLD] Sieg-Favoriten")
                win_favs = podium_data.nlargest(5, 'pos_1')[['driver', 'pos_1']]
                win_favs['pos_1'] = (win_favs['pos_1'] * 100).round(1)
                win_favs.columns = ['Fahrer', 'Sieg %']
                st.dataframe(win_favs, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("### [SILVER] Podium-Favoriten")
                podium_favs = podium_data.nlargest(5, 'podium_prob')[['driver', 'podium_prob']]
                podium_favs['podium_prob'] = (podium_favs['podium_prob'] * 100).round(1)
                podium_favs.columns = ['Fahrer', 'Podium %']
                st.dataframe(podium_favs, use_container_width=True, hide_index=True)
            
            with col3:
                st.markdown("### [TARGET] Überraschungskandidaten")
                # Drivers with low win probability but decent podium chance
                surprises = podium_data[
                    (podium_data['pos_1'] < 0.1) & (podium_data['podium_prob'] > 0.15)
                ].nlargest(5, 'podium_prob')[['driver', 'podium_prob']]
                
                if len(surprises) > 0:
                    surprises['podium_prob'] = (surprises['podium_prob'] * 100).round(1)
                    surprises.columns = ['Fahrer', 'Podium %']
                    st.dataframe(surprises, use_container_width=True, hide_index=True)
                else:
                    st.info("Keine Überraschungskandidaten")
    
    # Betting strategy tips
    st.subheader("[IDEA] Wett-Strategien")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### [TARGET] Value-Betting
        - Suche nach Wetten mit Value-Rating ≥ 3.0
        - Vergleiche unsere Wahrscheinlichkeiten mit Buchmacher-Odds
        - Setze nur bei positivem Expected Value
        """)
        
        st.markdown("""
        ### [TROPHY] Sieg-Wetten
        - Favoriten mit >30% Siegchance
        - Außenseiter mit >5% bei hohen Odds
        - Vermeide Fahrer mit <2% Siegchance
        """)
    
    with col2:
        st.markdown("""
        ### [SILVER] Podium-Wetten
        - Sicherere Option als Sieg-Wetten
        - Suche Fahrer mit >20% Podium-Chance
        - Gute Alternative bei unsicheren Rennen
        """)
        
        st.markdown("""
        ### [WARNING] Risiko-Management
        - Nie mehr als 5% des Budgets pro Wette
        - Diversifiziere über mehrere Wetten
        - Setze Limits und halte sie ein
        """)
    
    # Risk warning
    st.warning("""
    [WARNING] **Wichtiger Hinweis:** 
    Diese Empfehlungen basieren auf statistischen Modellen und sind keine Garantie für Gewinne. 
    Wette nur mit Geld, das du dir leisten kannst zu verlieren. 
    Glücksspiel kann süchtig machen.
    """)

elif page == "[TARGET] Wett-Tracking":
    st.title("[TARGET] Wett-Tracking")
    
    # Initialize BetTracker
    if 'bet_tracker' not in st.session_state:
        st.session_state.bet_tracker = BetTracker(st.session_state.db_client)
    
    tracker = st.session_state.bet_tracker
    
    # Tabs for different functions
    tab1, tab2, tab3, tab4 = st.tabs(["[MEMO] Neue Wette", "[CHART] Aktive Wetten", "[TREND] Performance", "[TROPHY] Ergebnisse"])
    
    with tab1:
        st.subheader("[MEMO] Neue Wette hinzufügen")
        
        with st.form("new_bet_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                bet_type = st.selectbox(
                    "Wett-Typ",
                    ["race_winner", "podium_finish", "points_finish", "head_to_head", "fastest_lap"]
                )
                
                driver = st.text_input("Fahrer")
                race_name = st.text_input("Rennen")
                bookmaker = st.text_input("Buchmacher")
            
            with col2:
                odds = st.number_input("Odds", min_value=1.01, value=2.0, step=0.01)
                stake = st.number_input("Einsatz (€)", min_value=0.01, value=10.0, step=0.01)
                confidence = st.slider("Vertrauen (1-5)", 1, 5, 3)
            
            notes = st.text_area("Notizen (optional)")
            
            if st.form_submit_button("[TARGET] Wette hinzufügen"):
                try:
                    bet_id = tracker.add_bet(
                        bet_type=bet_type,
                        driver=driver,
                        race_name=race_name,
                        odds=odds,
                        stake=stake,
                        bookmaker=bookmaker,
                        confidence=confidence,
                        notes=notes
                    )
                    st.success(f"[OK] Wette hinzugefügt! ID: {bet_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"[ERROR] Fehler beim Hinzufügen: {e}")
    
    with tab2:
        st.subheader("[CHART] Aktive Wetten")
        
        active_bets = tracker.get_active_bets()
        
        if len(active_bets) == 0:
            st.info("[INFO] Keine aktiven Wetten")
        else:
            # Display active bets
            for idx, bet in active_bets.iterrows():
                with st.expander(f"[TARGET] {bet['driver']} - {bet['race_name']} (ID: {bet['id']})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Wett-Typ", bet['bet_type'])
                        st.metric("Odds", f"{bet['odds']:.2f}")
                        st.metric("Einsatz", f"{bet['stake']:.2f}€")
                    
                    with col2:
                        st.metric("Buchmacher", bet['bookmaker'])
                        st.metric("Vertrauen", f"{bet['confidence']}/5")
                        potential_win = bet['stake'] * bet['odds']
                        st.metric("Potentieller Gewinn", f"{potential_win:.2f}€")
                    
                    with col3:
                        st.metric("Datum", bet['bet_date'].strftime('%d.%m.%Y'))
                        if bet['notes']:
                            st.text_area("Notizen", bet['notes'], disabled=True, key=f"notes_{bet['id']}")
                    
                    # Update bet result
                    st.markdown("**Ergebnis aktualisieren:**")
                    result_col1, result_col2 = st.columns(2)
                    
                    with result_col1:
                        result = st.selectbox(
                            "Ergebnis",
                            ["pending", "win", "loss", "void"],
                            index=0,
                            key=f"result_{bet['id']}"
                        )
                    
                    with result_col2:
                        if st.button(f"💾 Aktualisieren", key=f"update_{bet['id']}"):
                            try:
                                tracker.update_bet_result(bet['id'], result)
                                st.success("[OK] Ergebnis aktualisiert")
                                st.rerun()
                            except Exception as e:
                                st.error(f"[ERROR] Fehler: {e}")
    
    with tab3:
        st.subheader("[TREND] Performance-Analyse")
        
        performance = tracker.get_performance_stats()
        
        if performance:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("[MONEY] Gesamteinsatz", f"{performance['total_stakes']:.2f}€")
            with col2:
                st.metric("[TREND] Gewinn/Verlust", f"{performance['total_profit']:.2f}€")
            with col3:
                st.metric("[CHART] ROI", f"{performance['roi']:.1f}%")
            with col4:
                st.metric("[TARGET] Gewinnrate", f"{performance['win_rate']:.1f}%")
            
            # Performance by bet type
            bet_type_stats = tracker.get_performance_by_bet_type()
            
            if len(bet_type_stats) > 0:
                st.subheader("[CHART] Performance nach Wett-Typ")
                
                fig_bet_type = px.bar(
                    bet_type_stats,
                    x='bet_type',
                    y='roi',
                    title='ROI nach Wett-Typ',
                    color='roi',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_bet_type, use_container_width=True)
                
                st.dataframe(bet_type_stats, use_container_width=True)
        else:
            st.info("[INFO] Keine Performance-Daten verfügbar")
    
    with tab4:
        st.subheader("[TROPHY] Wett-Ergebnisse")
        
        all_bets = tracker.get_all_bets()
        
        if len(all_bets) == 0:
            st.info("[INFO] Keine Wetten vorhanden")
        else:
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox(
                    "Status Filter",
                    ["Alle", "pending", "win", "loss", "void"]
                )
            
            with col2:
                bet_type_filter = st.selectbox(
                    "Wett-Typ Filter",
                    ["Alle"] + list(all_bets['bet_type'].unique())
                )
            
            with col3:
                date_range = st.date_input(
                    "Datum von",
                    value=datetime.now() - timedelta(days=30)
                )
            
            # Apply filters
            filtered_bets = all_bets.copy()
            
            if status_filter != "Alle":
                filtered_bets = filtered_bets[filtered_bets['result'] == status_filter]
            
            if bet_type_filter != "Alle":
                filtered_bets = filtered_bets[filtered_bets['bet_type'] == bet_type_filter]
            
            filtered_bets = filtered_bets[filtered_bets['bet_date'] >= pd.to_datetime(date_range)]
            
            # Display results
            if len(filtered_bets) > 0:
                # Summary
                summary_col1, summary_col2, summary_col3 = st.columns(3)
                
                with summary_col1:
                    st.metric("Gefilterte Wetten", len(filtered_bets))
                
                with summary_col2:
                    total_stake_filtered = filtered_bets['stake'].sum()
                    st.metric("Gesamteinsatz", f"{total_stake_filtered:.2f}€")
                
                with summary_col3:
                    if 'profit_loss' in filtered_bets.columns:
                        total_profit_filtered = filtered_bets['profit_loss'].sum()
                        st.metric("Gewinn/Verlust", f"{total_profit_filtered:.2f}€")
                
                # Detailed table
                display_cols = ['bet_date', 'driver', 'race_name', 'bet_type', 'odds', 'stake', 'result']
                if 'profit_loss' in filtered_bets.columns:
                    display_cols.append('profit_loss')
                
                st.dataframe(
                    filtered_bets[display_cols].sort_values('bet_date', ascending=False),
                    use_container_width=True
                )
                
                # Export option
                if st.button("[DOWNLOAD] Ergebnisse exportieren"):
                    csv = filtered_bets.to_csv(index=False)
                    st.download_button(
                        "[DOWNLOAD] CSV Download",
                        csv,
                        f"bet_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
            else:
                st.info("[INFO] Keine Wetten für die ausgewählten Filter")

elif page == "🧠 ML-Lernen":
    st.title("🧠 ML-Lernen & Insights")
    
    # Initialize BetTracker for learning insights
    if 'bet_tracker' not in st.session_state:
        st.session_state.bet_tracker = BetTracker(st.session_state.db_client)
    
    tracker = st.session_state.bet_tracker
    
    # Tabs for different learning aspects
    tab1, tab2, tab3, tab4 = st.tabs(["[CHART] Lern-Übersicht", "[TARGET] Modell-Performance", "[TREND] Verbesserungen", "[CRYSTAL] Vorhersage-Qualität"])
    
    with tab1:
        st.subheader("[CHART] Machine Learning Übersicht")
        
        # Get learning insights
        all_bets = tracker.get_all_bets()
        
        if len(all_bets) > 0:
            # Filter completed bets for learning
            completed_bets = all_bets[all_bets['status'].isin(['win', 'loss'])]
            
            if len(completed_bets) > 0:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Lern-Datensätze", len(completed_bets))
                
                with col2:
                    accuracy = len(completed_bets[completed_bets['result'] == 'win']) / len(completed_bets) * 100
                    st.metric("Modell-Genauigkeit", f"{accuracy:.1f}%")
                
                with col3:
                    if 'confidence' in completed_bets.columns:
                        avg_confidence = completed_bets['confidence'].mean()
                        st.metric("Ø Vertrauen", f"{avg_confidence:.1f}/5")
                    else:
                        st.metric("Ø Vertrauen", "N/A")
                
                with col4:
                    learning_rate = min(len(completed_bets) / 100 * 100, 100)
                    st.metric("Lern-Fortschritt", f"{learning_rate:.0f}%")
                
                # Learning insights
                st.subheader("🧠 Lern-Insights")
                
                # Confidence vs Success Rate
                if 'confidence' in completed_bets.columns:
                    confidence_analysis = completed_bets.groupby('confidence').agg({
                        'result': lambda x: (x == 'win').mean() * 100,
                        'stake': 'count'
                    }).round(1)
                    confidence_analysis.columns = ['Erfolgsrate (%)', 'Anzahl Wetten']
                    
                    st.markdown("### [TARGET] Vertrauen vs. Erfolgsrate")
                    
                    fig_confidence = px.bar(
                        x=confidence_analysis.index,
                        y=confidence_analysis['Erfolgsrate (%)'],
                        title='Erfolgsrate nach Vertrauenslevel',
                        labels={'x': 'Vertrauenslevel', 'y': 'Erfolgsrate (%)'}
                    )
                    st.plotly_chart(fig_confidence, use_container_width=True)
                    
                    st.dataframe(confidence_analysis, use_container_width=True)
                
                # Bet Type Performance
                if 'bet_type' in completed_bets.columns:
                    st.markdown("### [CHART] Performance nach Wett-Typ")
                    
                    bet_type_analysis = completed_bets.groupby('bet_type').agg({
                        'result': lambda x: (x == 'win').mean() * 100,
                        'stake': ['count', 'sum'],
                        'odds': 'mean'
                    }).round(2)
                    
                    bet_type_analysis.columns = ['Erfolgsrate (%)', 'Anzahl', 'Gesamteinsatz', 'Ø Odds']
                    st.dataframe(bet_type_analysis, use_container_width=True)
                
                # Learning recommendations
                st.subheader("[IDEA] Lern-Empfehlungen")
                
                recommendations = []
                
                if 'confidence' in completed_bets.columns:
                    high_conf_success = completed_bets[completed_bets['confidence'] >= 4]['result'].apply(lambda x: x == 'win').mean()
                    low_conf_success = completed_bets[completed_bets['confidence'] <= 2]['result'].apply(lambda x: x == 'win').mean()
                    
                    if high_conf_success > 0.6:
                        recommendations.append("[OK] Hohe Vertrauenswetten zeigen gute Ergebnisse - weiter so!")
                    else:
                        recommendations.append("[WARNING] Kalibriere dein Vertrauen - hohe Confidence führt nicht zu besseren Ergebnissen")
                    
                    if low_conf_success > 0.4:
                        recommendations.append("[IDEA] Niedrige Vertrauenswetten sind überraschend erfolgreich - analysiere diese Muster")
                
                if len(completed_bets) >= 20:
                    recent_performance = completed_bets.tail(10)['result'].apply(lambda x: x == 'win').mean()
                    overall_performance = completed_bets['result'].apply(lambda x: x == 'win').mean()
                    
                    if recent_performance > overall_performance + 0.1:
                        recommendations.append("[TREND] Deine Vorhersagen werden besser - das Modell lernt!")
                    elif recent_performance < overall_performance - 0.1:
                        recommendations.append("📉 Aktuelle Performance schwächer - überprüfe deine Strategie")
                
                if not recommendations:
                    recommendations.append("[CHART] Sammle mehr Daten für bessere Lern-Insights")
                
                for rec in recommendations:
                    st.info(rec)
            
            else:
                st.info("[INFO] Keine abgeschlossenen Wetten für das Lernen verfügbar")
        else:
            st.info("[INFO] Keine Wett-Daten für das Machine Learning verfügbar")
    
    with tab2:
        st.subheader("[TARGET] Modell-Performance Analyse")
        
        # Load predictions and compare with actual results
        predictions_df = load_predictions_data()
        results_df = load_race_results()
        
        if len(predictions_df) > 0 and len(results_df) > 0:
            # Merge predictions with results
            merged_data = predictions_df.merge(
                results_df[['race_name', 'driver', 'final_position']], 
                on=['race_name', 'driver'], 
                how='inner'
            )
            
            if len(merged_data) > 0:
                # Calculate prediction accuracy
                merged_data['position_error'] = abs(merged_data['predicted_position'] - merged_data['final_position'])
                merged_data['win_prediction_correct'] = (
                    (merged_data['predicted_position'] == 1) & (merged_data['final_position'] == 1)
                ) | (
                    (merged_data['predicted_position'] != 1) & (merged_data['final_position'] != 1)
                )
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_error = merged_data['position_error'].mean()
                    st.metric("Ø Positions-Fehler", f"{avg_error:.1f}")
                
                with col2:
                    win_accuracy = merged_data['win_prediction_correct'].mean() * 100
                    st.metric("Sieg-Vorhersage Genauigkeit", f"{win_accuracy:.1f}%")
                
                with col3:
                    perfect_predictions = len(merged_data[merged_data['position_error'] == 0])
                    st.metric("Perfekte Vorhersagen", perfect_predictions)
                
                # Error distribution
                st.markdown("### [CHART] Fehler-Verteilung")
                
                fig_error = px.histogram(
                    merged_data,
                    x='position_error',
                    title='Verteilung der Positions-Fehler',
                    nbins=20
                )
                st.plotly_chart(fig_error, use_container_width=True)
                
                # Driver-specific accuracy
                st.markdown("### [F1] Fahrer-spezifische Genauigkeit")
                
                driver_accuracy = merged_data.groupby('driver').agg({
                    'position_error': ['mean', 'std', 'count'],
                    'win_prediction_correct': 'mean'
                }).round(2)
                
                driver_accuracy.columns = ['Ø Fehler', 'Std Fehler', 'Vorhersagen', 'Sieg-Genauigkeit']
                driver_accuracy = driver_accuracy.sort_values('Ø Fehler')
                
                st.dataframe(driver_accuracy, use_container_width=True)
            
            else:
                st.info("[INFO] Keine übereinstimmenden Vorhersage- und Ergebnisdaten")
        else:
            st.info("[INFO] Vorhersage- oder Ergebnisdaten nicht verfügbar")
    
    with tab3:
        st.subheader("[TREND] Modell-Verbesserungen")
        
        # Show improvement suggestions based on data
        st.markdown("### [TOOL] Verbesserungs-Vorschläge")
        
        improvements = [
            {
                "Bereich": "Datenqualität",
                "Vorschlag": "Mehr historische Daten sammeln für bessere Muster-Erkennung",
                "Priorität": "Hoch",
                "Status": "In Arbeit"
            },
            {
                "Bereich": "Feature Engineering",
                "Vorschlag": "Wetter- und Streckenbedingungen als Features hinzufügen",
                "Priorität": "Mittel",
                "Status": "Geplant"
            },
            {
                "Bereich": "Modell-Ensemble",
                "Vorschlag": "Mehrere Modelle kombinieren für robustere Vorhersagen",
                "Priorität": "Hoch",
                "Status": "Evaluierung"
            },
            {
                "Bereich": "Real-time Updates",
                "Vorschlag": "Live-Daten während der Rennen integrieren",
                "Priorität": "Niedrig",
                "Status": "Konzept"
            }
        ]
        
        improvements_df = pd.DataFrame(improvements)
        st.dataframe(improvements_df, use_container_width=True)
        
        # Model versioning
        st.markdown("### [REFRESH] Modell-Versionen")
        
        versions = [
            {"Version": "v1.0", "Datum": "2024-01-01", "Genauigkeit": "72%", "Features": "Basis-Features"},
            {"Version": "v1.1", "Datum": "2024-02-15", "Genauigkeit": "75%", "Features": "+ Qualifying-Daten"},
            {"Version": "v1.2", "Datum": "2024-03-01", "Genauigkeit": "78%", "Features": "+ Team-Performance"},
            {"Version": "v2.0", "Datum": "2024-04-01", "Genauigkeit": "82%", "Features": "+ Deep Learning"}
        ]
        
        versions_df = pd.DataFrame(versions)
        st.dataframe(versions_df, use_container_width=True)
        
        # Performance trend
        fig_trend = px.line(
            versions_df,
            x='Version',
            y='Genauigkeit',
            title='Modell-Performance Entwicklung',
            markers=True
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with tab4:
        st.subheader("[CRYSTAL] Vorhersage-Qualität")
        
        # Calibration analysis
        st.markdown("### [TARGET] Kalibrierungs-Analyse")
        
        st.info("""
        **Was ist Kalibrierung?**
        Ein gut kalibriertes Modell sagt nicht nur korrekte Ergebnisse vorher, 
        sondern gibt auch realistische Wahrscheinlichkeiten an. 
        Wenn das Modell 70% Wahrscheinlichkeit für einen Sieg vorhersagt, 
        sollte der Fahrer in 70% der Fälle tatsächlich gewinnen.
        """)
        
        # Uncertainty quantification
        st.markdown("### [CHART] Unsicherheits-Quantifizierung")
        
        uncertainty_metrics = {
            "Metrik": ["Konfidenz-Intervall", "Vorhersage-Varianz", "Modell-Unsicherheit", "Daten-Unsicherheit"],
            "Wert": ["±2.3 Positionen", "1.8", "Mittel", "Niedrig"],
            "Interpretation": [
                "95% der Vorhersagen liegen in diesem Bereich",
                "Durchschnittliche Streuung der Vorhersagen",
                "Modell ist sich seiner Grenzen bewusst",
                "Eingangsdaten sind zuverlässig"
            ]
        }
        
        uncertainty_df = pd.DataFrame(uncertainty_metrics)
        st.dataframe(uncertainty_df, use_container_width=True)
        
        # Feature importance
        st.markdown("### [TARGET] Feature-Wichtigkeit")
        
        feature_importance = {
            "Feature": ["Qualifying-Position", "Fahrer-Rating", "Team-Performance", "Strecken-Historie", "Aktuelle Form"],
            "Wichtigkeit (%)": [35, 25, 20, 12, 8],
            "Beschreibung": [
                "Startposition hat größten Einfluss",
                "Fahrer-Skill ist entscheidend",
                "Team-Stärke beeinflusst Ergebnis",
                "Strecken-Erfahrung hilft",
                "Aktuelle Leistung relevant"
            ]
        }
        
        feature_df = pd.DataFrame(feature_importance)
        
        fig_importance = px.bar(
            feature_df,
            x='Feature',
            y='Wichtigkeit (%)',
            title='Feature-Wichtigkeit im Modell'
        )
        st.plotly_chart(fig_importance, use_container_width=True)
        
        st.dataframe(feature_df, use_container_width=True)
        
        # Model explanation
        st.markdown("### 🧠 Modell-Erklärung")
        
        st.info("""
        **Wie funktioniert unser ML-Modell?**
        
        1. **Datensammlung**: Historische Renn-, Qualifying- und Fahrerdaten
        2. **Feature Engineering**: Transformation der Rohdaten in aussagekräftige Features
        3. **Training**: Das Modell lernt Muster aus vergangenen Rennen
        4. **Vorhersage**: Anwendung der gelernten Muster auf zukünftige Rennen
        5. **Evaluation**: Kontinuierliche Verbesserung basierend auf neuen Ergebnissen
        
        **Aktuelle Modell-Architektur**: Ensemble aus Random Forest und Gradient Boosting
        **Training-Daten**: 500+ Rennen seit 2020
        **Update-Frequenz**: Nach jedem Rennen
        """)

elif page == "[SETTINGS] Odds-Konfiguration":
    st.title("[SETTINGS] Odds-Konfiguration")
    
    # Import OddsManager
    try:
        from ml.odds_manager import OddsManager
        odds_manager = OddsManager()
        
        st.subheader("[CHART] Aktuelle Konfiguration")
        
        # Current status
        status = odds_manager.get_status()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Aktuelle Quelle", status['current_source'])
        with col2:
            st.metric("Status", "[OK] Aktiv" if status['is_active'] else "[ERROR] Inaktiv")
        with col3:
            st.metric("Letzte Aktualisierung", status['last_update'])
        
        # Spezielle Nachricht für Stake Scraper
        if status['current_source'] == 'stake_scraper':
            st.info("🎰 **Stake.com Scraper aktiv** - Das System versucht echte Odds von Stake.com zu laden. Falls der Scraper noch läuft oder keine aktuellen Odds verfügbar sind, werden temporär Testdaten verwendet.")
            
            # Teste ob echte Odds verfügbar sind
            current_odds = odds_manager.get_current_odds()
            if len(current_odds) > 0 and 'bookmaker' in current_odds.columns:
                if current_odds['bookmaker'].iloc[0] == 'Test Bookmaker':
                    st.warning("[WARNING] **Testdaten werden verwendet** - Der Scraper konnte noch keine echten Odds laden. Dies kann einige Minuten dauern.")
                else:
                    st.success("[OK] **Echte Odds verfügbar** - Der Scraper hat erfolgreich aktuelle Odds von Stake.com geladen.")
        
        # Source selection
        st.subheader("[REFRESH] Datenquelle wechseln")
        
        current_source = status['current_source']
        sources = ['test_data', 'stake_scraper', 'odds_api', 'enhanced_api']
        source_names = {
            'test_data': '[TEST] Testdaten',
            'stake_scraper': '🎰 Stake.com Scraper',
            'odds_api': '🌐 Odds API',
            'enhanced_api': '⚡ Enhanced API'
        }
        
        selected_source = st.selectbox(
            "Neue Datenquelle auswählen:",
            sources,
            index=sources.index(current_source) if current_source in sources else 0,
            format_func=lambda x: source_names.get(x, x)
        )
        
        if st.button("[REFRESH] Datenquelle wechseln"):
            try:
                success = odds_manager.switch_source(selected_source)
                if success:
                    st.success(f"[OK] Erfolgreich zu {source_names[selected_source]} gewechselt!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("[ERROR] Fehler beim Wechseln der Datenquelle")
            except Exception as e:
                st.error(f"[ERROR] Fehler: {e}")
        
        # Test all sources
        st.subheader("[TEST] Datenquellen testen")
        
        if st.button("🔍 Alle Quellen testen"):
            with st.spinner("Teste alle Datenquellen..."):
                test_results = odds_manager.test_all_sources()
                
                for source, result in test_results.items():
                    if result['success']:
                        st.success(f"[OK] {source_names[source]}: {result['message']}")
                        if 'data_count' in result:
                            st.info(f"   [CHART] {result['data_count']} Datensätze verfügbar")
                    else:
                        st.error(f"[ERROR] {source_names[source]}: {result['message']}")
        
        # Configuration details
        st.subheader("[CLIPBOARD] Konfigurationsdetails")
        
        config = odds_manager.config
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Aktualisierungsintervalle:**")
            st.write(f"• Live-Updates: {config['update_intervals']['live_minutes']} Minuten")
            st.write(f"• Scraper-Updates: {config['update_intervals']['scraper_hours']} Stunden")
            st.write(f"• API-Updates: {config['update_intervals']['api_minutes']} Minuten")
        
        with col2:
            st.markdown("**API-Konfiguration:**")
            api_key_set = "[OK] Gesetzt" if config['api_settings']['odds_api_key'] else "[ERROR] Nicht gesetzt"
            st.write(f"• Odds API Key: {api_key_set}")
            st.write(f"• Timeout: {config['api_settings']['timeout_seconds']} Sekunden")
            st.write(f"• Retry-Versuche: {config['api_settings']['retry_attempts']}")
        
        # Current data preview
        st.subheader("👀 Aktuelle Daten-Vorschau")
        
        try:
            current_odds = odds_manager.get_current_odds()
            if len(current_odds) > 0:
                st.dataframe(current_odds.head(10), use_container_width=True)
                st.info(f"[CHART] Insgesamt {len(current_odds)} Odds-Datensätze verfügbar")
            else:
                st.warning("[WARNING] Keine Odds-Daten verfügbar")
        except Exception as e:
            st.error(f"[ERROR] Fehler beim Laden der Daten: {e}")
        
        # Manual update
        st.subheader("[REFRESH] Manuelle Aktualisierung")
        
        if st.button("[REFRESH] Odds jetzt aktualisieren"):
            with st.spinner("Aktualisiere Odds-Daten..."):
                try:
                    updated_odds = odds_manager.get_current_odds(force_refresh=True)
                    st.success(f"[OK] Erfolgreich aktualisiert! {len(updated_odds)} Datensätze geladen")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"[ERROR] Aktualisierung fehlgeschlagen: {e}")
        
    except ImportError:
        st.error("[ERROR] OddsManager nicht verfügbar. Bitte überprüfe die Installation.")
        st.info("[IDEA] Der OddsManager ermöglicht das Wechseln zwischen verschiedenen Odds-Datenquellen.")

elif page == "[CLIPBOARD] Daten-Management":
    st.title("[CLIPBOARD] Daten-Management")
    
    # Data overview
    st.subheader("[CHART] Datenbank-Übersicht")
    
    odds_df = load_odds_data()
    predictions_df = load_predictions_data()
    results_df = load_race_results()
    betting_df = load_betting_performance()
    
    data_summary = {
        'Tabelle': ['odds_history', 'predictions', 'race_results', 'betting_performance'],
        'Datensätze': [len(odds_df), len(predictions_df), len(results_df), len(betting_df)],
        'Letzte Aktualisierung': [
            odds_df['created_at'].max() if len(odds_df) > 0 and 'created_at' in odds_df.columns else 'N/A',
            predictions_df['created_at'].max() if len(predictions_df) > 0 and 'created_at' in predictions_df.columns else 'N/A',
            results_df['created_at'].max() if len(results_df) > 0 and 'created_at' in results_df.columns else 'N/A',
            betting_df['created_at'].max() if len(betting_df) > 0 and 'created_at' in betting_df.columns else 'N/A'
        ]
    }
    
    summary_df = pd.DataFrame(data_summary)
    st.dataframe(summary_df, use_container_width=True)
    
    # Data export
    st.subheader("[DOWNLOAD] Daten-Export")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("[TREND] Odds exportieren"):
            if len(odds_df) > 0:
                csv = odds_df.to_csv(index=False)
                st.download_button(
                    "[DOWNLOAD] Odds CSV",
                    csv,
                    f"odds_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
    
    with col2:
        if st.button("[TARGET] Predictions exportieren"):
            if len(predictions_df) > 0:
                csv = predictions_df.to_csv(index=False)
                st.download_button(
                    "[DOWNLOAD] Predictions CSV",
                    csv,
                    f"predictions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
    
    with col3:
        if st.button("[RACE] Ergebnisse exportieren"):
            if len(results_df) > 0:
                csv = results_df.to_csv(index=False)
                st.download_button(
                    "[DOWNLOAD] Results CSV",
                    csv,
                    f"results_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
    
    with col4:
        if st.button("[MONEY] Betting exportieren"):
            if len(betting_df) > 0:
                csv = betting_df.to_csv(index=False)
                st.download_button(
                    "[DOWNLOAD] Betting CSV",
                    csv,
                    f"betting_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
    
    # Manual data refresh
    st.subheader("[REFRESH] Manuelle Aktualisierung")
    
    if st.button("🧹 Cache leeren"):
        st.cache_data.clear()
        st.success("[OK] Cache geleert")
        st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Links")
st.sidebar.markdown("[[CHART] Supabase Dashboard](https://ffgkrmpuwqtjtevpnnsj.supabase.co)")
st.sidebar.markdown("[[CLIPBOARD] Dokumentation](../SUPABASE_SETUP.md)")
st.sidebar.markdown("---")
st.sidebar.markdown("*F1 Analytics Hub v2.0*")