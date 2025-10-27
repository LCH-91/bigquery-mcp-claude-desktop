# 安全性說明

## 資料流向

```
Claude Desktop (本機)
    ↓ stdio (本機通訊)
MCP Toolbox (本機)
    ↓ TLS 1.2+
BigQuery (Google Cloud)
    ↓ 查詢結果
Anthropic API (分析結果)
```

⚠️ **關鍵風險**：查詢結果會傳送至 Anthropic 進行分析

**適用場景**：
- 聚合統計資料（SUM, COUNT, AVG）
- 已脫敏的資料集
- 公開資訊

**不適用場景**：
- 包含 PII（個人識別資訊）
- 財務明細資料
- 原始日誌（IP、session ID）

---

## 權限設定

**最小權限**：
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"
```

**Dataset 層級限制**（更安全）：
```bash
bq grant --dataset YOUR_DATASET \
    serviceAccount:bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    roles/bigquery.dataViewer
```

---

## 金鑰管理

- 加入 `.gitignore`
- 定期輪換（建議每季）
- 使用環境變數，不硬編碼

**輪換金鑰**：
```bash
# 建立新金鑰
gcloud iam service-accounts keys create bigquery-key-new.json \
    --iam-account=bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 刪除舊金鑰
gcloud iam service-accounts keys delete OLD_KEY_ID \
    --iam-account=bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

## 威脅模型

| 威脅 | 風險 | 緩解措施 |
|------|------|---------|
| 金鑰洩露 | 🔴 高 | 不上傳 Git、定期輪換 |
| 資料外洩 | 🔴 高 | 只開放脫敏/聚合 dataset |
| 權限過大 | 🟡 中 | Dataset 層級限制 |
| 查詢濫用 | 🟡 中 | 設定配額限制 |

---

## 應變流程

**金鑰洩露**：
```bash
# 立即撤銷金鑰
gcloud iam service-accounts keys delete KEY_ID \
    --iam-account=bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**異常查詢**：
```bash
# 停用服務帳戶
gcloud iam service-accounts disable bigquery-mcp@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

**延伸閱讀**：[BigQuery Security](https://cloud.google.com/bigquery/docs/security)
