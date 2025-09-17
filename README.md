# 🛠️ Ashby Job Scraper (Scrapy-based)

This repository contains a custom job scraper built using **Scrapy** to extract structured job listings from companies hosted on the **Ashby** job platform. It parses open positions, extracts structured job metadata, and pushes the cleaned data to MongoDB.

## 📸 Screenshots

<div align="center">
  <h3>Project Overview & Results</h3>
</div>

<div align="center">
  <img src="images/images (0).png" alt="Screenshot 1" width="80%" style="margin: 10px;">
  <br><em>Project Overview</em>
</div>

<div align="center">
  <img src="images/images (1).png" alt="Screenshot 2" width="80%" style="margin: 10px;">
  <br><em>Scraping Process</em>
</div>

<div align="center">
  <img src="images/images (2).png" alt="Screenshot 3" width="80%" style="margin: 10px;">
  <br><em>Data Processing</em>
</div>

<div align="center">
  <img src="images/images (4).png" alt="Screenshot 4" width="80%" style="margin: 10px;">
  <br><em>Results & Output</em>
</div>

<div align="center">
  <img src="images/images (5).png" alt="Screenshot 5" width="80%" style="margin: 10px;">
  <br><em>Final Results</em>
</div>

---

## 🔍 Features

- Scrapes job listings from multiple Ashby company URLs (input via CSV)
- Parses job details including:
  - Title, Description, Salary, Location, Employment Type
  - Required Application Questions
  - Company Info and Logos
- Uses schema.org JSON-LD for structured data extraction
- Classifies job types and infers remote status
- Pushes validated job data into MongoDB via custom utility methods
- Logs number of new jobs scraped per run

---

## 📂 Project Structure

```
├── Ashby_companies_test.csv      # Input file with list of Ashby company job URLs
├── spiders/
│   └── get_jobs.py               # Main Scrapy spider logic
├── utils/
│   └── scraper_utils.py          # Helper functions for classification, validation, etc.
├── oh_utils.py                   # Additional helper logic
├── push_mongo.py                 # MongoDB interaction functions
├── Scraping_log.log              # Log file for scrape results
```

---

## 🧠 Tech Stack

- **Python**
- **Scrapy**
- **Pandas**
- **Parsel**
- **MongoDB** (used via push_mongo.py)
- **JSON-LD Schema Parsing**
- Optional: **Zyte Smart Proxy Manager** (via zyte_api usage)

---

## 📥 Input

The spider reads a CSV file named Ashby_companies_test.csv with one column: companies, which contains Ashby job board URLs. Example:

csv
companies
https://jobs.ashbyhq.com/acme
https://jobs.ashbyhq.com/foobar

---

## 🚀 How to Run

1. **Install dependencies:**
   bash
   pip install -r requirements.txt

2. **Place your company URLs in Ashby_companies_test.csv.**

3. **Run the Scrapy spider:**
   bash
   scrapy crawl get_jobs

4. **Check the log for how many new jobs were scraped:**
   Scraping_log.log

---

## ✅ Output

Each valid job posting is pushed to MongoDB using:

- push(final_job_object)
- verify_job_format() ensures data structure consistency

The job object includes:

- job – Main job info
- requirements – Required form fields
- company – Company metadata
- raw_content – Full HTML response
- job_schema – Original structured data from Ashby
- job_site – 'Ashby'

---

## 📌 Notes

- The scraper skips duplicates by checking existing job URLs via job_exists().
- It attempts to enrich job data using both DOM and JSON-LD parsing.
- Salary and remote tags are extracted and normalized.

---

## 📧 Contact

For questions or collaboration, feel free to reach out via GitHub or email.

---

© 2025 – Built for job data enrichment and smart automation
