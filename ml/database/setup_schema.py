from supabase_client import get_db_client
import logging

def create_database_schema():
    """Create all necessary tables in Supabase"""
    client = get_db_client()
    
    # SQL commands to create tables
    tables = {
        'odds_history': '''
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
        ''',
        
        'predictions': '''
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
        ''',
        
        'race_results': '''
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
        ''',
        
        'betting_performance': '''
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
        ''',
        
        'session_data': '''
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
        ''',
        
        'weather_data': '''
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
        '''
    }
    
    print("🗄️ Creating database schema...")
    print("\n⚠️  IMPORTANT: Run these SQL commands in your Supabase SQL Editor:")
    print("=" * 80)
    
    for table_name, sql in tables.items():
        print(f"\n-- {table_name.upper()} TABLE")
        print("-" * 50)
        print(sql)
        print()
    
    print("=" * 80)
    print("\n📋 After running the SQL commands above, you can test the connection with:")
    print("python ml/database/supabase_client.py")
    
    # Also create a SQL file for easy execution
    sql_content = "-- F1 Analytics Hub Database Schema\n\n"
    for table_name, sql in tables.items():
        sql_content += f"-- {table_name.upper()} TABLE\n"
        sql_content += sql + "\n\n"
    
    with open("database_schema.sql", "w") as f:
        f.write(sql_content)
    
    print(f"\n💾 SQL schema also saved to: database_schema.sql")

def create_sample_data():
    """Create some sample data for testing"""
    try:
        client = get_db_client()
        
        # Sample odds data
        sample_odds = [
            {
                'race_name': '2025 Test Grand Prix',
                'driver': 'Max Verstappen',
                'bookmaker': 'Bet365',
                'odds': 1.85,
                'market_type': 'winner'
            },
            {
                'race_name': '2025 Test Grand Prix',
                'driver': 'Lando Norris',
                'bookmaker': 'Bet365',
                'odds': 3.20,
                'market_type': 'winner'
            }
        ]
        
        # Sample predictions
        sample_predictions = [
            {
                'race_name': '2025 Test Grand Prix',
                'driver': 'Max Verstappen',
                'predicted_position': 1,
                'win_probability': 0.65,
                'podium_probability': 0.85,
                'points_probability': 0.95
            },
            {
                'race_name': '2025 Test Grand Prix',
                'driver': 'Lando Norris',
                'predicted_position': 2,
                'win_probability': 0.25,
                'podium_probability': 0.70,
                'points_probability': 0.90
            }
        ]
        
        print("🧪 Creating sample data...")
        
        # Store sample data
        client.store_odds_data(pd.DataFrame(sample_odds), '2025 Test Grand Prix')
        client.store_predictions(pd.DataFrame(sample_predictions), '2025 Test Grand Prix')
        
        print("✅ Sample data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

if __name__ == "__main__":
    import sys
    import pandas as pd
    
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        create_sample_data()
    else:
        create_database_schema()