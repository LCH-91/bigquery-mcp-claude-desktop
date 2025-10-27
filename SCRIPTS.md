# Python 腳本說明

## update_bigquery_descriptions.py

將 Google Sheets 中的表格與欄位描述寫入 BigQuery metadata。

### 配置

設定環境變數（或建立 `.env` 檔案，參考 `.env.example`）：

```bash
export BIGQUERY_PROJECT=your-project-id
export GOOGLE_SHEET_ID=your-sheet-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/bigquery-key.json
export TARGET_DATASETS=dataset1,dataset2
```

### Google Sheets 結構

**工作表 "Table 列表"**：

| 欄位 | 說明 |
|------|------|
| BQ Table | `dataset.table_name` |
| Table 說明 | 表格描述 |
| 狀態 | 表格狀態 |

**工作表 "{dataset}.{table_name}"**：

| 欄位 | 說明 |
|------|------|
| BQ 欄位 | 欄位名稱 |
| 說明 | 欄位描述 |

### 執行

```bash
pip install -r requirements.txt
python update_bigquery_descriptions.py
```

### 故障排除

| 錯誤 | 解決方法 |
|------|---------|
| `Sheets API not enabled` | `gcloud services enable sheets.googleapis.com` |
| `Permission denied` | 在 Google Sheets 加入服務帳戶 email |
| `Worksheet not found` | 確認工作表名稱格式為 `{dataset}.{table_name}` |
