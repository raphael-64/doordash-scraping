# DoorDash Menu Scraper

A Python script to scrape menu items from DoorDash restaurant pages using Playwright and Scrapybara.

## Setup

1. Install Python 3.8+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Select the restaurant you want to be scraped by changing the url.
2. Run the script:

   ```bash
   python doordash-scraper.py
   ```

3. The script will:
   - Navigate to the specified DoorDash restaurant page
   - Set a delivery address
   - Scan and collect all menu items
   - Save the results to `menu_items.json`

## Requirements

- Python 3.8+
- Scrapybara API key
- See `requirements.txt` for package dependencies
