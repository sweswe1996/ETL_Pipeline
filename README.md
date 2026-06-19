# 📚 Book ETL Pipeline

A Python ETL pipeline that scrapes book data from [books.toscrape.com](https://books.toscrape.com), cleans it with Pandas, and exports to CSV, JSON, Excel, and SQLite.

## Project Overview

This project automates the full data pipeline process:

- **Extract** — Scrapes all 50 pages (1,000 books) using requests and BeautifulSoup. Includes retry logic for network errors and polite crawl delay between pages.
- **Transform** — Cleans price strings, converts data types, filters invalid rows, and adds a price band category using Pandas.
- **Load** — Saves the cleaned data and aggregation tables to 4 formats: CSV, JSON, Excel (multi-sheet), and SQLite.

## Project Structure

```
ETL_Pipeline/
├── extract.py       # Web scraping
├── transform.py     # Data cleaning and aggregation
├── load.py          # Export to CSV, JSON, Excel, SQLite
├── main.py          # Pipeline entry point
├── db_check.py      # SQLite viewer
├── requirements.txt
└── output/
    ├── books.csv
    ├── books.json
    ├── books.xlsx
    ├── books.db
    └── pipeline.log
```

## Getting Started

```bash
git clone https://github.com/sweswe1996/ETL_Pipeline.git
cd ETL_Pipeline
pip install -r requirements.txt
python main.py
```

## Tech Stack

`Python` `requests` `BeautifulSoup4` `Pandas` `SQLite3` `openpyxl`
