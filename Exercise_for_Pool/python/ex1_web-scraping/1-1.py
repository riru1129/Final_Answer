import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

# 定数の設定
BASE_URL = "https://r.gnavi.co.jp"
AREA_URL = f"{BASE_URL}/area/kanagawa/rs/?fw=%E3%82%AA%E3%83%A0%E3%83%A9%E3%82%A4%E3%82%B9"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
PAGE_LIMIT = 3
TIME_DELAY = 3

store_urls = []
data = []

def fetch_page(url, retries=3):
    for _ in range(retries):
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.content
        print(f"Failed to fetch: {url}, Status Code: {response.status_code}")
        time.sleep(TIME_DELAY)
    return None

def fetch_store_urls(pages=PAGE_LIMIT):
    for page in range(1, pages + 1):
        page_url = f"{AREA_URL}&p={page}"
        page_content = fetch_page(page_url)
        if page_content:
            soup = BeautifulSoup(page_content, "html.parser")
            for link in soup.select("a.style_titleLink__oiHVJ"):
                href = link.get("href")
                if href:
                    full_url = f"{BASE_URL}{href}" if not href.startswith("http") else href
                    store_urls.append(full_url)

def extract_store_info(soup):
    store_name = soup.find("p", id="info-name").text.strip() if soup.find("p", id="info-name") else ""
    phone_number = soup.find("span", class_="number").text.strip() if soup.find("span", class_="number") else ""
    email = "" 
    
    address_tag = soup.find("p", class_="adr slink")
    if address_tag:
        region_text = address_tag.find("span", class_="region").text.strip() if address_tag.find("span", class_="region") else ""
        building_name = address_tag.find("span", class_="locality").text.strip() if address_tag.find("span", class_="locality") else ""
        match = re.match(r"^(.*?[都道府県])(.*?[市区町村].*?)(\d+.*)$", region_text)
        if match:
            prefecture = match.group(1)
            city = match.group(2)
            rest = match.group(3)
        else:
            prefecture, city, rest = "", "", ""
    else:
        prefecture, city, rest, building_name = "", "", "", ""
    
    store_url = ""
    is_ssl = store_url.startswith("https")
    
    return [store_name, phone_number, email, prefecture, city, rest, building_name, store_url, is_ssl]

def fetch_store_data(store_url):
    time.sleep(TIME_DELAY)
    store_content = fetch_page(store_url)
    if store_content:
        soup = BeautifulSoup(store_content, "html.parser")
        return extract_store_info(soup)
    return None

fetch_store_urls(pages=PAGE_LIMIT)

for store_url in store_urls[:50]:
    store_data = fetch_store_data(store_url)
    if store_data:
        data.append(store_data)

columns = ["店舗名", "電話番号", "メールアドレス", "都道府県", "市区町村", "番地", "建物名", "URL", "SSL"]
df = pd.DataFrame(data, columns=columns)

output_file = "1-1.csv"
df.to_csv(output_file, index=False, encoding="utf-8-sig")
print(f"データが保存されました: {output_file}")