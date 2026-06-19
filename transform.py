import re
import logging
import pandas as pd
from typing import Any
from extract import RawBook

# ログ設定
logger = logging.getLogger(__name__)

# 星評価の変換マップ
RATING_MAP = {
    "One" : 1,
    "Two" : 2,
    "Three" : 3,
    "Four" : 4,
    "Five" : 5,
}

# 価格文字列をfloatに変換する（変換失敗時はNoneを返す）
def clean_price(raw : Any) -> float | None:
    if not isinstance(raw, str):
        return None

    # 通貨記号・空白を除去
    cleaned = re.sub(r"[Â£$€¥,\s]", "", raw.strip())
    try:
        return float(cleaned)
    except ValueError:
        logger.warning("price data clean is fail : %r", raw)
        return None

# RawBookリストをクレンジング済みDataFrameに変換する
def transform_infolist(raw_books : list[RawBook]) -> pd.DataFrame:

    if not raw_books:
        logger.warning("transform data is nothing")
        return pd.DataFrame()

    logger.info("%d books of transform data loading", len(raw_books))

    # リストをDataFrameに変換
    df = pd.DataFrame([vars(b) for b in raw_books])

    # 価格をfloatに変換
    df["price_gbp"] = df["price_raw"].apply(clean_price)

    # 星評価を数値に変換
    df["rating"] = df["rating_text"].map(RATING_MAP)

    # 在庫状況をbooleanに変換
    df["in_stock"] = df["availability"].str.lower().str.contains("in stock")

    # タイトルの空白を整理
    df["title"] = df["title"].str.strip().str.replace(r"\s+", " ", regex=True)

    # 価格が無効な行を除外
    invalid_price = df["price_gbp"].isna()
    if invalid_price.any():
        invalid_price_titles = df.loc[invalid_price, "title"].tolist()
        logger.warning(
            "%d books excluded due to invalid price: %s",
            len(invalid_price_titles),
            invalid_price_titles)
        df = df[~invalid_price].copy()

    # 価格帯カラムを追加
    bins = [0, 10, 20, 30, 50, float("inf")]
    labels = ["£0-10", "£10-20", "£20-30", "£30-50", "£50+"]
    df["price_band"] = pd.cut(df["price_gbp"], bins=bins, labels=labels, right=True)

    # 必要カラムだけ選択して価格の高い順にソート
    df = (df[["title", "price_gbp", "rating", "rating_text",
              "in_stock", "price_band", "url", "scraped_at"]]
            .sort_values("price_gbp", ascending=False)
            .reset_index(drop=True)
         )

    logger.info("transform is finished. records : %d books", len(df))
    return df

# 集計テーブルを作成して辞書形式で返す
def aggregate(df: pd.DataFrame) -> dict[str, pd.DataFrame]:

    if df.empty:
        logger.warning("aggregate data is nothing.")
        return {}

    aggs: dict[str, pd.DataFrame] = {}

    # 全体サマリー
    total        = len(df)
    in_stock     = df["in_stock"].sum()
    out_stock    = total - in_stock
    avg_price    = df["price_gbp"].mean()
    median_price = df["price_gbp"].median()
    avg_rating   = df["rating"].mean()

    aggs["summary"] = pd.DataFrame({
        "metric" : [
            "total_books", "in_stock", "out_of_stock",
            "avg_price_gbp", "median_price_gbp",
            "min_price_gbp", "max_price_gbp", "avg_rating",
        ],
        "value" : [
            total, in_stock, out_stock,
            round(avg_price, 2), round(median_price, 2),
            round(df["price_gbp"].min(), 2),
            round(df["price_gbp"].max(), 2),
            round(avg_rating, 2),
        ],
    })

    # 星評価ごとの集計
    aggs["by_rating"] = (
        df.groupby("rating_text", observed=True)
          .agg(
                book_count = ("title",     "count"),
                avg_price  = ("price_gbp", "mean"),
                min_price  = ("price_gbp", "min"),
                max_price  = ("price_gbp", "max"),
              )
          .round(2)
          .reset_index()
          .rename(columns={"rating_text" : "rating"})
          .sort_values("rating", key=lambda x: x.map(RATING_MAP))
          .reset_index(drop=True)
    )

    # 価格帯ごとの集計
    aggs["by_price_band"] = (
        df.groupby("price_band", observed=True)
          .agg(
                book_count   = ("title",    "count"),
                avg_rating   = ("rating",   "mean"),
                in_stock_cnt = ("in_stock", "sum"),
              )
          .round(2)
          .reset_index()
    )

    # 在庫あり上位10冊（高価格順）
    aggs["top10_expensive"] = (
        df[df["in_stock"]]
        .nlargest(10, "price_gbp")[["title", "price_gbp", "rating_text"]]
        .rename(columns={"rating_text" : "rating"})
        .sort_values("rating", key=lambda x: x.map(RATING_MAP))
        .reset_index(drop=True)
    )

    # 在庫なし書籍一覧
    aggs["out_of_stock"] = (
        df[~df["in_stock"]]
        [["title", "price_gbp", "rating_text"]]
        .reset_index(drop=True)
    )

    return aggs
