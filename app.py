import sqlite3
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
        "OR IGNORE INTO users VALUES ('admin', '店長', 'manager')"
    )
    c.execute(
        "OR IGNORE INTO users VALUES ('staff01', '夥伴A', 'staff')"
    )
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect("wish_pool.db", check_same_thread=False)

# --- 介面設定 ---
st.set_page_config(page_title="紅斗泥許願池與點數系統", page_icon="✨", layout="centered")

st.title("✨ 紅斗泥 · 夥伴許願池與點數福利站")
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
                # 檢查帳號是否存在
                c.execute("SELECT * FROM users WHERE username = ?", (user_account,))
                user = c.fetchone()
                if not user:
                    st.error("找不到此員工帳號，請跟店長確認帳號是否正確。")
                else:
                    # 檢查本月是否許過願
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
    
    # 簡單設定預設密碼為 "daifuku888" (可自行更改)
    if password == "daifuku888":
        st.success("密碼驗證成功！")
        
        tab1, tab2, tab3 = st.tabs(["➕ 點數加減管理", "👥 員工帳號管理", "📋 點數明細與願望審核"])
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 取得所有員工清單
        c.execute("SELECT username, name FROM users WHERE role != 'manager'")
        staff_list = c.fetchall()
        staff_dict = {f"{name} ({username})": username for username, name in staff_list}
        
        with tab1:
            st.markdown("### 給予夥伴點數")
            if not staff_dict:
                st.warning("目前尚無員工帳號，請先至「員工帳號管理」新增。")
            else:
                selected_staff_label = st.selectbox("選擇要加減分的夥伴：", list(staff_dict.keys()))
                target_username = staff_dict[selected_staff_label]
                
                # KPI 選項快速給分
                kpi_choice = st.selectbox("選擇加分項目 / 常用操作：", [
                    "自訂分數",
                    "📦 折一箱紙盒 (+10點)",
                    "🧹 環境打掃很乾淨 (+10點)",
                    "🛡️ 這週都沒客訴 (+20點)",
                    "🌸 大福包得很漂亮 (+5點)",
                    "🎯 口味這週都沒出錯 (+15點)",
                    "💡 隱藏版：前台問卷收集 10 張 (+2點)",
                    "🔄 點數歸零重置"
                ])
                
                if kpi_choice == "自訂分數":
                    points_val = st.number_input("輸入點數（增加填正數，扣分/歸零前置請看下方）：", value=10, step=1)
                    reason_val = st.text_input("事由說明：")
                elif "歸零" in kpi_choice:
                    points_val = 0
                    reason_val = "結算歸零"
                else:
                    # 從字串中解析點數
                    import re
                    match = re.search(r'\+(\d+)點', kpi_choice)
                    points_val = int(match.group(1)) if match else 0
                    reason_val = kpi_choice
                
                if st.button("確認送出點數變動"):
                    if "歸零" in kpi_choice:
                        # 歸零邏輯：插入一筆負的總和，或直接清空該使用者點數紀錄
                        c.execute("SELECT SUM(points) FROM points_log WHERE username = ?", (target_username,))
                        current_user_pts = c.fetchone()[0] or 0
                        if current_user_pts > 0:
                            c.execute("INSERT INTO points_log (username, points, reason) VALUES (?, ?, ?)", 
                                      (target_username, -current_user_pts, "結算歸零重置"))
                            conn.commit()
                            st.success(f"已將 {selected_staff_label} 的點數歸零！")
                            st.rerun()
                        else:
                            st.info("該夥伴目前點數已經是 0。")
                    else:
                        c.execute("INSERT INTO points_log (username, points, reason) VALUES (?, ?, ?)", 
                                  (target_username, points_val, reason_val))
                        conn.commit()
                        st.success(f"成功為 {selected_staff_label} 增加 {points_val} 點！（事由：{reason_val}）")
                        st.rerun()
                        
        with tab2:
            st.markdown("### 新增員工帳號")
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
            st.markdown("### 目前所有員工清單")
            c.execute("SELECT username, name FROM users WHERE role != 'manager'")
            users = c.fetchall()
            for u, n in users:
                st.write(f"- 帳號：`{u}` | 姓名：{n}")
                
        with tab3:
            st.markdown("### 點數獲得總明細與許願審核")
            st.markdown("#### 點數發放紀錄")
            c.execute("SELECT l.date, u.name, l.points, l.reason FROM points_log l JOIN users u ON l.username = u.username ORDER BY l.id DESC LIMIT 20")
            logs = c.fetchall()
            for date, name, pts, reason in logs:
                st.write(f"- `{date[:16]}` | **{name}**獲得 `{pts}點` | 原因：{reason}")
                
            st.markdown("---")
            st.markdown("#### 許願池管理")
            c.execute("SELECT id, username, wish_item, status FROM wishes")
            all_wishes = c.fetchall()
            for wid, wuser, witem, wstatus in all_wishes:
                st.write(f"ID: {wid} | 內容：**{witem}** | 目前狀態：`{wstatus}`")
                
        conn.close()
        
    elif password != "":
        st.error("密碼錯誤，請重新輸入！")
