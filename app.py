import random
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="『信長の野望 真戦』部隊ダメージシミュレータ", layout="centered"
)

st.title("⚔️ 部隊ダメージ計算")
st.caption("主将・副将・伝授戦法対応 / 8ターン試行シミュレータ")

# --- 戦法データベース（戦法名: [発動率(%), ダメージ率(%)]) ---
SKILL_DATABASE = {
    "（なし）": [0, 0],
    "水の如し": [35, 158],
    "伝授戦法A": [35, 100],
    "伝授戦法B": [40, 120],
    "伝授戦法C": [30, 150],
    "伝授戦法D": [50, 80],
}
SKILL_LIST = list(SKILL_DATABASE.keys())

# --- サイドバー：敵ステータス設定 ---
st.sidebar.header("🛡️ 敵軍ステータス")
defense_power = st.sidebar.number_input(
    "敵の統率（防御）", min_value=1, max_value=1000, value=180, step=5
)
sim_trials = st.sidebar.selectbox(
    "試行回数 (モンテカルロ法)", [1000, 5000, 10000], index=1
)

# --- 武将・戦法入力エリア（タブ化でスマホに最適化） ---
st.subheader("👥 部隊構成")

roles = ["主将", "副将1", "副将2"]
default_officers = [
    {"name": "黒田官兵衛", "atk": 250, "buff": 0, "s1": "水の如し"},
    {"name": "副将A", "atk": 200, "buff": 0, "s1": "伝授戦法A"},
    {"name": "副将B", "atk": 200, "buff": 0, "s1": "伝授戦法B"},
]

tabs = st.tabs([f"【{r}】" for r in roles])
officers = []

for idx, tab in enumerate(tabs):
    with tab:
        col1, col2 = st.columns(2)
        with col1:
            o_name = st.text_input(
                "武将名",
                value=default_officers[idx]["name"],
                key=f"off_{idx}_name",
            )
            o_atk = st.number_input(
                "攻撃ステータス",
                min_value=1,
                max_value=1000,
                value=default_officers[idx]["atk"],
                key=f"off_{idx}_atk",
            )
        with col2:
            o_buff = (
                st.number_input(
                    "与ダメバフ(%)",
                    min_value=0,
                    max_value=200,
                    value=default_officers[idx]["buff"],
                    key=f"off_{idx}_buff",
                )
                / 100.0
            )

        st.markdown("**▼ 戦法選択**")
        # 固有戦法（固定または手入力名）
        s1_name = st.text_input(
            "固有戦法名",
            value=default_officers[idx]["s1"],
            key=f"off_{idx}_s1_name",
        )
        # 固有戦法がデータベースにない場合はデフォルト値を適用
        s1_data = SKILL_DATABASE.get(s1_name, [35, 158 if idx == 0 else 120])

        # 伝授戦法はセレクトボックスから選択
        s2_name = st.selectbox(
            "伝授戦法1",
            SKILL_LIST,
            index=2 if idx == 0 else 3,
            key=f"off_{idx}_s2_name",
        )
        s2_data = SKILL_DATABASE[s2_name]

        s3_name = st.selectbox(
            "伝授戦法2",
            SKILL_LIST,
            index=3 if idx == 0 else 0,
            key=f"off_{idx}_s3_name",
        )
        s3_data = SKILL_DATABASE[s3_name]

        skills = [
            {"name": s1_name, "rate": s1_data[0] / 100.0, "dmg": s1_data[1] / 100.0},
            {"name": s2_name, "rate": s2_data[0] / 100.0, "dmg": s2_data[1] / 100.0},
            {"name": s3_name, "rate": s3_data[0] / 100.0, "dmg": s3_data[1] / 100.0},
        ]

        # 選択された戦法のスペック表示（スマホで確認しやすいように）
        for sk in skills:
            if sk["name"] != "（なし）" and sk["rate"] > 0:
                st.caption(f"・{sk['name']}: 発動率 {int(sk['rate']*100)}% / ダメージ率 {int(sk['dmg']*100)}%")

        officers.append(
            {
                "role": roles[idx],
                "name": o_name,
                "atk": o_atk,
                "buff": o_buff,
                "skills": skills,
            }
        )

st.write("---")

# --- ダメージ計算ロジック関数の定義 ---
defense_mitigation = 100.0 / (100.0 + defense_power)


def calc_skill_damage(atk, dmg_rate, buff, def_mitigation):
    if dmg_rate == 0:
        return 0
    effective_atk = atk * dmg_rate
    return int((effective_atk * def_mitigation * 10) * (1.0 + buff))


# 単回発動時のダメージを各スキルに事前計算
for off in officers:
    for sk in off["skills"]:
        sk["single_damage"] = calc_skill_damage(
            off["atk"], sk["dmg"], off["buff"], defense_mitigation
        )

# --- 理論期待値の計算と表示 ---
total_expected_dmg = sum(
    sk["single_damage"] * 8 * sk["rate"]
    for off in officers
    for sk in off["skills"]
)

st.metric("8ターン総ダメージ期待値", f"{int(total_expected_dmg):,} ダメージ")

# --- モンテカルロシミュレーション実行 ---
if st.button("🚀 8ターン戦闘シミュレーション実行", type="primary", use_container_width=True):

    st.subheader(f"🎲 結果 ({sim_trials:,} 回試行)")

    total_damages = []

    for _ in range(sim_trials):
        battle_total = 0
        for turn in range(8):
            for off in officers:
                for sk in off["skills"]:
                    if sk["rate"] > 0 and random.random() < sk["rate"]:
                        battle_total += sk["single_damage"]
        total_damages.append(battle_total)

    avg_dmg = int(sum(total_damages) / sim_trials)
    max_dmg = max(total_damages)
    min_dmg = min(total_damages)

    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("平均", f"{avg_dmg:,}")
    res_col2.metric("最大", f"{max_dmg:,}")
    res_col3.metric("最小", f"{min_dmg:,}")

    # --- 直近の1戦闘サンプルログ ---
    st.write("#### 📜 1戦闘の詳細ログサンプル")
    sample_log = []
    sample_battle_total = 0

    for turn in range(1, 9):
        turn_dmg = 0
        triggered_skills = []

        for off in officers:
            for sk in off["skills"]:
                if sk["rate"] > 0 and sk["name"] != "（なし）" and random.random() < sk["rate"]:
                    dmg = sk["single_damage"]
                    turn_dmg += dmg
                    triggered_skills.append(
                        f"【{off['name']}】{sk['name']}({dmg:,})"
                    )

        sample_battle_total += turn_dmg
        sample_log.append(
            {
                "ターン": f"第{turn}T",
                "発動戦法": " / ".join(triggered_skills) if triggered_skills else "（なし）",
                "与ダメ": f"{turn_dmg:,}",
                "累計": f"{sample_battle_total:,}",
            }
        )

    df_sample = pd.DataFrame(sample_log)
    st.dataframe(df_sample, hide_index=True, use_container_width=True)
