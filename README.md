# BigQuery + Claude Desktop Integration

讓 Claude Desktop 用自然語言查詢 BigQuery，支援中文欄位描述。

## 安全聲明

**資料傳輸風險**：
- 查詢結果會傳送至 Anthropic 進行分析
- 不適用於包含 PII、財務資料、敏感日誌的環境
- 使用前需確認符合 GDPR/CCPA 等法規要求

**限制**：
- 個人 PoC，非官方整合
- 不提供任何擔保或 SLA

---

## 特色

- 中文語意支援：自動同步 Google Sheets 中的中文欄位描述到 BigQuery metadata
- Schema 感知查詢：自動讀取 BigQuery schema 生成準確的 SQL
- 本機執行：MCP 通訊使用 stdio 協定
- 最小權限：僅需 `dataViewer` + `jobUser`

---

## 系統架構

```
Claude Desktop (本機)
    ↓ stdio
MCP Toolbox (本機)
    ↓ HTTPS TLS 1.2+
BigQuery (Google Cloud)
    ↓ 查詢結果
Anthropic API (分析)
```

---

## 快速開始

### 前置需求

| 項目 | 安裝 |
|------|------|
| Claude Desktop | [下載](https://claude.com/download) |
| Python 3.8+ | [下載](https://python.org) 或 `brew install python` |
| gcloud CLI | [安裝](https://cloud.google.com/sdk/docs/install) |

### 配置流程

#### 1. 設定 Google Cloud

```bash
# 設定專案並啟用 API
gcloud config set project YOUR_PROJECT_ID
gcloud services enable bigquery.googleapis.com sheets.googleapis.com

# 建立服務帳戶並授予最小權限
gcloud iam service-accounts create bigquery-mcp --display-name="BigQuery MCP"
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

#### 2. 安裝 MCP Toolbox

請參考 [MCP 官方文件](https://modelcontextprotocol.io/introduction) 下載對應平台的 MCP server。

#### 3. 配置 Claude Desktop

編輯配置檔（Windows: `%APPDATA%\Claude\claude_desktop_config.json` / macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`）：

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

#### 4. 驗證

重啟 Claude Desktop，詢問：`請列出所有可用的 datasets`

**失敗排查**：檢查日誌 `%APPDATA%\Claude\logs\mcp*.log` (Windows) 或 `~/Library/Application Support/Claude/logs/mcp*.log` (macOS)

---

## 使用範例

在 Claude Desktop 詢問：
- "列出 dataset.table 的欄位"
- "查過去 7 天的記錄"
- "請查詢 bigquery-public-data.samples.shakespeare 中出現次數最多的前 10 個單字"

---

## 安全性

詳見 [SECURITY.md](SECURITY.md)

**最小權限**：

| 角色 | 用途 |
|------|------|
| `bigquery.dataViewer` | 讀取資料與 schema |
| `bigquery.jobUser` | 執行查詢任務 |

**禁止授予**：`bigquery.dataEditor`、`bigquery.admin`、`bigquery.dataOwner`

---

## 授權

MIT License - 詳見 [LICENSE](LICENSE)
