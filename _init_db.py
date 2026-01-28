import pandas as pd
import sqlite3
import os
import re

# =========================
# 1️⃣ 設定與初始化資料庫
# =========================
DB_NAME = "scholarship.db"
EXCEL_FILE = "scholarship.xlsx"

def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS scholarship")
    cursor.execute("""
    CREATE TABLE scholarship (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        name TEXT,
        country TEXT,
        department TEXT,
        grade TEXT,
        scholarship_type TEXT,
        can_renew TEXT,
        m1 REAL DEFAULT 0, m2 REAL DEFAULT 0, m3 REAL DEFAULT 0, m4 REAL DEFAULT 0,
        m5 REAL DEFAULT 0, m6 REAL DEFAULT 0, m7 REAL DEFAULT 0, m8 REAL DEFAULT 0,
        m9 REAL DEFAULT 0, m10 REAL DEFAULT 0, m11 REAL DEFAULT 0, m12 REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        email TEXT
    )
    """)

    conn.commit()
    conn.close()
    print(f"✅ 資料庫 {DB_NAME} 已初始化完成")

# =========================
# 2️⃣ Email 獨立抽取函式
# =========================
def extract_email(row):
    email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    for val in row.values:
        if pd.isna(val):
            continue
        match = re.search(email_pattern, str(val))
        if match:
            return match.group(0)
    return None

# =========================
# 3️⃣ Excel 匯入資料
# =========================
def import_initial_data():
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ 找不到 {EXCEL_FILE}")
        return

    conn = sqlite3.connect(DB_NAME)
    all_sheets = pd.read_excel(EXCEL_FILE, sheet_name=None)

    # 欄位關鍵字對照
    mapping = {
        'student_id': ['學號', 'Student ID'],
        'name': ['姓名', 'Name', '英文姓名', '受獎生姓名'],
        'country': ['國籍', 'Country'],
        'department': ['系所', 'Department', '國內就讀學程'],
        'grade': ['年級', 'Grade'],
        'total_amount': ['小計', 'Total', '請款金額'],
        'email': ['電子郵件', 'Email', 'E-mail', 'Email Address']
    }

    total_count = 0

    for sheet_name, df in all_sheets.items():

        if df.empty or "for" in sheet_name.lower():
            continue

        # --- 找標題列 ---
        header_idx = -1
        for i, row in df.iterrows():
            if any("學號" in str(v) or "Student ID" in str(v) for v in row.values):
                header_idx = i
                break

        if header_idx == -1:
            continue

        clean_df = df.iloc[header_idx + 1:].copy()
        clean_df.columns = df.iloc[header_idx].values

        to_db = pd.DataFrame()

        # A. 基本欄位
        for db_col, keywords in mapping.items():
            for kw in keywords:
                matched = [c for c in clean_df.columns if kw in str(c)]
                if matched:
                    to_db[db_col] = clean_df[matched[0]]
                    break

        # B. 月份欄位
        for i in range(1, 13):
            month_kw = f"{i}月"
            matched = [c for c in clean_df.columns if month_kw in str(c)]
            if matched:
                to_db[f"m{i}"] = pd.to_numeric(
                    clean_df[matched[0]], errors="coerce"
                ).fillna(0)
            else:
                to_db[f"m{i}"] = 0

        # C. 額外資訊
        to_db["scholarship_type"] = sheet_name
        to_db["can_renew"] = clean_df.apply(
            lambda x: "否" if "不得再續領" in str(x.values) else "是",
            axis=1
        )

        # D. Email 強制獨立抽取（覆蓋）
        to_db["email"] = clean_df.apply(extract_email, axis=1)

        # 清除無效資料
        to_db = to_db.dropna(subset=["student_id"])

        to_db.to_sql("scholarship", conn, if_exists="append", index=False)
        total_count += len(to_db)

        print(f"📊 [{sheet_name}] 匯入 {len(to_db)} 筆")

    conn.close()
    print(f"🚀 完成匯入，共 {total_count} 筆資料")

# =========================
# 4️⃣ 主程式(main)
# =========================
if __name__ == "__main__":
    init_database()
    import_initial_data()