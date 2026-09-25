import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import re

# --- AIモデルの自動フォールバック（切り替え）関数 ---
# 最新版でエラーが起きた場合、自動的に従来版へ切り替えてアプリの停止を防ぎます。
def generate_with_fallback(prompt_text):
    try:
        # 第一候補：最新モデル
        model = genai.GenerativeModel('gemini-3.8-flash')
        return model.generate_content(prompt_text)
    except Exception as e_new:
        try:
            # 失敗した場合、自動的に従来のモデルに切り替える
            model_old = genai.GenerativeModel('gemini-2.5-flash')
            return model_old.generate_content(prompt_text)
        except Exception as e_old:
            # どちらも失敗した場合は詳細なエラーを返す
            raise Exception(f"最新版エラー: {e_new} / 従来版エラー: {e_old}")

# --- ページ設定 ---
st.set_page_config(page_title="AI面接練習アシスタント", layout="wide")

# --- カスタムCSS（壁紙・明朝体・桜色テーマ・スマホ対応） ---
st.markdown("""
<style>
/* 1. 全体のフォントを游明朝に統一 */
html, body, p, div, a, button, h1, h2, h3, h4, h5, h6, label {
    font-family: 'Yu Mincho', '游明朝', 'YuMincho', 'Hiragino Mincho ProN', 'HGS明朝E', serif !important;
}

/* 2. ページ全体の壁紙（和紙風テクスチャ） */
.stApp {
    background-color: #FCFAFA;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.04'/%3E%3C/svg%3E");
    background-attachment: fixed;
}

/* 3. ヘッダーデザイン（PC用） */
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
.stTabs [data-baseweb="tab-list"] { gap: 20px; width: 100%; }
.stTabs [data-baseweb="tab"] {
    height: 70px !important; flex-grow: 1; background-color: rgba(255, 255, 255, 0.7) !important;
    border: 1px solid #EAE1E3 !important; border-radius: 8px 8px 0 0 !important;
    font-size: 1.2rem !important; font-weight: 600 !important; color: #5C4B4D !important; transition: all 0.3s ease;
}
.stTabs [aria-selected="true"] { background-color: #DB90A0 !important; color: #ffffff !important; border-color: #DB90A0 !important; box-shadow: 0 -4px 10px rgba(219, 144, 160, 0.15); }

/* 5. フォームとコンテナのデザイン */
div[data-testid="stForm"] { background-color: rgba(255, 255, 255, 0.9) !important; border-radius: 8px !important; padding: 30px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important; }
.interview-box { background-color: #FDFEFE; padding: 25px; border-radius: 8px; border-left: 5px solid #DB90A0; margin-bottom: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); font-size: 1.05rem; line-height: 1.8; }
.story-box { background-color: rgba(255, 255, 255, 0.7); padding: 25px; border-radius: 8px; border: 2px solid #EAE1E3; margin-bottom: 20px; font-size: 1.05rem; line-height: 1.8; }

/* 面接官の証明写真風アバター設定 */
.interviewer-avatar { display: block; margin: 0 auto 5px auto; width: 100px; height: 120px; object-fit: cover; border-radius: 12px; border: 3px solid #DB90A0; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }

h1, h2, h3 { color: #3D2D2E !important; }

/* 6. スマートフォン向けの画面表示設定（レスポンシブ対応） */
@media screen and (max-width: 768px) {
    .header-title { font-size: 1.5rem !important; }
    .header-subtitle { font-size: 0.95rem !important; margin-top: 0.8rem !important; }
    .header-box { padding: 2rem 1rem !important; }
    div[data-testid="stForm"] { padding: 15px !important; }
    .interview-box, .story-box { padding: 15px !important; font-size: 0.95rem !important; }
    .interviewer-avatar { width: 80px; height: 96px; }
    h2 { font-size: 1.3rem !important; } h3 { font-size: 1.1rem !important; margin-bottom: 0.5rem !important; }
    p, label { font-size: 0.95rem !important; line-height: 1.6 !important; }
    .stTabs [data-baseweb="tab"] { height: auto !important; padding: 10px !important; font-size: 1rem !important; }
    [data-testid="stFormSubmitButton"] button, .stButton button, [data-testid="stDownloadButton"] button, [data-testid="stLinkButton"] a { padding: 0.6rem 1rem !important; font-size: 1rem !important; width: 100% !important; text-align: center; margin-bottom: 10px !important; }
}

/* 7. ボタンのデザイン（PC用ベース） */
[data-testid="stFormSubmitButton"] button, .stButton button, [data-testid="stDownloadButton"] button, [data-testid="stLinkButton"] a { background-color: #DB90A0 !important; color: #ffffff !important; border-radius: 6px !important; padding: 0.7rem 3rem !important; font-size: 1.1rem !important; font-weight: 600 !important; width: 100% !important; text-align: center; text-decoration: none !important; transition: all 0.3s ease; }
[data-testid="stFormSubmitButton"] button:hover, .stButton button:hover, [data-testid="stDownloadButton"] button:hover, [data-testid="stLinkButton"] a:hover { background-color: #C27082 !important; transform: translateY(-2px); }
[data-testid="stLinkButton"] a *, [data-testid="stDownloadButton"] button * { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- タイトル表示 ---
st.markdown('''
<div class="header-box">
    <div class="header-title">🗣️ AI面接練習アシスタント</div>
    <div class="header-subtitle">
        本番の面接で動じないための実践練習の場です。<br>
        お互いに「声」でやり取りする音声モードと、静かな場所で使える文字モードを切り替えて練習できます。
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

# 面接官のアバター
avatar_urls = {
    "👨‍💼 若手男性": "https://images.unsplash.com/photo-1552374196-c4e7ffc6e126?auto=format&fit=crop&w=150&h=150&q=80",
    "👩‍💼 若手女性": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=150&h=150&q=80",
    "👴 ベテラン男性": "https://images.unsplash.com/photo-1506803682981-6e718a9dd3ee?auto=format&fit=crop&w=150&h=150&q=80",
    "👵 ベテラン女性": "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=150&h=150&q=80",
    "👤 アイコン（写真なし）": "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"
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
            avatar = st.selectbox("面接官の見た目（写真）を選んでください", list(avatar_urls.keys()), key="q_avatar")
            age = st.selectbox("あなたの年代（任意）", ["選択しない", "20代", "30代", "40代", "50代以上"], key="q_age")
            
            st.markdown("##### 🫣 弱点特訓：一番聞かれたくない、痛い質問")
            dreaded_q = st.text_input("面接で一番恐れている質問があれば入力してください。AIがあえてその質問を投げかけます。", placeholder="例：なぜ前職を半年で辞めたのですか？")
            
            st.markdown("##### 🎯 その他、対策したいテーマ（複数選択可）")
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
                    "avatar": avatar,
                    "name": "あなた",
                    "desired_job": "応募企業が求める職種",
                    "experiences": "一般的なこれまでの職務経歴",
                    "age": age if age != "選択しない" else "未指定",
                    "gender": "未指定",
                    "traps": selected_traps,
                    "dreaded_question": dreaded_q,
                    "free_trap": ""
                }
                st.session_state.interview_step = 1
                st.rerun()

    with tab2:
        st.write("実際の求人内容やご自身の経歴をAIに読み込ませ、あなた専用のカスタマイズされた面接を行います。")
        with st.form("detailed_form"):
            interviewer = st.radio("面接官のタイプを選んでください（必須）", list(interviewer_types.keys()), key="d_interviewer", horizontal=True)
            avatar = st.selectbox("面接官の見た目（写真）を選んでください", list(avatar_urls.keys()), key="d_avatar")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                user_name = st.text_input("お名前（ニックネーム可）", value="あなた")
            with col_b:
                gender = st.radio("性別", ["男性", "女性", "回答しない"], horizontal=True)
            with col_c:
                age = st.selectbox("年代", ["20代", "30代", "40代", "50代以上"], key="d_age")
                
            desired_job = st.text_input("今回応募する職種（例：一般事務、製造、営業など）", placeholder="例：医療事務職")
            experiences = st.text_area("これまでのキャリア・経験の簡易版（例：接客業5年、職業訓練でExcelと簿記を3ヶ月学習など）", placeholder="AIがここから質問のヒントを抽出します")
            
            st.markdown("##### 🫣 弱点特訓：一番聞かれたくない、痛い質問")
            dreaded_d = st.text_input("面接で一番恐れている質問があれば入力してください。AIがあえてその質問を投げかけます。", placeholder="例：空白の3年間は何をしていたのですか？")
            
            st.markdown("##### 🎯 その他、対策したいテーマ（複数選択可）")
            selected_traps = []
            for t in trap_questions:
                if st.checkbox(t, key=f"d_trap_{t}"):
                    selected_traps.append(t)
                    
            free_trap = st.text_area("👆上記以外で、面接官にどう伝えたらいいか表現に迷っていることや、本音があれば入力してください", 
                                     placeholder="例：前職を体調不良で辞めたが、今は元気なことを前向きに伝えたい")
            
            submit_d = st.form_submit_button("📝 あなた専用の質問を生成して、面接を開始する ➔")
            
        if submit_d:
            if not api_key:
                st.error("⚠️ 左側のメニューにAPIキーを入力してください。")
            else:
                st.session_state.config = {
                    "mode": "じっくり面接",
                    "interviewer_style": interviewer_types[interviewer],
                    "avatar": avatar,
                    "name": user_name,
                    "desired_job": desired_job if desired_job else "応募職種",
                    "experiences": experiences if experiences else "これまでの職務経歴",
                    "age": age,
                    "gender": gender,
                    "traps": selected_traps,
                    "dreaded_question": dreaded_d,
                    "free_trap": free_trap
                }
                st.session_state.interview_step = 1
                st.rerun()

# ==================================================
# 【面接進行画面（ステップ1）】
# ==================================================
elif st.session_state.interview_step == 1:
    st.markdown(f"### 📋 面接進行中（設定モード：{st.session_state.config['mode']}）")
    
    st.markdown("##### ⚙️ 練習スタイルを選択")
    interview_mode = st.radio(
        "モード切替",
        ["🗣️ 音声モード（主：AIが喋ります）", "⌨️ テキストモード（副：文字のみ）"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.write("---")
    
    avatar_url = avatar_urls[st.session_state.config.get("avatar", "👤 アイコン（写真なし）")]
    st.markdown(f"""
    <div style="text-align: center;">
        <img src="{avatar_url}" class="interviewer-avatar" alt="面接官">
        <div style="color: #5C4B4D; font-weight: bold; margin-bottom: 15px;">担当面接官</div>
    </div>
    """, unsafe_allow_html=True)
    
    if len(st.session_state.chat_history) == 0:
        genai.configure(api_key=api_key)
        
        setup_prompt = f"""
        あなたは、企業の採用担当者です。これから求職者（{st.session_state.config['name']}さん、{st.session_state.config['age']}、{st.session_state.config['gender']}）の採用面接を行います。
        
        【面接官としてのあなたの性格・役割】
        {st.session_state.config['interviewer_style']}
        
        【求職者の情報】
        ・応募職種：{st.session_state.config['desired_job']}
        ・これまでの経験：{st.session_state.config['experiences']}
        ・特に重点的に対策したいテーマ：{', '.join(st.session_state.config['traps'])}
        ・伝え方に迷っている本音：{st.session_state.config['free_trap']}
        ・【★最重要★ 求職者が一番恐れている・聞かれたくない質問】：{st.session_state.config['dreaded_question']}
        
        【面接の基本ルール】
        ・まずは、求職者に対して『最初の質問（1回目の質問）』を1つだけ投げかけます。
        ・もし上記の【求職者が一番恐れている質問】が入力されている場合は、面接官の自然な口調にアレンジした上で、必ずその内容を「最初の質問」としてズバリ投げかけてください。
        ・入力がない場合は、経験や応募職種に基づいた自然な質問をしてください。
        ・挨拶と最初の質問以外、余計な解説やナレーションは一切出力しないでください。
        """
        
        with st.spinner("面接官が入室しています..."):
            try:
                # ★ 新しい自動フォールバック関数を使って生成 ★
                response = generate_with_fallback(setup_prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"面接官の起動に失敗しました。キーを確認してください。 エラー詳細: {e}")

    for idx, msg in enumerate(st.session_state.chat_history):
        if msg["role"] == "assistant":
            st.markdown(f"<div class='interview-box'><strong>👤 AI面接官：</strong><br>{msg['content']}</div>", unsafe_allow_html=True)
            
            if "音声モード" in interview_mode and idx == len(st.session_state.chat_history) - 1:
                clean_text = re.sub(r'[*#]', '', msg['content'])
                escaped_text = clean_text.replace('\n', ' ').replace("'", "\\'").replace('"', '\\"')
                
                js_code = f"""
                <style>body {{ margin: 0; padding: 0; overflow: hidden; }}</style>
                <div style="text-align: right; padding-right: 5px; margin-bottom: 20px;">
                    <button onclick="playVoice()" style="background-color: #DB90A0; color: white; border: none; padding: 8px 15px; border-radius: 5px; font-weight: bold; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1); font-family: sans-serif;">
                        🔊 面接官の声を再生する
                    </button>
                </div>
                <script>
                    function playVoice() {{
                        window.speechSynthesis.cancel(); 
                        const msg = new SpeechSynthesisUtterance('{escaped_text}');
                        msg.lang = 'ja-JP';
                        msg.rate = 1.0; 
                        window.speechSynthesis.speak(msg);
                    }}
                    playVoice();
                </script>
                """
                components.html(js_code, height=60)
        else:
            st.markdown(f"<div style='background-color:#EAE1E3; padding:15px; border-radius:8px; margin-bottom:20px;'><strong>💬 {st.session_state.config['name']}さんの回答：</strong><br>{msg['content']}</div>", unsafe_allow_html=True)

    user_turns = [m for m in st.session_state.chat_history if m["role"] == "user"]
    
    if len(user_turns) < 2:
        with st.form("reply_form", clear_on_submit=True):
            input_placeholder = "📱スマホはキーボードのマイクマーク、💻PCは「Winキー＋H」（MacはFnキー2回）で音声入力できます" if "音声モード" in interview_mode else "💻 文字を入力して回答してください"
            
            st.info(f"💡 **音声入力のヒント:** {input_placeholder}")
            
            user_reply = st.text_input(
                "あなたの回答入力欄", 
                placeholder="ここに入力してください（例：はい、お答えいたします。 / 私はこれまでに〜）",
                label_visibility="collapsed"
            )
            col_btn1, col_btn2 = st.columns([4, 1])
            with col_btn1:
                submit_reply = st.form_submit_button("💬 回答を面接官に伝える（送信）")
            with col_btn2:
                exit_early = st.form_submit_button("🚪 面接を終了する")

        if submit_reply and user_reply:
            st.session_state.chat_history.append({"role": "user", "content": user_reply})
            
            genai.configure(api_key=api_key)
            current_turn = len([m for m in st.session_state.chat_history if m["role"] == "user"])
            
            if current_turn == 1:
                next_prompt = f"""
                求職者から1回目の回答が届きました。
                【面接官としての性格】\n{st.session_state.config['interviewer_style']}
                【これまでの会話履歴】\n{st.session_state.chat_history}
                【指示】\n1. 今回の求職者の回答に対して、採用担当者・キャリアコンサルタントの目線から、その場で『良かった点』と『悪かった点（改善点）』をバランスよく丁寧に挙げ、具体的なアドバイスを伝えてください。\n2. もし求職者が「一番恐れている質問」に対して回答していた場合、その不安を払拭するような前向きな言い換えのコツも添えてください。\n3. アドバイスの直後に、今回の回答内容をさらに深掘りする『2つ目の質問』を行ってください。\n\n※HTMLタグは厳禁です。
                """
            else:
                next_prompt = f"""
                求職者から2回目の回答が届きました。面接の最終質問への回答となります。\n【これまでの会話履歴】\n{st.session_state.chat_history}\n【指示】\n1. 今回の回答に対しても、同様に『良かった点』と『悪かった点（改善点）』をバランスよく挙げ、具体的なアドバイスを伝えてください。\n2. アドバイスが終わりましたら、『以上で本日の面接練習はすべて終了となります。大変お疲れ様でした。』と伝え、締めくくってください。\n\n※HTMLタグは厳禁です。
                """
                
            with st.spinner("面接官があなたの回答をじっくり聴いています..."):
                try:
                    # ★ 新しい自動フォールバック関数を使って生成 ★
                    response = generate_with_fallback(next_prompt)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                    st.rerun()
                except Exception as e:
                    st.error(f"回答の処理中にエラーが発生しました: {e}")
                
        if exit_early:
            st.session_state.interview_step = 2
            st.rerun()
    else:
        st.success("✨ すべての面接質問が終了しました！総合フィードバックを生成しましょう。")
        if st.button("📊 総合フィードバック（改善レポート）を見る ➔"):
            st.session_state.interview_step = 2
            st.rerun()

# ==================================================
# 【総合フィードバック画面（ステップ2）】
# ==================================================
elif st.session_state.interview_step == 2:
    st.progress(1.0)
    st.success(f"✨ 大変お疲れ様でした！{st.session_state.config['name']}さんのための改善レポートが完成しました。")
    
    genai.configure(api_key=api_key)
    
    final_prompt = f"""
    あなたはプロのキャリアコンサルタントです。実施されたAI面接練習の全ログを分析し、総合フィードバックを作成してください。\n\n【面接の全履歴】\n{st.session_state.chat_history}\n\n【出力構成】\n1. 【今回の面接の総括】\n2. 【徹底解説：突っ込まれた質問への最適な答え方】（言い換えの模範解答例）\n3. 【次への具体的なステップ】\n\n※HTMLタグは厳禁です。
    """
    
    with st.spinner("⏳ キャリアコンサルタントが全体の振り返りレポートを作成しています..."):
        try:
            # ★ 新しい自動フォールバック関数を使って生成 ★
            response = generate_with_fallback(final_prompt)
            st.markdown("<div class='story-box'>", unsafe_allow_html=True)
            st.write(response.text)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.download_button(
                label="📝 面接改善レポートを保存（ダウンロード）する",
                data=f"【面接練習改善レポート】\n\n{response.text}",
                file_name="面接練習改善レポート.txt",
                mime="text/plain"
            )
        except Exception as e:
            st.error(f"レポートの生成に失敗しました。 エラー詳細: {e}")
            
    st.markdown("---")
    if st.button("🔄 最初に戻って別の条件で練習する"):
        st.session_state.interview_step = 0
        st.session_state.chat_history = []
        st.session_state.config = {}
        st.rerun()

# ==================================================
# 共通最下部：ポータルサイトへの戻りボタン
# ==================================================
st.markdown("---")
st.link_button("🏠 C.HARIGOMA キャリア支援ポータルへ戻る", "https://harigoma-career.streamlit.app/")
