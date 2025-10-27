# 安全性說明

## 核心安全架構

### 資料傳輸路徑

```
你的電腦 (本機)              Google Cloud
┌────────────────┐           ┌──────────┐
│ Claude Desktop │           │          │
└───────┬────────┘           │          │
        │ stdio              │          │
        │ (本機通訊)          │          │
        ▼                    │          │
┌────────────────┐           │          │
│  MCP Toolbox   │  ─────────┼────────► │ BigQuery │
│   (本機執行)   │  TLS 1.2+ │          │
└────────────────┘           │          │
                             └──────────┘
```

### 安全特性

| 安全面向 | 機制 | 說明 |
|---------|------|------|
| **資料傳輸** | TLS 1.2+ | 企業級加密（可協商至 TLS 1.3）|
| **本機處理** | stdio | Claude ↔ MCP Toolbox 在本機通訊，不經過網路 |
| **認證方式** | Service Account | Google Cloud 企業級認證 |
| **權限控制** | IAM + RBAC | 精細權限管理，最小權限原則 |

### 資料流向分析

| 階段 | 執行位置 | 傳輸內容 | 包含真實資料？ |
|------|---------|---------|---------------|
| 理解需求 | Anthropic Cloud | 使用者問題 | ❌ 僅問題文字 |
| 查詢 Schema | 本機 MCP Toolbox | 欄位名稱與描述 | ❌ 僅 metadata |
| 生成 SQL | Anthropic Cloud | SQL 語句 | ❌ 僅 SQL 語法 |
| 執行查詢 | BigQuery | 實際執行 | ✅ 資料在 BigQuery |
| **分析結果** | **Anthropic Cloud** | **查詢結果** | **⚠️ 結果會傳至 Anthropic** |

**關鍵風險**：查詢結果會傳送至 Anthropic 進行分析，這是唯一真實資料離開 Google Cloud 的環節。

### 風險控制策略

**低風險場景（適用）**：
- 聚合統計資料（SUM, COUNT, AVG）
- 已脫敏的資料集
- 公開資訊或 metadata
- Dashboard 分析數據

**高風險場景（不建議）**：
- 包含 PII（個人識別資訊）
- 財務明細資料
- 原始日誌（IP、session ID）
- 未加密的敏感欄位

**建議做法**：
```bash
# 只開放聚合或脫敏後的 dataset
bq grant --dataset analytics_summary \
    serviceAccount:bigquery-mcp@PROJECT.iam.gserviceaccount.com \
    roles/bigquery.dataViewer

# 使用 Authorized Views 限制資料範圍
CREATE VIEW analytics.summary AS
SELECT DATE(ts) as date, COUNT(*) as count
FROM raw.events
GROUP BY 1
```

---

## 權限與存取控制

### 最小權限設定（推薦）

```bash
# 只給查詢權限，禁止修改/刪除資料
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"
```

### 權限說明

| 角色 | 權限 | 可以做什麼 | 不能做什麼 |
|------|------|-----------|-----------|
| `bigquery.dataViewer` | 讀取資料 | 查詢表格、查看 schema | ❌ 修改資料、刪除表格 |
| `bigquery.jobUser` | 執行查詢 | 執行 SQL 查詢 | ❌ 建立/修改表格結構 |

### 進階：Dataset 層級權限

```bash
# 只允許存取特定 dataset（更安全）
bq grant --dataset YOUR_DATASET \
    serviceAccount:bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    roles/bigquery.dataViewer
```

---

## 金鑰管理

### 金鑰安全

| 最佳實踐 | 說明 |
|---------|------|
| ✅ 加入 `.gitignore` | 防止意外上傳到 Git |
| ✅ 定期輪換 | 建議每季更換一次 |
| ✅ 限制權限 | 只給必要的最小權限 |
| ✅ 監控使用 | 啟用 Cloud Audit Logs |
| ❌ 不分享 | 金鑰等同密碼，不可分享 |
| ❌ 不硬編碼 | 不要寫在程式碼裡 |

### 金鑰輪換流程

```bash
# 1. 建立新金鑰
gcloud iam service-accounts keys create bigquery-key-new.json \
    --iam-account=bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 2. 更新 Claude Desktop 配置
# 修改 claude_desktop_config.json 指向新金鑰

# 3. 重啟 Claude Desktop 並測試

# 4. 刪除舊金鑰
gcloud iam service-accounts keys list \
    --iam-account=bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com

gcloud iam service-accounts keys delete OLD_KEY_ID \
    --iam-account=bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

## 資料隱私

### Cloud Audit Logs

```bash
gcloud logging read \
    "resource.type=bigquery_resource AND protoPayload.methodName=jobservice.insert" \
    --limit 50 --format json
```

---

## 威脅模型與防護

### 潛在威脅與緩解措施

| 威脅 | 風險等級 | 緩解措施 |
|------|---------|---------|
| **金鑰洩露** | 🔴 高 | • 不上傳 Git<br>• 定期輪換<br>• 啟用監控警報<br>• 發現異常立即撤銷 |
| **權限過大** | 🟡 中 | • 使用最小權限原則<br>• Dataset 層級限制<br>• 禁用 `bigquery.admin` |
| **查詢濫用** | 🟡 中 | • 設定配額限制<br>• 單次查詢上限<br>• 監控查詢成本 |
| **資料外洩** | 🔴 高 | • 查詢結果傳至 Anthropic<br>• 只開放脫敏/聚合 dataset<br>• 使用 Authorized Views |
| **本機惡意軟體** | 🟡 中 | • 安裝防毒軟體<br>• 使用 BitLocker 加密硬碟<br>• 定期安全掃描 |
| **中間人攻擊 (BigQuery)** | 🟢 低 | • TLS 1.2+ 加密<br>• Google 管理的 SSL 憑證 |
| **中間人攻擊 (Anthropic)** | 🟡 中 | • 依賴 Claude Desktop 安全性 |

### 配額限制與監控

BigQuery Console → IAM & Admin → Quotas → "BigQuery API"

建議啟用 Cloud Monitoring 警報：查詢量、成本、異常存取

---

## 安全檢查清單

### 初次設定

- [ ] 服務帳戶只有 `dataViewer` + `jobUser` 權限
- [ ] `bigquery-key.json` 已加入 `.gitignore`
- [ ] Claude Desktop 配置檔使用絕對路徑
- [ ] 已測試查詢功能正常運作

### 定期檢查（每月）

- [ ] 檢查 Audit Logs 是否有異常存取
- [ ] 確認查詢成本在預期範圍內
- [ ] 檢視服務帳戶權限是否仍符合最小原則
- [ ] 確認金鑰未洩露（檢查 GitHub、雲端硬碟等）

### 每季維護

- [ ] 輪換服務帳戶金鑰
- [ ] 審查並更新權限設定
- [ ] 檢查 Python 依賴套件是否有安全更新
- [ ] 更新 MCP Toolbox 到最新版本

---

## 安全事件應變

### 懷疑金鑰洩露

```bash
# 立即撤銷金鑰（30秒內完成）
gcloud iam service-accounts keys delete KEY_ID \
    --iam-account=bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 建立新金鑰
gcloud iam service-accounts keys create bigquery-key-new.json \
    --iam-account=bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 更新配置並重啟
```

### 發現異常查詢

```bash
# 檢查最近的查詢記錄
bq ls -j -a --max_results=100

# 停用服務帳戶（暫時）
gcloud iam service-accounts disable bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 調查完成後重新啟用
gcloud iam service-accounts enable bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

## 延伸閱讀

- [BigQuery Security](https://cloud.google.com/bigquery/docs/security)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)

---

**最後更新**: 2025-10-11
**安全聯絡**: 如發現安全問題請開 GitHub Issue (標註 [SECURITY])
