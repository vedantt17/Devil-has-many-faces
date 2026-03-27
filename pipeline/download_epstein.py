import requests
from bs4 import BeautifulSoup
import os
import time
import csv
from datetime import date

BASE_URL = "https://www.justice.gov"
PAGE_URL = "https://www.justice.gov/epstein/doj-disclosures/court-records-united-states-v-maxwell-no-120-cr-00330-sdny-2020"
SAVE_DIR = "data/raw/epstein"
SOURCES_FILE = "data/sources.csv"

os.makedirs(SAVE_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# Age verification cookie
session.cookies.set("age_verified", "1", domain="www.justice.gov")
session.cookies.set("doj_age_gate", "true", domain="www.justice.gov")

print("Fetching Maxwell case page...")
response = session.get(PAGE_URL)
soup = BeautifulSoup(response.text, "html.parser")

pdf_links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if ".pdf" in href.lower():
        full_url = href if href.startswith("http") else BASE_URL + href
        pdf_links.append(full_url)

print(f"Found {len(pdf_links)} PDF links.")

if len(pdf_links) == 0:
    print("No PDFs found. The age gate may be blocking access.")
    print("Response preview:")
    print(response.text[:500])
    exit()

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

with open(SOURCES_FILE, "a", newline="") as csvfile:
    writer = csv.writer(csvfile)
    for url in pdf_links:
        filename = url.split("/")[-1].split("?")[0]
        filename = requests.utils.unquote(filename)

        if filename in existing:
            skipped += 1
            continue

        save_path = os.path.join(SAVE_DIR, filename)
        if os.path.exists(save_path):
            skipped += 1
            continue

        try:
            print(f"  Downloading: {filename}")
            r = session.get(url, timeout=30)
            r.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(r.content)

            writer.writerow(["epstein", filename, url, date.today().isoformat(), 0])
            existing.add(filename)
            downloaded += 1
            time.sleep(0.75)

        except Exception as e:
            print(f"  ERROR: {filename}: {e}")

print(f"\nDone. Downloaded: {downloaded}, Skipped: {skipped}")