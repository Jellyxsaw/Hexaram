import os
from sys import platform

from google.cloud import storage


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """
    上傳本地檔案到指定的 GCS Bucket 中

    參數:
    bucket_name (str): 目標 GCS Bucket 名稱
    source_file_name (str): 本地檔案路徑（例如模型檔案）
    destination_blob_name (str): 上傳後在 GCS 中的檔案名稱（包含路徑）
    """
    # 建立一個 storage client
    storage_client = storage.Client()

    # 取得 bucket 物件
    bucket = storage_client.bucket(bucket_name)
    # 建立 blob 物件
    blob = bucket.blob(destination_blob_name)

    # 將本地檔案上傳到 GCS
    blob.upload_from_filename(source_file_name)

    print(f"檔案 {source_file_name} 已成功上傳到 {bucket_name}/{destination_blob_name}。")


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """
    從指定的 GCS Bucket 下載檔案

    參數:
    bucket_name (str): GCS Bucket 名稱
    source_blob_name (str): 在 GCS 上的檔案名稱（包含路徑）
    destination_file_name (str): 下載到本地的檔案名稱（包含路徑）
    """
    # 建立 storage client
    storage_client = storage.Client()

    # 取得指定的 bucket 與 blob
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    # 檢查 blob 是否存在（若不存在則會拋出例外）
    if not blob.exists():
        raise FileNotFoundError(f"GCS 中不存在檔案: {bucket_name}/{source_blob_name}")

    # 根據作業系統設定下載路徑
    if platform == "Windows":
        temp_dir = os.path.join("C:\\", "Temp")
    else:
        temp_dir = "/tmp"

    # 確保目標資料夾存在
    os.makedirs(temp_dir, exist_ok=True)

    # 設定最終下載檔案的完整路徑
    destination_file_path = os.path.join(temp_dir, os.path.basename(source_blob_name))

    blob.download_to_filename(destination_file_path)
    print(f"檔案 {bucket_name}/{source_blob_name} 已下載到 {destination_file_path}")


if __name__ == '__main__':
    # 請依據實際狀況修改以下參數：
    bucket_name = 'hexaram'  # 請替換為你的 GCS Bucket 名稱
    source_file_name = '../advanced_aram_model_v2.h5'  # 本地模型檔案的路徑
    destination_blob_name = 'advanced_aram_model_v2.h5'  # GCS 上想要存放的路徑及檔名

    upload_blob(bucket_name, source_file_name, destination_blob_name)
