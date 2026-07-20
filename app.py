import random
import re
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

# --- 特性名から兵種適性加算（ボーナス）を自動判別するヘルパー関数 ---
def parse_trait_troop_bonus(trait_name):
    """
    特性名に含まれるキーワードから適性向上兵種を判定
    """
    bonuses = []
    if any(k in trait_name for k in ["槍", "足軽"]):
        bonuses.append("足軽")
    if any(k in trait_name for k in ["馬", "騎"]):
        bonuses.append("騎兵")
    if any(k in trait_name for k in ["弓"]):
        bonuses.append("弓兵")
    if any(k in trait_name for k in ["砲", "鉄砲"]):
        bonuses.append("鉄砲")
    return bonuses

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

# --- 武将生データ定義（テキストデータより構築） ---
# 形式: [勢力, 名前, レア, コスト, 統率, 武勇, 知略, 速度, 主特性, 1凸特性, 3凸特性, 5凸特性, 固有戦法]
RAW_OFFICER_LIST = [
    # 織田
    ["織田", "織田信長", "名将", 7, 231, 161, 175, 110, "魔王", "覇王", "攻勢Ⅱ", "砲術Ⅱ", "新生"],
    ["織田", "明智光秀", "名将", 7, 183, 140, 220, 116, "連歌百韻", "波風", "知謀Ⅱ", "砲術Ⅱ", "時は今"],
    ["織田", "まつ", "名将", 6, 157, 71, 166, 65, "淑徳", "馬槍術Ⅰ", "忍耐Ⅱ", "守勢Ⅲ", "松柏之操"],
    ["織田", "帰蝶", "名将", 6, 161, 99, 177, 139, "短刀の契", "忍耐Ⅲ", "知恵Ⅱ", "砲術Ⅱ", "帰蝶の舞"],
    ["織田", "荒木村重", "名将", 6, 158, 91, 185, 64, "弓術Ⅱ", "知恵Ⅲ", "看破Ⅱ", "堅固Ⅱ", "形影相弔"],
    ["織田", "佐久間信盛", "名将", 6, 173, 95, 160, 86, "堅固Ⅲ", "固守Ⅱ", "統帥Ⅱ", "馬術Ⅱ", "陣前無我"],
    ["織田", "妻木煕子", "名将", 6, 116, 55, 182, 60, "謀攻Ⅲ", "砲術Ⅲ", "奮戦Ⅱ", "知恵Ⅱ", "内助の賢"],
    ["織田", "柴田勝家", "名将", 6, 162, 208, 138, 167, "瓶割り", "馬術Ⅲ", "武威Ⅱ", "血気Ⅱ", "かかれ柴田"],
    ["織田", "前田慶次", "名将", 6, 127, 206, 132, 123, "傾奇者", "馬槍術Ⅱ", "武威Ⅱ", "牢固Ⅱ", "天下御免"],
    ["織田", "前田利家", "名将", 6, 158, 186, 121, 114, "算盤勘定", "馬槍術Ⅱ", "奮戦Ⅲ", "武威I", "槍の又左"],
    ["織田", "明智秀満", "名将", 6, 147, 129, 182, 61, "統帥Ⅲ", "看破Ⅰ", "攻勢Ⅲ", "砲術Ⅱ", "湖水渡り"],
    ["織田", "稲葉一鉄", "名将", 5, 175, 101, 150, 56, "防護Ⅲ", "統帥Ⅱ", "剛猛I", "槍術Ⅱ", "一徹の意志"],
    ["織田", "森可成", "名将", 5, 145, 189, 112, 125, "槍術Ⅲ", "攻勢Ⅱ", "血気Ⅲ", "器術Ⅲ", "攻めの三左"],
    ["織田", "お市", "名将", 3, 128, 64, 156, 97, "砲術Ⅱ", "牢固Ⅲ", "槍術Ⅰ", "器術Ⅱ", "夢幻泡影"],

    # 豊臣
    ["豊臣", "黒田官兵衛", "名将", 7, 167, 113, 229, 68, "方円の器", "玄謀", "妙計Ⅱ", "砲術Ⅱ", "水の如し"],
    ["豊臣", "豊臣秀吉", "名将", 7, 180, 111, 228, 81, "人たらし", "立身出世", "器術Ⅱ", "弓砲術Ⅱ", "千成瓢箪"],
    ["豊臣", "お初", "名将", 6, 143, 63, 171, 68, "手足之愛", "弓槍術Ⅱ", "攻勢Ⅱ", "知恵Ⅱ", "同気連枝"],
    ["豊臣", "ねね", "名将", 6, 152, 58, 178, 61, "謀攻Ⅲ", "防護Ⅱ", "弓術Ⅱ", "知恵Ⅱ", "比翼連理"],
    ["豊臣", "加藤清正", "名将", 6, 158, 191, 124, 117, "築城名手", "気勢Ⅲ", "槍術Ⅱ", "武威Ⅱ", "破竹の勢い"],
    ["豊臣", "宮部継潤", "名将", 6, 153, 72, 199, 77, "弓槍術Ⅱ", "固守Ⅱ", "知謀Ⅱ", "器術Ⅱ", "積水成淵"],
    ["豊臣", "成田甲斐", "名将", 6, 145, 164, 117, 117, "姫武者", "馬弓術Ⅱ", "猛攻Ⅱ", "防護Ⅱ", "東国無双の麗"],
    ["豊臣", "竹中半兵衛", "名将", 6, 150, 89, 231, 76, "鳳凰", "知謀Ⅲ", "弓術Ⅲ", "看破Ⅱ", "十面埋伏"],
    ["豊臣", "福島正則", "名将", 6, 151, 206, 120, 117, "猪武者", "尽力Ⅱ", "槍術Ⅲ", "弓術Ⅰ", "七本槍筆頭"],
    ["豊臣", "蜂須賀小六", "名将", 5, 126, 166, 173, 79, "弓砲術Ⅱ", "急速Ⅱ", "破敵Ⅲ", "牢固Ⅰ", "楼岸一番"],
    ["豊臣", "可児才蔵", "名将", 4, 97, 183, 104, 95, "武威Ⅲ", "血気Ⅱ", "攻勢Ⅰ", "槍術Ⅲ", "笹の才蔵"],
    ["豊臣", "加藤嘉明", "名将", 3, 135, 146, 148, 98, "弓槍術Ⅱ", "武威Ⅱ", "知略Ⅱ", "牢固Ⅱ", "剛毅木訥"],

    # 徳川
    ["徳川", "酒井忠次", "名将", 7, 187, 187, 153, 119, "血気Ⅲ", "槍術Ⅲ", "統帥Ⅱ", "守勢Ⅰ", "破陣乱舞"],
    ["徳川", "徳川家康", "名将", 7, 231, 155, 169, 61, "三河武士", "古狸", "牢固Ⅱ", "弓槍術Ⅱ", "三河魂"],
    ["徳川", "本多忠勝", "名将", 7, 169, 229, 116, 81, "無傷の誇り", "剛猛Ⅱ", "槍術Ⅱ", "器術Ⅱ", "古今独歩"],
    ["徳川", "お江", "名将", 6, 154, 65, 169, 71, "花枝招展", "馬槍術Ⅱ", "守勢Ⅱ", "知恵Ⅱ", "風姿綽約"],
    ["徳川", "榊原康政", "名将", 6, 155, 182, 140, 151, "馬術Ⅲ", "急速Ⅱ", "血気Ⅲ", "統帥Ⅰ", "無想掃討"],
    ["徳川", "松平信康", "名将", 6, 160, 179, 131, 141, "威勢Ⅲ", "血気Ⅱ", "武威Ⅲ", "槍術Ⅱ", "勇志不抜"],
    ["徳川", "高力清長", "名将", 5, 180, 104, 148, 76, "統帥Ⅲ", "看破Ⅱ", "弓槍術Ⅱ", "守勢Ⅰ", "仏の高力"],
    ["徳川", "本多正信", "名将", 5, 83, 43, 192, 86, "弓術Ⅱ", "看破Ⅲ", "猛攻Ⅰ", "知恵Ⅲ", "非常の器"],

    # 武田
    ["武田", "山県昌景", "名将", 7, 169, 224, 139, 162, "赤備え", "勇烈", "馬術Ⅲ", "気勢Ⅰ", "武田之赤備"],
    ["武田", "真田昌幸", "名将", 7, 176, 105, 231, 76, "老獪", "虚実", "弓砲術Ⅱ", "知恵Ⅰ", "表裏比興"],
    ["武田", "武田信玄", "名将", 7, 202, 191, 194, 139, "甲斐の虎", "人は城", "固守Ⅱ", "馬術Ⅱ", "風林火山"],
    ["武田", "甘利虎泰", "名将", 6, 163, 176, 94, 59, "槍術Ⅲ", "破敵Ⅱ", "急速Ⅱ", "武威Ⅱ", "剛の武者"],
    ["武田", "山本勘助", "名将", 6, 155, 103, 224, 117, "側撃", "弓槍術Ⅱ", "知謀Ⅱ", "攻勢Ⅰ", "啄木鳥"],
    ["武田", "内藤昌豊", "名将", 6, 154, 101, 189, 68, "牢固Ⅲ", "知恵Ⅱ", "馬術Ⅱ", "謀攻Ⅱ", "死灰復然"],
    ["武田", "馬場信春", "名将", 6, 203, 161, 170, 102, "不死身", "剛猛Ⅲ", "馬術Ⅱ", "防護Ⅱ", "鬼美濃"],
    ["武田", "板垣信方", "名将", 6, 165, 88, 176, 47, "知恵Ⅲ", "防護Ⅱ", "器術Ⅲ", "攻勢Ⅰ", "先手必勝"],
    ["武田", "飯富虎昌", "名将", 6, 136, 203, 95, 109, "赤備え", "馬術Ⅲ", "血気Ⅲ", "武威I", "甲山猛虎"],
    ["武田", "一条信龍", "名将", 5, 153, 156, 125, 90, "弓術Ⅱ", "統帥Ⅱ", "防護Ⅱ", "剛猛I", "不屈の精神"],
    ["武田", "岡部元信", "名将", 5, 131, 134, 179, 63, "攻勢Ⅲ", "威勢Ⅱ", "剛猛I", "知恵I", "洞察反撃"],
    ["武田", "原虎胤", "名将", 5, 108, 185, 96, 69, "統帥Ⅲ", "牢固Ⅱ", "剛猛I", "看破Ⅰ", "夜叉美濃"],
    ["武田", "諏訪姫", "名将", 4, 143, 75, 145, 100, "猛攻Ⅲ", "器術Ⅱ", "看破Ⅰ", "攻勢Ⅱ", "諏訪の光"],
]

# --- 全武将統合データベース構築 ---
OFFICER_DATABASE = {}

for item in RAW_OFFICER_LIST:
    faction, name, rare, cost, tousotsu, buyou, chiryaku, speed, t_main, t_r1, t_r3, t_r5, skill_name = item
    
    # 固有戦法の仮パラメータ（発動率100%, 威力120%, 受動, 兵刃 or 計略）
    # 武勇 > 知略 の場合は兵刃、知略 >= 武勇 の場合は計略
    s_attr = "計略" if chiryaku >= buyou else "兵刃"
    s_rate = 100
    s_dmg = 120
    
    # 兵種適性（初期の基礎適性レベル: 全兵種1とし、主特性からボーナス付加）
    base_aptitudes = {"足軽": 1, "騎兵": 1, "弓兵": 1, "鉄砲": 1}
    main_bonus_troops = parse_trait_troop_bonus(t_main)
    for b_troop in main_bonus_troops:
        if b_troop in base_aptitudes:
            base_aptitudes[b_troop] += 1

    # 特性リスト（初期・1凸・3凸・5凸）
    trait_defs = [
        {"req": 0, "name": t_main, "raw": t_main},
        {"req": 1, "name": t_r1, "raw": t_r1},
        {"req": 3, "name": t_r3, "raw": t_r3},
        {"req": 5, "name": t_r5, "raw": t_r5},
    ]

    traits = []
    for td in trait_defs:
        b_troops = parse_trait_troop_bonus(td["raw"])
        # 単一の対応兵種、または複数兵種へ適用
        primary_troop = b_troops[0] if len(b_troops) > 0 else None
        traits.append({
            "req": td["req"],
            "name": td["name"],
            "troop": primary_troop,
            "bonus": 1 if primary_troop else 0,
            "all_bonus_troops": b_troops
        })

    OFFICER_DATABASE[name] = [
        buyou, chiryaku, tousotsu, skill_name, s_rate, s_dmg, "受動", s_attr,
        base_aptitudes, traits
    ]

OFFICER_LIST = sorted(list(OFFICER_DATABASE.keys()))

def get_officer_data(o_name):
    if o_name in OFFICER_DATABASE:
        return OFFICER_DATABASE[o_name]
    else:
        return [
            100, 100, 100, "汎用武将", 50, 100, "能動", "兵刃",
            {"足軽": 1, "騎兵": 1, "弓兵": 1, "鉄砲": 1},
            [
                {"req": 0, "name": "汎用初期", "troop": "足軽", "bonus": 1, "all_bonus_troops": ["足軽"]},
                {"req": 1, "name": "汎用1凸", "troop": "騎兵", "bonus": 1, "all_bonus_troops": ["騎兵"]},
                {"req": 3, "name": "汎用3凸", "troop": "弓兵", "bonus": 1, "all_bonus_troops": ["弓兵"]},
                {"req": 5, "name": "汎用5凸", "troop": "鉄砲", "bonus": 1, "all_bonus_troops": ["鉄砲"]}
            ]
        ]

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

    total_troop_levels = {t: 0 for t in TROOP_TYPES}

    for idx, tab in enumerate(tabs):
        with tab:
            default_idx = OFFICER_LIST.index(default_choices[idx]) if default_choices[idx] in OFFICER_LIST else 0
            o_name = st.selectbox("武将を選択", OFFICER_LIST, index=default_idx, key=f"{team_prefix}_{idx}_select")
            
            o_data = get_officer_data(o_name)
            o_buyou, o_chiryaku, o_tousotsu, db_s1_name, db_s1_rate, db_s1_dmg, db_s1_type, db_s1_attr, troop_aptitudes, traits = o_data

            # ランクアップ（凸数）選択
            rank = st.radio(
                "ランクアップ（凸数）",
                [0, 1, 2, 3, 4, 5],
                format_func=lambda x: "無 (★0)" if x == 0 else f"★{x}",
                horizontal=True,
                key=f"{team_prefix}_{idx}_rank"
            )

            active_traits = []
            for trait in traits:
                is_unlocked = rank >= trait["req"]
                active_traits.append({**trait, "unlocked": is_unlocked})
                
                # 凸特性による兵種適性加算（複数対象特性にも対応）
                if is_unlocked:
                    for b_t in trait.get("all_bonus_troops", []):
                        if b_t in total_troop_levels:
                            total_troop_levels[b_t] += 1

            # 武将本体の基礎兵種適性を加算
            for t_type, val in troop_aptitudes.items():
                if t_type in total_troop_levels:
                    total_troop_levels[t_type] += val

            # UI表示：特性（凸連動）
            st.caption("📜 **特性（凸連動）**")
            trait_cols = st.columns(len(traits))
            for t_idx, trait in enumerate(active_traits):
                with trait_cols[t_idx]:
                    if trait["unlocked"]:
                        st.success(f"**[{trait['req']}凸]** {trait['name']}")
                    else:
                        st.info(f"🔒 **[{trait['req']}凸]** {trait['name']}")

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

    team_troop_level = total_troop_levels.get(selected_troop, 0)

    # 部隊兵種レベル表示
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
    my_team, my_troop, my_troop_lvl = input_team_data("my", "自軍編成", ["織田信長", "柴田勝家", "明智光秀"], default_troop_idx=1) # 騎兵

with main_tab2:
    enemy_team, enemy_troop, enemy_troop_lvl = input_team_data("enemy", "敵軍編成", ["徳川家康", "本多忠勝", "酒井忠次"], default_troop_idx=0) # 足軽

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
