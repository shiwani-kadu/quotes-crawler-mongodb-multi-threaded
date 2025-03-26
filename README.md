# Multi-Threaded Quotes Scraper 📝🚀

## 📖 Project Overview

This Python script is designed to:
- Connect to a MongoDB database.
- Retrieve category URLs with a status of `pending`.
- Scrape quotes, authors, and tags from each paginated category page.
- Store the extracted data in a MongoDB collection.
- Export the collected data to CSV and Excel formats.
- Use multi-threading for faster scraping.

---

## 📂 Key Features

✅ Multi-threaded scraping using `ThreadPoolExecutor`  
✅ Pagination handling until no next page or request limit is reached  
✅ Automatically marks category status as 'done' after processing  
✅ Exports data to both CSV and Excel formats  

---

## 🛠️ Technologies Used
- `requests` — for HTTP requests  
- `lxml` — for HTML parsing using XPath  
- `pymongo` — to interact with MongoDB  
- `concurrent.futures` — for multi-threading  
- `pandas` — for data export to CSV and Excel  

---

## 📦 MongoDB Collections
| Collection Name   | Purpose                                                      |
|-------------------|--------------------------------------------------------------|
| `category_urls`   | Stores category URLs with their status (`pending` or `done`) |
| `quotes_data`     | Stores scraped quotes, authors, and tags                    |

---

## ⚙️ User Inputs (Prompted at Runtime)
| Input                | Description                                               |
|----------------------|-----------------------------------------------------------|
| `request_limit`      | The maximum number of HTTP requests the script will send |
| `max_workers`        | The number of concurrent threads for scraping            |

---

## 📜 How to Run

### 1️⃣ Clone the repository:
```bash
git clone https://github.com/your-username/multi-threaded-quotes-scraper.git

cd multi-threaded-quotes-scraper
