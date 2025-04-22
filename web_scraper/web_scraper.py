import csv
import pathlib
import time
from urllib.parse import quote_plus as qp

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException

# Define synonyms
SYNONYMS = {
    "mpmc": ["multi-producer multi-consumer", "multi-writer multi-reader", "many-to-many"],
    "spmc": ["single-producer multi-consumer", "single-writer multi-reader", "one-to-many"],
    "mpsc": ["multi-producer single-consumer", "multi-writer single-reader", "many-to-one"],
    "spsc": ["single-producer single-consumer", "single-writer single-reader", "one-to-one"],
}

# Build queries
QUERIES = ['"wait-free FIFO queue"']
for acr, phrases in SYNONYMS.items():
    items = [f'"{acr}"'] + [f'"{p}"' for p in phrases]
    clause = ' OR '.join(items)
    QUERIES.append(f'"wait-free" "fifo queue" ({clause})')

# ("wait-free" OR "wait free") AND ((("multi-writer" OR "singe-writer" OR "multi writer" OR "single writer" OR "multi-producer" OR "single-producer" OR "multi producer" OR "single producer" OR "multi-enqueue" OR "single-enqueue" OR "multi enqueue" OR "single enqueue") AND ("multi-reader" OR "singe-reader" OR "multi reader" OR "single reader" OR "multi-consumer" OR "single-consumer" OR "multi consumer" OR "single comsumer" OR "multi-dequeue" OR "single-dequeue" OR "multi dequeue" OR "single dequeue")) OR "mpmc" OR "mpsc" OR "spsc" OR "spmc") AND "queue"
# Google Scholar configuration
GS_CFG = {
    "url_pattern": lambda q: f"https://scholar.google.com/scholar?q={qp(q)}&hl=en&as_sdt=0,5",
    "title_css": "h3.gs_rt a",
    "year_css": "div.gs_a",
    "abs_css": "div.gs_rs",
    "next_locator": {"by": By.XPATH, "value": '//*[@id="gs_nm"]/button[2]'},
    "output": "google_scholar.csv"
}

# Pause and timeout settings
PAUSE = 0.5
HEADLESS = True
TIMEOUT = 15


def open_chrome():
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless")
        opts.add_argument("--disable-gpu")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    driver.set_page_load_timeout(TIMEOUT)
    return driver


def scrape_google_scholar(driver, cfg, queries):
    print("[+] Scraping Google Scholar")
    out_file = pathlib.Path(cfg['output'])
    with out_file.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['query', 'rank', 'title', 'url', 'year', 'abstract'])
        for q in queries:
            print(f"  → {q}")
            driver.get(cfg['url_pattern'](q))
            try:
                WebDriverWait(driver, TIMEOUT).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, cfg['title_css']))
                )
            except TimeoutException:
                print(f"    No results for query: {q}")
                continue
            time.sleep(1)
            rank = 1
            while True:
                elems = driver.find_elements(By.CSS_SELECTOR, cfg['title_css'])
                if not elems:
                    break
                for e in elems:
                    title = e.text.strip()
                    link = e.get_attribute('href') or ''

                    # Year
                    year = ''
                    try:
                        container = e.find_element(
                            By.XPATH, 'ancestor::div[contains(@class, "gs_r")]'
                        )
                        y_elem = container.find_element(By.CSS_SELECTOR, cfg['year_css'])
                        year = y_elem.text.strip()
                    except Exception:
                        pass

                    # Abstract
                    abs_text = ''
                    try:
                        container = e.find_element(By.XPATH, 'ancestor::div[contains(@class, "gs_r")]')
                        abs_elem = container.find_element(By.CSS_SELECTOR, cfg['abs_css'])
                        abs_text = abs_elem.text.strip()
                    except Exception:
                        pass

                    writer.writerow([q, rank, title, link, year, abs_text])
                    rank += 1
                    time.sleep(PAUSE)

                # Next page
                locator = cfg['next_locator']
                try:
                    next_btn = driver.find_element(locator['by'], locator['value'])
                    if not next_btn.is_enabled():
                        break
                    next_btn.click()
                    WebDriverWait(driver, TIMEOUT).until(
                        EC.staleness_of(elems[0])
                    )
                except (NoSuchElementException, ElementNotInteractableException, TimeoutException):
                    break
                time.sleep(1)

def main():
    driver = open_chrome()
    scrape_google_scholar(driver, GS_CFG, QUERIES)
    driver.quit()
    print("Done scraping")


if __name__ == '__main__':
    main()
