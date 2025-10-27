# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Principles

1. Follow SOLID principles
2. Only implement what's required; avoid overengineering
3. Ask for clarification if spec is unclear or contradictory
4. Understand task context before modifying code—use tools or ask if uncertain
5. Suggest process improvements if inefficiencies detected
6. Prefer modifying existing files; avoid creating new ones unless necessary
7. Do not generate documentation unless explicitly requested

## Documentation Standards

**Prohibited**:
- Fabricating non-existent features, APIs, files, or configurations
- Assuming system behavior (must verify)
- Guessing user intent (must confirm)
- Describing planned features as existing

**Required**:
- All technical details must come from actual code/config files
- Check files or ask when uncertain
- Distinguish reality from planning (mark future items as "planned")

**Verification Checklist**:
- [ ] Use Read/Glob to verify files exist before documenting
- [ ] Use Grep to verify APIs/functions exist in code
- [ ] Check for conflicts with other documentation
- [ ] Test example code executes

## Code Standards

**Naming**:
- Functions/Variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`

**Error Handling**:
```python
# Correct: Explicit error handling
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"Invalid data: {e}")
    raise
```

**Logging**:
```python
# Correct: Structured logging
logger.info(f"Processing {file_path}, size: {file_size}")
logger.error(f"Failed to process {file_path}: {error}", exc_info=True)

# Wrong
print("Debug")  # Never use print
```

## Git Conventions

**Branch Naming**: `feature-[desc]` | `fix-[desc]` | `update-[desc]`

**Commit Message**:
```
<type>(<scope>): <description>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: `feat` | `fix` | `docs` | `refactor` | `test` | `chore` | `update`

## Project Overview

Enables Claude Desktop to query BigQuery using natural language through MCP. Syncs Chinese field descriptions from Google Sheets to BigQuery metadata.

**Architecture**: Claude Desktop ↔ MCP Toolbox (local, stdio) ↔ BigQuery (HTTPS/TLS 1.2+)

## Development Workflow

### Setup
```bash
pip install -r requirements.txt
```

### Sync Schema Descriptions
```bash
python update_bigquery_descriptions.py
```
Run whenever Google Sheets descriptions are updated.

### Verify Configuration
```bash
# Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:bigquery-mcp@*"
```

### Test Changes
1. Restart Claude Desktop completely
2. Test: "請列出所有可用的 datasets"
3. Check logs: `%APPDATA%\Claude\logs\mcp*.log` (Windows) or `~/Library/Application Support/Claude/logs/mcp*.log` (macOS)

## Critical Implementation Details

### update_bigquery_descriptions.py

**Configuration**: Uses environment variables (see `.env.example`)
- `BIGQUERY_PROJECT`
- `GOOGLE_SHEET_ID`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `TARGET_DATASETS`

**Google Sheets Structure**:
1. "Table 列表" worksheet: Columns `BQ Table`, `Table 說明`, `狀態`
2. Table worksheets: Named `{dataset}.{table_name}`, columns `BQ 欄位`, `說明`

**Permissions**:
- Google Sheets: Service account shared as "Viewer"
- BigQuery: `bigquery.dataEditor` (for metadata updates only, higher than runtime)

### Claude Desktop Config

**Location**: See README.md for platform-specific paths

**Structure**:
```json
{
  "mcpServers": {
    "bigquery": {
      "command": "/absolute/path/to/toolbox.exe",
      "args": ["--prebuilt", "bigquery", "--stdio"],
      "env": {
        "BIGQUERY_PROJECT": "project-id",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/key.json"
      }
    }
  }
}
```
**Critical**: Use absolute paths only.

### Security

**Runtime Permissions (minimal)**:
- `roles/bigquery.dataViewer` (read only)
- `roles/bigquery.jobUser` (query execution only)

**Key Management**:
- `bigquery-key.json` in `.gitignore`
- Rotate quarterly
- Revoke if leaked: `gcloud iam service-accounts keys delete KEY_ID`

**Data Privacy**:
- MCP communication is local (stdio)
- Query results are sent to Anthropic for analysis
- BigQuery uses TLS 1.2+ encryption

## Common Issues

**Tools Not Available**: Validate JSON, verify absolute paths, restart Claude Desktop, check logs

**Permission Denied**: Re-grant `bigquery.dataViewer` role

**Descriptions Missing**: Verify script success (`[OK] 成功更新`), check BigQuery Console, restart Claude Desktop

**Windows Paths**: Use `C:\\path\\file.exe` or `C:/path/file.exe`, not `C:\path\file.exe`

## Project-Specific Notes

- Chinese field descriptions stored in BigQuery metadata
- MCP Toolbox is platform-specific binary (Windows: .exe, macOS: Intel/ARM)
- Schema updates require: Python script execution + Claude Desktop restart
- stdio communication (local only, not network)
- Worksheet ID (16282389) must match "Table 列表" sheet in Google Sheets
