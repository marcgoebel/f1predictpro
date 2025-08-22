# 🚀 Nächste Schritte - F1 Analytics Hub Setup

## ⚠️ WICHTIG: Supabase-Tabellen erstellen

Die Supabase-Integration ist vorbereitet, aber die Datenbank-Tabellen müssen noch erstellt werden.

### 📋 Schritt-für-Schritt Anleitung:

#### 1. Supabase Dashboard öffnen
🔗 **Link**: https://ffgkrmpuwqtjtevpnnsj.supabase.co

#### 2. SQL Editor öffnen
- Klicke in der linken Seitenleiste auf **"SQL Editor"**
- Oder gehe direkt zu: https://ffgkrmpuwqtjtevpnnsj.supabase.co/project/ffgkrmpuwqtjtevpnnsj/sql

#### 3. SQL-Schema ausführen
**Option A**: Kopiere den Inhalt aus `database_schema.sql`
**Option B**: Führe aus: `python setup_supabase_tables.py` und kopiere die SQL-Befehle

#### 4. SQL ausführen
- Füge die SQL-Befehle in den SQL Editor ein
- Klicke auf **"Run"** (oder Strg+Enter)
- Warte bis alle Befehle erfolgreich ausgeführt wurden

#### 5. Verbindung testen
```bash
python setup_supabase_tables.py --check
```

---

## 🎯 Nach dem Setup verfügbare Features:

### 1. Enhanced Odds Fetcher testen
```bash
python ml/enhanced_odds_fetcher.py
```
**Features:**
- ✅ Automatische Speicherung in Supabase + CSV
- ✅ Historische Odds-Analyse
- ✅ Value-Bet-Erkennung
- ✅ Best-Odds-Vergleich

### 2. Bestehende Daten migrieren
```bash
python migrate_data_to_supabase.py
```
**Migriert:**
- 📊 Alle CSV-Dateien aus `data/`
- 🔮 Vorhersagen und Ergebnisse
- 💰 Wett-Performance-Daten

### 3. Integration in bestehende Scripts
Deine bestehenden Scripts funktionieren weiterhin, aber mit zusätzlichen Supabase-Features:

```python
# Beispiel: Enhanced Odds in auto_race_monitor.py
from ml.enhanced_odds_fetcher import fetch_odds_for_next_f1_race

# Speichert automatisch in Supabase + CSV
odds_df = fetch_odds_for_next_f1_race()
```

---

## 🗄️ Datenbank-Schema Übersicht

| Tabelle | Zweck | Hauptfelder |
|---------|-------|-------------|
| `odds_history` | Historische Wettquoten | race_name, driver, bookmaker, odds |
| `predictions` | Modell-Vorhersagen | race_name, driver, win_probability |
| `race_results` | Rennergebnisse | race_name, driver, final_position |
| `betting_performance` | Wett-Tracking | stake, odds, profit_loss |
| `session_data` | Training/Qualifying | lap_times, sector_times |
| `weather_data` | Wetterdaten | temperature, humidity, wind |

---

## 🔧 Troubleshooting

### Problem: "relation does not exist"
**Lösung**: SQL-Schema in Supabase ausführen (siehe Schritte oben)

### Problem: Verbindungsfehler
**Prüfen**:
- ✅ Supabase URL korrekt in `.env`
- ✅ Service Role Key korrekt in `.env`
- ✅ Internet-Verbindung

### Problem: Permission denied
**Lösung**: Service Role Key verwenden (nicht anon key)

---

## 📞 Support

**Verbindung testen**: `python setup_supabase_tables.py --check`
**Logs prüfen**: Detaillierte Fehlermeldungen in der Konsole
**Dokumentation**: `SUPABASE_SETUP.md`

---

## ✅ Checkliste

- [ ] Supabase Dashboard geöffnet
- [ ] SQL Editor gefunden
- [ ] SQL-Schema aus `database_schema.sql` kopiert
- [ ] SQL-Befehle erfolgreich ausgeführt
- [ ] Verbindungstest bestanden: `python setup_supabase_tables.py --check`
- [ ] Enhanced Odds Fetcher getestet: `python ml/enhanced_odds_fetcher.py`
- [ ] Daten migriert: `python migrate_data_to_supabase.py`

**Status**: 🟡 Warten auf Supabase-Schema-Setup
**Nächster Schritt**: SQL-Befehle in Supabase ausführen