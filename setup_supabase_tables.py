#!/usr/bin/env python3
"""
Supabase Tables Setup Guide
Zeigt die SQL-Befehle an, die in der Supabase-Konsole ausgeführt werden müssen
"""

def show_setup_instructions():
    print("🗄️ F1 Analytics Hub - Supabase Setup")
    print("=" * 60)
    print()
    print("⚠️  WICHTIG: Diese SQL-Befehle müssen in der Supabase-Konsole ausgeführt werden!")
    print()
    print("📋 Schritte:")
    print("1. Gehe zu: https://ffgkrmpuwqtjtevpnnsj.supabase.co")
    print("2. Klicke auf 'SQL Editor' in der linken Seitenleiste")
    print("3. Kopiere und füge die folgenden SQL-Befehle ein")
    print("4. Klicke auf 'Run' um die Befehle auszuführen")
    print()
    print("=" * 60)
    print("📝 SQL-BEFEHLE ZUM KOPIEREN:")
    print("=" * 60)
    
    sql_commands = """
-- F1 Analytics Hub Database Schema

-- 1. ODDS_HISTORY TABLE
CREATE TABLE IF NOT EXISTS odds_history (
    id SERIAL PRIMARY KEY,
    race_name TEXT NOT NULL,
    driver TEXT NOT NULL,
    bookmaker TEXT NOT NULL,
    odds DECIMAL NOT NULL,
    market_type TEXT DEFAULT 'winner',
    fetch_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(race_name, driver, bookmaker, market_type, fetch_timestamp)
);

CREATE INDEX IF NOT EXISTS idx_odds_race_name ON odds_history(race_name);
CREATE INDEX IF NOT EXISTS idx_odds_driver ON odds_history(driver);
CREATE INDEX IF NOT EXISTS idx_odds_created_at ON odds_history(created_at);

-- 2. PREDICTIONS TABLE
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    race_name TEXT NOT NULL,
    driver TEXT NOT NULL,
    predicted_position INTEGER,
    win_probability DECIMAL,
    podium_probability DECIMAL,
    points_probability DECIMAL,
    model_version TEXT DEFAULT 'v1',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(race_name, driver, model_version)
);

CREATE INDEX IF NOT EXISTS idx_predictions_race_name ON predictions(race_name);
CREATE INDEX IF NOT EXISTS idx_predictions_driver ON predictions(driver);
CREATE INDEX IF NOT EXISTS idx_predictions_model_version ON predictions(model_version);

-- 3. RACE_RESULTS TABLE
CREATE TABLE IF NOT EXISTS race_results (
    id SERIAL PRIMARY KEY,
    race_name TEXT NOT NULL,
    driver TEXT NOT NULL,
    final_position INTEGER,
    points INTEGER DEFAULT 0,
    dnf BOOLEAN DEFAULT FALSE,
    fastest_lap BOOLEAN DEFAULT FALSE,
    grid_position INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(race_name, driver)
);

CREATE INDEX IF NOT EXISTS idx_results_race_name ON race_results(race_name);
CREATE INDEX IF NOT EXISTS idx_results_driver ON race_results(driver);
CREATE INDEX IF NOT EXISTS idx_results_position ON race_results(final_position);

-- 4. BETTING_PERFORMANCE TABLE
CREATE TABLE IF NOT EXISTS betting_performance (
    id SERIAL PRIMARY KEY,
    race_name TEXT NOT NULL,
    driver TEXT NOT NULL,
    bet_type TEXT NOT NULL,
    stake DECIMAL NOT NULL,
    odds DECIMAL NOT NULL,
    result TEXT, -- 'win', 'loss', 'pending'
    profit_loss DECIMAL DEFAULT 0,
    bookmaker TEXT,
    bet_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_betting_race_name ON betting_performance(race_name);
CREATE INDEX IF NOT EXISTS idx_betting_result ON betting_performance(result);
CREATE INDEX IF NOT EXISTS idx_betting_date ON betting_performance(bet_date);

-- 5. SESSION_DATA TABLE
CREATE TABLE IF NOT EXISTS session_data (
    id SERIAL PRIMARY KEY,
    race_name TEXT NOT NULL,
    session_type TEXT NOT NULL, -- 'practice1', 'practice2', 'practice3', 'qualifying', 'race'
    driver TEXT NOT NULL,
    lap_number INTEGER,
    lap_time DECIMAL,
    sector_1_time DECIMAL,
    sector_2_time DECIMAL,
    sector_3_time DECIMAL,
    compound TEXT, -- tire compound
    stint_number INTEGER,
    track_status TEXT,
    weather_data JSONB,
    telemetry_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_race_name ON session_data(race_name);
CREATE INDEX IF NOT EXISTS idx_session_driver ON session_data(driver);
CREATE INDEX IF NOT EXISTS idx_session_type ON session_data(session_type);

-- 6. WEATHER_DATA TABLE
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    race_name TEXT NOT NULL,
    forecast_date TIMESTAMP NOT NULL,
    temperature DECIMAL,
    humidity DECIMAL,
    wind_speed DECIMAL,
    wind_direction DECIMAL,
    precipitation_probability DECIMAL,
    precipitation_amount DECIMAL,
    track_temperature DECIMAL,
    weather_condition TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weather_race_name ON weather_data(race_name);
CREATE INDEX IF NOT EXISTS idx_weather_forecast_date ON weather_data(forecast_date);

-- Enable Row Level Security (RLS) for all tables
ALTER TABLE odds_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE race_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE betting_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE weather_data ENABLE ROW LEVEL SECURITY;

-- Create policies for service role access
CREATE POLICY "Enable all operations for service role" ON odds_history
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON predictions
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON race_results
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON betting_performance
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON session_data
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON weather_data
    FOR ALL USING (true);
"""
    
    print(sql_commands)
    print("=" * 60)
    print()
    print("✅ Nach der Ausführung der SQL-Befehle:")
    print("   python ml/enhanced_odds_fetcher.py")
    print()
    print("📁 Die SQL-Befehle sind auch gespeichert in: database_schema.sql")
    print()
    print("🔗 Supabase Dashboard: https://ffgkrmpuwqtjtevpnnsj.supabase.co")

def check_tables_exist():
    """Prüfe ob die Tabellen bereits existieren"""
    try:
        from ml.database.supabase_client import get_db_client
        
        print("🔍 Prüfe Supabase-Verbindung...")
        db_client = get_db_client()
        
        if db_client.test_connection():
            print("✅ Alle Tabellen sind korrekt eingerichtet!")
            print("\n🚀 Du kannst jetzt fortfahren mit:")
            print("   python ml/enhanced_odds_fetcher.py")
            print("   python migrate_data_to_supabase.py")
            return True
        else:
            print("❌ Tabellen existieren noch nicht.")
            print("\n📋 Bitte führe die SQL-Befehle oben in Supabase aus.")
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei der Verbindung: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_tables_exist()
    else:
        show_setup_instructions()
        print("\n" + "="*60)
        print("🔍 VERBINDUNGSTEST:")
        print("="*60)
        check_tables_exist()