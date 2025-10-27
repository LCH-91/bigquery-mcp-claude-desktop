# BigQuery + Claude Desktop Integration

讓 Claude Desktop 用自然語言查詢 BigQuery，支援中文欄位描述。

## 安全聲明

**資料傳輸風險**：
- 查詢**結果**會傳送至 Anthropic 進行分析
- 不適用於包含 PII、財務資料、敏感日誌的環境
- 使用前需確認符合 GDPR/CCPA 等法規要求

**限制**：
- 個人 PoC，非 Google 或 Anthropic 官方整合
- 不提供任何擔保或 SLA

---

## 功能說明

```
使用者：「查詢過去 7 天的資料」
   ↓
Claude Desktop：理解需求並查詢 schema
   ↓
MCP Toolbox：生成 SQL 並執行
   ↓
BigQuery：返回查詢結果
   ↓
Claude Desktop：分析並回覆
```

## 專案特色

- **中文語意支援**：自動同步 Google Sheets 中的中文欄位描述到 BigQuery metadata
- **Schema 感知查詢**：自動讀取 BigQuery schema 生成更準確的 SQL
- **本機執行**：MCP 通訊使用 stdio 協定
- **最小權限**：僅需 `dataViewer` + `jobUser`
- **跨平台**：Windows / macOS

---

## 系統架構

```
┌────────────────┐
│ Claude Desktop │  你的問題
└───────┬────────┘
        │ MCP Protocol (stdio, 本機通訊)
        ▼
┌────────────────┐
│  MCP Toolbox   │  生成 SQL
│   (本機執行)   │
└───────┬────────┘
        │ HTTPS (TLS 1.2+)
        ▼
┌────────────────┐
│   BigQuery     │  執行查詢
└────────────────┘
```

**關鍵**:
- 本機執行，MCP 通訊不經過網路
- BigQuery 連線使用 TLS 1.2+ 加密
- 查詢結果會傳至 Anthropic 進行分析

---

## 快速開始

### 前置需求

| 項目 | Windows | macOS |
|------|---------|-------|
| Claude Desktop | [下載](https://claude.com/download) | [下載](https://claude.com/download) |
| Python 3.8+ | [下載](https://python.org) | `brew install python` |
| gcloud CLI | [安裝](https://cloud.google.com/sdk/docs/install) | `brew install google-cloud-sdk` |

### 配置流程

#### Step 1: 設定 Google Cloud

```bash
# 設定專案
gcloud config set project YOUR_PROJECT_ID

# 啟用 API
gcloud services enable bigquery.googleapis.com sheets.googleapis.com

# 建立服務帳戶
gcloud iam service-accounts create bigquery-mcp \
    --display-name="BigQuery MCP"

# 授予最小權限
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# 下載金鑰
gcloud iam service-accounts keys create bigquery-key.json \
    --iam-account=bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

#### Step 2: 安裝 MCP Toolbox

請參考 [MCP 官方文件](https://modelcontextprotocol.io/introduction) 下載對應平台的 MCP server。

或使用已打包的 toolbox (需自行取得)：
- Windows: `toolbox.exe`
- macOS: `toolbox` (需 `chmod +x`)

#### Step 3: 配置 Claude Desktop

**配置檔位置**:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

**內容**（使用絕對路徑）:
```json
{
  "mcpServers": {
    "bigquery": {
      "command": "/absolute/path/to/toolbox",
      "args": ["--prebuilt", "bigquery", "--stdio"],
      "env": {
        "BIGQUERY_PROJECT": "YOUR_PROJECT_ID",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/bigquery-key.json"
      }
    }
  }
}
```

#### Step 4: 重啟並驗證

```bash
# 重啟 Claude Desktop
```

在 Claude Desktop 詢問：
```
請列出所有可用的 datasets
```

**預期輸出**：顯示 dataset 列表

**失敗排查**：
- 檢查日誌：`%APPDATA%\Claude\logs\mcp*.log` (Windows) 或 `~/Library/Application Support/Claude/logs/mcp*.log` (macOS)
- 驗證 JSON 配置語法
- 確認使用絕對路徑

---

## 使用指南

### 查詢範例

| 你的問題 | Claude 的處理 |
|---------|--------------|
| "列出 dataset.table 的欄位" | 使用 `get_table_info` 查詢 schema |
| "查過去 7 天的記錄" | 生成 SQL: `WHERE date_column >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)` |
| "統計每個類別的數量" | GROUP BY + COUNT |
| "分析用戶活躍度" | JOIN 多表 + 聚合分析 |

### 快速測試

在 Claude Desktop 詢問：`請查詢 bigquery-public-data.samples.shakespeare 中出現次數最多的前 10 個單字`

---


## 安全性

### 資料傳輸路徑

```
Claude Desktop (本機)
    ↓ stdio (本機程序通訊)
MCP Toolbox (本機)
    ↓ HTTPS TLS 1.2+
BigQuery (Google Cloud)
    ↓ 查詢結果
Anthropic API (分析結果)
```

- 本機通訊使用 stdio，不經過網路
- BigQuery 連線使用 TLS 1.2+ 加密
- 查詢結果會傳至 Anthropic 進行分析

### 權限最小化

| 角色 | 用途 |
|------|------|
| `bigquery.dataViewer` | 讀取資料與 schema |
| `bigquery.jobUser` | 執行查詢任務 |

**禁止授予**：
- `bigquery.dataEditor`、`bigquery.admin`、`bigquery.dataOwner`

### 安全檢查

**初次設定**：
- [ ] `bigquery-key.json` 已加入 `.gitignore`
- [ ] 服務帳戶僅有 `dataViewer` + `jobUser` 權限
- [ ] 測試查詢功能正常

**檢查敏感檔案是否被誤 commit**：
```bash
git log --all --full-history -- bigquery-key.json
# 如有輸出，立即撤銷並重新生成金鑰
```

完整安全最佳實踐請見 [SECURITY.md](SECURITY.md)

---

## 授權

MIT License - 詳見 [LICENSE](LICENSE)

---

**最後更新**: 2025-10-11
