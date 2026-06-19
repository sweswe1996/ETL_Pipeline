import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional
import logging
import time

# ログ設定
logger = logging.getLogger(__name__)

# サイトURL
BASE_URL = "https://books.toscrape.com"
CATALOGUE_URL = f"{BASE_URL}/catalogue"

# リクエストヘッダー
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# データ型定義
@dataclass
class RawBook:
    title : str
    price_raw : str
    rating_text : str
    availability : str
    url : str
    scraped_at : str = field(default_factory = lambda : datetime.now(UTC).isoformat())

# URLからHTMLを取得する（失敗時は最大retries回リトライ）
def get_urlinfo(url : str, retries : int = 3, delay : float = 2.0) -> Optional[BeautifulSoup]:
    for attempt in range(1, retries+1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.HTTPError as e:
            logger.warning("HTTP Error - %s - %s (%d/%d times)", e, url, attempt, retries)
        except requests.exceptions.ConnectionError:
            logger.warning("Connection Error - %s (%d/%d times)", url, attempt, retries)
        except requests.exceptions.Timeout:
            logger.warning("TimeOut Error - %s (%d/%d times)", url, attempt, retries)
        except requests.exceptions.RequestException as e:
            logger.error("unexpected Error : %s", e)
            break
        except Exception as e:
            logger.error("Error Message : %s", e)
            return None

        # リトライ前に待機
        if attempt < retries:
            logger.info("%.1f second waiting", delay)
            time.sleep(delay)

    logger.error("%d times tried, but failed. %s", retries, url)
    return None

# 次ページのURLを取得する（最終ページはNoneを返す）
def next_page_urlinfo(soup : BeautifulSoup, current_url: str) -> Optional[str]:
    next_btn = soup.select_one("li.next > a")
    if not next_btn:
        return None

    href = next_btn["href"]
    if "catalogue/" in current_url:
        base = current_url.rsplit("/", 1)[0]
        return f"{base}/{href}"

    return f"{CATALOGUE_URL}/{href}"

# 1ページ分の書籍情報を取得する
def books_getinfo(soup : BeautifulSoup) -> list[RawBook]:
    books = []
    articles = soup.select("article.product_pod")

    for article in articles:
        try:
            # タイトル取得
            title_tag = article.select_one("h3 > a")
            title = title_tag["title"].strip() if title_tag else "N/A"

            # URL取得
            relative_url = title_tag["href"] if title_tag else ""
            book_url = f"{CATALOGUE_URL}/{relative_url}"

            # 価格取得
            price_tag = article.select_one("p.price_color")
            price_raw = price_tag.get_text(strip=True) if price_tag else ""

            # 星評価取得
            rating_tag = article.select_one("p.star-rating")
            rating_text = "Unknown"
            if rating_tag:
                classes = rating_tag.get("class", [])
                rating_text = classes[1] if len(classes) > 1 else "Unknown"

            # 在庫状況取得
            avail_tag = article.select_one("p.availability")
            availability = avail_tag.get_text(strip=True) if avail_tag else "Unknown"

            books.append(RawBook(
                title=title,
                price_raw=price_raw,
                rating_text=rating_text,
                availability=availability,
                url=book_url,
            ))
        except Exception as e:
            logger.warning("Skip!! %s", e)

    return books

# 全ページをスクレイピングして書籍リストを返す
def extract_infolist(max_pages: Optional[int] = None) -> list[RawBook]:
    all_books : list[RawBook] = []
    url = f"{BASE_URL}/catalogue/page-1.html"
    page_num = 0

    while url:
        page_num += 1

        # 最大ページ数チェック
        if max_pages and page_num > max_pages:
            logger.info("maximum page number %d is reached", max_pages)
            break

        logger.info("%d page is getting info -> %s", page_num, url)
        soup = get_urlinfo(url)

        # 取得失敗時は中断
        if soup is None:
            logger.info("%d page is failed.", page_num)
            break

        books = books_getinfo(soup)
        all_books.extend(books)
        logger.info("%d books info (total : %d rows)", len(books), len(all_books))

        url = next_page_urlinfo(soup, url)
        if url:
            time.sleep(0.5)

    logger.info("extract is finished. total records: %d rows", len(all_books))
    return all_books
