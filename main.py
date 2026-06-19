import logging
from pathlib import Path
from extract import extract_infolist
from transform import transform_infolist, aggregate
from load import load_all

# ログ設定（ファイルとターミナル両方に出力）
Path("output").mkdir(exist_ok=True)

logger_root = logging.getLogger()
logger_root.setLevel(logging.INFO)

fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(filename)s - %(message)s")

# ターミナル出力
stream = logging.StreamHandler()
stream.setFormatter(fmt)

# ファイル出力
file_handler = logging.FileHandler("output/pipeline.log", encoding="utf-8")
file_handler.setFormatter(fmt)

logger_root.addHandler(stream)
logger_root.addHandler(file_handler)

logger = logging.getLogger(__name__)


def main():
    logger.info("pipeline is start.")

    # ステップ1: データ取得
    raw = extract_infolist()
    logger.info("extract is finished - row : %d", len(raw))

    # ステップ2: データ変換・集計
    df = transform_infolist(raw)
    logger.info("transform is finished - row : %d", len(df))

    aggs = aggregate(df)
    logger.info("aggregate is finished - tables : %d", len(aggs))

    # ステップ3: データ保存（csv・json・excel・sqlite）
    load_all(df, aggs)
    logger.info("pipeline is end.")


if __name__ == "__main__":
    main()
