# 射龍門遊戲

這是一個多人撲克牌遊戲專案，使用 Python 開發，採用伺服器-客戶端架構。玩家可以透過客戶端連接至伺服器，進行即時的撲克牌操作，例如抽牌和下注。

---

## 功能特色

- 支援多名玩家連線，透過中央伺服器進行遊戲管理。
- 即時撲克牌廣播功能，所有玩家可同步更新牌面。
- 客戶端具備互動式圖形介面，使用 `tkinter` 開發。
- 動態顯示撲克牌圖像（使用 `Pillow` 圖像處理）。
- 基本遊戲功能：
  - 抽牌。
  - 下注。
  - 登出功能。

---

## 環境需求

### 伺服器端
- Python 3.x
- 無需額外安裝的第三方依賴（僅使用標準庫）。

### 客戶端
- Python 3.x
- 必需安裝的第三方庫：
  - `Pillow`（用於處理撲克牌圖像）

使用以下指令安裝 `Pillow`：
```bash
pip install Pillow
```

---

## 運行方式

### 伺服器
1. 移動到伺服器腳本所在的目錄。
2. 運行伺服器腳本：
   ```bash
   python server.py
   ```
3. 伺服器將啟動，並在 `localhost:12345` 監聽玩家的連線請求。

### 客戶端
1. 移動到客戶端腳本所在的目錄。
2. 運行客戶端腳本：
   ```bash
   python client.py
   ```
3. 在介面中輸入玩家名稱，點擊「登入」或「註冊」。
4. 使用遊戲介面進行互動：
   - 點擊「Draw Cards」按鈕抽牌。
   - 點擊下注按鈕進行下注。
   - 點擊「Logout」按鈕登出。

---

## 專案結構

```
.
├── server.py          # 伺服器端腳本，負責管理連線與遊戲邏輯
├── client.py          # 客戶端腳本，提供圖形介面與遊戲互動功能
├── poker_cards/       # 存放撲克牌圖像的目錄（如 2_of_H.jpg）
└── README.md          # 專案文件
```

---

## 運作方式

1. **伺服器**：
   - 使用 Socket 與多線程技術管理玩家連線。
   - 維護共享的撲克牌資料（`shared_cards`），並廣播更新給所有客戶端。
   - 處理客戶端的請求，例如 `GET_CARDS`、`NEW_CARDS` 和 `EXIT`。

2. **客戶端**：
   - 連接伺服器並透過 `tkinter` 提供互動式介面。
   - 使用獨立線程監聽伺服器的廣播，及時更新撲克牌顯示。
   - 提供玩家抽牌、下注和登出的功能。