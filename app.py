import random
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="『信長の野望 真戦』部隊対戦シミュレータ", layout="centered"
)

st.title("⚔️ 部隊対戦シミュレータ")
st.caption("自軍 vs 敵軍 8ターン対戦・勝率検証ツール（最新固有戦法DB統合版）")

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

# --- 新・武将データベース（ご提示いただいた戦法リストを完全反映） ---
# 構造： "武将名": [攻撃力, 防御力, "固有戦法名", 発動率%, ダメージ率%, "準備ターン", "種別"]
OFFICER_DATABASE = {
    "柴田勝家": [162, 208, "かかれ柴田", 50, 154, "-", "能動"],
    "安宅冬康": [145, 72, "一舟軒", 40, 0, "-", "能動"],  # 回復・鉄壁メイン
    "毛利隆元": [165, 92, "一心一徳", 50, 0, "-", "能動"],  # 回復メイン
    "本願寺顕如": [182, 119, "一切皆空", 100, 72, "-", "受動"],
    "稲葉一鉄": [175, 101, "一徹の意志", 40, 0, "-", "能動"],  # 挑発・統率上昇
    "柿崎景家": [157, 222, "越後二天", 90, 108, "-", "突撃"],
    "宇佐美定満": [153, 112, "越後流軍学", 100, 0, "-", "指揮"],
    "真柄直隆": [108, 202, "怪力無双", 75, 333, "2", "能動"],
    "今川義元": [194, 174, "海道一", 70, 134, "-", "突撃"],
    "帰蝶": [161, 99, "帰蝶の舞", 100, 0, "-", "受動"],  # デバフ・混乱メイン
    "長宗我部元親": [187, 188, "鬼若子", 100, 0, "-", "指揮"],  # 連撃付与
    "十河一存": [123, 205, "鬼十河", 35, 188, "-", "突撃"],
    "小島弥太郎": [104, 193, "鬼小島", 55, 304, "-", "突撃"],
    "馬場信春": [203, 161, "鬼美濃", 100, 0, "-", "受動"],  # 浄化・回復
    "上杉謙信": [186, 247, "軍神", 100, 160, "-", "受動"],
    "荒木村重": [158, 91, "形影相弔", 45, 192, "-", "能動"],
    "大祝鶴": [144, 171, "月華鶴影", 100, 102, "-", "指揮"],
    "仙桃院": [148, 67, "献身", 100, 262, "-", "指揮"],
    "本多忠勝": [169, 229, "古今独歩", 100, 70, "-", "受動"],
    "明智秀満": [147, 129, "湖水渡り", 65, 0, "-", "能動"],  # 奇策獲得
    "森可成": [145, 189, "攻めの三左", 45, 142, "-", "能動"],
    "飯富虎昌": [136, 203, "甲山猛虎", 45, 96, "-", "能動"],
    "尼子晴久": [162, 121, "綱紀粛正", 50, 196, "1", "能動"],
    "甘利虎泰": [163, 176, "剛の武者", 35, 246, "-", "突撃"],
    "加藤嘉明": [135, 146, "剛毅木訥", 45, 86, "-", "指揮"],
    "可児才蔵": [97, 183, "笹の才蔵", 30, 522, "1", "能動"],
    "徳川家康": [231, 155, "三河魂", 100, 0, "-", "指揮"],
}
OFFICER_LIST = sorted(list(OFFICER_DATABASE.keys()))

# --- サイドバー：対戦・環境設定 ---
st.sidebar.header("⚙️ 対戦設定")
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
            
            db_atk, db_def, db_s1_name, db_s1_rate, db_s1_dmg, db_s1_prep, db_s1_type = OFFICER_DATABASE[o_name]

            c1, c2, c3 = st.columns(3)
            with c1:
                o_atk = st.number_input("攻撃力(変更可)", value=db_atk, key=f"{team_prefix}_{idx}_atk")
            with c2:
                o_def = st.number_input("防御力(変更可)", value=db_def, key=f"{team_prefix}_{idx}_def")
            with c3:
                o_buff = st.number_input("与ダメバフ(%)", min_value=0, max_value=200, value=0, key=f"{team_prefix}_{idx}_buff") / 100.0

            prep_info = f" / 準備: {db_s1_prep}T" if db_s1_prep != "-" else ""
            st.markdown(f"**▼ 戦法構成**")
            st.caption(f"・固有: 【{db_s1_name}】 ({db_s1_type} / 発動率: {db_s1_rate}% / ダメージ率: {db_s1_dmg}%{prep_info})")
            
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
    my_team = input_team_data("my", "自軍編成", ["柴田勝家", "上杉謙信", "本多忠勝"])

with main_tab2:
    enemy_team = input_team_data("enemy", "敵軍編成", ["徳川家康", "今川義元", "可児才蔵"])

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
