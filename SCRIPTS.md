# Python 腳本說明

## update_bigquery_descriptions.py

將 Google Sheets 中的表格與欄位描述寫入 BigQuery metadata。

### 運作流程

```
Google Sheets
  ├─ "Table 列表" 工作表 → 表格描述
  └─ "sem.*" 工作表 → 欄位描述
        ↓
update_bigquery_descriptions.py
        ↓
BigQuery metadata (table.description + column.description)
        ↓
Claude Desktop (透過 MCP Toolbox 自動讀取)
```

### 使用方法

#### 1. 設定環境變數

```bash
export BIGQUERY_PROJECT=your-project-id
export GOOGLE_SHEET_ID=your-sheet-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/bigquery-key.json
export TARGET_DATASETS=dataset1,dataset2
```

或建立 `.env` 檔案（參考 `.env.example`）

#### 2. 準備 Google Sheets

**工作表 1: "Table 列表"**

| 欄位 | 說明 |
|------|------|
| BQ Table | 格式: `dataset.table_name` |
| Table 說明 | 表格描述 |
| 狀態 | 表格狀態 (會附加到描述中) |

**工作表 2~N: "{dataset}.{table_name}"** (每個表格獨立分頁)

| 欄位 | 說明 |
|------|------|
| BQ 欄位 | 欄位名稱 |
| 說明 | 欄位描述 |

#### 3. 執行腳本

```bash
# 安裝依賴
pip install -r requirements.txt

# 執行
python update_bigquery_descriptions.py
```

#### 4. 預期輸出

```
正在讀取 Google Sheets 的表格說明...
  找到 N 個表格說明

正在讀取 Google Sheets 的欄位說明...
  讀取分頁: dataset.table_name
    找到 X 個欄位
  ...

總共處理了 N 個表格的欄位說明

============================================================
開始更新 BigQuery metadata
============================================================

處理 dataset: your_dataset
  找到 N 個表格

  處理表格: table_name
    更新表格說明: [描述]
    更新 X 個欄位說明
    [OK] 成功更新

...
```

### 故障排除

| 錯誤 | 解決方法 |
|------|---------|
| `APIError: [403] Sheets API not enabled` | `gcloud services enable sheets.googleapis.com` |
| `Permission denied` | 在 Google Sheets 加入服務帳戶 email |
| `Worksheet not found` | 確認工作表名稱格式為 `{dataset}.{table_name}` |

---

**最後更新**: 2025-10-11
