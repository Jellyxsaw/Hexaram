#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本程式用於將來源資料庫中的指定資料表（結構與資料）複製到目標資料庫中，
並支援排除某些不需要複製的表。
請先安裝 sqlalchemy 與 psycopg2 套件：
    pip install sqlalchemy psycopg2
"""

import sys

from sqlalchemy import create_engine, MetaData, select


def main():
    # 設定來源與目標資料庫的連線字串
    source_db_url = "postgresql+psycopg2://user:password@localhost/source_database"
    target_db_url = "postgresql+psycopg2://user:password@target_host/target_database"

    # 定義要排除的資料表名稱清單 (不複製的表)
    exclude_tables = ['model_matches']

    try:
        # 建立來源與目標資料庫的連線引擎
        source_engine = create_engine(source_db_url)
        target_engine = create_engine(target_db_url)

        # 建立 metadata 物件並反射來源資料庫中的所有資料表結構
        source_metadata = MetaData()
        print("開始反射來源資料庫結構...")
        source_metadata.reflect(bind=source_engine)
        print(f"反射完成，共發現 {len(source_metadata.tables)} 張資料表。")

        # 過濾掉不需要複製的資料表
        tables_to_copy = {name: table for name, table in source_metadata.tables.items() if name not in exclude_tables}
        print(f"過濾後，將複製 {len(tables_to_copy)} 張資料表。")

        # 在目標資料庫依來源資料庫的 schema 建立所有需複製的資料表
        print("在目標資料庫建立資料表結構...")
        for table in tables_to_copy.values():
            table.create(target_engine, checkfirst=True)  # checkfirst=True 可避免重複建立
        print("資料表結構建立完成。")

        # 逐一複製每張資料表的資料
        with source_engine.connect() as source_conn:
            for table_name, table in tables_to_copy.items():
                print(f"開始複製資料表：{table_name} ...")
                # 使用 SELECT 指令讀取來源資料表中的資料
                select_stmt = select(table)
                result = source_conn.execute(select_stmt)
                rows = result.fetchall()
                if rows:
                    # 將每筆資料轉換為字典格式以便插入
                    data = [dict(row) for row in rows]
                    # 使用目標資料庫的 transaction 進行批次插入
                    with target_engine.begin() as target_conn:
                        target_conn.execute(table.insert(), data)
                    print(f"資料表 {table_name} 複製完成，共複製 {len(data)} 筆資料。")
                else:
                    print(f"資料表 {table_name} 無資料，略過。")
        print("所有指定資料表資料複製完成！")
    except Exception as e:
        print("執行過程發生錯誤：", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
