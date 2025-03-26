"""
Quotes Scraper Script

This script connects to a MongoDB database, retrieves category URLs marked as 'pending',
scrapes quotes from each paginated category page, stores the extracted data into a MongoDB collection,
and finally exports the data to CSV and Excel files.

User Inputs (prompted at runtime):
    - request_limit (int): Maximum number of HTTP requests the script will send.
    - max_workers (int): Number of threads for concurrent scraping.

Key MongoDB Collections:
    - category_urls: Contains category URLs with their status ('pending' or 'done').
    - quotes_data: Stores extracted quotes, authors, and tags.

Main Features:
    - Multi-threaded scraping using ThreadPoolExecutor.
    - Pagination handling until no next page or request limit reached.
    - Updates category status to 'done' after processing.
    - Exports data to CSV and Excel formats.
"""

import requests
from lxml import html
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import time

# -------------- USER INPUTS -----------------
request_limit = int(input("Enter the maximum number of requests to send: "))
max_workers = int(input("Enter the number of max workers (threads): "))

# -------------- DATABASE CONNECTION ----------
client = MongoClient('mongodb://localhost:27017/')
db = client['quotes_db']
category_collection = db['category_urls']
quotes_collection = db['quotes_data']

# -------------- FETCH PENDING CATEGORIES -----
pending_categories = list(category_collection.find({"status": "pending"}).limit(request_limit))
if not pending_categories:
    print("⚠️ No pending categories found.")
    exit()

print(f"🚀 Found {len(pending_categories)} pending categories. Processing...")

request_counter = {'count': 0}


def process_category(category, request_counter):
    """
    Parses a single category page and all its paginated sub-pages to extract quotes,
    and inserts them into the MongoDB `quotes_data` collection.

    Args:
        category (dict): The category document from the `category_urls` collection, containing the `page_url`.
        request_counter (dict): A shared dictionary with a key `count` that tracks total HTTP requests made.

    Behavior:
        - Makes paginated requests to the category page.
        - Extracts quotes, authors, and tags from each page.
        - Continues until no next page is found, request limit is reached, or an error occurs.
        - Inserts all collected quotes into the MongoDB collection.
        - Marks the category status as `done` after completion.

    Raises:
        requests.exceptions.RequestException: If HTTP request fails.
        lxml.etree.ParserError: If response parsing fails.
        pymongo.errors.PyMongoError: If database insertion or update encounters an error.

    Returns:
        None
    """
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


# -------------- START PROCESSING --------------
start_time = time.time()

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = [executor.submit(process_category, cat, request_counter) for cat in pending_categories]
    for future in as_completed(futures):
        future.result()

end_time = time.time()
print("🏁 All categories processed!")
print(f"📊 Total Requests Sent: {request_counter['count']}")
print(f"⏱️ Total Execution Time: {round(end_time - start_time, 2)} seconds")


def export_data():
    """
    Exports all scraped quote data from the `quotes_data` collection to CSV and Excel files.

    Behavior:
        - Fetches all documents from MongoDB.
        - Converts data into a pandas DataFrame.
        - Saves the data as `quotes_data.csv` and `quotes_data.xlsx`.
        - Prints success or no-data-found messages.

    Raises:
        pandas.errors.PandasError: If export operations encounter an error.

    Returns:
        None
    """
    data = list(quotes_collection.find({}, {"_id": 0}))
    if not data:
        print("⚠️ No data found to export.")
        return

    df = pd.DataFrame(data)

    df.to_csv("quotes_data.csv", index=False, encoding="utf-8")
    print("✅ Data exported to quotes_data.csv")

    df.to_excel("quotes_data.xlsx", index=False)
    print("✅ Data exported to quotes_data.xlsx")


# -------------- EXPORT DATA ---------------
export_data()
