import random
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="『信長の野望 真戦』部隊対戦シミュレータ", layout="centered"
)

st.title("⚔️ 部隊対戦シミュレータ")
st.caption("自軍 vs 敵軍 8ターン対戦（兵種適性・凸特性・兵種相性・最低保証床補正・負傷兵完全実装版）")

# --- 兵種相性の関係定義 ---
TROOP_TYPES = ["足軽", "騎兵", "弓兵", "鉄砲"]

def get_troop_advantage(attacker_type, defender_type):
    """
    兵種相性による倍率判定
    - 有利: 1.125 (+12.5%)
    - 不利: 0.875 (-12.5%)
    """
    adv_map = {
        "足軽": "騎兵",
        "騎兵": "弓兵",
        "弓兵": "鉄砲",
        "鉄砲": "足軽",
    }
    if adv_map.get(attacker_type) == defender_type:
        return 1.125  # 有利
    elif adv_map.get(defender_type) == attacker_type:
        return 0.875  # 不利
    return 1.0  # 中立

# --- 伝授・事件戦法データベース ---
SKILL_DATABASE = {
    "（なし）": [0, 0, "-", "-", "兵刃"],
    
    # ─── 攻撃系伝授・事件戦法 ───
    "一力当先": [40, 70, "S", "能動", "兵刃"],
    "境目奮戦": [35, 260, "S", "突撃", "兵刃"],
    "御旗楯無": [100, 94, "S", "受動", "兵刃"],
    "攻其不備": [40, 168, "S", "能動", "兵刃"],
    "紅蓮の炎": [35, 104, "S", "能動", "計略"],
    "死中求活": [100, 125, "S", "受動", "兵刃"],
    "七十二の計": [100, 120, "S", "受動", "計略"],
    "瞬息万変": [45, 162, "S", "能動", "計略"],
    "所向無敵": [30, 254, "S", "能動", "兵刃"],
    "乗勝追撃": [30, 136, "S", "突撃", "兵刃"],
    "陣形崩し": [35, 102, "S", "能動", "兵刃"],
    "千軍辟易": [35, 106, "S", "能動", "兵刃"],
    "草木皆兵": [50, 142, "S", "能動", "計略"],
    "電光石火": [40, 96, "S", "能動", "兵刃"],
    "勇猛無比": [40, 116, "S", "能動", "兵刃"],
    "乱世の華": [40, 158, "S", "突撃", "計略"],
    "理非曲直": [35, 192, "S", "突撃", "兵刃"],
    "霹靂一撃": [35, 228, "S", "能動", "兵刃"],
    "離心の計": [35, 352, "S", "事件", "計略"],

    # ─── 回復・補助戦法 ───
    "有備無患": [40, 60, "S", "能動", "回復"],         # 直接回復型・知略依存
    "按甲休兵": [100, 140, "S", "受動", "休養_非依存"],   # 休養型・知略非依存
    "懐柔": [35, 48.9, "A", "能動", "休養"],           # 休養型・知略依存
    "守禦": [100, 100, "A", "指揮", "回復_非依存"],     # 直接回復型・知略非依存
    "恵風和雨": [40, 88, "S", "指揮", "回復"],          # 直接回復型・知略依存
}
SKILL_LIST = sorted(list(SKILL_DATABASE.keys()))

# --- 武将統合データベース（基礎ステータス・兵種適性・凸特性拡張版） ---
# 形式: [武勇, 知略, 統率, 固有名, 確率, 発動ダメ, タイプ, 属性, 兵種適性Dict, 特性リスト]
# 特性リスト形式: [{"req": 必要凸数, "name": 特性名, "troop": 兵種, "bonus": 適正加算値}]
OFFICER_DATABASE = {
    "柴田勝家": [
        208, 95, 162, "かかれ柴田", 50, 154, "能動", "兵刃",
        {"足軽": 2, "騎兵": 3, "弓兵": 1, "鉄砲": 1},
        [
            {"req": 0, "name": "騎兵大将", "troop": "騎兵", "bonus": 1},
            {"req": 1, "name": "突破", "troop": "騎兵", "bonus": 1},
            {"req": 3, "name": "猛将", "troop": None, "bonus": 0},
            {"req": 5, "name": "鬼柴田", "troop": "騎兵", "bonus": 1}
        ]
    ],
    "明智光秀": [
        140, 183, 165, "時は今", 70, 56, "能動", "計略",
        {"足軽": 1, "騎兵": 1, "弓兵": 2, "鉄砲": 3},
        [
            {"req": 0, "name": "鉄砲大将", "troop": "鉄砲", "bonus": 1},
            {"req": 1, "name": "狙撃", "troop": "鉄砲", "bonus": 1},
            {"req": 3, "name": "策士", "troop": None, "bonus": 0},
            {"req": 5, "name": "金ヶ崎の執念", "troop": "鉄砲", "bonus": 1}
        ]
    ],
    "本多正信": [
        43, 195, 120, "非常の器", 100, 66, "指揮", "休養",
        {"足軽": 2, "騎兵": 1, "弓兵": 3, "鉄砲": 2},
        [
            {"req": 0, "name": "弓兵大将", "troop": "弓兵", "bonus": 1},
            {"req": 1, "name": "参謀", "troop": "弓兵", "bonus": 1},
            {"req": 3, "name": "謀略", "troop": None, "bonus": 0},
            {"req": 5, "name": "権謀術数", "troop": "弓兵", "bonus": 1}
        ]
    ],
    "上杉謙信": [
        247, 186, 210, "軍神", 100, 160, "受動", "兵刃",
        {"足軽": 3, "騎兵": 3, "弓兵": 1, "鉄砲": 1},
        [
            {"req": 0, "name": "騎兵大将", "troop": "騎兵", "bonus": 1},
            {"req": 1, "name": "毘沙門天", "troop": "騎兵", "bonus": 1},
            {"req": 3, "name": "車懸かり", "troop": "足軽", "bonus": 1},
            {"req": 5, "name": "越後の龍", "troop": "騎兵", "bonus": 1}
        ]
    ],
    "徳川家康": [
        155, 231, 210, "三河魂", 100, 0, "指揮", "計略",
        {"足軽": 3, "騎兵": 2, "弓兵": 2, "鉄砲": 2},
        [
            {"req": 0, "name": "足軽大将", "troop": "足軽", "bonus": 1},
            {"req": 1, "name": "忍耐", "troop": "足軽", "bonus": 1},
            {"req": 3, "name": "統帥", "troop": None, "bonus": 0},
            {"req": 5, "name": "神君", "troop": "足軽", "bonus": 1}
        ]
    ],
    "武田信玄": [
        191, 202, 205, "風林火山", 100, 124, "指揮", "計略",
        {"足軽": 2, "騎兵": 3, "弓兵": 2, "鉄砲": 1},
        [
            {"req": 0, "name": "騎兵大将", "troop": "騎兵", "bonus": 1},
            {"req": 1, "name": "侵略如火", "troop": "騎兵", "bonus": 1},
            {"req": 3, "name": "不動如山", "troop": "足軽", "bonus": 1},
            {"req": 5, "name": "甲斐の虎", "troop": "騎兵", "bonus": 1}
        ]
    ],
    "今川義元": [
        174, 194, 180, "海道一", 70, 134, "突撃", "計略",
        {"足軽": 1, "騎兵": 1, "弓兵": 3, "鉄砲": 2},
        [
            {"req": 0, "name": "弓兵大将", "troop": "弓兵", "bonus": 1},
            {"req": 1, "name": "射術", "troop": "弓兵", "bonus": 1},
            {"req": 3, "name": "威風", "troop": None, "bonus": 0},
            {"req": 5, "name": "海道一の弓取り", "troop": "弓兵", "bonus": 1}
        ]
    ],
    "織田信長": [
        180, 231, 195, "新生", 100, 0, "指揮", "計略",
        {"足軽": 2, "騎兵": 2, "弓兵": 1, "鉄砲": 3},
        [
            {"req": 0, "name": "鉄砲大将", "troop": "鉄砲", "bonus": 1},
            {"req": 1, "name": "三段構え", "troop": "鉄砲", "bonus": 1},
            {"req": 3, "name": "覇王", "troop": None, "bonus": 0},
            {"req": 5, "name": "天下布武", "troop": "鉄砲", "bonus": 1}
        ]
    ]
}

# データベースにない武将のデフォルトフォールバック用関数
def get_officer_data(o_name):
    if o_name in OFFICER_DATABASE:
        return OFFICER_DATABASE[o_name]
    else:
        return [
            100, 100, 100, "汎用武将", 50, 100, "能動", "兵刃",
            {"足軽": 1, "騎兵": 1, "弓兵": 1, "鉄砲": 1},
            [
                {"req": 0, "name": "汎用初期", "troop": "足軽", "bonus": 1},
                {"req": 1, "name": "汎用1凸", "troop": "騎兵", "bonus": 1},
                {"req": 3, "name": "汎用3凸", "troop": "弓兵", "bonus": 1},
                {"req": 5, "name": "汎用5凸", "troop": "鉄砲", "bonus": 1}
            ]
        ]

OFFICER_LIST = sorted(list(OFFICER_DATABASE.keys()))

# --- UI・設定 ---
st.sidebar.header("⚙️ 対戦設定")
initial_hp_per_officer = st.sidebar.number_input(
    "1武将あたりの兵力", min_value=1000, max_value=20000, value=10000, step=1000
)
sim_trials = st.sidebar.selectbox(
    "対戦試行回数", [1000, 5000, 10000], index=0
)

def input_team_data(team_prefix, team_name, default_choices, default_troop_idx):
    st.markdown(f"### {team_name}")
    
    selected_troop = st.selectbox(
        f"{team_name}の選択兵種", TROOP_TYPES, index=default_troop_idx, key=f"{team_prefix}_troop"
    )

    roles = ["主将", "副将1", "副将2"]
    tabs = st.tabs([f"【{r}】" for r in roles])
    team_officers = []

    # 兵種適性および凸特性による合計適性レベル集計用
    total_troop_levels = {t: 0 for t in TROOP_TYPES}

    for idx, tab in enumerate(tabs):
        with tab:
            default_idx = OFFICER_LIST.index(default_choices[idx]) if default_choices[idx] in OFFICER_LIST else 0
            o_name = st.selectbox("武将を選択", OFFICER_LIST, index=default_idx, key=f"{team_prefix}_{idx}_select")
            
            o_data = get_officer_data(o_name)
            o_buyou, o_chiryaku, o_tousotsu, db_s1_name, db_s1_rate, db_s1_dmg, db_s1_type, db_s1_attr, troop_aptitudes, traits = o_data

            # --- ランクアップ（凸数）選択 ---
            rank = st.radio(
                "ランクアップ（凸数）",
                [0, 1, 2, 3, 4, 5],
                format_func=lambda x: "無 (★0)" if x == 0 else f"★{x}",
                horizontal=True,
                key=f"{team_prefix}_{idx}_rank"
            )

            # 凸に応じた特性の解放状態判定
            active_traits = []
            for trait in traits:
                is_unlocked = rank >= trait["req"]
                active_traits.append({**trait, "unlocked": is_unlocked})
                
                # 兵種適性加算
                if is_unlocked and trait["troop"] in total_troop_levels:
                    total_troop_levels[trait["troop"]] += trait["bonus"]

            # 武将本体の基礎兵種適性も加算
            for t_type, val in troop_aptitudes.items():
                if t_type in total_troop_levels:
                    total_troop_levels[t_type] += val

            # --- UI表示：特性（凸連動）の表示 ---
            st.caption("📜 **特性（凸連動）**")
            trait_cols = st.columns(len(traits))
            for t_idx, trait in enumerate(active_traits):
                with trait_cols[t_idx]:
                    if trait["unlocked"]:
                        st.success(f"**[{trait['req']}凸]** {trait['name']}")
                    else:
                        st.info(f"🔒 **[{trait['req']}凸]** 封印中")

            st.caption(f"・固有戦法: **【{db_s1_name}】**")

            s2_default_idx = SKILL_LIST.index("有備無患") if "有備無患" in SKILL_LIST else 0
            s3_default_idx = SKILL_LIST.index("離心の計") if "離心の計" in SKILL_LIST else 0
            
            s2_name = st.selectbox("伝授/事件戦法1", SKILL_LIST, index=s2_default_idx if idx==0 else s3_default_idx, key=f"{team_prefix}_{idx}_s2_name")
            s2_data = SKILL_DATABASE[s2_name]

            s3_name = st.selectbox("伝授/事件戦法2", SKILL_LIST, index=s3_default_idx if idx==0 else 0, key=f"{team_prefix}_{idx}_s3_name")
            s3_data = SKILL_DATABASE[s3_name]

            skills = [
                {"name": db_s1_name, "rate": db_s1_rate / 100.0, "dmg": db_s1_dmg / 100.0, "quality": "固有", "attr": db_s1_attr},
                {"name": s2_name, "rate": s2_data[0] / 100.0, "dmg": s2_data[1] / 100.0, "quality": s2_data[2], "attr": s2_data[4]},
                {"name": s3_name, "rate": s3_data[0] / 100.0, "dmg": s3_data[1] / 100.0, "quality": s3_data[2], "attr": s3_data[4]},
            ]

            team_officers.append({
                "role": roles[idx],
                "name": o_name,
                "rank": rank,
                "buyou": o_buyou,
                "chiryaku": o_chiryaku,
                "tousotsu": o_tousotsu,
                "skills": skills
            })

    # 部隊の選択兵種における合計兵種レベル
    team_troop_level = total_troop_levels.get(selected_troop, 0)

    # --- 部隊兵種レベル表示領域 ---
    st.markdown("#### 🛡️ 部隊合計兵種適性レベル")
    lvl_cols = st.columns(len(TROOP_TYPES))
    for idx, t_type in enumerate(TROOP_TYPES):
        with lvl_cols[idx]:
            is_active = (t_type == selected_troop)
            label = f"**{t_type}**" if is_active else t_type
            st.metric(label, f"Lv.{total_troop_levels[t_type]}", delta="出陣兵種" if is_active else None)

    return team_officers, selected_troop, team_troop_level

main_tab1, main_tab2 = st.tabs(["🔵 自軍（あなた）", "🔴 敵軍（対戦相手）"])

with main_tab1:
    my_team, my_troop, my_troop_lvl = input_team_data("my", "自軍編成", ["本多正信", "上杉謙信", "柴田勝家"], default_troop_idx=1) # 騎兵

with main_tab2:
    enemy_team, enemy_troop, enemy_troop_lvl = input_team_data("enemy", "敵軍編成", ["徳川家康", "武田信玄", "今川義元"], default_troop_idx=2) # 弓兵

# 相性倍率 & 兵種レベル補正の計算
base_my_adv = get_troop_advantage(my_troop, enemy_troop)
base_enemy_adv = get_troop_advantage(enemy_troop, my_troop)

# 兵種レベル1ごとに +2% のダメージ補正を追加
my_advantage_mult = base_my_adv * (1.0 + (my_troop_lvl * 0.02))
enemy_advantage_mult = base_enemy_adv * (1.0 + (enemy_troop_lvl * 0.02))

col_adv1, col_adv2 = st.columns(2)
with col_adv1:
    st.info(f"🔵 **自軍({my_troop} Lv.{my_troop_lvl}) → 敵軍**: 総合与ダメ倍率 **{my_advantage_mult:.3f}倍**")
with col_adv2:
    st.info(f"🔴 **敵軍({enemy_troop} Lv.{enemy_troop_lvl}) → 自軍**: 総合与ダメ倍率 **{enemy_advantage_mult:.3f}倍**")

st.write("---")

# ──────────── 計算・ダメージ・回復モデル ────────────

def get_h_hp(hp):
    if hp <= 1800:
        return hp * 0.10
    else:
        return (1800 * 0.10) + ((hp - 1800) ** 0.85) * 0.15

def calc_heal_cap(skill_rate, chiryaku, current_hp, is_intel_dep=True):
    h_val = get_h_hp(current_hp)
    if is_intel_dep:
        base_val = (1.02 * chiryaku) + h_val
    else:
        base_val = h_val
    return skill_rate * base_val

def get_floor_damage(current_hp, is_skill=False, dmg_rate=1.0, troop_mult=1.0):
    if current_hp <= 600:
        base_floor = 11.0
    elif current_hp <= 3000:
        base_floor = 18.75 * (current_hp / 1000.0)
    else:
        base_floor = (18.75 * 3.0) + (16.0 * ((current_hp - 3000) / 1000.0))

    if is_skill:
        raw_floor = base_floor * (20.5 / 18.75) * dmg_rate
    else:
        raw_floor = base_floor

    return raw_floor * troop_mult

def calc_damage(atk_stat, def_stat, current_hp, dmg_rate=1.0, is_skill=False, troop_mult=1.0):
    if dmg_rate == 0:
        return 0

    floor_val = get_floor_damage(current_hp, is_skill=is_skill, dmg_rate=dmg_rate, troop_mult=troop_mult)
    eff_atk = atk_stat * 1.44
    eff_def = def_stat * 1.44
    stat_diff = eff_atk - eff_def

    hp_scaling = (current_hp / 1000.0) ** 1.35
    stat_component = stat_diff * 0.22 * (current_hp / 1000.0)
    hp_component = 12.0 * hp_scaling

    calculated_dmg = (hp_component + stat_component) * dmg_rate
    final_dmg_base = calculated_dmg * troop_mult
    final_dmg = max(floor_val, final_dmg_base)

    random_factor = random.uniform(0.96, 1.04)
    return int(final_dmg * random_factor)

def apply_damage_to_officer(officer, raw_damage):
    if raw_damage <= 0 or officer["hp"] <= 0:
        return

    actual_dmg = min(officer["hp"], raw_damage)
    dead_now = int(actual_dmg * 0.104)
    injured_now = actual_dmg - dead_now

    officer["hp"] -= actual_dmg
    officer["injured_hp"] += injured_now
    officer["total_dead"] += dead_now

def process_turn_deadification(team):
    for o in team:
        if o["injured_hp"] > 0:
            turn_dead = int(o["injured_hp"] * 0.1036)
            o["injured_hp"] -= turn_dead
            o["total_dead"] += turn_dead

def simulate_turn_attack(attacker_team, defender_team, troop_mult):
    logs = []
    alive_defenders = [o for o in defender_team if o["hp"] > 0]
    if not alive_defenders:
        return 0, []

    total_turn_dmg = 0

    for off in attacker_team:
        if off["hp"] <= 0:
            continue
            
        # 回復・休養戦法
        for sk in off["skills"]:
            if "回復" in sk["attr"] or "休養" in sk["attr"]:
                if sk["rate"] > 0 and random.random() < sk["rate"]:
                    ref_intel = off["init_chiryaku"] if "休養" in sk["attr"] else off["chiryaku"]
                    ref_hp = off["init_hp"] if "休養" in sk["attr"] else off["hp"]
                    is_intel = not ("非依存" in sk["attr"])

                    heal_cap = calc_heal_cap(sk["dmg"], ref_intel, ref_hp, is_intel_dep=is_intel)
                    actual_heal = int(min(heal_cap, off["injured_hp"]))
                    
                    if actual_heal > 0:
                        off["hp"] += actual_heal
                        off["injured_hp"] -= actual_heal
                        logs.append(f"【{off['name']}】{sk['name']} → {actual_heal:,}回復 (残負傷:{off['injured_hp']:,})")
                    else:
                        logs.append(f"【{off['name']}】{sk['name']} → 0回復 (空撃ち)")

        # 通常攻撃
        avg_def = sum(o["tousotsu"] for o in alive_defenders) / len(alive_defenders)
        normal_dmg = calc_damage(off["buyou"], avg_def, off["hp"], dmg_rate=1.0, is_skill=False, troop_mult=troop_mult)
        total_turn_dmg += normal_dmg

        dmg_per_target = normal_dmg // len(alive_defenders)
        for target in alive_defenders:
            apply_damage_to_officer(target, dmg_per_target)

        # 攻撃戦法
        for sk in off["skills"]:
            if sk["rate"] > 0 and not ("回復" in sk["attr"] or "休養" in sk["attr"]) and sk["name"] != "（なし）":
                if random.random() < sk["rate"]:
                    stat_val = off["chiryaku"] if sk["attr"] == "計略" else off["buyou"]
                    s_dmg = calc_damage(stat_val, avg_def, off["hp"], dmg_rate=sk["dmg"], is_skill=True, troop_mult=troop_mult)
                    
                    total_turn_dmg += s_dmg
                    dmg_per_target_sk = s_dmg // len(alive_defenders)
                    for target in alive_defenders:
                        apply_damage_to_officer(target, dmg_per_target_sk)

                    q_label = f"[{sk['quality']}]" if sk['quality'] != "固有" else "【固有】"
                    logs.append(f"【{off['name']}】{q_label}{sk['name']} → {s_dmg:,}ダメ")

    return total_turn_dmg, logs

# ──────────── シミュレーション実行 ────────────
if st.button("⚔️ 対戦シミュレーション開始", type="primary", use_container_width=True):

    total_my_hp_init = initial_hp_per_officer * 3
    total_enemy_hp_init = initial_hp_per_officer * 3

    my_wins = 0
    enemy_wins = 0
    draws = 0
    end_my_dead_list = []
    end_enemy_dead_list = []

    for _ in range(sim_trials):
        my_team_sim = [{
            **o,
            "hp": initial_hp_per_officer,
            "injured_hp": 0,
            "total_dead": 0,
            "init_hp": initial_hp_per_officer,
            "init_chiryaku": o["chiryaku"]
        } for o in my_team]

        enemy_team_sim = [{
            **o,
            "hp": initial_hp_per_officer,
            "injured_hp": 0,
            "total_dead": 0,
            "init_hp": initial_hp_per_officer,
            "init_chiryaku": o["chiryaku"]
        } for o in enemy_team]

        for turn in range(1, 9):
            process_turn_deadification(my_team_sim)
            process_turn_deadification(enemy_team_sim)

            simulate_turn_attack(my_team_sim, enemy_team_sim, my_advantage_mult)
            if sum(e["hp"] for e in enemy_team_sim) == 0: break

            simulate_turn_attack(enemy_team_sim, my_team_sim, enemy_advantage_mult)
            if sum(m["hp"] for m in my_team_sim) == 0: break

        for o in my_team_sim:
            fin_dead = int(o["injured_hp"] * 0.42)
            o["total_dead"] += fin_dead
            o["injured_hp"] -= fin_dead

        for o in enemy_team_sim:
            fin_dead = int(o["injured_hp"] * 0.42)
            o["total_dead"] += fin_dead
            o["injured_hp"] -= fin_dead

        final_my_total = sum(m["hp"] for m in my_team_sim)
        final_enemy_total = sum(e["hp"] for e in enemy_team_sim)

        end_my_dead_list.append(sum(m["total_dead"] for m in my_team_sim))
        end_enemy_dead_list.append(sum(e["total_dead"] for e in enemy_team_sim))

        if final_my_total > final_enemy_total: my_wins += 1
        elif final_enemy_total > final_my_total: enemy_wins += 1
        else: draws += 1

    # --- 結果表示 ---
    st.subheader(f"📊 対戦結果サマリー ({sim_trials:,} 回対戦)")

    col1, col2, col3 = st.columns(3)
    col1.metric("自軍勝率", f"{(my_wins / sim_trials * 100):.1f}%", f"{my_wins:,}勝")
    col2.metric("引き分け", f"{(draws / sim_trials * 100):.1f}%", f"{draws:,}分")
    col3.metric("敵軍勝率", f"{(enemy_wins / sim_trials * 100):.1f}%", f"{enemy_wins:,}敗")

    avg_my_dead = int(sum(end_my_dead_list) / sim_trials)
    avg_enemy_dead = int(sum(end_enemy_dead_list) / sim_trials)

    st.caption(f"・自軍 平均確定戦死者数: **{avg_my_dead:,}** / {total_my_hp_init:,} (戦死率: {(avg_my_dead/total_my_hp_init*100):.1f}%)")
    st.caption(f"・敵軍 平均確定戦死者数: **{avg_enemy_dead:,}** / {total_enemy_hp_init:,} (戦死率: {(avg_enemy_dead/total_enemy_hp_init*100):.1f}%)")

    # --- サンプル戦闘ログ ---
    st.write("---")
    st.subheader("📜 1戦闘の詳細ログサンプル")
    
    sample_log = []
    my_team_sample = [{**o, "hp": initial_hp_per_officer, "injured_hp": 0, "total_dead": 0, "init_hp": initial_hp_per_officer, "init_chiryaku": o["chiryaku"]} for o in my_team]
    enemy_team_sample = [{**o, "hp": initial_hp_per_officer, "injured_hp": 0, "total_dead": 0, "init_hp": initial_hp_per_officer, "init_chiryaku": o["chiryaku"]} for o in enemy_team]

    for turn in range(1, 9):
        process_turn_deadification(my_team_sample)
        process_turn_deadification(enemy_team_sample)

        my_dmg, my_sk_logs = simulate_turn_attack(my_team_sample, enemy_team_sample, my_advantage_mult)
        enemy_dmg, enemy_sk_logs = simulate_turn_attack(enemy_team_sample, my_team_sample, enemy_advantage_mult)

        cur_my_hp = sum(m["hp"] for m in my_team_sample)
        cur_my_inj = sum(m["injured_hp"] for m in my_team_sample)
        cur_enemy_hp = sum(e["hp"] for e in enemy_team_sample)
        cur_enemy_inj = sum(e["injured_hp"] for e in enemy_team_sample)

        sample_log.append({
            "ターン": f"第{turn}T",
            "自軍ログ": " / ".join(my_sk_logs) if my_sk_logs else "（攻撃のみ）",
            "自残兵(負傷)": f"{cur_my_hp:,} ({cur_my_inj:,})",
            "敵軍ログ": " / ".join(enemy_sk_logs) if enemy_sk_logs else "（攻撃のみ）",
            "敵残兵(負傷)": f"{cur_enemy_hp:,} ({cur_enemy_inj:,})"
        })
        if cur_my_hp == 0 or cur_enemy_hp == 0: break

    st.dataframe(pd.DataFrame(sample_log), hide_index=True, use_container_width=True)
