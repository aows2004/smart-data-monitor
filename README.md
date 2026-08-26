# 📊 SmartData Monitor

[![Live Demo](https://img.shields.io/badge/Live_Demo-Open_App-success)](https://smart-data-monitor.onrender.com/)

SmartData Monitor is a configurable Python web-monitoring application for tracking product listings across websites and detecting changes over time.

It supports both traditional server-rendered websites and JavaScript-rendered pages, custom CSS selector configurations, multi-page crawling, persistent monitor profiles, historical snapshots, automatic change detection, and CSV/Excel exports.

## Live Demo

Try SmartData Monitor online:

**https://smart-data-monitor.onrender.com/**

> The public demo runs on a free cloud instance, so the first load after a period of inactivity may take a short time. Demo data and saved monitor history may also reset between deployments or service restarts.

---

## Features

- Static website scraping with Requests
- JavaScript-rendered website scraping with Playwright
- Reusable custom CSS selector configurations
- Multi-page pagination crawling
- Saved monitor profiles
- Independent history for different monitor configurations
- Price normalization across multiple currency formats
- Availability normalization
- New product detection
- Removed product detection
- Price and availability change detection
- SQLite snapshot persistence
- Historical run tracking
- CSV export
- Excel export
- Streamlit dashboard
- Retry and backoff handling for temporary HTTP failures
- Scrape validation to prevent corrupted snapshots
- Automated test suite

---

## Dashboard

SmartData Monitor provides a Streamlit interface for creating and running monitoring configurations.

Users can either:

- Use a predefined demo configuration
- Create a custom website monitor
- Save configurations for later reuse
- Run previously saved monitors
- Inspect detected changes
- Review historical runs
- Export the latest dataset

---

## Architecture

```text
Streamlit UI
     │
     ▼
MonitorService
     │
     ▼
CatalogScraper
     │
     ├── RequestsScraper
     │       └── Static websites
     │
     └── PlaywrightScraper
             └── JavaScript-rendered websites
     │
     ▼
ProductParser
     │
     ▼
ProductCleaner
     │
     ▼
ScrapeValidator
     │
     ▼
ProductComparator
     │
     ▼
DatabaseManager
     │
     └── SQLite
```

The application separates scraping, parsing, normalization, validation, comparison, persistence, exporting, and presentation into independent components.

---

## Change Detection

Each monitor stores historical snapshots.

When a monitor runs again, SmartData Monitor compares the latest dataset against the previous snapshot using the product URL as its stable identity.

It detects:

```text
NEW
Products that did not exist in the previous snapshot.

REMOVED
Products that existed previously but no longer appear.

CHANGED
Products whose name, price, or availability changed.
```

Monitor histories are isolated by configuration.

This means two monitors can use the same URL while maintaining completely independent histories if their selectors, scraping mode, or page limits differ.

---

## Static and Dynamic Scraping

### Standard Mode

Uses Requests with:

- Persistent HTTP sessions
- Custom User-Agent
- Retry handling
- Exponential backoff
- HTTP error detection

This mode is optimized for server-rendered websites.

### Dynamic / JavaScript Mode

Uses Playwright with Chromium.

The browser is reused throughout a multi-page crawl rather than restarted for every page.

This allows SmartData Monitor to process pages whose content is created dynamically using JavaScript.

---

## Custom Website Configuration

Custom monitors support:

```text
Website URL
Product card selector
Name selector
Price selector
Availability selector
Product link selector
Next-page selector
Name attribute
Link attribute
Scraping mode
Maximum page count
```

The same monitoring pipeline can therefore be reused across websites with different HTML structures.

---

## Data Normalization

SmartData Monitor normalizes common price formats such as:

```text
£47.82
$1,299.99
€79,95
€1.299,99
USD 228 511
```

into numeric values suitable for comparison and storage.

Availability labels such as:

```text
In stock
Available
Only 3 left
Out of stock
Sold out
Reserved
Unavailable
```

are normalized into boolean availability values.

---

## Scrape Validation

Before a new snapshot is stored, the result is validated.

The validator can reject:

- Empty scrapes
- Missing required data
- Suspiciously large drops in product count

This helps prevent a broken CSS selector or temporary website failure from replacing a valid historical snapshot with corrupted data.

---

## Database

SQLite is used for local persistence.

The database stores:

```text
Monitors
Monitoring runs
Product snapshots
Monitor-to-run relationships
```

Monitor identity is generated from a fingerprint containing:

```text
URL
CSS selectors
Scraping mode
Maximum page count
```

This prevents different monitoring configurations from contaminating each other's histories.

---

## Project Structure

```text
smart-data-monitor/
│
├── app.py
├── config.py
├── requirements.txt
├── requirements-dev.txt
│
├── scraper/
│   ├── requests_scraper.py
│   ├── playwright_scraper.py
│   └── catalog_scraper.py
│
├── processing/
│   ├── parser.py
│   ├── cleaner.py
│   ├── comparator.py
│   └── validator.py
│
├── storage/
│   └── database.py
│
├── exporters/
│   └── exporter.py
│
├── services/
│   └── monitor_service.py
│
├── utils/
│   └── logger.py
│
└── tests/
```

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd smart-data-monitor
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Install the Playwright Chromium browser:

```bash
python -m playwright install chromium
```

---

## Running the Application

Start SmartData Monitor with:

```bash
python -m streamlit run app.py
```

Then open the local Streamlit address shown in the terminal.

---

## Running Tests

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run the complete test suite:

```bash
python -m pytest -v
```

Current test suite:

```text
27 automated tests passing
```

The suite covers:

- Parsing
- Multiple site structures
- Pagination
- Data cleaning
- Price normalization
- Availability normalization
- Duplicate handling
- Change detection
- Database persistence
- Monitor-profile isolation
- CSV and Excel exports
- HTTP retry behavior
- JavaScript rendering
- Browser reuse
- Scrape validation
- Full monitoring pipeline integration

---

## Demonstrated Configurations

SmartData Monitor has been tested against multiple independent website structures.

### Books to Scrape

Used to validate:

- Multi-page catalogue crawling
- Price extraction
- Availability extraction
- Product URLs
- Snapshot comparison

### Web Scraper Test Site

Used to validate:

- Custom CSS selector configuration
- Alternative HTML structure
- Alternative price format
- Alternative availability values
- Independent pagination configuration
- Saved monitor profiles

---

## Technology Stack

```text
Python
Streamlit
Requests
BeautifulSoup
Playwright
Pandas
SQLite
OpenPyXL
Pytest
```

---

## Intended Use

SmartData Monitor is designed as a reusable foundation for applications such as:

- Competitor price monitoring
- Product availability monitoring
- Inventory tracking
- Catalogue change detection
- Marketplace monitoring
- Custom client-specific monitoring systems

Websites should only be monitored where scraping is permitted and in accordance with the site's terms and applicable policies.

---

## Status

**Version 1**

Core monitoring functionality is complete and covered by automated tests.