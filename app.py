import sqlite3
import pandas as pd
import streamlit as st

# --- 資料庫初始化 ---
def init_db():
    conn = sqlite3.connect("wish_pool.db", check_same_thread=False)
    c = conn.cursor()
    # 員工帳號表
    c.execute(
        """CREATE TABLE IF NOT EXISTS users 
                  (username TEXT PRIMARY KEY, name TEXT, role TEXT)"""
    )
    # 點數紀錄表
    c.execute(
        """CREATE TABLE IF NOT EXISTS points_log 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, points INTEGER, reason TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )
    # 許願池表
    c.execute(
        """CREATE TABLE IF NOT EXISTS wishes 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, wish_item TEXT, status TEXT DEFAULT '審核中', date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )
    # 預設建立一個管理員與測試員工
    c.execute(
        "INSERT OR IGNORE INTO users VALUES ('admin', '店長', 'manager')"
    )
    c.execute(
        "INSERT OR IGNORE INTO users VALUES ('staff01', '夥伴A', 'staff')"
    )
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("wish_pool.db", check_same_thread=False)

# --- 介面設定 ---
st.set_page_config(page_title="紅斗泥許願池與點數系統", page_icon="✨", layout="centered")

# --- 自訂 CSS 樣式（設定背景色 #cf9287、按鈕顏色 #bb837a 與全域白色字體 #fffeee） ---
st.markdown("""
    <style>
    /* 全局背景色 */
    .stApp {
        background-color: #cf9287 !important;
    }
    
    /* 讓所有文字、標題、說明預設為清晰的白色 / #fffeee */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, div[data-testid="stMarkdownContainer"] {
        color: #fffeee !important;
    }
    
    /* 側邊欄背景與文字 */
    section[data-testid="stSidebar"] {
        background-color: #b87d72 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #fffeee !important;
    }
    
    /* 輸入框文字設為深色，確保輸入時看得清楚，外框與背景用柔和米色 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #fff9f5 !important;
        color: #2c2c2c !important;
    }
    
    /* 下拉選單展開後的文字顏色 */
    div[data-baseweb="popover"] * {
        color: #2c2c2c !important;
    }
    
    /* 資訊框 (st.info, st.success 等) 文字與背景調整 */
    .stAlert {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: #fffeee !important;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .stAlert * {
        color: #fffeee !important;
    }
    
    /* 表格內的文字維持清晰深色 */
    dataframe, table * {
        color: #2c2c2c !important;
    }
    
    /* 所有按鈕顏色改為 #bb837a，文字改為白色 */
    .stButton button, .stFormSubmitButton button, div.stDownloadButton > button {
        background-color: #bb837a !important;
        color: #fffeee !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        font-weight: 600;
        border-radius: 8px;
    }
    .stButton button:hover, .stFormSubmitButton button:hover, div.stDownloadButton > button:hover {
        background-color: #a8736a !important;
        color: #ffffff !important;
        border-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>✨ 紅斗泥 · 夥伴許願池與點數福利站</h1>", unsafe_allow_html=True)
st.markdown("工作不無聊，目標自己選！累積點數實現大家的願望清單 🎁")

# 側邊欄：模式切換
st.sidebar.markdown("### 🧭 導覽選單")
mode = st.sidebar.radio("選擇模式", ["🏠 前台：點數與許願池", "🔐 後台：店長管理專區"])

# ==================== 前台：員工專區 ====================
if mode == "🏠 前台：點數與許願池":
    st.subheader("🌟 團隊點數與心願牆")
    
    # 1. 總點數與 KPI 說明
    conn = get_db_connection()
    c = conn.cursor()
    
    # 計算全店總點數
    c.execute("SELECT SUM(points) FROM points_log")
    total_points = c.fetchone()[0] or 0
    
    # 計算兌換金額 (1點 = 5元)
    total_money = total_points * 5
    
    col1, col2 = st.columns(2)
    col1.metric("目前全店累積總點數", f"{total_points} 點")
    col2.metric("相當於可運用福利金", f"NT$ {total_money}")
    
    st.markdown("---")
    st.markdown("### 🎯 本週小 KPI 累積項目（唯賞不罰）")
    st.markdown("""
    - 📦 **折一箱紙盒**：+10 點
    - 🧹 **環境打掃很乾淨**：+10 點
    - 🛡️ **這週都沒客訴**：+20 點
    - 🌸 **大福包得很漂亮**：+5 點
    - 🎯 **口味這週都沒出錯**：+15 點
    - 💡 **隱藏版：前台問卷收集 10 張**：+2 點
    """)
    
    st.markdown("---")
    st.markdown("### 🎁 大家的匿名許願池")
    st.info("許願內容不設限：藍牙音響、零食櫃、外送飲料、聖誕樹、公共衛生棉、披薩炸雞、員工聚餐...大家自己發揮！")
    
    # 顯示匿名許願清單
    c.execute("SELECT wish_item, status, date FROM wishes ORDER BY id DESC")
    wishes = c.fetchall()
    
    if wishes:
        for idx, (item, status, date) in enumerate(wishes, 1):
            st.markdown(f"**{idx}. 🔮 {item}**  \n*(狀態：{status} | 許願時間：{date[:10]})*")
    else:
        st.write("目前還沒有人許願，趕快來當第一個許願的人吧！")
        
    st.markdown("---")
    st.markdown("### ✍️ 我要來許願（每人每月限一個）")
    with st.form("wish_form"):
        user_account = st.text_input("請輸入你的員工帳號（僅用於驗證身分與計算次數，顯示時絕對匿名）：")
        wish_input = st.text_input("你想許願什麼物品或福利？")
        submit_wish = st.form_submit_button("送出許願")
        
        if submit_wish:
            if not user_account or not wish_input:
                st.error("請完整輸入帳號與許願內容！")
            else:
                c.execute("SELECT * FROM users WHERE username = ?", (user_account,))
                user = c.fetchone()
                if not user:
                    st.error("找不到此員工帳號，請跟店長確認帳號是否正確。")
                else:
                    c.execute("SELECT * FROM wishes WHERE username = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')", (user_account,))
                    already_wished = c.fetchone()
                    if already_wished:
                        st.warning("你這個月已經許過願囉！把機會留到下個月，或者大家一起努力集點達成現有的願望吧！")
                    else:
                        c.execute("INSERT INTO wishes (username, wish_item) VALUES (?, ?)", (user_account, wish_input))
                        conn.commit()
                        st.success("🎉 許願成功！你的願望已經匿名加入許願池了！")
                        st.rerun()
    conn.close()

# ==================== 後台：店長管理專區 ====================
elif mode == "🔐 後台：店長管理專區":
    st.subheader("🔐 店長管理後台")
    
    password = st.text_input("請輸入店長管理密碼：", type="password")
    
    if password == "daifuku888":
        st.success("密碼驗證成功！")
        
        tab1, tab2, tab3 = st.tabs(["➕ 點數加減與全店歸零", "👥 員工帳號管理", "📋 點數報表與願望審核"])
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 取得所有員工清單
        c.execute("SELECT username, name FROM users WHERE role != 'manager'")
        staff_list = c.fetchall()
        # 加入「全店」選項
        staff_dict = {"🌟 【全店夥伴一起加分/歸零】": "ALL"}
        for username, name in staff_list:
            staff_dict[f"{name} ({username})"] = username
        
        with tab1:
            st.markdown("### 給予夥伴點數或全店結算歸零")
            if not staff_list:
                st.warning("目前尚無員工帳號，請先至「員工帳號管理」新增。")
            else:
                selected_staff_label = st.selectbox("選擇對象（可選單人或全店）：", list(staff_dict.keys()))
                target_username = staff_dict[selected_staff_label]
                
                kpi_choice = st.selectbox("選擇加分項目 / 常用操作：", [
                    "自訂分數",
                    "📦 折一箱紙盒 (+10點)",
                    "🧹 環境打掃很乾淨 (+10點)",
                    "🛡️ 這週都沒客訴 (+20點)",
                    "🌸 大福包得很漂亮 (+5點)",
                    "🎯 口味這週都沒出錯 (+15點)",
                    "💡 隱藏版：前台問卷收集 10 張 (+2點)",
                    "🔄 點數歸零重置（將目前點數歸零）"
                ])
                
                if kpi_choice == "自訂分數":
                    points_val = st.number_input("輸入點數：", value=10, step=1)
                    reason_val = st.text_input("事由說明：")
                elif "歸零" in kpi_choice:
                    points_val = 0
                    reason_val = "結算歸零"
                else:
                    import re
                    match = re.search(r'\+(\d+)點', kpi_choice)
                    points_val = int(match.group(1)) if match else 0
                    reason_val = kpi_choice
                
                if st.button("確認送出點數變動"):
                    if "歸零" in kpi_choice:
                        if target_username == "ALL":
                            for _, u_name in staff_list:
                                c.execute("SELECT SUM(points) FROM points_log WHERE username = ?", (u_name,))
                                u_pts = c.fetchone()[0] or 0
                                if u_pts > 0:
                                    c.execute("INSERT INTO points_log (username, points, reason) VALUES (?, ?, ?)", 
                                              (u_name, -u_pts, "全店結算歸零重置"))
                            conn.commit()
                            st.success("已將【全店所有夥伴】的點數全數歸零重置！")
                            st.rerun()
                        else:
                            c.execute("SELECT SUM(points) FROM points_log WHERE username = ?", (target_username,))
                            current_user_pts = c.fetchone()[0] or 0
                            if current_user_pts > 0:
                                c.execute("INSERT INTO points_log (username, points, reason) VALUES (?, ?, ?)", 
                                          (target_username, -current_user_pts, "結算歸零重置"))
                                conn.commit()
                                st.success(f"已將該夥伴的點數歸零！")
                                st.rerun()
                            else:
                                st.info("該夥伴目前點數已經是 0。")
                    else:
                        if target_username == "ALL":
                            for _, u_name in staff_list:
                                c.execute("INSERT INTO points_log (username, points, reason) VALUES (?, ?, ?)", 
                                          (u_name, points_val, f"[全店] {reason_val}"))
                            conn.commit()
                            st.success(f"成功為【全店所有夥伴】各增加 {points_val} 點！（事由：{reason_val}）")
                            st.rerun()
                        else:
                            c.execute("INSERT INTO points_log (username, points, reason) VALUES (?, ?, ?)", 
                                      (target_username, points_val, reason_val))
                            conn.commit()
                            st.success(f"成功增加 {points_val} 點！（事由：{reason_val}）")
                            st.rerun()
                        
        with tab2:
            st.markdown("### 新增或刪除員工帳號")
            with st.form("add_user_form"):
                new_username = st.text_input("設定員工登入帳號（例如：staff02）：")
                new_name = st.text_input("員工姓名/暱稱（例如：小美）：")
                submit_user = st.form_submit_button("新增帳號")
                
                if submit_user:
                    if not new_username or not new_name:
                        st.error("請填寫帳號與姓名！")
                    else:
                        try:
                            c.execute("INSERT INTO users (username, name, role) VALUES (?, ?, 'staff')", (new_username, new_name))
                            conn.commit()
                            st.success(f"成功新增員工帳號：{new_name} ({new_username})")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("此帳號已經存在，請換一個帳號名稱。")
                            
            st.markdown("---")
            st.markdown("### 現有員工清單與刪除管理")
            if staff_list:
                del_staff_label = st.selectbox("選擇要刪除的員工帳號：", list(staff_dict.keys())[1:])
                del_username = staff_dict[del_staff_label]
                if st.button("🗑️ 確認刪除此員工帳號"):
                    c.execute("DELETE FROM users WHERE username = ?", (del_username,))
                    conn.commit()
                    st.warning(f"已刪除帳號：{del_staff_label}")
                    st.rerun()
            else:
                st.info("目前沒有任何員工帳號可刪除。")
                            
        with tab3:
            st.markdown("### 📊 點數報表與下載 Excel")
            
            st.markdown("#### 👥 目前各夥伴點數即時總覽")
            c.execute("""
                SELECT u.username, u.name, COALESCE(SUM(l.points), 0) as total_pts 
                FROM users u 
                LEFT JOIN points_log l ON u.username = l.username 
                WHERE u.role != 'manager'
                GROUP BY u.username, u.name
            """)
            summary_data = c.fetchall()
            if summary_data:
                df_summary = pd.DataFrame(summary_data, columns=["帳號", "姓名", "目前累積點數"])
                df_summary["相當於福利金(元)"] = df_summary["目前累積點數"] * 5
                st.dataframe(df_summary, use_container_width=True)
            else:
                st.info("目前尚無點數資料。")
            
            st.markdown("---")
            st.markdown("#### 📥 下載完整發放紀錄 (Excel 格式)")
            c.execute("""
                SELECT l.id, l.date, u.name, l.username, l.points, l.reason 
                FROM points_log l 
                JOIN users u ON l.username = u.username 
                ORDER BY l.id DESC
            """)
            logs_data = c.fetchall()
            if logs_data:
                df_logs = pd.DataFrame(logs_data, columns=["紀錄ID", "時間", "姓名", "帳號", "變動點數", "事由說明"])
                
                csv_data = df_logs.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 下載點數發放紀錄 CSV (可用 Excel 開啟)",
                    data=csv_data,
                    file_name="hongtouni_points_log.csv",
                    mime="text/csv",
                )
                
                st.markdown("#### 最近發放明細預覽")
                st.dataframe(df_logs.head(10), use_container_width=True)
            else:
                st.write("目前尚無發放紀錄。")
                
            st.markdown("---")
            st.markdown("#### 🔮 許願池管理")
            c.execute("SELECT id, username, wish_item, status FROM wishes")
            all_wishes = c.fetchall()
            for wid, wuser, witem, wstatus in all_wishes:
                st.write(f"ID: {wid} | 內容：**{witem}** | 目前狀態：`{wstatus}`")
                
        conn.close()
        
    elif password != "":
        st.error("密碼錯誤，請重新輸入！")
