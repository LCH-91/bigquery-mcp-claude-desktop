#!/usr/bin/env python3
"""
Update BigQuery table and column descriptions from Google Sheets.
This makes descriptions available directly in BigQuery, so Claude Desktop
can access them through MCP Toolbox without needing to read local files.
"""

import gspread
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# Configuration - Use environment variables for sensitive data
PROJECT_ID = os.getenv("BIGQUERY_PROJECT", "your-project-id")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "your-sheet-id")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "bigquery-key.json")
TARGET_DATASETS = os.getenv("TARGET_DATASETS", "dataset1,dataset2").split(",")

def get_table_descriptions_from_sheet():
    """Read table descriptions from 'Table 列表' worksheet"""
    print("\n正在讀取 Google Sheets 的表格說明...")

    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )

    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(GOOGLE_SHEET_ID)

    # 使用 worksheet ID 來取得正確的工作表
    worksheet = spreadsheet.get_worksheet_by_id(16282389)
    records = worksheet.get_all_records()

    table_info = {}
    for row in records:
        bq_table = row.get('BQ Table')
        description = row.get('Table 說明', '')
        status = row.get('狀態', '')

        if bq_table and '.' in bq_table:
            dataset_name, table_name = bq_table.split('.')
            if dataset_name in TARGET_DATASETS:
                table_info[table_name] = {
                    'description': description,
                    'status': status
                }

    print(f"  找到 {len(table_info)} 個表格說明")
    return table_info

def get_column_schemas_from_sheet():
    """Read column-level schema from Google Sheet (only sem.* worksheets)"""
    print("\n正在讀取 Google Sheets 的欄位說明...")

    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )

    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(GOOGLE_SHEET_ID)

    column_schemas = {}
    worksheets = spreadsheet.worksheets()

    for worksheet in worksheets:
        sheet_title = worksheet.title

        # 只處理 sem. 開頭的分頁
        if not sheet_title.startswith('sem.'):
            continue

        print(f"  讀取分頁: {sheet_title}")
        table_name = sheet_title.replace('sem.', '')

        try:
            records = worksheet.get_all_records()
            columns = {}

            for row in records:
                col_name = row.get('BQ 欄位')
                col_desc = row.get('說明', '')

                if col_name:
                    columns[col_name] = col_desc

            if columns:
                column_schemas[table_name] = columns
                print(f"    找到 {len(columns)} 個欄位")

        except Exception as e:
            print(f"    警告: 讀取分頁失敗 - {e}")
            continue

    print(f"\n總共處理了 {len(column_schemas)} 個表格的欄位說明")
    return column_schemas

def update_bigquery_metadata():
    """Update BigQuery table and column descriptions"""

    # Get descriptions from Google Sheets
    table_descriptions = get_table_descriptions_from_sheet()
    column_descriptions = get_column_schemas_from_sheet()

    # Initialize BigQuery client
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH
    )
    client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

    print("\n" + "="*60)
    print("開始更新 BigQuery metadata")
    print("="*60)

    for dataset_id in TARGET_DATASETS:
        print(f"\n處理 dataset: {dataset_id}")
        dataset_ref = client.dataset(dataset_id)

        tables = list(client.list_tables(dataset_ref))
        print(f"  找到 {len(tables)} 個表格")

        for table_item in tables:
            table_id = table_item.table_id
            table_ref = dataset_ref.table(table_id)
            table = client.get_table(table_ref)

            print(f"\n  處理表格: {table_id}")

            # Update table description
            table_info = table_descriptions.get(table_id, {})
            if table_info.get('description'):
                new_description = table_info['description']
                if table_info.get('status'):
                    new_description += f" (狀態: {table_info['status']})"

                table.description = new_description
                print(f"    更新表格說明: {new_description}")

            # Update column descriptions
            if table_id in column_descriptions:
                col_descs = column_descriptions[table_id]
                new_schema = []
                updated_count = 0

                for field in table.schema:
                    new_desc = col_descs.get(field.name, field.description)

                    # Only update if description changed
                    if new_desc and new_desc != field.description:
                        updated_count += 1

                    new_field = bigquery.SchemaField(
                        name=field.name,
                        field_type=field.field_type,
                        mode=field.mode,
                        description=new_desc or field.description,
                        fields=field.fields
                    )
                    new_schema.append(new_field)

                table.schema = new_schema
                print(f"    更新 {updated_count} 個欄位說明")

            # Apply the changes
            try:
                client.update_table(table, ["description", "schema"])
                print(f"    [OK] 成功更新")
            except Exception as e:
                print(f"    [ERROR] 更新失敗: {e}")

    print("\n" + "="*60)
    print("BigQuery metadata 更新完成！")
    print("="*60)
    print("\n現在 Claude Desktop 可以透過 MCP Toolbox 直接取得欄位說明了！")

if __name__ == "__main__":
    update_bigquery_metadata()
