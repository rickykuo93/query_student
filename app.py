import streamlit as st
import sqlite3
import pandas as pd
import io



# ==============================================================
# 1. 基本設定與中英對照表
# ==============================================================
st.set_page_config(page_title="獎學金管理系統", layout="wide")
DB_NAME = "scholarship.db"
DEPT_LIST = [
    "（自行輸入）",

    # ===== 學士 =====
    "資訊工程系",
    "電子工程系",
    "機械工程系",
    "電機工程系",
    "營建工程系",
    "環境與安全衛生工程系",
    "化學工程與材料工程系",
    "會計系",
    "企業管理系",
    "資訊管理系",
    "財務金融系",
    "工業工程與管理系",
    "工商管理學士學位學程",
    "國際管理學士學位學程",
    "視覺傳達設計系",
    "創意生活設計系",
    "工業設計系",
    "數位媒體設計系",
    "建築與室內設計系",

    # ===== 碩士 =====
    "資訊工程系碩士班",
    "電機工程系碩士班",
    "機械工程系碩士班",
    "營建工程系碩士班",
    "電子工程系碩士班",
    "企業管理系碩士班",
    "財務金融系碩士班",
    "高階管理碩士學位學程",
    "創業管理碩士學位學程",
    "工業工程與管理系碩士班",
    "國際人工智慧管理研究所碩士班",
    "技術及職業教育研究所碩士班",
    "視覺傳達設計系碩士班",
    "設計學研究所",
    "應用外語系碩士班",
    "文化資產維護系碩士班",
    "建築與室內設計系碩士班",
    "智慧數據科學研究所碩士班",

    # ===== 博士 =====
    "機械工程系博士班",
    "工程科技研究所博士班",
    "財務金融系博士班",
    "化學工程與材料工程系博士班",
    "資訊管理系博士班",
    "技術及職業教育研究所博士班",
    "產業經營專業博士學位學程",
    "企業管理系博士班（行銷組）",
    "會計系博士班",
]
TYPE_LIST = ["豐泰","教臺","新南向","MOU清寒","雲科清寒","其他僑生獎學金"]
COLUMN_MAPPING = {
    'student_id': '學號',
    'name': '姓名',
    'country': '國籍',
    'department': '系所',
    'grade': '年級',
    'scholarship_type': '種類',
    'can_renew': '可否續領',
    'total_amount': '總額',
    'email': '電子郵件'
}

for i in range(1, 13):
    COLUMN_MAPPING[f'm{i}'] = f'{i}月'

# ==============================================================
# 2. 資料庫工具函式
# ==============================================================
def get_connection():
    return sqlite3.connect(DB_NAME)

def query_student(search_term):
    conn = get_connection()
    query = """
        SELECT * FROM scholarship
        WHERE student_id = ?
           OR name LIKE ?
           OR email LIKE ?
    """
    df = pd.read_sql(
        query,
        conn,
        params=(search_term, f"%{search_term}%", f"%{search_term}%")
    )
    conn.close()

    if 'id' in df.columns:
        df = df.drop(columns=['id'])
    return df

# ==============================================================
# 3. UI 主畫面
# ==============================================================
st.title("🎓 獎學金資料管理系統")

menu = ["🔍 查詢資料", "➕ 新增資料", "🗑️ 刪除資料", "🔁 資料雙向同步"]
choice = st.sidebar.selectbox("功能選單", menu)

# ==============================================================
# A. 查詢資料
# ==============================================================
if choice == "🔍 查詢資料":
    st.subheader("學生資料查詢")
    search_input = st.text_input("請輸入學號 / 姓名 / Email")

    if search_input:
        results = query_student(search_input)
        if not results.empty:
            st.success(f"找到 {len(results)} 筆資料")
            display_df = results.rename(columns=COLUMN_MAPPING)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("查無資料")

# ==============================================================
# B. 新增資料
# ==============================================================
elif choice == "➕ 新增資料":
    st.subheader("手動新增獎學金資料")

    with st.form("add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            s_id = st.text_input("學號（必填）")
            name = st.text_input("姓名（必填）")
            email = st.text_input("Email")

        with col2:
            country = st.text_input("國籍")

            dept_select = st.selectbox("系所", DEPT_LIST)
            if dept_select == "（自行輸入）":
                dept = st.text_input("請輸入系所名稱")
            else:
                dept = dept_select

            grade = st.text_input("年級")

        with col3:
            s_type = st.selectbox("獎學金種類", TYPE_LIST)
            renew = st.selectbox("可否續領", ["是", "否"])
            amount = st.number_input("本月金額", value=0)

        submit = st.form_submit_button("新增資料")

        if submit:
            if not s_id or not name:
                st.error("學號與姓名為必填")
            else:
                conn = get_connection()
                conn.execute("""
                    INSERT INTO scholarship
                    (student_id, name, email, country, department, grade,
                     scholarship_type, can_renew, m1, total_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    s_id, name, email, country, dept, grade,
                    s_type, renew, amount, amount
                ))
                conn.commit()
                conn.close()
                st.success("資料新增成功")

# ==============================================================
# C. 刪除資料
# ==============================================================
elif choice == "🗑️ 刪除資料":
    st.subheader("刪除學生資料")
    del_id = st.text_input("輸入學號")

    if del_id:
        preview = query_student(del_id)
        if not preview.empty:
            st.warning("以下資料將被刪除")
            st.dataframe(preview.rename(columns=COLUMN_MAPPING))

            if st.button("確認刪除"):
                conn = get_connection()
                conn.execute(
                    "DELETE FROM scholarship WHERE student_id = ?",
                    (del_id,)
                )
                conn.commit()
                conn.close()
                st.success("已刪除資料")
        else:
            st.info("查無此學號")

# ==============================================================
# D. 匯出 / 同步
# ==============================================================
elif choice == "🔁 資料雙向同步":
    st.subheader("資料匯出")

    if st.button("📤 下載目前資料庫 Excel"):
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM scholarship", conn)
        conn.close()

        if 'id' in df.columns:
            df = df.drop(columns=['id'])

        df = df.rename(columns=COLUMN_MAPPING)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="獎學金資料")

        st.download_button(
            "下載 Excel",
            output.getvalue(),
            file_name="獎學金資料.xlsx"
        )