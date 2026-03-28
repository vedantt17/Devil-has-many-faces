import requests
from bs4 import BeautifulSoup
import os
import time
import csv
from datetime import date

BASE_URL = "https://www.justice.gov"
MAIN_PAGE = "https://www.justice.gov/epstein/doj-disclosures"
SAVE_DIR = "data/raw/epstein"
SOURCES_FILE = "data/sources.csv"

os.makedirs(SAVE_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})
session.cookies.set("justiceGovAgeVerified", "true", domain="www.justice.gov")

def get_pdf_links_from_page(url):
    try:
        r = session.get(url, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".pdf" in href.lower():
                full = href if href.startswith("http") else BASE_URL + href
                links.append(full)
        return links
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return []

print("Fetching main DOJ disclosures page...")
r = session.get(MAIN_PAGE)
soup = BeautifulSoup(r.text, "html.parser")

court_pages = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if "/epstein/doj-disclosures/" in href and "data-set" not in href:
        full = href if href.startswith("http") else BASE_URL + href
        if full not in court_pages:
            court_pages.append(full)

print(f"Found {len(court_pages)} court record pages.")

existing = set()
if os.path.exists(SOURCES_FILE):
    with open(SOURCES_FILE, "r") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row:
                existing.add(row[1])

downloaded = 0
skipped = 0
errors = 0

with open(SOURCES_FILE, "a", newline="") as csvfile:
    writer = csv.writer(csvfile)

    for page_url in court_pages:
        print(f"\nScraping: {page_url}")
        pdf_links = get_pdf_links_from_page(page_url)
        print(f"  Found {len(pdf_links)} PDFs")

        for url in pdf_links:
            filename = requests.utils.unquote(url.split("/")[-1].split("?")[0])

            if filename in existing:
                skipped += 1
                continue

            save_path = os.path.join(SAVE_DIR, filename)
            if os.path.exists(save_path):
                skipped += 1
                continue

            try:
                print(f"  Downloading: {filename}")
                resp = session.get(url, timeout=30)
                resp.raise_for_status()

                with open(save_path, "wb") as f:
                    f.write(resp.content)

                writer.writerow(["epstein", filename, url, date.today().isoformat(), 0])
                existing.add(filename)
                downloaded += 1
                time.sleep(0.5)

            except Exception as e:
                print(f"  ERROR: {filename}: {e}")
                errors += 1

print(f"\nAll done. Downloaded: {downloaded}, Skipped: {skipped}, Errors: {errors}")