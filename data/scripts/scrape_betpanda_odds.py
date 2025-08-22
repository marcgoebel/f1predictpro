from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import os
import random

def scrape_betpanda_f1_odds(url, output_file="data/live/betpanda_odds.csv", max_retries=3):
    """
    Robuster Selenium-Scraper für Betpanda F1-Quoten.
    
    Args:
        url: Betpanda URL für F1 Outright-Quoten
        output_file: Pfad für die Ausgabe-CSV
        max_retries: Maximale Anzahl von Wiederholungsversuchen
    
    Returns:
        List of dictionaries mit Fahrer und Quoten
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    import random
    
    # CSS-Selektoren für Betpanda (müssen angepasst werden)
    SELECTORS = {
        'market_rows': [
            ".bet-row",
            ".outcome-row",
            "[data-testid='outcome']",
            ".market-outcome",
            "[class*='outcome']",
            ".selection",
            ".bet-selection"
        ],
        'driver_names': [
            ".outcome-name",
            ".selection-name",
            "[data-testid='outcome-name']",
            ".bet-name",
            "[class*='name']",
            ".participant-name"
        ],
        'odds_prices': [
            ".odds",
            ".price",
            "[data-testid='odds']",
            ".outcome-odds",
            "[class*='odds']",
            "[class*='price']",
            ".coefficient"
        ]
    }
    
    for attempt in range(max_retries):
        driver = None
        try:
            print(f"🔄 Versuch {attempt + 1}/{max_retries} - Scraping Betpanda...")
            
            # Chrome-Optionen für Robustheit
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            driver = webdriver.Chrome(options=options)
            driver.implicitly_wait(10)
            
            print(f"📡 Lade URL: {url}")
            driver.get(url)
            
            # Warte auf Seitenladung mit zufälliger Verzögerung
            wait_time = random.uniform(3, 7)
            print(f"⏳ Warte {wait_time:.1f} Sekunden auf Seitenladung...")
            time.sleep(wait_time)
            
            # Versuche verschiedene Selektoren
            records = []
            wait = WebDriverWait(driver, 15)
            
            # Scroll nach unten für dynamisches Laden
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Versuche verschiedene Selector-Kombinationen
            for market_selector in SELECTORS['market_rows']:
                try:
                    print(f"🔍 Versuche Selector: {market_selector}")
                    
                    # Warte auf Elemente
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, market_selector)))
                    
                    items = driver.find_elements(By.CSS_SELECTOR, market_selector)
                    print(f"📊 {len(items)} Markt-Zeilen gefunden")
                    
                    if len(items) == 0:
                        continue
                    
                    # Extrahiere Daten aus gefundenen Elementen
                    for item in items:
                        driver_name = None
                        odds_value = None
                        
                        # Versuche Fahrername zu finden
                        for name_selector in SELECTORS['driver_names']:
                            try:
                                name_element = item.find_element(By.CSS_SELECTOR, name_selector)
                                driver_name = name_element.text.strip()
                                if driver_name:
                                    break
                            except NoSuchElementException:
                                continue
                        
                        # Versuche Odds zu finden
                        for price_selector in SELECTORS['odds_prices']:
                            try:
                                price_element = item.find_element(By.CSS_SELECTOR, price_selector)
                                odds_text = price_element.text.strip()
                                # Bereinige Odds-Text (entferne Währungssymbole, etc.)
                                odds_clean = ''.join(c for c in odds_text if c.isdigit() or c == '.')
                                if odds_clean:
                                    odds_value = float(odds_clean)
                                    break
                            except (NoSuchElementException, ValueError):
                                continue
                        
                        # Füge Datensatz hinzu wenn beide Werte gefunden
                        if driver_name and odds_value:
                            clean_name = clean_driver_name(driver_name)
                            if clean_name:
                                records.append({
                                    'driver': clean_name,
                                    'odds': odds_value,
                                    'bookmaker': 'Betpanda',
                                    'market_type': 'winner',
                                    'race_name': 'Next F1 Race',
                                    'fetch_timestamp': pd.Timestamp.now()
                                })
                                print(f"✅ Gefunden: {clean_name} - {odds_value}")
                    
                    # Wenn Daten gefunden wurden, beende die Schleife
                    if records:
                        print(f"🎯 {len(records)} Odds erfolgreich extrahiert")
                        break
                        
                except TimeoutException:
                    print(f"⏰ Timeout für Selector: {market_selector}")
                    continue
                except Exception as e:
                    print(f"❌ Fehler mit Selector {market_selector}: {e}")
                    continue
            
            if records:
                # Erstelle DataFrame und speichere
                df = pd.DataFrame(records)
                
                # Erstelle Ausgabeverzeichnis falls nicht vorhanden
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                
                # Speichere CSV
                df.to_csv(output_file, index=False)
                print(f"💾 Daten gespeichert in: {output_file}")
                
                return df
            else:
                print(f"❌ Keine Daten gefunden in Versuch {attempt + 1}")
                
        except Exception as e:
            print(f"❌ Fehler in Versuch {attempt + 1}: {e}")
            
        finally:
            if driver:
                driver.quit()
        
        # Warte vor nächstem Versuch
        if attempt < max_retries - 1:
            wait_time = random.uniform(5, 10)
            print(f"⏳ Warte {wait_time:.1f} Sekunden vor nächstem Versuch...")
            time.sleep(wait_time)
    
    print(f"❌ Alle {max_retries} Versuche fehlgeschlagen")
    return pd.DataFrame()

def clean_driver_name(raw_name):
    """
    Bereinige und normalisiere Fahrernamen
    """
    if not raw_name:
        return None
    
    # Entferne häufige Präfixe/Suffixe
    name = raw_name.strip()
    
    # Entferne Nummern am Anfang (z.B. "1. Max Verstappen")
    import re
    name = re.sub(r'^\d+\.\s*', '', name)
    
    # Mapping für bekannte Fahrer (2025 Saison)
    driver_mapping = {
        'verstappen': 'Max Verstappen',
        'hamilton': 'Lewis Hamilton',
        'russell': 'George Russell',
        'leclerc': 'Charles Leclerc',
        'sainz': 'Carlos Sainz',
        'norris': 'Lando Norris',
        'piastri': 'Oscar Piastri',
        'alonso': 'Fernando Alonso',
        'stroll': 'Lance Stroll',
        'ocon': 'Esteban Ocon',
        'gasly': 'Pierre Gasly',
        'tsunoda': 'Yuki Tsunoda',
        'albon': 'Alexander Albon',
        'sargeant': 'Logan Sargeant',
        'hulkenberg': 'Nico Hulkenberg',
        'magnussen': 'Kevin Magnussen',
        'bottas': 'Valtteri Bottas',
        'zhou': 'Zhou Guanyu',
        'ricciardo': 'Daniel Ricciardo',
        'perez': 'Sergio Perez'
    }
    
    # Suche nach bekannten Fahrern
    name_lower = name.lower()
    for key, full_name in driver_mapping.items():
        if key in name_lower:
            return full_name
    
    # Falls kein Mapping gefunden, gib bereinigten Namen zurück
    return name

def scrape_and_save_betpanda_odds(betpanda_url=None, output_file="data/live/betpanda_odds.csv"):
    """
    Hauptfunktion zum Scrapen und Speichern von Betpanda Odds
    """
    if not betpanda_url:
        # Standard Betpanda F1 URL (muss angepasst werden)
        betpanda_url = "https://www.betpanda.com/de/sport/motorsport/formel-1"
    
    print(f"🎯 Starte Betpanda Odds Scraping...")
    print(f"📡 URL: {betpanda_url}")
    
    try:
        df = scrape_betpanda_f1_odds(betpanda_url, output_file)
        
        if not df.empty:
            print(f"\n✅ Scraping erfolgreich!")
            print(f"📊 {len(df)} Odds gefunden")
            print(f"📁 Gespeichert in: {output_file}")
            print("\n📋 Vorschau:")
            print(df.head())
            return df
        else:
            print(f"\n❌ Keine Odds gefunden")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Fehler beim Scraping: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

if __name__ == "__main__":
    # Kommandozeilen-Interface
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape F1 odds from Betpanda")
    parser.add_argument("--url", type=str, help="Betpanda F1 URL")
    parser.add_argument("--output", type=str, default="data/live/betpanda_odds.csv", help="Output CSV file")
    
    args = parser.parse_args()
    
    try:
        df = scrape_and_save_betpanda_odds(args.url, args.output)
        if not df.empty:
            print(f"\n✅ Scraping erfolgreich abgeschlossen!")
            print(f"📁 Datei gespeichert: {args.output}")
        else:
            print(f"\n❌ Scraping fehlgeschlagen")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()