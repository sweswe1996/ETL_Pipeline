import logging
import pandas as pd
import json
import sqlite3
from pathlib import Path

# ログ設定
logger = logging.getLogger(__name__)

# 出力先ディレクトリ
OUTPUT_DIR = Path("output")

# ディレクトリを作成する
def create_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

# 保存先パスを取得する
def get_path(mode: int) -> Path:
    create_dir(OUTPUT_DIR)
    if mode == 1:
        return OUTPUT_DIR / "books.csv"
    elif mode == 2:
        return OUTPUT_DIR / "books.json"
    elif mode == 3:
        return OUTPUT_DIR / "books.xlsx"
    elif mode == 4:
        return OUTPUT_DIR / "books.db"

# CSVとして保存する
def load_csv(df: pd.DataFrame) -> Path:
    path = get_path(1)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info("CSV file save is complete. %s (%d rows)", path, len(df))
    return path

# JSONとして保存する
def load_json(df: pd.DataFrame) -> Path:
    path = get_path(2)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, indent=2, ensure_ascii=False)
    logger.info("json file save is complete. %s (%d rows)", path, len(df))
    return path

# Excelとして保存する（集計シートも含む）
def load_excel(df: pd.DataFrame, aggs: dict[str, pd.DataFrame]) -> Path:
    path = get_path(3)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        # 全データシート
        df.to_excel(writer, sheet_name="Books", index=False)
        # 集計シート
        for sheet_name, agg_df in aggs.items():
            sheet = sheet_name[:31]
            agg_df.to_excel(writer, sheet_name=sheet, index=False)
    logger.info("excel file save is complete. %s (%d rows)", path, len(df))
    return path

# SQLiteとして保存する
def load_sqlite(df: pd.DataFrame, aggs: dict[str, pd.DataFrame]) -> Path:
    path = get_path(4)
    conn = sqlite3.connect(path)
    with conn:
        # booksテーブルに保存
        df.to_sql(name="books", con=conn, if_exists="replace", index=False)
        # 集計テーブルに保存
        for sheet_name, agg_df in aggs.items():
            agg_df.to_sql(name=sheet_name, con=conn, if_exists="replace", index=False)
    logger.info("SQLite file is complete. %s (%d rows)", path, len(df))
    return path

# CSV・JSON・Excel・SQLiteをまとめて保存する
def load_all(df: pd.DataFrame, aggs: dict[str, pd.DataFrame]) -> dict[str, Path]:
    paths = {
        "csv"    : load_csv(df),
        "json"   : load_json(df),
        "excel"  : load_excel(df, aggs),
        "sqlite" : load_sqlite(df, aggs),
    }
    return paths
