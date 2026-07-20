import random
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="『信長の野望 真戦』部隊対戦シミュレータ", layout="centered"
)

st.title("⚔️ 部隊対戦シミュレータ")
st.caption("自軍 vs 敵軍 8ターン対戦・勝率検証ツール（Excelデータベース完全統合版）")

# --- Excelから拡張した伝授・事件戦法データベース ---
# 構造: "戦法名": [発動確率(%), ダメージ率(%), "品質", "タイプ"]
SKILL_DATABASE = {
    "（なし）": [0, 0, "-", "-"],
    # ─── S級戦法 ───
    "意気衝天": [45, 0, "S", "指揮"],       # 封印メインのためシミュレータ上はダメージ0
    "千軍一掃": [40, 100, "S", "アクティブ"],  # 固有連携等があるがベースダメ
    "万矢斉射": [40, 130, "S", "アクティブ"],
    "破陣砕堅": [35, 158, "S", "アクティブ"],
    "避実撃虚": [50, 185, "S", "アクティブ"],
    "一騎当千": [30, 108, "S", "突撃"],
    "百騎劫営": [40, 162, "S", "突撃"],
    "折衝禦侮": [45, 0, "S", "突撃"],
    "杯中蛇影": [50, 153, "S", "アクティブ"],
    "四面楚歌": [50, 144, "S", "アクティブ"],
    "奪魂挟魄": [55, 0, "S", "アクティブ"],   # ステータス奪取
    "八門金鎖の陣": [100, 0, "S", "陣法"],
    "白馬義従": [100, 0, "S", "兵種"],
    # ─── A級戦法 ───
    "強攻": [45, 0, "A", "パッシブ"],        # 連撃付与
    "手起刀落": [30, 214, "A", "突撃"],
    "落鳳": [35, 250, "A", "アクティブ"],
    "縦兵掠奪": [35, 172, "A", "アクティブ"],
    "軽勇飛燕": [40, 84, "A", "アクティブ"],   # 多段ヒット系ベース
    "両刀大斧": [35, 180, "A", "アクティブ"],
    "御敵屏障": [100, 0, "A", "指揮"],
    "坐守孤城": [45, 0, "A", "アクティブ"],   # 回復
    "機略縦横": [45, 58, "A", "アクティブ"],
    "風声鶴唳": [45, 105, "A", "アクティブ"],
    "天降火雨": [50, 118, "A", "アクティブ"],
    "後発制人": [100, 52, "A", "パッシブ"],   # 反撃ベース
}
SKILL_LIST = list(SKILL_DATABASE.keys())

# --- 武将データベース ---
# 構造： "武将名": [攻撃力, 防御力, "固有戦法名", 発動率%, ダメージ率%]
OFFICER_DATABASE = {
    # 織田
    "織田信長": [231, 161, "新生", 40, 160],
    "明智光秀": [183, 140, "時は今", 35, 150],
    "まつ": [157, 71, "松柏之操", 35, 120],
    "帰蝶": [161, 99, "帰蝶の舞", 40, 130],
    "荒木村重": [158, 91, "形影相弔", 35, 120],
    "佐久間信盛": [173, 95, "陣前無我", 35, 110],
    "妻木煕子": [116, 55, "内助の賢", 35, 100],
    "柴田勝家": [162, 208, "かかれ柴田", 35, 160],
    "前田慶次": [127, 206, "天下御免", 35, 150],
    "前田利家": [158, 186, "槍の又左", 40, 130],
    "明智秀満": [147, 129, "湖水渡り", 35, 120],
    "稲葉一鉄": [175, 101, "一徹の意志", 35, 120],
    "森可成": [145, 189, "攻めの三左", 40, 140],
    "お市": [128, 64, "夢幻泡影", 35, 110],
    # 豊臣
    "黒田官兵衛": [167, 113, "水の如し", 35, 158],
    "豊臣秀吉": [180, 111, "千成瓢箪", 40, 140],
    "お初": [143, 63, "同気連枝", 35, 120],
    "ねね": [152, 58, "比翼連理", 35, 110],
    "加藤清正": [158, 191, "破竹の勢い", 35, 150],
    "宮部継潤": [153, 72, "積水成淵", 35, 120],
    "成田甲斐": [145, 164, "東国無双の麗", 40, 130],
    "竹中半兵衛": [150, 89, "十面埋伏", 35, 160],
    "福島正則": [151, 206, "七本槍筆頭", 35, 150],
    "蜂須賀小六": [126, 166, "楼岸一番", 35, 130],
    "可児才蔵": [97, 183, "笹の才蔵", 40, 140],
    "加藤嘉明": [135, 146, "剛毅木訥", 35, 120],
    # 徳川
    "酒井忠次": [187, 187, "破陣乱舞", 35, 150],
    "徳川家康": [231, 155, "三河魂", 40, 140],
    "本多忠勝": [169, 229, "古今独歩", 35, 160],
    "お江": [154, 65, "風姿綽約", 35, 110],
    "榊原康政": [155, 182, "無想掃討", 35, 140],
    "松平信康": [160, 179, "勇志不抜", 35, 130],
    "高力清長": [180, 104, "仏の高力", 35, 110],
    "本多正信": [83, 43, "非常の器", 40, 120],
    # 武田
    "山県昌景": [169, 224, "武田之赤備", 35, 160],
    "真田昌幸": [176, 105, "表裏比興", 35, 150],
    "武田信玄": [202, 191, "風林火山", 40, 150],
    "甘利虎泰": [163, 176, "剛の武者", 35, 130],
    "山本勘助": [155, 103, "啄木鳥", 35, 140],
    "内藤昌豊": [154, 101, "死灰復然", 35, 120],
    "馬場信春": [203, 161, "鬼美濃", 35, 140],
    "板垣信方": [165, 88, "先手必勝", 35, 120],
    "飯富虎昌": [136, 203, "甲山猛虎", 35, 140],
    "一条信龍": [153, 156, "不屈の精神", 35, 120],
    "岡部元信": [131, 134, "洞察反撃", 35, 120],
    "原虎胤": [108, 185, "夜叉美濃", 35, 130],
    "諏訪姫": [143, 75, "諏訪の光", 35, 110],
    # 上杉
    "柿崎景家": [157, 222, "越後二天", 35, 150],
    "上杉謙信": [186, 247, "軍神", 40, 170],
    "宇佐美定満": [153, 112, "越後流軍学", 35, 130],
    "甘粕景持": [147, 186, "疾風怒濤", 35, 140],
    "太田資正": [159, 179, "三楽犬", 35, 140],
    "小島弥太郎": [104, 193, "鬼小島", 35, 130],
    "仙桃院": [148, 67, "献身", 35, 110],
    "千坂景親": [164, 161, "耐苦鍛錬", 35, 130],
    "樋口兼豊": [139, 89, "密報通暁", 35, 120],
    "河田長親": [146, 69, "先制攻撃", 35, 120],
    # 群雄
    "今川義元": [194, 174, "海道一", 35, 140],
    "松永久秀": [173, 113, "梟雄の計", 35, 150],
    "長宗我部元親": [187, 188, "鬼若子", 35, 140],
    "陶晴賢": [166, 185, "冷徹無情", 35, 140],
    "北条綱成": [165, 224, "地黄八幡", 35, 150],
    "本願寺顕如": [182, 119, "一切皆空", 35, 130],
    "毛利元就": [180, 100, "百万一心", 40, 160],
    "立花道雪": [173, 193, "電光雷轟", 35, 150],
    "立花誾千代": [163, 200, "疾風迅雷", 35, 140],
    "伊達晴宗": [156, 181, "掃疑平乱", 35, 130],
    "高橋紹運": [184, 190, "豊後の戦陣", 35, 140],
    "寿桂尼": [148, 35, "尼御台", 35, 100],
    "真柄直隆": [108, 202, "怪力無双", 35, 130],
    "浅井長政": [161, 184, "信義貫徹", 35, 140],
    "大祝鶴": [144, 171, "月華鶴影", 35, 120],
    "大内義隆": [172, 78, "末世の道者", 35, 110],
    "島津貴久": [160, 100, "旋乾転坤", 35, 130],
    "北条氏康": [182, 137, "相模の獅子", 35, 150],
    "鈴木佐大夫": [151, 179, "弾嵐雨霰", 35, 140],
    "安宅冬康": [145, 72, "一舟軒", 35, 110],
    "安東愛季": [174, 110, "斗星北天", 35, 130],
    "伊達輝宗": [153, 80, "樽俎折衝", 35, 120],
    "斎藤義龍": [165, 163, "傲岸不遜", 35, 130],
    "十河一存": [123, 205, "鬼十河", 35, 140],
    "瑞溪院": [138, 45, "諸行無常", 35, 110],
    "相馬盛胤": [156, 165, "先陣鼓舞", 35, 130],
    "津田算長": [145, 156, "津田流砲術", 35, 130],
    "南部晴政": [164, 169, "満ちゆく月", 35, 140],
    "尼子晴久": [162, 121, "綱紀粛正", 35, 130],
    "毛利隆元": [165, 92, "一心一徳", 35, 120],
    "朝倉義景": [110, 53, "落花啼鳥", 35, 100],
    "里見義堯": [165, 106, "仁者の沈勇", 35, 130],
}
OFFICER_LIST = sorted(list(OFFICER_DATABASE.keys()))

# --- サイドバー：対戦・環境設定 ---
st.sidebar.header("⚙️ 对戦設定")
initial_hp_per_officer = st.sidebar.number_input(
    "1武将あたりの兵力", min_value=1000, max_value=20000, value=10000, step=1000
)
sim_trials = st.sidebar.selectbox(
    "対戦試行回数", [1000, 5000, 10000], index=0
)

# 武将データの入力 UI 作成用関数
def input_team_data(team_prefix, team_name, default_choices):
    st.markdown(f"### {team_name}")
    roles = ["主将", "副将1", "副将2"]
    tabs = st.tabs([f"【{r}】" for r in roles])
    team_officers = []

    for idx, tab in enumerate(tabs):
        with tab:
            default_idx = OFFICER_LIST.index(default_choices[idx]) if default_choices[idx] in OFFICER_LIST else 0
            o_name = st.selectbox("武将を選択", OFFICER_LIST, index=default_idx, key=f"{team_prefix}_{idx}_select")
            
            db_atk, db_def, db_s1_name, db_s1_rate, db_s1_dmg = OFFICER_DATABASE[o_name]

            c1, c2, c3 = st.columns(3)
            with c1:
                o_atk = st.number_input("攻撃力(変更可)", value=db_atk, key=f"{team_prefix}_{idx}_atk")
            with c2:
                o_def = st.number_input("防御力(変更可)", value=db_def, key=f"{team_prefix}_{idx}_def")
            with c3:
                o_buff = st.number_input("与ダメバフ(%)", min_value=0, max_value=200, value=0, key=f"{team_prefix}_{idx}_buff") / 100.0

            st.markdown(f"**▼ 戦法構成**")
            st.caption(f"・固有: 【{db_s1_name}】 (発動率: {db_s1_rate}% / ダメージ率: {db_s1_dmg}%)")
            
            # 初期選択値を実用的なS級・A級戦法にマッピング
            s2_default_idx = SKILL_LIST.index("万矢斉射") if "万矢斉射" in SKILL_LIST else 0
            s3_default_idx = SKILL_LIST.index("落鳳") if "落鳳" in SKILL_LIST else 0
            
            s2_name = st.selectbox("伝授戦法1", SKILL_LIST, index=s2_default_idx if idx==0 else s3_default_idx, key=f"{team_prefix}_{idx}_s2_name")
            s2_data = SKILL_DATABASE[s2_name]

            s3_name = st.selectbox("伝授戦法2", SKILL_LIST, index=s3_default_idx if idx==0 else 0, key=f"{team_prefix}_{idx}_s3_name")
            s3_data = SKILL_DATABASE[s3_name]

            skills = [
                {"name": db_s1_name, "rate": db_s1_rate / 100.0, "dmg": db_s1_dmg / 100.0, "quality": "固有"},
                {"name": s2_name, "rate": s2_data[0] / 100.0, "dmg": s2_data[1] / 100.0, "quality": s2_data[2]},
                {"name": s3_name, "rate": s3_data[0] / 100.0, "dmg": s3_data[1] / 100.0, "quality": s3_data[2]},
            ]

            team_officers.append({
                "role": roles[idx],
                "name": o_name,
                "atk": o_atk,
                "def": o_def,
                "buff": o_buff,
                "skills": skills
            })
    return team_officers

# --- 自軍・敵軍設定 ---
main_tab1, main_tab2 = st.tabs(["🔵 自軍（あなた）", "🔴 敵軍（対戦相手）"])

with main_tab1:
    my_team = input_team_data("my", "自軍編成", ["黒田官兵衛", "織田信長", "柴田勝家"])

with main_tab2:
    enemy_team = input_team_data("enemy", "敵軍編成", ["徳川家康", "本多忠勝", "酒井忠次"])

st.write("---")

# --- ダメージ計算ロジック ---
def calc_damage(atk, def_power, dmg_rate, buff):
    if dmg_rate == 0:
        return 0
    def_mitigation = 100.0 / (100.0 + def_power)
    effective_atk = atk * dmg_rate
    return int((effective_atk * def_mitigation * 10) * (1.0 + buff))

def simulate_turn_attack(attacker_team, defender_team):
    turn_dmg = 0
    logs = []
    avg_def = sum(o["def"] for o in defender_team) / len(defender_team)
    
    for off in attacker_team:
        for sk in off["skills"]:
            if sk["rate"] > 0 and sk["name"] != "（なし）" and random.random() < sk["rate"]:
                dmg = calc_damage(off["atk"], avg_def, sk["dmg"], off["buff"])
                turn_dmg += dmg
                # ログに品質（S/A）を表示してわかりやすく
                q_label = f"[{sk['quality']}]" if sk['quality'] != "固有" else "【固有】"
                logs.append(f"【{off['name']}】{q_label}{sk['name']} → {dmg:,}ダメ")
    return turn_dmg, logs

# --- シミュレーション実行 ---
if st.button("⚔️ 対戦シミュレーション開始", type="primary", use_container_width=True):

    total_my_hp_init = initial_hp_per_officer * 3
    total_enemy_hp_init = initial_hp_per_officer * 3

    my_wins = 0
    enemy_wins = 0
    draws = 0
    end_my_hps = []
    end_enemy_hps = []

    for _ in range(sim_trials):
        my_hp = total_my_hp_init
        enemy_hp = total_enemy_hp_init

        for turn in range(8):
            # 自軍攻撃
            my_dmg, _ = simulate_turn_attack(my_team, enemy_team)
            enemy_hp = max(0, enemy_hp - my_dmg)
            if enemy_hp == 0: break

            # 敵軍攻撃
            enemy_dmg, _ = simulate_turn_attack(enemy_team, my_team)
            my_hp = max(0, my_hp - enemy_dmg)
            if my_hp == 0: break

        end_my_hps.append(my_hp)
        end_enemy_hps.append(enemy_hp)

        if my_hp > enemy_hp: my_wins += 1
        elif enemy_hp > my_hp: enemy_wins += 1
        else: draws += 1

    # --- 結果表示 ---
    st.subheader(f"📊 対戦結果サマリー ({sim_trials:,} 回対戦)")

    col1, col2, col3 = st.columns(3)
    col1.metric("自軍勝率", f"{(my_wins / sim_trials * 100):.1f}%", f"{my_wins:,}勝")
    col2.metric("引き分け", f"{(draws / sim_trials * 100):.1f}%", f"{draws:,}分")
    col3.metric("敵軍勝率", f"{(enemy_wins / sim_trials * 100):.1f}%", f"{enemy_wins:,}敗")

    st.caption(f"・自軍 平均残兵力: {int(sum(end_my_hps)/sim_trials):,} / {total_my_hp_init:,}")
    st.caption(f"・敵軍 平均残兵力: {int(sum(end_enemy_hps)/sim_trials):,} / {total_enemy_hp_init:,}")

    # --- サンプル戦闘ログ ---
    st.write("---")
    st.subheader("📜 1戦闘の詳細ログサンプル")
    
    sample_log = []
    my_hp = total_my_hp_init
    enemy_hp = total_enemy_hp_init

    for turn in range(1, 9):
        my_dmg, my_sk_logs = simulate_turn_attack(my_team, enemy_team)
        enemy_hp = max(0, enemy_hp - my_dmg)
        
        enemy_dmg, enemy_sk_logs = simulate_turn_attack(enemy_team, my_team)
        my_hp = max(0, my_hp - enemy_dmg)

        sample_log.append({
            "T": f"第{turn}T",
            "自軍行動": " / ".join(my_sk_logs) if my_sk_logs else "（発動なし）",
            "自ダメ": f"{my_dmg:,}",
            "敵軍行動": " / ".join(enemy_sk_logs) if enemy_sk_logs else "（発動なし）",
            "敵ダメ": f"{enemy_dmg:,}",
            "残兵力(自/敵)": f"{my_hp:,} / {enemy_hp:,}"
        })
        if my_hp == 0 or enemy_hp == 0: break

    st.dataframe(pd.DataFrame(sample_log), hide_index=True, use_container_width=True)
