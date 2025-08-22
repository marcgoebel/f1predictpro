# F1 Analytics Hub - Supabase Integration Setup

## 🚀 Quick Start

### 1. Database Schema Setup

**IMPORTANT**: You need to manually execute the SQL schema in your Supabase dashboard before using the system.

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `database_schema.sql`
4. Execute the SQL commands

Alternatively, you can copy the SQL from the setup script output:
```bash
python ml/database/setup_schema.py
```

### 2. Environment Variables

Your `.env` file should contain:
```env
# Supabase Configuration
SUPABASE_URL=https://ffgkrmpuwqtjtevpnnsj.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Existing API Keys
ODDS_API_KEY=your_odds_api_key

# Optional: Weather API (for future features)
OPENWEATHER_API_KEY=your_weather_api_key

# Development Settings
DEBUG=True
LOG_LEVEL=INFO
```

### 3. Test Connection

```bash
python ml/database/supabase_client.py
```

Expected output:
```
✅ Connected to Supabase: https://ffgkrmpuwqtjtevpnnsj.supabase.co
✅ Supabase connection successful!
```

### 4. Migrate Existing Data (Optional)

```bash
python migrate_data_to_supabase.py
```

### 5. Test Enhanced Odds Fetcher

```bash
python ml/enhanced_odds_fetcher.py
```

## 📊 Database Schema

### Tables Created

1. **odds_history** - Historical betting odds
   - `race_name`, `driver`, `bookmaker`, `odds`, `market_type`
   - Indexes on race_name, driver, created_at

2. **predictions** - Model predictions
   - `race_name`, `driver`, `predicted_position`, `win_probability`, `podium_probability`
   - Supports multiple model versions

3. **race_results** - Actual race results
   - `race_name`, `driver`, `final_position`, `points`, `dnf`, `fastest_lap`
   - Grid position tracking

4. **betting_performance** - Betting tracking
   - `race_name`, `driver`, `bet_type`, `stake`, `odds`, `result`, `profit_loss`
   - ROI calculation support

5. **session_data** - Practice/Qualifying data
   - Lap times, sector times, tire compounds
   - Weather and telemetry data (JSONB)

6. **weather_data** - Weather forecasts
   - Temperature, humidity, wind, precipitation
   - Track-specific conditions

## 🔧 Key Features

### Enhanced Odds Fetcher
- **Dual Storage**: Saves to both Supabase and CSV (backward compatibility)
- **Historical Analysis**: Track odds movements over time
- **Value Bet Detection**: Identify betting opportunities
- **Best Odds Finder**: Compare across bookmakers

### Database Client
- **Automatic Connection Management**: Global client instance
- **Error Handling**: Comprehensive logging and error recovery
- **Data Validation**: Ensures data integrity
- **Performance Tracking**: ROI and accuracy calculations

## 📈 Usage Examples

### Fetch and Store Odds
```python
from ml.enhanced_odds_fetcher import EnhancedOddsFetcher

fetcher = EnhancedOddsFetcher()
odds_df = fetcher.fetch_f1_odds("2025 Bahrain Grand Prix")
```

### Get Best Odds
```python
best_odds = fetcher.get_best_odds("2025 Bahrain Grand Prix")
print(best_odds)
```

### Analyze Odds Movement
```python
movement = fetcher.analyze_odds_movement("Max Verstappen", "2025 Bahrain Grand Prix")
print(movement)
```

### Store Predictions
```python
from ml.database.supabase_client import get_db_client

db_client = get_db_client()
db_client.store_predictions(predictions_df, "2025 Bahrain Grand Prix")
```

### Get Prediction Accuracy
```python
accuracy = db_client.get_prediction_accuracy("2025 Bahrain Grand Prix")
print(f"Model accuracy: {accuracy['overall_accuracy']:.2%}")
```

## 🔄 Integration with Existing System

### Auto Race Monitor Integration
The enhanced odds fetcher is designed to work with your existing `auto_race_monitor.py`:

```python
# Replace existing odds fetcher
from ml.enhanced_odds_fetcher import fetch_odds_for_next_f1_race

# This function now stores in both Supabase and CSV
odds_df = fetch_odds_for_next_f1_race()
```

### Dashboard Integration
Your Streamlit dashboard can now access historical data:

```python
from ml.database.supabase_client import get_db_client

db_client = get_db_client()

# Get latest odds for dashboard
latest_odds = db_client.get_latest_odds(hours_back=6)

# Get historical performance
performance = db_client.get_overall_roi()
```

## 🛠️ Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check your Supabase URL and Service Role Key
   - Ensure your Supabase project is active
   - Verify network connectivity

2. **Table Does Not Exist**
   - Run the SQL schema in your Supabase dashboard
   - Check that all tables were created successfully

3. **Permission Denied**
   - Ensure you're using the Service Role Key (not anon key)
   - Check Row Level Security policies

4. **Data Migration Issues**
   - Check CSV file formats and column names
   - Review migration logs for specific errors
   - Ensure data types match schema requirements

### Debug Mode
Enable debug logging in your `.env`:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

## 📋 Next Steps

1. **Weather Integration**: Add OpenWeather API for race conditions
2. **Advanced Analytics**: Implement machine learning models
3. **Real-time Updates**: Set up webhooks for live data
4. **Dashboard Enhancement**: Create comprehensive analytics views
5. **API Development**: Build REST API for external access

## 🔐 Security Notes

- Never commit your `.env` file to version control
- Use Service Role Key only for server-side operations
- Enable Row Level Security in production
- Regularly rotate API keys
- Monitor database usage and costs

## 📞 Support

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify your Supabase project settings
3. Test individual components separately
4. Review the database schema in Supabase dashboard

---

**Status**: ✅ Supabase integration ready for use!
**Last Updated**: January 2025