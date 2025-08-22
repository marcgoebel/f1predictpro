#!/usr/bin/env python3
"""
Data Migration Script for F1 Analytics Hub
Migrates existing CSV data to Supabase database
"""

import os
import pandas as pd
from datetime import datetime
import glob
from ml.database.supabase_client import get_db_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_odds_data():
    """Migrate existing odds CSV files to Supabase"""
    try:
        db_client = get_db_client()
        
        # Find all odds CSV files
        odds_files = glob.glob('data/**/*odds*.csv', recursive=True)
        odds_files.extend(glob.glob('data/**/*value_bets*.csv', recursive=True))
        
        logger.info(f"Found {len(odds_files)} odds files to migrate")
        
        for file_path in odds_files:
            try:
                logger.info(f"Processing: {file_path}")
                
                # Read CSV file
                df = pd.read_csv(file_path)
                
                if df.empty:
                    logger.warning(f"Empty file: {file_path}")
                    continue
                
                # Extract race name from file path or use filename
                race_name = extract_race_name_from_path(file_path)
                
                # Standardize column names
                df = standardize_odds_columns(df)
                
                if 'driver' in df.columns and 'odds' in df.columns:
                    # Store in Supabase
                    result = db_client.store_odds_data(df, race_name)
                    if result:
                        logger.info(f"✅ Migrated {len(df)} records from {file_path}")
                    else:
                        logger.error(f"❌ Failed to migrate {file_path}")
                else:
                    logger.warning(f"⚠️ Skipping {file_path} - missing required columns")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {file_path}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Error in odds migration: {e}")

def migrate_predictions_data():
    """Migrate existing predictions CSV files to Supabase"""
    try:
        db_client = get_db_client()
        
        # Find all prediction CSV files
        prediction_files = glob.glob('data/**/*prediction*.csv', recursive=True)
        prediction_files.extend(glob.glob('data/**/*forecast*.csv', recursive=True))
        
        logger.info(f"Found {len(prediction_files)} prediction files to migrate")
        
        for file_path in prediction_files:
            try:
                logger.info(f"Processing: {file_path}")
                
                # Read CSV file
                df = pd.read_csv(file_path)
                
                if df.empty:
                    logger.warning(f"Empty file: {file_path}")
                    continue
                
                # Extract race name from file path
                race_name = extract_race_name_from_path(file_path)
                
                # Standardize column names
                df = standardize_predictions_columns(df)
                
                if 'driver' in df.columns:
                    # Store in Supabase
                    result = db_client.store_predictions(df, race_name)
                    if result:
                        logger.info(f"✅ Migrated {len(df)} prediction records from {file_path}")
                    else:
                        logger.error(f"❌ Failed to migrate {file_path}")
                else:
                    logger.warning(f"⚠️ Skipping {file_path} - missing required columns")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {file_path}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Error in predictions migration: {e}")

def migrate_results_data():
    """Migrate existing race results CSV files to Supabase"""
    try:
        db_client = get_db_client()
        
        # Find all results CSV files
        results_files = glob.glob('data/**/*result*.csv', recursive=True)
        results_files.extend(glob.glob('data/**/*race_data*.csv', recursive=True))
        
        logger.info(f"Found {len(results_files)} results files to migrate")
        
        for file_path in results_files:
            try:
                logger.info(f"Processing: {file_path}")
                
                # Read CSV file
                df = pd.read_csv(file_path)
                
                if df.empty:
                    logger.warning(f"Empty file: {file_path}")
                    continue
                
                # Extract race name from file path
                race_name = extract_race_name_from_path(file_path)
                
                # Standardize column names
                df = standardize_results_columns(df)
                
                if 'driver' in df.columns and 'final_position' in df.columns:
                    # Store in Supabase
                    result = db_client.store_race_results(df, race_name)
                    if result:
                        logger.info(f"✅ Migrated {len(df)} results records from {file_path}")
                    else:
                        logger.error(f"❌ Failed to migrate {file_path}")
                else:
                    logger.warning(f"⚠️ Skipping {file_path} - missing required columns")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {file_path}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Error in results migration: {e}")

def extract_race_name_from_path(file_path):
    """Extract race name from file path"""
    # Try to extract race name from path
    path_parts = file_path.replace('\\', '/').split('/')
    filename = os.path.splitext(path_parts[-1])[0]
    
    # Look for race-related keywords
    race_keywords = ['gp', 'grand_prix', 'race', '2024', '2025']
    
    for part in path_parts:
        for keyword in race_keywords:
            if keyword.lower() in part.lower():
                return part.replace('_', ' ').title()
    
    # Fallback to filename
    return filename.replace('_', ' ').title()

def standardize_odds_columns(df):
    """Standardize odds DataFrame columns"""
    # Common column name mappings
    column_mappings = {
        'Driver': 'driver',
        'DRIVER': 'driver',
        'driver_name': 'driver',
        'Odds': 'odds',
        'ODDS': 'odds',
        'price': 'odds',
        'Bookmaker': 'bookmaker',
        'BOOKMAKER': 'bookmaker',
        'bookie': 'bookmaker',
        'source': 'bookmaker',
        'Market': 'market_type',
        'market': 'market_type',
        'type': 'market_type'
    }
    
    # Rename columns
    df = df.rename(columns=column_mappings)
    
    # Ensure required columns exist
    if 'market_type' not in df.columns:
        df['market_type'] = 'winner'
    
    if 'bookmaker' not in df.columns:
        df['bookmaker'] = 'Unknown'
    
    if 'fetch_timestamp' not in df.columns:
        df['fetch_timestamp'] = datetime.now()
    
    return df

def standardize_predictions_columns(df):
    """Standardize predictions DataFrame columns"""
    column_mappings = {
        'Driver': 'driver',
        'DRIVER': 'driver',
        'driver_name': 'driver',
        'Position': 'predicted_position',
        'position': 'predicted_position',
        'predicted_pos': 'predicted_position',
        'Win_Prob': 'win_probability',
        'win_prob': 'win_probability',
        'win_probability_pct': 'win_probability',
        'Podium_Prob': 'podium_probability',
        'podium_prob': 'podium_probability',
        'Points_Prob': 'points_probability',
        'points_prob': 'points_probability'
    }
    
    df = df.rename(columns=column_mappings)
    
    # Convert percentage values to decimals if needed
    for col in ['win_probability', 'podium_probability', 'points_probability']:
        if col in df.columns:
            # If values are > 1, assume they're percentages
            if df[col].max() > 1:
                df[col] = df[col] / 100
    
    return df

def standardize_results_columns(df):
    """Standardize results DataFrame columns"""
    column_mappings = {
        'Driver': 'driver',
        'DRIVER': 'driver',
        'driver_name': 'driver',
        'Position': 'final_position',
        'position': 'final_position',
        'finish_position': 'final_position',
        'Points': 'points',
        'POINTS': 'points',
        'championship_points': 'points',
        'Grid': 'grid_position',
        'grid': 'grid_position',
        'starting_position': 'grid_position',
        'DNF': 'dnf',
        'did_not_finish': 'dnf',
        'FastestLap': 'fastest_lap',
        'fastest_lap_flag': 'fastest_lap'
    }
    
    df = df.rename(columns=column_mappings)
    
    # Ensure boolean columns are properly formatted
    for col in ['dnf', 'fastest_lap']:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    
    # Set default values
    if 'points' not in df.columns:
        df['points'] = 0
    
    if 'dnf' not in df.columns:
        df['dnf'] = False
    
    if 'fastest_lap' not in df.columns:
        df['fastest_lap'] = False
    
    return df

def create_backup():
    """Create backup of existing data before migration"""
    try:
        import shutil
        from datetime import datetime
        
        backup_dir = f"data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if os.path.exists('data'):
            shutil.copytree('data', backup_dir)
            logger.info(f"✅ Created backup: {backup_dir}")
            return backup_dir
        else:
            logger.warning("⚠️ No data directory found to backup")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error creating backup: {e}")
        return None

def main():
    """Main migration function"""
    print("🚀 Starting F1 Analytics Hub Data Migration")
    print("=" * 50)
    
    # Test database connection first
    try:
        db_client = get_db_client()
        if not db_client.test_connection():
            print("❌ Database connection failed. Please check your Supabase setup.")
            return
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return
    
    # Create backup
    print("\n📦 Creating backup...")
    backup_dir = create_backup()
    
    # Migrate data
    print("\n📊 Migrating odds data...")
    migrate_odds_data()
    
    print("\n🔮 Migrating predictions data...")
    migrate_predictions_data()
    
    print("\n🏁 Migrating results data...")
    migrate_results_data()
    
    print("\n✅ Migration completed!")
    print("\n📋 Next steps:")
    print("1. Verify data in your Supabase dashboard")
    print("2. Test the enhanced odds fetcher: python ml/enhanced_odds_fetcher.py")
    print("3. Update your existing scripts to use the new Supabase integration")
    
    if backup_dir:
        print(f"\n💾 Backup created: {backup_dir}")

if __name__ == "__main__":
    main()