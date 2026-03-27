import requests
from bs4 import BeautifulSoup
import os
import time
import csv
from datetime import date

BASE_URL = "https://www.archives.gov"
PAGE_URL = "https://www.archives.gov/research/jfk/release-2025"
SAVE_DIR = "data/raw/jfk"
SOURCES_FILE = "data/sources.csv"

os.makedirs(SAVE_DIR, exist_ok=True)

print("Fetching JFK release page...")
response = requests.get(PAGE_URL, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(response.text, "html.parser")

# Find all PDF links on the page
pdf_links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if href.endswith(".pdf") or ".pdf" in href.lower():
        full_url = href if href.startswith("http") else BASE_URL + href
        pdf_links.append(full_url)

print(f"Found {len(pdf_links)} PDF links.")

# Load existing sources to avoid duplicates
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

        if filename in existing:
            print(f"  Skipping (already logged): {filename}")
            skipped += 1
            continue

        save_path = os.path.join(SAVE_DIR, filename)

        if os.path.exists(save_path):
            print(f"  Skipping (already exists): {filename}")
            skipped += 1
            continue

        try:
            print(f"  Downloading: {filename}")
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            r.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(r.content)

            page_count = 0
            writer.writerow(["jfk", filename, url, date.today().isoformat(), page_count])
            existing.add(filename)
            downloaded += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"  ERROR on {filename}: {e}")

print(f"\nDone. Downloaded: {downloaded}, Skipped: {skipped}")