import requests
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

api_key = os.getenv('ODDS_API_KEY')
print(f"API Key: {api_key[:10]}...")

# Get available sports
response = requests.get('https://api.the-odds-api.com/v4/sports/', params={'apiKey': api_key})
print(f'Status: {response.status_code}')

if response.status_code == 200:
    data = response.json()
    print(f'Total sports available: {len(data)}')
    
    # Look for Formula 1 or motorsport related sports
    motorsports = []
    for sport in data:
        title_lower = sport['title'].lower()
        key_lower = sport['key'].lower()
        if any(keyword in title_lower or keyword in key_lower for keyword in ['formula', 'f1', 'motor', 'racing', 'grand prix']):
            motorsports.append(sport)
    
    if motorsports:
        print('\nMotorsport related sports found:')
        for sport in motorsports:
            print(f'- {sport["key"]}: {sport["title"]}')
    else:
        print('\nNo motorsport related sports found.')
        print('\nAll available sports:')
        for sport in data[:10]:  # Show first 10
            print(f'- {sport["key"]}: {sport["title"]}')
        if len(data) > 10:
            print(f'... and {len(data) - 10} more')
else:
    print(f'Error: {response.text}')