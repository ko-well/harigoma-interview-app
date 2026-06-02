import streamlit as st
import google.generativeai as genai

# --- ページ設定 ---
st.set_page_config(page_title="AI面接練習アシスタント", layout="wide")

# --- カスタムCSS（游明朝・大きなタブ・桜色ホバー） ---
st.markdown("""
<style>
/* 1. 全体のフォントを游明朝に統一 */
html, body, p, div, span, a, button, h1, h2, h3, h4, h5, h6, label {
    font-family: 'Yu Mincho', '游明朝', 'YuMincho', 'Hiragino Mincho ProN', 'HGS明朝E', serif !important;
}

/* 2. ページ全体の壁紙（和紙風テクスチャ） */
.stApp {
    background-color: #FCFAFA;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.04'/%3E%3C/svg%3E");
    background-attachment: fixed;
}

/* 3. ヘッダーデザイン */
.header-box {
    text-align: center;
    padding: 3rem 1rem;
    background-color: rgba(255, 255, 255, 0.8);
    border-bottom: 2px solid #DB90A0;
    margin-bottom: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.02);
}
.header-title { font-size: 2.2rem; font-weight: 700; color: #3D2D2E; }
.header-subtitle { font-size: 1.1rem; color: #5C4B4D; margin-top: 0.8rem; line-height: 1.6; }

/* 4. 大きくて幅広いタブのデザイン調整 */
.stTabs [data-baseweb="tab-list"] {
    gap: 20px;
    width: 100%;
}
.stTabs [data-baseweb="tab"] {
    height: 70px !important;
    flex-grow: 1;
    background-color: rgba(255, 255, 255, 0.7) !important;
    border: 1px solid #EAE1E3 !important;
    border-radius: 8px 8px 0 0 !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    color: #5C4B4D !important;
    transition: all 0.3s ease;
}
.stTabs [aria-selected="true"] {
    background-color: #DB90A0 !important;
    color: #ffffff !important;
    border-color: #DB90A0 !important;
    box-shadow: 0 -4px 10px rgba(219, 144, 160, 0.15);
}

/* 5. フォームとコンテナ、ボタン */
div[data-testid="stForm"] {
    background-color: rgba(255, 255, 255, 0.9) !important;
    border-radius: 8px !important;
    padding: 30px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important;
}
.interview-box {
    background-color: #FDFEFE;
    padding: 25px;
    border-radius: 8px;
    border-left: 5px solid #DB90A0;
    margin-bottom: 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}

[data-testid="stFormSubmitButton"] button, 
.stButton button,
[data-testid="stLinkButton"] a {
    background-color: #DB90A0 !important;
    color: #ffffff !important;
    border-radius: 6px !important;
    padding: 0.7rem 3rem !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    text-align: center;
    text-decoration: none !important;
    transition: all 0.3s ease;
}
[data-testid="stFormSubmitButton"] button:hover,
.stButton button:hover,
[data-testid="stLinkButton"] a:hover {
    background-color: #C27082 !important;
    transform: translateY(-2px);
}
[data-testid="stLinkButton"] a * {
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# --- タイトル表示 ---
st.markdown('''
<div class="header-box">
    <div class="header-title">🗣️ AI面接練習アシスタント</div>
    <div class="header-subtitle">
        本番の面接で動じないための実践練習の場です。<br>
        お使いの端末（ノートPC・スマホ・タブレット）のマイク機能をオンにして、声で回答を伝えてください。
    </div>
</div>
''', unsafe_allow_html=True)

# --- APIキー設定 ---
st.sidebar.header("🔑 セキュリティ設定")
api_key = st.sidebar.text_input("Gemini APIキー", type="password")

# --- セッション状態の初期化 ---
if 'interview_step' not in st.session_state:
    st.session_state.interview_step = 0  
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'config' not in st.session_state:
    st.session_state.config = {}

# 面接官のペルソナ定義
interviewer_types = {
    "😐 寄り添い・共感型（優しい面接官）": "常に受容的な態度で、求職者の緊張をほぐすように優しく丁寧な口調で質問します。肯定から入る面接官です。",
    "🔍 論理・深掘り型（具体的に追及する面接官）": "回答の『なぜ？』『具体的には？』を重視します。論理的な矛盾や行動の背景を冷静に深く掘り下げる面接官です。",
    "🛡️ ストレス耐性確認型（やや厳しめの面接官）": "少し厳格で冷徹なトーンを保ちます。『それは当社でなくても良いのでは？』といった、あえて少し答えにくい鋭い切り返しを行う面接官です。"
}

# 特訓テーマ10選
trap_questions = [
    "これまでの転職回数やその理由の一貫性について",
    "前職の退職理由（人間関係や環境の不満など）の伝え方について",
    "次の仕事に就くまでの離職期間（ブランク）の過ごし方について",
    "以前の職場での勤務期間が短くなってしまった理由について",
    "年齢と、未経験の職種へ新しく挑戦することへの覚悟について",
    "これまでの仕事の中で経験した一番の失敗や挫折の乗り越え方について",
    "マネジメントや役職の経験が少ない（または無い）点について",
    "新しい職場で、年下の社員が上司や先輩になる場合の対応について",
    "前職と比べて給与や勤務条件が下がる可能性への納得度について",
    "自身の短所（弱み）を、どのように克服しようとしているかについて"
]

# ==================================================
# 【面接設定画面（ステップ0）】
# ==================================================
if st.session_state.interview_step == 0:
    tab1, tab2 = st.tabs(["⚡ 設定を省いて、すぐに面接を始める", "📝 経歴や職種に合わせて、じっくり練習する"])
    
    with tab1:
        st.write("最小限の設定で、今すぐ実戦的な面接の質問に答える練習ができます。")
        with st.form("quick_form"):
            interviewer = st.radio("面接官のタイプを選んでください（必須）", list(interviewer_types.keys()), key="q_interviewer", horizontal=True)
            age = st.selectbox("あなたの年代（任意）", ["選択しない", "20代", "30代", "40代", "50代以上"], key="q_age")
            
            st.markdown("##### 🎯 今回の練習で、特に自信を持って答えられるようにしたいテーマ（複数選択可・選ばなくても可）")
            selected_traps = []
            for t in trap_questions:
                if st.checkbox(t, key=f"q_trap_{t}"):
                    selected_traps.append(t)
                    
            submit_q = st.form_submit_button("⚡ この設定で面接を開始する ➔")
            
        if submit_q:
            if not api_key:
                st.error("⚠️ 左側のメニューにAPIキーを入力してください。")
            else:
                st.session_state.config = {
                    "mode": "クイック面接",
                    "interviewer_style": interviewer_types[interviewer],
                    "name": "あなた",
                    "desired_job": "応募企業が求める職種",
                    "experiences": "一般的なこれまでの職務経歴",
                    "age": age if age != "選択しない" else "未指定",
                    "gender": "未指定",
                    "traps": selected_traps,
                    "free_trap": ""
                }
                st.session_state.interview_step = 1
                st.rerun()

    with tab2:
        st.write("実際の求人内容やご自身の経歴をAIに読み込ませ、あなた専用 of カスタマイズされた面接を行います。")
        with st.form("detailed_form"):
            interviewer = st.radio("面接官のタイプを選んでください（必須）", list(interviewer_types.keys()), key="d_interviewer", horizontal=True)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                user_name = st.text_input("お名前（ニックネーム可）", value="あなた")
            with col_b:
                gender = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)
            with col_c:
                age = st.selectbox("年代", ["20代", "30代", "40代", "50代以上"], key="d_age")
                
            desired_job = st.text_input("今回応募する職種（例：一般事務、製造、営業など）", placeholder="例：医療事務職")
            experiences = st.text_area("これまでのキャリア・経験の簡易版（例：接客業5年、職業訓練でExcelと簿記を3ヶ月学習など）", placeholder="AIがここから質問のヒントを抽出します")
            
            st.markdown("##### 🎯 今回の練習で、特に自信を持って答えられるようにしたいテーマ（複数選択可）")
            selected_traps = []
            for t in trap_questions:
                if st.checkbox(t, key=f"d_trap_{t}"):
                    selected_traps.append(t)
                    
            free_trap = st.text_area("👆上記以外で、面接官にどう伝えたらいいか表現に迷っていることや、突っ込まれたら不安なことがあれば自由に入力してください", 
                                     placeholder="例：前職を体調不良で3ヶ月で辞めてしまったが、現在は完治して元気に働けることを前向きに伝えたい、など")
            
            submit_d = st.form_submit_button("📝 あなた専用の質問を生成して、面接を開始する ➔")
            
        if submit_d:
            if not api_key:
                st.error("⚠️ 左側のメニューにAPIキーを入力してください。")
            else:
                st.session_state.config = {
                    "mode": "じっくり面接",
                    "interviewer_style": interviewer_types[interviewer],
                    "name": user_name,
                    "desired_job": desired_job if desired_job else "応募職種",
                    "experiences": experiences if experiences else "これまでの職務経歴",
                    "age": age,
                    "gender": gender,
                    "traps": selected_traps,
                    "free_
