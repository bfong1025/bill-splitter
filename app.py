import streamlit as st
import datetime
import json

st.set_page_config(page_title="聚會分賬小幫手", page_icon="💰", layout="centered")

# --- 初始化 Session State ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "people" not in st.session_state:
    st.session_state.people = []
if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "editing_index" not in st.session_state:
    st.session_state.editing_index = -1

if "party_name" not in st.session_state:
    st.session_state.party_name = "例如：日本東京 5 日遊"
if "party_date" not in st.session_state:
    st.session_state.party_date = datetime.date.today()
if "curr_count" not in st.session_state:
    st.session_state.curr_count = 1
if "settle_currency" not in st.session_state:
    st.session_state.settle_currency = "HKD"

if "curr_settings" not in st.session_state:
    st.session_state.curr_settings = {0: {'choice': 'HKD', 'custom': '', 'rate': 1.0}}

if "form_reset_counter" not in st.session_state:
    st.session_state.form_reset_counter = 0

# --- 側邊欄：專案儲存與載入功能 ---
st.sidebar.title("📁 專案存檔管理")

save_data = {
    'party_name': st.session_state.party_name,
    'party_date': str(st.session_state.party_date),
    'curr_count': st.session_state.curr_count,
    'settle_currency': st.session_state.settle_currency,
    'curr_settings': st.session_state.curr_settings,
    'people': st.session_state.people,
    'expenses': st.session_state.expenses,
    'party_info': st.session_state.get('party_info', {})
}
json_str = json.dumps(save_data, ensure_ascii=False, indent=4)

st.sidebar.download_button(
    label="💾 儲存專案 (下載JSON)",
    data=json_str,
    file_name=f"{st.session_state.party_name}_project.json",
    mime="application/json"
)

# 載入專案檔案處理
uploaded_file = st.sidebar.file_uploader("📂 載入專案檔案", type=["json"])
if uploaded_file is not None:
    try:
        loaded_data = json.load(uploaded_file)
        
        # 1. 更新各項狀態變數
        st.session_state.party_name = loaded_data.get('party_name', '例如：日本東京 5 日遊')
        
        date_str = loaded_data.get('party_date', str(datetime.date.today()))
        try:
            st.session_state.party_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            st.session_state.party_date = datetime.date.today()
        
        st.session_state.curr_count = int(loaded_data.get('curr_count', 1))
        st.session_state.settle_currency = loaded_data.get('settle_currency', 'HKD')
        
        raw_curr_settings = loaded_data.get('curr_settings', {0: {'choice': 'HKD', 'custom': '', 'rate': 1.0}})
        st.session_state.curr_settings = {int(k): v for k, v in raw_curr_settings.items()}
        
        raw_people = loaded_data.get('people', [])
        formatted_people = []
        for p in raw_people:
            if isinstance(p, str):
                formatted_people.append({'name': p, 'share': 1.0})
            elif isinstance(p, dict):
                p['share'] = float(p.get('share', 1.0))
                formatted_people.append(p)
        st.session_state.people = formatted_people
        
        st.session_state.expenses = loaded_data.get('expenses', [])
        
        currencies_dict = loaded_data.get('party_info', {}).get('currencies', {})
        if not currencies_dict and st.session_state.curr_settings:
            currencies_dict = {}
            for k, v in st.session_state.curr_settings.items():
                c_name = v['custom'] if v['choice'] == '自訂' else v['choice']
                if c_name:
                    currencies_dict[c_name] = v['rate']

        st.session_state.party_info = {
            'name': st.session_state.party_name,
            'date': str(st.session_state.party_date),
            'currencies': currencies_dict,
            'settle_currency': st.session_state.settle_currency
        }
        
        # 2. 強制跳回第一頁
        st.session_state.step = 1
        
        # 3. 透過 rerun 兩次或搭配清除 key 確保輸入框元件強制更新
        st.sidebar.success("專案載入成功！")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"載入失敗：{e}")

# --- 頁面 1：聚會基本資料與多貨幣設定 ---
if st.session_state.step == 1:
    st.title("💰 聚會分賬小幫手 - 基本設定")
    
    # 每次渲染時直接抓取最新的 session_state 確保數值顯示正確
    party_name_input = st.text_input("聚會名稱", value=st.session_state.party_name, key="input_party_name_main")
    st.session_state.party_name = party_name_input
    
    party_date_input = st.date_input("聚會日期", value=st.session_state.party_date, key="input_party_date_main")
    st.session_state.party_date = party_date_input
    
    curr_count_input = st.number_input("涉及貨幣單位數目", min_value=1, max_value=10, value=int(st.session_state.curr_count), step=1, key="input_curr_count_main")
    st.session_state.curr_count = curr_count_input
    
    currencies_dict = {}
    preset_currencies = ['HKD', 'RMB', 'JPY', 'USD', 'EUR', 'GBP', '自訂']
    
    st.subheader("設定貨幣與匯率（相對於最終結算貨幣）")
    for i in range(int(curr_count_input)):
        if i not in st.session_state.curr_settings:
            st.session_state.curr_settings[i] = {'choice': 'HKD', 'custom': '', 'rate': 1.0}
            
        col1, col2 = st.columns(2)
        with col1:
            default_choice = st.session_state.curr_settings[i].get('choice', 'HKD')
            c_choice = st.selectbox(f"貨幣 {i+1}", preset_currencies, index=preset_currencies.index(default_choice) if default_choice in preset_currencies else 0, key=f"curr_choice_{i}")
            st.session_state.curr_settings[i]['choice'] = c_choice
            
            if c_choice == '自訂':
                default_custom = st.session_state.curr_settings[i].get('custom', '')
                c_name = st.text_input(f"輸入自訂代號 {i+1}", value=default_custom, key=f"custom_curr_{i}")
                st.session_state.curr_settings[i]['custom'] = c_name
            else:
                c_name = c_choice
        with col2:
            default_rate = st.session_state.curr_settings[i].get('rate', 1.0)
            rate = st.number_input(f"對結算貨幣匯率", min_value=0.0001, value=float(default_rate), format="%.4f", key=f"rate_{i}")
            st.session_state.curr_settings[i]['rate'] = rate
        
        if c_name:
            currencies_dict[c_name] = rate

    curr_list = list(currencies_dict.keys()) if currencies_dict else ['HKD']
    default_settle_idx = curr_list.index(st.session_state.settle_currency) if st.session_state.settle_currency in curr_list else 0
    settle_select = st.selectbox("最終結算貨幣單位", curr_list, index=default_settle_idx, key="input_settle_curr_main")
    st.session_state.settle_currency = settle_select

    st.subheader("參與人員名單與份額")
    col_p1, col_p2 = st.columns([3, 1])
    with col_p1:
        new_person = st.text_input("輸入朋友名字", key="new_person_input")
    with col_p2:
        new_share = st.number_input("份額", min_value=0.1, value=1.0, step=0.1, format="%.1f", key="new_person_share")

    if st.button("新增朋友"):
        if new_person.strip():
            if not any(p['name'] == new_person.strip() for p in st.session_state.people):
                st.session_state.people.append({'name': new_person.strip(), 'share': float(new_share)})
                st.rerun()
            else:
                st.warning("此名字已存在！")

    if st.session_state.people:
        st.write("當前成員與份額：")
        for p in st.session_state.people:
            st.write(f"- **{p['name']}** (份額: {p['share']:.1f})")
            
        person_to_del = st.selectbox("選擇要刪除的成員", [""] + [p['name'] for p in st.session_state.people], key="del_person_select")
        if st.button("刪除選中成員") and person_to_del:
            st.session_state.people = [p for p in st.session_state.people if p['name'] != person_to_del]
            st.rerun()

    if st.button("下一步：記錄使費 ➡️", type="primary"):
        if not st.session_state.people:
            st.warning("請至少輸入一位參與人員！")
        elif not currencies_dict:
            st.warning("請至少設定一個有效的貨幣單位！")
        else:
            st.session_state.party_info = {
                'name': st.session_state.party_name,
                'date': str(st.session_state.party_date),
                'currencies': currencies_dict,
                'settle_currency': st.session_state.settle_currency
            }
            st.session_state.step = 2
            st.rerun()

# --- 頁面 2：記錄與修改使費 ---
elif st.session_state.step == 2:
    st.title("📝 記錄使費")
    st.write(f"當前聚會：**{st.session_state.party_info.get('name')}**（結算幣：{st.session_state.party_info.get('settle_currency')}）")
    
    edit_idx = st.session_state.editing_index
    if edit_idx != -1 and edit_idx < len(st.session_state.expenses):
        curr_exp = st.session_state.expenses[edit_idx]
        default_name = curr_exp['name']
        try:
            default_date = datetime.datetime.strptime(curr_exp['date'], "%Y-%m-%d").date()
        except:
            default_date = datetime.date.today()
        default_curr = curr_exp['currency']
        default_amount = curr_exp['amount']
        default_note = curr_exp['note']
        form_title = f"正在修改第 {edit_idx+1} 項使費：{default_name}"
        btn_label = "儲存修改"
    else:
        default_name = ""
        default_date = datetime.date.today()
        curr_keys_list = list(st.session_state.party_info.get('currencies', {}).keys())
        default_curr = curr_keys_list[0] if curr_keys_list else 'HKD'
        default_amount = 0.0
        default_note = ""
        form_title = "新增一筆使費"
        btn_label = "新增使費"

    st.subheader(form_title)
    
    rc = st.session_state.form_reset_counter
    
    exp_name = st.text_input("項目名稱", value=default_name, placeholder="例如：晚餐、門票", key=f"input_exp_name_{edit_idx}_{rc}")
    exp_date = st.date_input("消費日期", value=default_date, key=f"input_exp_date_{edit_idx}_{rc}")
    
    curr_keys = list(st.session_state.party_info.get('currencies', {}).keys())
    if not curr_keys:
        curr_keys = ['HKD']
    curr_idx = curr_keys.index(default_curr) if default_curr in curr_keys else 0
    exp_curr = st.selectbox("使用貨幣", curr_keys, index=curr_idx, key=f"input_exp_curr_{edit_idx}_{rc}")
    
    amount = st.number_input("總金額", min_value=0.0, value=float(default_amount), format="%.2f", key=f"input_amount_{edit_idx}_{rc}")
    note = st.text_input("備註 (選填)", value=default_note, key=f"input_note_{edit_idx}_{rc}")

    payer_dict = {}
    split_saved_dict = {}
    if edit_idx != -1 and edit_idx < len(st.session_state.expenses):
        for p_info in curr_exp['payers']:
            payer_dict[p_info['name']] = p_info['amount']
        for s_info in curr_exp['split']:
            split_saved_dict[s_info['name']] = s_info

    st.subheader("1. 誰付了錢（預支設定）")
    payer_amounts = {}
    for p in st.session_state.people:
        p_name = p['name']
        def_val = payer_dict.get(p_name, 0.0)
        payer_amounts[p_name] = st.number_input(f"{p_name} 付了多少金額", min_value=0.0, value=float(def_val), format="%.2f", key=f"payer_{edit_idx}_{rc}_{p_name}")

    st.subheader("2. 攤分設定（「總額均分」會自動依成員份額比例計算）")
    split_details = []
    for p in st.session_state.people:
        p_name = p['name']
        p_share = p['share']
        saved_s = split_saved_dict.get(p_name, None)
        def_chk = True if (edit_idx == -1 or saved_s is not None) else False
        def_mode_idx = saved_s['mode'] if saved_s else 0
        def_val = saved_s['value'] if saved_s else 0.0

        col1, col2, col3 = st.columns([1.5, 2, 2])
        with col1:
            is_checked = st.checkbox(f"{p_name} (份額:{p_share:.1f})", value=def_chk, key=f"split_chk_{edit_idx}_{rc}_{p_name}")
        with col2:
            modes = ['總額均分', '餘額均分', '自訂金額']
            mode = st.selectbox("模式", modes, index=def_mode_idx, key=f"split_mode_{edit_idx}_{rc}_{p_name}", label_visibility="collapsed")
        with col3:
            val = st.number_input("自訂值", min_value=0.0, value=float(def_val), format="%.2f", key=f"split_val_{edit_idx}_{rc}_{p_name}", label_visibility="collapsed")
        
        if is_checked:
            mode_idx = 0 if mode == '總額均分' else (1 if mode == '餘額均分' else 2)
            split_details.append({'name': p_name, 'share': p_share, 'mode': mode_idx, 'value': val})

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(btn_label, type="primary"):
            payers_data = [{'name': p_name, 'amount': amt} for p_name, amt in payer_amounts.items() if amt > 0]
            total_payer_amount = sum([p['amount'] for p in payers_data])

            if not exp_name.strip() or amount <= 0:
                st.error("請填寫正確的項目名稱與金額！")
            elif not payers_data:
                st.error("請至少填寫一位付錢人的預支金額！")
            elif abs(amount - total_payer_amount) > 0.01:
                st.error(f"金額不吻合！ 總金額為 ${amount:.2f}，但「誰付了錢」的總數為 ${total_payer_amount:.2f}。兩者必須完全相同方可儲存！")
            elif not split_details:
                st.error("請至少勾選一位參與分攤的人！")
            else:
                exp_item = {
                    'date': str(exp_date),
                    'name': exp_name.strip(),
                    'payers': payers_data,
                    'amount': amount,
                    'currency': exp_curr,
                    'split': split_details,
                    'note': note.strip()
                }
                
                if st.session_state.editing_index == -1:
                    st.session_state.expenses.append(exp_item)
                    st.success(f"成功新增項目：{exp_name}")
                else:
                    st.session_state.expenses[st.session_state.editing_index] = exp_item
                    st.success(f"成功更新項目：{exp_name}")
                    st.session_state.editing_index = -1
                
                st.session_state.form_reset_counter += 1
                st.rerun()
                
    with col_btn2:
        if st.session_state.editing_index != -1:
            if st.button("取消修改"):
                st.session_state.editing_index = -1
                st.rerun()

    if st.session_state.expenses:
        st.subheader("📜 已記錄的使費清單")
        
        indices_to_delete = []
        for idx, exp in enumerate(st.session_state.expenses):
            col_chk, col_info, col_edit = st.columns([1, 4, 1])
            with col_chk:
                is_selected = st.checkbox("選取", key=f"del_chk_{idx}", label_visibility="collapsed")
                if is_selected:
                    indices_to_delete.append(idx)
            with col_info:
                st.write(f"**{exp['name']}** - {exp['amount']:.2f} {exp['currency']} ({exp['date']}) | 備註: {exp['note'] or '無'}")
            with col_edit:
                if st.button("修改", key=f"edit_btn_{idx}"):
                    st.session_state.editing_index = idx
                    st.rerun()
        
        if st.button("刪除所選記錄", type="secondary"):
            if indices_to_delete:
                for index in sorted(indices_to_delete, reverse=True):
                    if st.session_state.editing_index == index:
                        st.session_state.editing_index = -1
                    st.session_state.expenses.pop(index)
                st.success("已成功刪除選中的記錄！")
                st.rerun()
            else:
                st.warning("請先勾選要刪除的記錄！")

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ 返回修改使費"):
            st.session_state.editing_index = -1
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("下一步：檢視結算 ➡️", type="primary"):
            st.session_state.editing_index = -1
            st.session_state.step = 3
            st.rerun()

# --- 頁面 3：最終結算報表 ---
elif st.session_state.step == 3:
    st.title("📊 最終結算報表與轉賬指引")
    
    party_info = st.session_state.get('party_info', {
        'name': st.session_state.party_name,
        'date': str(st.session_state.party_date),
        'settle_currency': st.session_state.settle_currency
    })
    currencies = party_info.get('currencies', {})
    settle_curr = party_info.get('settle_currency', 'HKD')
    
    people_names = [p['name'] for p in st.session_state.people]
    balances = {p: 0.0 for p in people_names}
    total_spent = {p: 0.0 for p in people_names}

    st.subheader("📜 全部使費明細總覽")
    if not st.session_state.expenses:
        st.info("目前尚無任何支出記錄。")
    else:
        for idx, exp in enumerate(st.session_state.expenses, 1):
            curr = exp['currency']
            rate = currencies.get(curr, 1.0)
            settle_amount = exp['amount'] * rate

            for p in exp['payers']:
                balances[p['name']] += p['amount'] * rate

            splits = exp['split']
            custom_total = sum([s['value'] for s in splits if s['mode'] == 2])
            
            total_share_mode_0 = sum([s.get('share', 1.0) for s in splits if s['mode'] == 0])
            total_share_mode_1 = sum([s.get('share', 1.0) for s in splits if s['mode'] == 1])

            remaining_amount = settle_amount - custom_total
            if remaining_amount < 0: remaining_amount = 0

            for s in splits:
                name = s['name']
                share = s.get('share', 1.0)
                item_share_amount = 0.0
                
                if s['mode'] == 0:
                    if total_share_mode_0 > 0:
                        item_share_amount = (settle_amount / total_share_mode_0) * share
                elif s['mode'] == 1:
                    if total_share_mode_1 > 0:
                        item_share_amount = (remaining_amount / total_share_mode_1) * share
                elif s['mode'] == 2:
                    item_share_amount = s['value'] * rate

                balances[name] -= item_share_amount
                total_spent[name] += item_share_amount

            payer_str = ", ".join([f"{p['name']} (${p['amount']:.2f})" for p in exp['payers']])
            st.text(f"{idx}. [{exp['date']}] {exp['name']} | 原幣: {exp['amount']:.2f} {curr} -> 結算幣: {settle_amount:.2f} {settle_curr}\n   預支: {payer_str} | 備註: {exp['note'] or '無'}")

    st.subheader("📊 每人實際消費統計")
    for p in people_names:
        st.write(f"• **{p}**: 實際消費總額 = **${total_spent[p]:.2f} {settle_curr}**")

    st.subheader("💸 最終結算與轉賬指引")
    debtors = [[p, -bal] for p, bal in balances.items() if bal < -0.01]
    creditors = [[p, bal] for p, bal in balances.items() if bal > 0.01]

    transfer_results = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        d_name, d_amt = debtors[i]
        c_name, c_amt = creditors[j]
        settled = min(d_amt, c_amt)
        transfer_results.append(f"👉 **{d_name}** 應轉賬給 **{c_name}**：**${settled:.2f} {settle_curr}**")
        debtors[i][1] -= settled
        creditors[j][1] -= settled
        if debtors[i][1] < 0.01: i += 1
        if creditors[j][1] < 0.01: j += 1

    if not transfer_results:
        st.success("大家已經互不相欠，無需轉賬！")
    else:
        for t in transfer_results:
            st.write(t)

    full_report = f"========================================\n"
    full_report += f"          聚會分賬結算報表          \n"
    full_report += f"========================================\n"
    full_report += f"【聚會名稱】: {party_info.get('name')}\n"
    full_report += f"【聚會日期】: {party_info.get('date')}\n"
    full_report += f"【結算貨幣】: {settle_curr}\n\n"
    full_report += "--- 📜 支出明細記錄 ---\n"
    for idx, exp in enumerate(st.session_state.expenses, 1):
        payer_desc = ", ".join([f"{p['name']} ({p['amount']:.2f} {exp['currency']})" for p in exp['payers']])
        full_report += f"{idx}. 日期: {exp['date']} | 項目: {exp['name']} | 金額: {exp['amount']:.2f} {exp['currency']} | 預支人: {payer_desc} | 備註: {exp['note'] or '無'}\n"
    full_report += "\n--- 💸 最終結算與轉賬指引 ---\n" + "\n".join(transfer_results)

    st.download_button(
        label="📥 下載完整結算報表 (TXT)",
        data=full_report,
        file_name=f"{party_info.get('name', 'party')}_{party_info.get('date')}.txt",
        mime="text/plain"
    )

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("⬅️ 返回修改使費"):
            st.session_state.step = 2
            st.rerun()
    with col_r2:
        if st.button("🆕 輸入新聚會", type="secondary"):
            st.session_state.step = 1
            st.session_state.people = []
            st.session_state.expenses = []
            st.session_state.editing_index = -1
            st.session_state.party_name = "例如：日本東京 5 日遊"
            st.session_state.party_date = datetime.date.today()
            st.session_state.curr_count = 1
            st.session_state.settle_currency = "HKD"
            st.session_state.curr_settings = {0: {'choice': 'HKD', 'custom': '', 'rate': 1.0}}
            st.rerun()