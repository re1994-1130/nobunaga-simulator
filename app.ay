import random
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="『信長の野望 真戦』部隊ダメージシミュレータ", layout="wide"
)
st.title("⚔️ 部隊ダメージ計算シミュレータ")
st.caption(
    "主将・副将・伝授戦法対応／8ターン発動率・ダメージ期待値検証ツール"
)

st.write("---")

# --- サイドバー：敵ステータス設定 ---
st.sidebar.header("🛡️ 敵軍ステータス")
defense_power = st.sidebar.number_input(
    "敵の統率（防御）", min_value=1, max_value=1000, value=180, step=5
)
sim_trials = st.sidebar.selectbox(
    "試行回数 (モンテカルロ法)", [1000, 5000, 10000], index=1
)


# --- 戦法データの入力関数 ---
def create_skill_input(prefix, default_name, default_rate, default_dmg):
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        s_name = st.text_input(f"戦法名", value=default_name, key=f"{prefix}_name")
    with col2:
        s_rate = (
            st.number_input(
                f"発動率(%)",
                min_value=0,
                max_value=100,
                value=default_rate,
                key=f"{prefix}_rate",
            )
            / 100.0
        )
    with col3:
        s_dmg = (
            st.number_input(
                f"ダメージ率(%)",
                min_value=0,
                max_value=500,
                value=default_dmg,
                key=f"{prefix}_dmg",
            )
            / 100.0
        )
    return {"name": s_name, "rate": s_rate, "dmg": s_dmg}


# --- 武将・戦法入力エリア ---
st.subheader("👥 部隊・戦法構成")

cols = st.columns(3)

officers = []
roles = ["主将", "副将1", "副将2"]
default_officers = [
    {"name": "黒田官兵衛", "atk": 250, "buff": 0},
    {"name": "副将A", "atk": 200, "buff": 0},
    {"name": "副将B", "atk": 200, "buff": 0},
]

for idx, col in enumerate(cols):
    with col:
        st.markdown(f"### 【{roles[idx]}】")
        o_name = st.text_input(
            "武将名",
            value=default_officers[idx]["name"],
            key=f"off_{idx}_name",
        )
        o_atk = st.number_input(
            "攻撃ステータス(武力/智略)",
            min_value=1,
            max_value=1000,
            value=default_officers[idx]["atk"],
            key=f"off_{idx}_atk",
        )
        o_buff = (
            st.number_input(
                "与ダメージバフ(%)",
                min_value=0,
                max_value=200,
                value=default_officers[idx]["buff"],
                key=f"off_{idx}_buff",
            )
            / 100.0
        )

        st.markdown("**▼ 固有戦法**")
        s1 = create_skill_input(
            f"off_{idx}_s1",
            "水の如し" if idx == 0 else f"固有戦法{idx+1}",
            35 if idx == 0 else 30,
            158 if idx == 0 else 120,
        )

        st.markdown("**▼ 伝授戦法1**")
        s2 = create_skill_input(
            f"off_{idx}_s2", "伝授戦法A", 35, 100
        )

        st.markdown("**▼ 伝授戦法2**")
        s3 = create_skill_input(
            f"off_{idx}_s3", "伝授戦法B", 35, 100
        )

        officers.append(
            {
                "role": roles[idx],
                "name": o_name,
                "atk": o_atk,
                "buff": o_buff,
                "skills": [s1, s2, s3],
            }
        )

st.write("---")

# --- ダメージ計算ロジック関数の定義 ---
# （※攻撃力はダメージ率にのみ適用。通常攻撃なし。バフはスキルに直乗り）
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
st.subheader("💡 1戦闘（8ターン）の理論期待値（全部隊合計）")

total_expected_dmg = 0
for off in officers:
    for sk in off["skills"]:
        total_expected_dmg += sk["single_damage"] * 8 * sk["rate"]

st.metric("8ターン部隊総ダメージ期待値", f"{int(total_expected_dmg):,} ダメージ")

# --- モンテカルロシミュレーション実行 ---
if st.button("🚀 部隊8ターン戦闘シミュレーション実行", type="primary"):

    st.subheader(f"🎲 シミュレーション結果 ({sim_trials:,} 回試行)")

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
    res_col1.metric("平均総ダメージ", f"{avg_dmg:,}")
    res_col2.metric("最大ダメージ", f"{max_dmg:,}")
    res_col3.metric("最小ダメージ", f"{min_dmg:,}")

    # --- 直近の1戦闘サンプルログ ---
    st.write("#### 📜 1戦闘（8ターン）の詳細戦闘ログサンプル")
    sample_log = []
    sample_battle_total = 0

    for turn in range(1, 9):
        turn_dmg = 0
        triggered_skills = []

        for off in officers:
            for sk in off["skills"]:
                if sk["rate"] > 0 and random.random() < sk["rate"]:
                    dmg = sk["single_damage"]
                    turn_dmg += dmg
                    triggered_skills.append(
                        f"【{off['name']}】{sk['name']}({dmg:,})"
                    )

        sample_battle_total += turn_dmg
        sample_log.append(
            {
                "ターン": f"第 {turn} ターン",
                "発動戦法": " / ".join(triggered_skills)
                if triggered_skills
                else "（発動なし）",
                "ターン与ダメージ": f"{turn_dmg:,}",
                "累計ダメージ": f"{sample_battle_total:,}",
            }
        )

    df_sample = pd.DataFrame(sample_log)
    st.table(df_sample)
