from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import time

options = Options()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--allow-insecure-localhost')
options.add_argument('--disable-web-security')
options.set_capability("acceptInsecureCerts", True)
options.add_argument('--disable-gpu')

service = Service("chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

store_urls = []
data = []

def click_next_page():
    try:
        next_page_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/div/div[2]/main/div[12]/nav/ul/li[9]/a'))
        )
        ActionChains(driver).move_to_element(next_page_button).click().perform()
        print("次ページをクリックしました。")
        time.sleep(3)
    except Exception as e:
        print(f"次ページのクリックに失敗しました: {e}")

def fetch_store_urls(max_stores=50):
    current_page_url = "https://r.gnavi.co.jp/area/kanagawa/rs/?fw=%E3%82%AA%E3%83%A0%E3%83%A9%E3%82%A4%E3%82%B9"
    while len(store_urls) < max_stores:
        driver.get(current_page_url)
        try:
            store_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.style_titleLink__oiHVJ"))
            )
            for link in store_links:
                href = link.get_attribute("href")
                if href not in store_urls:
                    store_urls.append(href)
                if len(store_urls) >= max_stores:
                    break

            if len(store_urls) < max_stores:
                click_next_page()
            else:
                break
        except Exception as e:
            print(f"店舗リストページの取得に失敗しました: {current_page_url}, エラー: {e}")
            break

def fetch_store_data(store_url):
    driver.get(store_url)
    try:
        store_name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "info-name"))
        ).text.strip()
    except Exception:
        store_name = ""

    try:
        phone_number = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "number"))
        ).text.strip()
    except Exception:
        phone_number = ""

    try:
        address_region = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "region"))
        ).text.strip()

        try:
            building_name = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "locality"))
            ).text.strip()
        except Exception:
            building_name = ""

        match = re.match(r"^(.*?[都道府県])(.*?[市区町村].*?)(\d+-\d+-?\d*)(.*)$", address_region)
        if match:
            prefecture = match.group(1)
            city = match.group(2).strip()
            street_number = match.group(3).strip()
        else:
            prefecture, city, street_number = "", "", ""

    except Exception:
        prefecture, city, street_number, building_name = "", "", "", ""
    try:
        email_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "email"))
        )
        email = email_element.text.strip()
    except Exception:
        email = ""

    try:
        url_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.url.go-off"))
        )
        url = url_element.get_attribute("href").strip()
    except Exception:
        url = ""

    is_ssl = url.startswith("https")
    
    data.append([store_name, phone_number, email, prefecture, city, street_number, building_name, url, is_ssl])

fetch_store_urls(max_stores=50)

for store_url in store_urls:
    fetch_store_data(store_url)

driver.quit()

columns = ["店舗名", "電話番号", "メールアドレス", "都道府県", "市区町村", "番地", "建物名", "URL", "SSL"]
df = pd.DataFrame(data, columns=columns)

output_file = "1-2.csv"
df.to_csv(output_file, index=False, encoding="utf-8-sig")
print(f"データが保存されました: {output_file}")