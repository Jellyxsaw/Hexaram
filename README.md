![image](https://github.com/user-attachments/assets/053a7bbe-49ff-4684-9d34-545c362b6946)# Hexaram - ARAM 勝率助手 & 陣容強度預測系統


> 此專案主要包含兩大部分：  
> 1. **GUI 勝率助手** – 透過 tkinter 提供即時/本地遊戲資料讀取、英雄資料展示及推薦陣容計算。  
> 2. **進階預測模型** – 利用深度學習模型對英雄陣容進行勝率預測，涵蓋資料庫數據讀取、數據處理、模型訓練與預測。

---

## 單純使用者

直接去release區下載最新版本(如果有的話)
如果讀取不到現場遊戲 請去檢查lockfile 會在你安裝LOL的資料夾裡面 預設位置 "C:\Riot Games\League of Legends\lockfile" 自己改一下

---

## 目錄
- [專案簡介](#專案簡介)
- [功能介紹](#功能介紹)
- [專案結構](#專案結構)
- [依賴與配置](#依賴與配置)
- [使用說明](#使用說明)
- [模型訓練與預測](#模型訓練與預測)
- [其他工具函數](#其他工具函數)
- [注意事項](#注意事項)

---

## 專案簡介

本專案旨在提供一個 ARAM（All Random All Mid）遊戲中的勝率預測及陣容推薦系統，分為兩大模組：

1. **GUI 勝率助手**  
   利用 tkinter 建構的桌面應用程式，提供即時遊戲數據讀取（透過 lockfile 與 Riot API）、英雄資料解析、候選陣容推薦及圖片展示功能。

2. **進階陣容強度預測模型**  
   透過從 PostgreSQL 資料庫讀取比賽 JSON 數據，進行資料解析、統計數據計算與正規化，並以 TensorFlow 建立深度學習模型，最終提供單筆及批量陣容勝率預測。

---

## 功能介紹

### 1. GUI 勝率助手
- **即時數據獲取**：從 League of Legends 的 lockfile 取得連線資訊，再利用 API 獲取即時比賽數據。
- **英雄資料管理**：優先從本地 JSON 文件讀取英雄映射資料；若不存在則自動從 PostgreSQL 資料庫讀取並生成對應 JSON。
- **推薦陣容計算**：對候選英雄組合進行勝率預測排序，推薦最佳 10 組陣容。
- **視覺化介面**：以深色風格呈現英雄圖片、已選英雄、候選池及預測結果，並支援設定（如 Lockfile 路徑與語言切換）。

### 2. 進階陣容強度預測模型
- **資料讀取與解析**：從資料庫中讀取比賽數據，解析 JSON 並整理各隊伍英雄與統計數據。
- **數據處理**：計算各英雄歷史平均統計數據，並保留每位英雄的原始數據，再利用 StandardScaler 進行正規化。
- **深度學習模型建立**：  
  - **英雄 ID 部分**：採用 Embedding 與 MultiHeadAttention 抽取英雄間隱藏關係。  
  - **統計數據部分**：以全連接層及殘差連接方式融合英雄數據。
- **模型訓練**：搭配 EarlyStopping、ReduceLROnPlateau 與 ModelCheckpoint 回呼函數，確保模型最佳化訓練。
- **預測功能**：透過 ARAMPredictor 類別支援單筆及批量陣容勝率預測。

---

## 專案結構

```plaintext
project/
│
├── main_app.py              # 主應用程式：GUI 勝率助手
├── chatDeep.py              # ARAMPredictor 與相關模型預測功能
├── champion_mapping.json    # 英雄映射 JSON (自動生成)
├── chinese_mapping.json     # 英雄中文映射 JSON (自動生成)
├── config.ini               # 配置文件（資料庫參數、Lockfile 路徑等）
├── champion_images/         # 英雄圖片資料夾
├── local_session.json       # 本地測試資料
│
├── model_training.py        # 模型訓練與數據處理腳本
├── advanced_aram_model_v2.h5  # 訓練好的模型文件 (生成後存在)
├── champion_to_idx_v2.pkl   # 英雄名稱與索引映射檔 (生成後存在)
├── scaler_v2.pkl            # StandardScaler 模型 (生成後存在)
└── champion_stats_dict_v2.pkl # 英雄統計數據 (生成後存在)

---

# Hexaram 打包說明

## 打包步驟

1. 確保已安裝所有依賴：
```bash
pip install -r requirements.txt
```

2. 準備資源文件：
   - 在專案根目錄創建 `images` 文件夾
   - 將應用程式圖標（.ico 格式）放入 `images` 文件夾，命名為 `icon.ico`
   - 確保 `fonts` 文件夾中包含所需的字體文件
   - 確保 `data` 文件夾中包含所需的數據文件

3. 運行打包腳本：
```bash
python build.py
```

4. 打包完成後，可執行檔將位於 `dist` 目錄中。

## 注意事項

- 確保所有資源文件（字體、圖片、數據等）都已正確放置在對應的文件夾中
- 打包過程可能需要幾分鐘時間
- 生成的可執行檔可以在其他 Windows 電腦上運行，無需安裝 Python
- 如果遇到問題，請檢查是否所有依賴都已正確安裝

## 文件結構要求

```
Hexaram/
├── claudeApp/
│   └── mainApp.py
├── images/
│   └── icon.ico
├── fonts/
│   ├── NotoSansTC-Regular.ttf
│   ├── NotoSansTC-Medium.ttf
│   └── NotoSansTC-Bold.ttf
├── data/
│   └── (其他數據文件)
├── build.py
└── requirements.txt
```


