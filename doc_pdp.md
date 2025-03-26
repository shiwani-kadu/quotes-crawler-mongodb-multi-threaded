
# 📜 Quotes Scraper Script Documentation

This script connects to a MongoDB database, retrieves category URLs marked as 'pending', scrapes quotes from each paginated category page, stores the extracted data into a MongoDB collection, and finally exports the data to CSV and Excel files.

---

## 📦 Imports  

```python
import requests
from lxml import html
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import time
```
- **Purpose:** This imports various libraries and modules used for web scraping, data processing, and system-level operations:
   - `requests`: For making HTTP requests to category pages.
   - `lxml.html`: For parsing HTML content and navigating using XPath.
   - `pymongo.MongoClient`: To connect to and interact with MongoDB.
   - `ThreadPoolExecutor, as_completed`: For concurrent scraping and handling multiple categories simultaneously.
   - `pandas`: To process and export scraped data to CSV/Excel formats.
   - `time`: To measure the execution duration.

---

## 🧑‍💻 User Inputs  

```python
request_limit = int(input("Enter the maximum number of requests to send: "))
max_workers = int(input("Enter the number of max workers (threads): "))
```
- **Purpose:**  
   - `request_limit`: The maximum number of HTTP requests allowed during script execution to avoid unnecessary overloading.
   - `max_workers`: The number of threads used for parallel processing of multiple category URLs.

---

## 🗄️ Database Connection  

```python
client = MongoClient('mongodb://localhost:27017/')
db = client['quotes_db']
category_collection = db['category_urls']
quotes_collection = db['quotes_data']
```
- **Purpose:**  
   - Establishes a connection to a local MongoDB instance.
   - Selects the database `quotes_db`.
   - Sets up two collections: 
     - `category_urls`: Stores category links and their scrape status.
     - `quotes_data`: Stores the extracted quote data.

---

## 📥 Fetch Pending Categories  

```python
pending_categories = list(category_collection.find({"status": "pending"}).limit(request_limit))
if not pending_categories:
    print("⚠️ No pending categories found.")
    exit()

print(f"🚀 Found {len(pending_categories)} pending categories. Processing...")

request_counter = {'count': 0}
```
- **Purpose:**  
   - Retrieves a list of category URLs from the `category_urls` collection where `status = "pending"`.
   - Limits the fetched categories based on the user-defined `request_limit`.
   - Exits the script if no pending categories are found.
   - Initializes `request_counter` to keep track of total HTTP requests made.

---

## 🔎 ### **Category Processing Function: process_category**  

```python
def process_category(category, request_counter):
    category_link = category.get("page_url")
    page_number = 1
    quotes_data = []

    while request_counter['count'] < request_limit:
        paginated_url = f"{category_link}/page/{page_number}/"
        print(f"📌 Request #{request_counter['count'] + 1}: {paginated_url}")

        try:
            response = requests.get(paginated_url, timeout=10)
            if response.status_code != 200:
                break

            request_counter['count'] += 1

            tree = html.fromstring(response.content)
            quotes = tree.xpath('//div[@class="quote"]')

            for quote in quotes:
                text = quote.xpath('span[@class="text"]/text()')[0]
                author = quote.xpath('span/small[@class="author"]/text()')[0]
                tags = quote.xpath('div[@class="tags"]/a[@class="tag"]/text()')

                quotes_data.append({
                    "quote": text,
                    "author": author,
                    "tags": ' | '.join(tags),
                    "category_link": paginated_url
                })

            next_page = tree.xpath('//li[@class="next"]/a/@href')
            if not next_page:
                break

            page_number += 1

        except Exception as e:
            print(f"⚠️ Error on {paginated_url}: {e}")
            break

    if quotes_data:
        quotes_collection.insert_many(quotes_data, ordered=False)

    category_collection.update_one({"_id": category["_id"]}, {"$set": {"status": "done"}})
```
- **Purpose:**  
   This function processes a single category and all its paginated pages to scrape quotes and store them in the `quotes_data` collection.

- **Step-by-step Explanation:**
   - Extracts `category_link` from the MongoDB document.
   - Iterates through paginated pages of that category while keeping request count under the `request_limit`.
   - Makes HTTP requests to paginated URLs.
   - Parses response content to extract:
     - Quote text
     - Author
     - Tags (joined by ' | ')
   - Appends the scraped data to a temporary list.
   - Checks for a next page via the "next" button; if absent, stops.
   - Inserts the collected quotes into MongoDB.
   - Updates the category status to `done` after completing the scraping for that category.

---

## 🚀 Start Processing  

```python
start_time = time.time()

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = [executor.submit(process_category, cat, request_counter) for cat in pending_categories]
    for future in as_completed(futures):
        future.result()

end_time = time.time()
print("🏁 All categories processed!")
print(f"📊 Total Requests Sent: {request_counter['count']}")
print(f"⏱️ Total Execution Time: {round(end_time - start_time, 2)} seconds")
```
- **Purpose:**  
   - Records the start time of the scraping process.
   - Uses `ThreadPoolExecutor` to concurrently scrape multiple categories using the defined `max_workers`.
   - Waits for all threads to complete.
   - Logs the total number of requests sent and total time taken.

---

## 💾 ### **Export Function: export_data**  

```python
def export_data():
    data = list(quotes_collection.find({}, {"_id": 0}))
    if not data:
        print("⚠️ No data found to export.")
        return

    df = pd.DataFrame(data)

    df.to_csv("quotes_data.csv", index=False, encoding="utf-8")
    print("✅ Data exported to quotes_data.csv")

    df.to_excel("quotes_data.xlsx", index=False)
    print("✅ Data exported to quotes_data.xlsx")
```
- **Purpose:**  
   - Fetches all scraped quotes from the `quotes_data` collection.
   - Converts the data into a pandas DataFrame.
   - Exports the data into two formats:
     - `quotes_data.csv`
     - `quotes_data.xlsx`
   - Logs success messages or warns if no data is found.

---

## 📤 Export Data Trigger  

```python
export_data()
```
- **Purpose:**  
   - Calls the `export_data` function at the end of the script to export all scraped quote data.

---

> ✅ Documentation generated for the Quotes Scraper Script.
