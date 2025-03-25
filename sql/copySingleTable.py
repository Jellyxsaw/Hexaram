#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡易單表複製工具
直接在程式中設定表名，將指定表從來源資料庫複製到目標資料庫
包含結構與資料，並在主鍵衝突時自動更新資料

請先安裝必要套件：
    pip install sqlalchemy psycopg2 tqdm
"""

import sys
import logging
from time import time

from sqlalchemy import create_engine, MetaData, select, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert
from tqdm import tqdm

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('table_copy.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 直接在程式中設定參數
SOURCE_DB = "postgresql+psycopg2://postgres:aa030566@localhost/aram"
TARGET_DB = "postgresql+psycopg2://jelly:pinky030566@13.55.54.92/aram"
TABLE_NAME = "champion_metrics"  # 在此設定要複製的表名
BATCH_SIZE = 1000
VERBOSE = True  # 是否顯示進度條


def copy_table():
    """將指定表從來源資料庫複製到目標資料庫"""
    start_time = time()

    try:
        # 連接來源和目標資料庫
        logger.info(f"正在連接資料庫...")
        source_engine = create_engine(SOURCE_DB)
        target_engine = create_engine(TARGET_DB)

        # 反射來源資料庫以取得資料表結構
        source_metadata = MetaData()
        source_metadata.reflect(bind=source_engine, only=[TABLE_NAME])

        if TABLE_NAME not in source_metadata.tables:
            logger.error(f"資料表 '{TABLE_NAME}' 不存在於來源資料庫！")
            return False

        table = source_metadata.tables[TABLE_NAME]

        # 1. 複製資料表結構
        logger.info(f"正在檢查資料表 {TABLE_NAME} 的結構...")

        # 檢查目標資料庫是否已有此表
        target_inspector = inspect(target_engine)
        if TABLE_NAME in target_inspector.get_table_names():
            logger.info(f"資料表 {TABLE_NAME} 已存在於目標資料庫，略過結構複製。")
        else:
            table.create(target_engine)
            logger.info(f"已建立資料表 {TABLE_NAME} 結構。")

        # 2. 複製資料
        logger.info(f"正在複製資料表 {TABLE_NAME} 的資料...")

        # 取得資料筆數
        with source_engine.connect() as conn:
            from sqlalchemy.sql import func
            row_count_query = select(func.count()).select_from(table)
            total_rows = conn.execute(row_count_query).scalar()

            if total_rows == 0:
                logger.info(f"資料表 {TABLE_NAME} 無資料，略過資料複製。")
                return True

            logger.info(f"資料表 {TABLE_NAME} 共有 {total_rows} 筆資料。")

            # 讀取來源資料表中的資料
            select_stmt = select(table)
            result = conn.execution_options(stream_results=True).execute(select_stmt)
            keys = result.keys()

            # 檢查資料表是否有主鍵
            target_inspector = inspect(target_engine)
            pk_constraint = target_inspector.get_pk_constraint(TABLE_NAME)
            pk_columns = pk_constraint['constrained_columns'] if pk_constraint else []
            has_pk = bool(pk_columns)

            if has_pk:
                logger.info(f"資料表 {TABLE_NAME} 有主鍵: {', '.join(pk_columns)}")
                logger.info(f"將使用 UPSERT 策略 (衝突時更新)。")
            else:
                logger.info(f"資料表 {TABLE_NAME} 無主鍵，將使用直接插入策略。")

            # 使用批次插入處理大量資料
            rows_copied = 0
            with tqdm(total=total_rows, desc=f"複製資料", disable=not VERBOSE) as pbar:
                batch_data = []

                for row in result:
                    batch_data.append(dict(zip(keys, row)))

                    if len(batch_data) >= BATCH_SIZE:
                        try:
                            with target_engine.begin() as target_conn:
                                if has_pk:
                                    # 如果有主鍵，使用 upsert 策略
                                    for item in batch_data:
                                        # 獲取所有可更新的欄位（除了主鍵外）
                                        update_columns = {
                                            c.name: item[c.name]
                                            for c in table.columns
                                            if c.name not in pk_columns
                                        }

                                        # 構建 insert 語句
                                        insert_stmt = pg_insert(table).values(**item)

                                        # 添加 ON CONFLICT DO UPDATE 子句
                                        if update_columns:
                                            upsert_stmt = insert_stmt.on_conflict_do_update(
                                                index_elements=pk_columns,
                                                set_=update_columns
                                            )
                                            target_conn.execute(upsert_stmt)
                                        else:
                                            # 如果沒有可更新的欄位，則忽略衝突
                                            upsert_stmt = insert_stmt.on_conflict_do_nothing(
                                                index_elements=pk_columns
                                            )
                                            target_conn.execute(upsert_stmt)
                                else:
                                    # 如果沒有主鍵，直接插入
                                    target_conn.execute(table.insert(), batch_data)

                            rows_copied += len(batch_data)
                            pbar.update(len(batch_data))
                        except SQLAlchemyError as e:
                            logger.warning(f"批次插入/更新錯誤: {e}")

                        batch_data = []

                # 處理剩餘的資料
                if batch_data:
                    try:
                        with target_engine.begin() as target_conn:
                            if has_pk:
                                # 如果有主鍵，使用 upsert 策略
                                for item in batch_data:
                                    # 獲取所有可更新的欄位（除了主鍵外）
                                    update_columns = {
                                        c.name: item[c.name]
                                        for c in table.columns
                                        if c.name not in pk_columns
                                    }

                                    # 構建 insert 語句
                                    insert_stmt = pg_insert(table).values(**item)

                                    # 添加 ON CONFLICT DO UPDATE 子句
                                    if update_columns:
                                        upsert_stmt = insert_stmt.on_conflict_do_update(
                                            index_elements=pk_columns,
                                            set_=update_columns
                                        )
                                        target_conn.execute(upsert_stmt)
                                    else:
                                        # 如果沒有可更新的欄位，則忽略衝突
                                        upsert_stmt = insert_stmt.on_conflict_do_nothing(
                                            index_elements=pk_columns
                                        )
                                        target_conn.execute(upsert_stmt)
                            else:
                                # 如果沒有主鍵，直接插入
                                target_conn.execute(table.insert(), batch_data)

                        rows_copied += len(batch_data)
                        pbar.update(len(batch_data))
                    except SQLAlchemyError as e:
                        logger.warning(f"最後批次插入/更新錯誤: {e}")

            logger.info(f"已複製 {rows_copied} 筆資料，耗時 {time() - start_time:.2f} 秒。")

        return True

    except SQLAlchemyError as e:
        logger.error(f"資料庫操作錯誤: {e}")
        return False
    except Exception as e:
        logger.error(f"未預期錯誤: {e}")
        return False


if __name__ == "__main__":
    logger.info(f"開始複製資料表 {TABLE_NAME}...")

    if copy_table():
        logger.info(f"資料表 {TABLE_NAME} 複製完成！")
    else:
        logger.error(f"資料表 {TABLE_NAME} 複製失敗！")
        sys.exit(1)