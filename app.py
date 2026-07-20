# -*- coding: utf-8 -*-
import random
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="『信長の野望 真戦』部隊対戦シミュレータ", layout="centered"
)

st.title("⚔️ 部隊対戦シミュレータ")
st.caption("自軍 vs 敵軍 8ターン対戦（兵種適性・凸特性・兵種相性・最低保証床補正・負傷兵・戦法発動順完全実装版）")

# --- 特性データベース定義 ---
TRAIT_DATABASE = {
    "一番槍": {"type": "金帯", "effect": "戦闘中に1回のみ、初めのターンに自身がダメージを与えた後、50%の確率でメイン属性+18", "category": "属性上昇", "characters": {"小島弥太郎": "無凸", "磯野員昌": "無凸"}},
    "三河武士": {"type": "金帯", "effect": "自軍全体は通常攻撃後、15%の確率で自身の次回の被ダメージ-50%", "category": "被ダメージ軽減", "characters": {"徳川家康": "無凸"}},
    "三矢家訓": {"type": "金帯", "effect": "自軍武将3名のメイン属性が異なる場合、そのメイン属性がそれぞれ+8", "category": "属性上昇", "characters": {"毛利元就": "1凸"}},
    "上下一心": {"type": "金帯", "effect": "自軍複数（2～3名）は1ターン目に制御耐性を獲得し、30%の確率で付与される制御状態を無効化する。この効果は一人につき最大1回まで発動可能", "category": "制御耐性", "characters": {"北条氏康": "1凸"}},
    "不死身": {"type": "金帯", "effect": "戦闘中の兵力損害が減少する", "category": "兵力損害軽減", "characters": {"馬場信春": "無凸"}},
    "人たらし": {"type": "金帯", "effect": "友軍を回復し、回復量が超過した場合、50%の確率で1ターンの間、そのメイン属性+15", "category": "回復・属性上昇", "characters": {"豊臣秀吉": "無凸"}},
    "人は城": {"type": "金帯", "effect": "自軍全体の統率+5％", "category": "固有特性", "characters": {"武田信玄": "1凸"}},
    "側撃": {"type": "金帯", "effect": "通常攻撃は14%の確率で攻撃対象に疲弊を付与、1ターン持続。自身が通常攻撃を受けるとそのターンの間疲弊が無効になる", "category": "制御", "characters": {"山本勘助": "無凸"}},
    "傾奇者": {"type": "金帯", "effect": "12%の確率で制御を無効化。自身の装備に付与された特技1つに付き、確率が1%増加", "category": "固有特性", "characters": {"前田慶次": "無凸"}},
    "先駆け": {"type": "金帯", "effect": "3ターン目終了まで、自身が制御状態を付与された際、40%の確率でそれを無効化（最大2回発動）", "category": "制御耐性", "characters": {"柿崎景家": "1凸"}},
    "公家趣味": {"type": "金帯", "effect": "敵軍大将の所持家宝の効果を無効にし、自身がその効果を獲得", "category": "家宝", "characters": {"今川義元": "無凸"}},
    "勇烈": {"type": "金帯", "effect": "毎ターン行動前に武勇を14（会心状態依存）獲得（1ターン持続）", "category": "固有特性", "characters": {"山県昌景": "1凸"}},
    "古狸": {"type": "金帯", "effect": "他勢力の武将2人（同じ勢力）と組むと、自身の所属もその勢力に変化", "category": "勢力変化", "characters": {"徳川家康": "1凸"}},
    "四州の雄": {"type": "金帯", "effect": "自軍全体の通常攻撃ダメージ+6%、駐屯中の場合は12%", "category": "通常攻撃与ダメージ上昇", "characters": {"長宗我部元親": "無凸"}},
    "姫城督": {"type": "金帯", "effect": "兵刃ダメージを6回与えるたびに、兵力が最も少ない自軍単体を回復（回復率98%、武勇依存。最大2回まで）", "category": "回復", "characters": {"立花誾千代": "1凸"}},
    "姫武者": {"type": "金帯", "effect": "2回攻撃するたびに、自身は2%の会心を獲得（最大8回まで重ね掛け可能）", "category": "会心", "characters": {"成田甲斐": "無凸"}},
    "手足之愛": {"type": "金帯", "effect": "毎ターン最初にほかの武将を回復した時、1ターンの間、自身の統率が回復した対象のメイン属性の12%分増加", "category": "回復・属性上昇", "characters": {"お初": "無凸"}},
    "方円の器": {"type": "金帯", "effect": "3ターン目から、毎ターン初めて計略ダメージを与えるとき、50%の確率で自軍全体の知略が5%増加、最大2回まで重ねがけ可能", "category": "属性上昇", "characters": {"黒田官兵衛": "無凸"}},
    "昇り龍": {"type": "金帯", "effect": "部隊の騎兵・鉄砲レベルが3増加", "category": "兵種レベル", "characters": {"伊達政宗": "1凸"}},
    "死守": {"type": "金帯", "effect": "戦闘中、自身の兵力が初めて50％以下に低下すると兵力を大量に回復", "category": "固有特性", "characters": {"鳥居元忠": "無凸"}},
    "求道": {"type": "金帯", "effect": "雑賀本願寺以外の友軍1名を雑賀本願寺に変更。発動していない場合、自軍全体の計略被ダメージが5％低下", "category": "タグ変更・計略被ダメージ軽減", "characters": {"本願寺顕如": "無凸"}},
    "波風": {"type": "金帯", "effect": "通常攻撃時、80%の確率で対象の知略を2吸収（最大10回まで重ね掛け可能）。低い確率で自軍大将を攻撃", "category": "属性吸収", "characters": {"明智光秀": "1凸"}},
    "淑徳": {"type": "金帯", "effect": "戦闘中、2ターン目まで、自軍大将が毎ターン最初に無策、封撃または混乱を付与された時、自身は80%の確率でそれを肩代わり", "category": "制御肩代わり", "characters": {"まつ": "無凸"}},
    "清濁併呑": {"type": "金帯", "effect": "25%の確率で自身がこれから受ける通常攻撃を無効化", "category": "通常攻撃無効", "characters": {"松永久秀": "無凸"}},
    "無傷の誇り": {"type": "金帯", "effect": "戦闘中の兵力損害が減少する", "category": "兵力損害軽減", "characters": {"本多忠勝": "無凸"}},
    "物外軒": {"type": "金帯", "effect": "戦闘中、4ターン目まで能動・突撃戦法の発動確率が4.5%上昇（茶道レベル依存）", "category": "発動率上昇", "characters": {"三好実休": "無凸"}},
    "独眼竜": {"type": "金帯", "effect": "毎ターン行動前、自身の与ダメージが1ターンの間上昇（上昇値は自身の武勇と知略の差が小さいほど大きくなり、最大10％上昇。自身が大将の場合、最大15％上昇。その差が20％を超えた場合は無効）", "category": "与ダメージ上昇", "characters": {"伊達政宗": "無凸"}},
    "猪武者": {"type": "金帯", "effect": "兵刃ダメージを与えると、60%の確率で1%の会心を獲得し、会心ダメージ+1%（最大6回まで重ね掛け可能）", "category": "会心", "characters": {"福島正則": "無凸"}},
    "玄謀": {"type": "金帯", "effect": "自身が大将の場合、統率が最も高い自軍武将の大将技を発動させる。この効果が発動しなかった場合、3%回避を獲得", "category": "大将技・回避", "characters": {"黒田官兵衛": "1凸"}},
    "瓶割り": {"type": "金帯", "effect": "5ターン目以降、10%の離反を獲得。自身の兵力が50%以下の場合、与ダメージが10%増加", "category": "離反・与ダメージ上昇", "characters": {"柴田勝家": "無凸"}},
    "甲斐の虎": {"type": "金帯", "effect": "部隊行動速度が10%上昇し、士気消費が10%減少する。占領、攻城命令の実行中は効果が2倍", "category": "行軍・士気", "characters": {"武田信玄": "無凸"}},
    "短刀の契": {"type": "金帯", "effect": "戦闘中、自軍男性大将の全属性+2%", "category": "属性上昇", "characters": {"帰蝶": "無凸"}},
    "禄壽応穏": {"type": "金帯", "effect": "部隊士気上限+5、最大レベルの資源建築1つにつき追加で+3", "category": "士気", "characters": {"北条氏康": "無凸"}},
    "立身出世": {"type": "金帯", "effect": "10回レベルアップするごとに、フリーポイント+3", "category": "育成", "characters": {"豊臣秀吉": "1凸"}},
    "算盤勘定": {"type": "金帯", "effect": "銀銭の産出量に応じて武勇上昇（最大+16）", "category": "内政・属性上昇", "characters": {"前田利家": "無凸"}},
    "築城名手": {"type": "金帯", "effect": "天守レベルが1上がるごとに、統率+2.4", "category": "内政・属性上昇", "characters": {"加藤清正": "無凸"}},
    "義の将": {"type": "金帯", "effect": "混乱になる確率低下", "category": "制御耐性", "characters": {"上杉謙信": "無凸"}},
    "老功古実": {"type": "金帯", "effect": "初めて能動戦法ダメージを受けた際、その発動者の知略-15", "category": "弱体", "characters": {"宇佐美定満": "無凸"}},
    "老獪": {"type": "金帯", "effect": "自勢力を大将勢力に変換。未変換時は心攻8%", "category": "勢力変化・心攻", "characters": {"真田昌幸": "無凸"}},
    "腰元斉射": {"type": "金帯", "effect": "通常攻撃後、20%の確率で対象に2ターン持続する麻痺（毎ターン30%の確率で行動不能）を付与", "category": "制御", "characters": {"立花誾千代": "無凸"}},
    "花枝招展": {"type": "金帯", "effect": "自身が通常攻撃を受けると、45%の確率（魅力依存）で自身の兵力を回復（回復率68%、知略依存。最大3回まで）", "category": "回復", "characters": {"お江": "無凸"}},
    "虚実": {"type": "金帯", "effect": "混乱中の敵がいる時、自身被ダメージ-3%（真田家武将は50%適用）", "category": "被ダメージ軽減", "characters": {"真田昌幸": "1凸"}},
    "覇王": {"type": "金帯", "effect": "自身が兵力を回復する時、敵軍単体の兵力を回復量の10%分削る（効果上限は自身の兵力の10%）", "category": "回復連動・兵力損失", "characters": {"織田信長": "1凸"}},
    "謀神": {"type": "金帯", "effect": "計略ダメージを与えた際、25%の確率でダメージ量に両者の知略差が反映される（各戦闘につき3回まで発動可能）", "category": "計略与ダメージ", "characters": {"毛利元就": "無凸"}},
    "赤備え": {"type": "金帯", "effect": "初めて通常攻撃を行った後、攻撃対象の統率-18（重ね掛け可能）", "category": "弱体", "characters": {"飯富虎昌": "無凸", "山県昌景": "無凸"}},
    "越後の龍": {"type": "金帯", "effect": "このターンでダメージを与えなかった場合、次の行動時まで自身の被ダメージ-22%", "category": "被ダメージ軽減", "characters": {"上杉謙信": "1凸"}},
    "足軽大将": {"type": "金帯", "effect": "部隊の足軽レベル+3、レベル上限+1", "category": "兵種大将", "characters": {"長宗我部元親": "1凸"}},
    "連歌百韻": {"type": "金帯", "effect": "能動戦法の発動に成功すると、7%の確率で再度発動判定を行う。固有戦法の場合、再判定の確率35%", "category": "能動発動判定", "characters": {"明智光秀": "無凸"}},
    "金城鉄壁": {"type": "金帯", "effect": "通常攻撃を受けた時、敵軍が弱体化状態であれば、30%の確率で兵力を回復（回復率52%、統率依存）", "category": "回復", "characters": {"長野業正": "無凸"}},
    "鉄砲大将": {"type": "金帯", "effect": "部隊の鉄砲レベル+3、レベル上限+1", "category": "兵種大将", "characters": {"津田算長": "無凸", "鈴木佐大夫": "無凸"}},
    "雄略絶倫": {"type": "金帯", "effect": "通常攻撃を受けた際、攻撃者から自身のメイン属性を2吸収、最大8回まで重ね掛け可能", "category": "固有特性", "characters": {"高橋紹運": "無凸"}},
    "雷の化身": {"type": "金帯", "effect": "通常攻撃を受けると、低確率で攻撃者に麻痺を付与", "category": "制御", "characters": {"立花道雪": "無凸"}},
    "騎兵大将": {"type": "金帯", "effect": "部隊の騎兵レベル+3、レベル上限+1", "category": "兵種大将", "characters": {"柿崎景家": "無凸", "北条綱成": "無凸"}},
    "弓兵大将": {"type": "金帯", "effect": "部隊の弓兵レベル+3、レベル上限+1", "category": "兵種大将", "characters": {"今川義元": "1凸"}},
    "魔王": {"type": "金帯", "effect": "自身の行動後、敵軍の各武将の兵力が初めて50%以下になると、ランダムに5%以下の兵力を損失", "category": "兵力損失", "characters": {"織田信長": "無凸"}},
    "鳳凰": {"type": "金帯", "effect": "自身の被ダメージが1.5%上昇する。戦闘開始から3ターン目以降、自身が初めて致命ダメージを受けた際にそのダメージを無効化する", "category": "致命回避", "characters": {"竹中半兵衛": "無凸"}}
}

# --- 兵種相性の関係定義 ---
TROOP_TYPES = ["足軽", "騎兵", "弓兵", "鉄砲"]

def get_troop_advantage(attacker_type, defender_type):
    adv_map = {
        "足軽": "騎兵",
        "騎兵": "弓兵",
        "弓兵": "鉄砲",
        "鉄砲": "足軽",
    }
    if adv_map.get(attacker_type) == defender_type:
        return 1.125
    elif adv_map.get(defender_type) == attacker_type:
        return 0.875
    return 1.0

def parse_trait_troop_bonus(trait_name):
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

# --- 伝授・事件戦法データベース（カテゴリ属性: 指揮 / 能動 / 突撃 / 受動） ---
SKILL_DATABASE = {
    "（なし）": [0, 0, "-", "-", "兵刃"],
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
    "有備無患": [40, 60, "S", "能動", "回復"],
    "按甲休兵": [100, 140, "S", "受動", "休養_非依存"],
    "懐柔": [35, 48.9, "A", "能動", "休養"],
    "守禦": [100, 100, "A", "指揮", "回復_非依存"],
    "恵風和雨": [40, 88, "S", "指揮", "回復"],
}
SKILL_LIST = sorted(list(SKILL_DATABASE.keys()))

# --- 武将生データ定義 ---
RAW_OFFICER_LIST = [
    ["織田", "織田信長", "名将", 7, 231, 161, 175, 110, 120, 130, "魔王", "覇王", "攻勢Ⅱ", "砲術Ⅱ", "新生"],
    ["織田", "明智光秀", "名将", 7, 183, 140, 220, 116, 110, 110, "連歌百韻", "波風", "知謀Ⅱ", "砲術Ⅱ", "時は今"],
    ["織田", "まつ", "名将", 6, 157, 71, 166, 65, 100, 100, "淑徳", "馬槍術Ⅰ", "忍耐Ⅱ", "守勢Ⅲ", "松柏之操"],
    ["織田", "帰蝶", "名将", 6, 161, 99, 177, 139, 100, 100, "短刀の契", "忍耐Ⅲ", "知恵Ⅱ", "砲術Ⅱ", "帰蝶の舞"],
    ["織田", "荒木村重", "名将", 6, 158, 91, 185, 64, 100, 100, "弓術Ⅱ", "知恵Ⅲ", "看破Ⅱ", "堅固Ⅱ", "形影相弔"],
    ["織田", "佐久間信盛", "名将", 6, 173, 95, 160, 86, 100, 100, "堅固Ⅲ", "固守Ⅱ", "統帥Ⅱ", "馬術Ⅱ", "陣前無我"],
    ["織田", "妻木煕子", "名将", 6, 116, 55, 182, 60, 100, 100, "謀攻Ⅲ", "砲術Ⅲ", "奮戦Ⅱ", "知恵Ⅱ", "内助の賢"],
    ["織田", "柴田勝家", "名将", 6, 162, 208, 138, 167, 100, 100, "瓶割り", "馬術Ⅲ", "武威Ⅱ", "血気Ⅱ", "かかれ柴田"],
    ["織田", "前田慶次", "名将", 6, 127, 206, 132, 123, 100, 100, "傾奇者", "馬槍術Ⅱ", "武威Ⅱ", "牢固Ⅱ", "天下御免"],
    ["織田", "前田利家", "名将", 6, 158, 186, 121, 114, 100, 100, "算盤勘定", "馬槍術Ⅱ", "奮戦Ⅲ", "武威I", "槍の又左"],
    ["織田", "明智秀満", "名将", 6, 147, 129, 182, 61, 100, 100, "統帥Ⅲ", "看破Ⅰ", "攻勢Ⅲ", "砲術Ⅱ", "湖水渡り"],
    ["織田", "稲葉一鉄", "名将", 5, 175, 101, 150, 56, 100, 100, "防護Ⅲ", "統帥Ⅱ", "剛猛I", "槍術Ⅱ", "一徹の意志"],
    ["織田", "森可成", "名将", 5, 145, 189, 112, 125, 100, 100, "槍術Ⅲ", "攻勢Ⅱ", "血気Ⅲ", "器術Ⅲ", "攻めの三左"],
    ["織田", "お市", "名将", 3, 128, 64, 156, 97, 100, 100, "砲術Ⅱ", "牢固Ⅲ", "槍術Ⅰ", "器術Ⅱ", "夢幻泡影"],

    ["豊臣", "黒田官兵衛", "名将", 7, 167, 113, 229, 68, 110, 120, "方円の器", "玄謀", "妙計Ⅱ", "砲術Ⅱ", "水の如し"],
    ["豊臣", "豊臣秀吉", "名将", 7, 180, 111, 228, 81, 110, 120, "人たらし", "立身出世", "器術Ⅱ", "弓砲術Ⅱ", "千成瓢箪"],
    ["豊臣", "お初", "名将", 6, 143, 63, 171, 68, 100, 100, "手足之愛", "弓槍術Ⅱ", "攻勢Ⅱ", "知恵Ⅱ", "同気連枝"],
    ["豊臣", "ねね", "名将", 6, 152, 58, 178, 61, 100, 100, "謀攻Ⅲ", "防護Ⅱ", "弓術Ⅱ", "知恵Ⅱ", "比翼連理"],
    ["豊臣", "加藤清正", "名将", 6, 158, 191, 124, 117, 100, 100, "築城名手", "気勢Ⅲ", "槍術Ⅱ", "武威Ⅱ", "破竹の勢い"],
    ["豊臣", "宮部継潤", "名将", 6, 153, 72, 199, 77, 100, 100, "弓槍術Ⅱ", "固守Ⅱ", "知謀Ⅱ", "器術Ⅱ", "積水成淵"],
    ["豊臣", "成田甲斐", "名将", 6, 145, 164, 117, 117, 100, 100, "姫武者", "馬弓術Ⅱ", "猛攻Ⅱ", "防護Ⅱ", "東国無双の麗"],
    ["豊臣", "竹中半兵衛", "名将", 6, 150, 89, 231, 76, 100, 100, "鳳凰", "知謀Ⅲ", "弓術Ⅲ", "看破Ⅱ", "十面埋伏"],
    ["豊臣", "福島正則", "名将", 6, 151, 206, 120, 117, 100, 100, "猪武者", "尽力Ⅱ", "槍術Ⅲ", "弓術Ⅰ", "七本槍筆頭"],
    ["豊臣", "蜂須賀小六", "名将", 5, 126, 166, 173, 79, 100, 100, "弓砲術Ⅱ", "急速Ⅱ", "破敵Ⅲ", "牢固Ⅰ", "楼岸一番"],
    ["豊臣", "可児才蔵", "名将", 4, 97, 183, 104, 95, 100, 100, "武威Ⅲ", "血気Ⅱ", "攻勢Ⅰ", "槍術Ⅲ", "笹の才蔵"],
    ["豊臣", "加藤嘉明", "名将", 3, 135, 146, 148, 98, 100, 100, "弓槍術Ⅱ", "武威Ⅱ", "知略Ⅱ", "牢固Ⅱ", "剛毅木訥"],

    ["徳川", "酒井忠次", "名将", 7, 187, 187, 153, 119, 110, 110, "血気Ⅲ", "槍術Ⅲ", "統帥Ⅱ", "守勢Ⅰ", "破陣乱舞"],
    ["徳川", "徳川家康", "名将", 7, 231, 155, 169, 61, 120, 130, "三河武士", "古狸", "牢固Ⅱ", "弓槍術Ⅱ", "三河魂"],
    ["徳川", "本多忠勝", "名将", 7, 169, 229, 116, 81, 120, 110, "無傷の誇り", "剛猛Ⅱ", "槍術Ⅱ", "器術Ⅱ", "古今独歩"],
    ["徳川", "お江", "名将", 6, 154, 65, 169, 71, 100, 100, "花枝招展", "馬槍術Ⅱ", "守勢Ⅱ", "知恵Ⅱ", "風姿綽約"],
    ["徳川", "榊原康政", "名将", 6, 155, 182, 140, 151, 100, 100, "馬術Ⅲ", "急速Ⅱ", "血気Ⅲ", "統帥Ⅰ", "無想掃討"],
    ["徳川", "松平信康", "名将", 6, 160, 179, 131, 141, 100, 100, "威勢Ⅲ", "血気Ⅱ", "武威Ⅲ", "槍術Ⅱ", "勇志不抜"],
    ["徳川", "高力清長", "名将", 5, 180, 104, 148, 76, 100, 100, "統帥Ⅲ", "看破Ⅱ", "弓槍術Ⅱ", "守勢Ⅰ", "仏の高力"],
    ["徳川", "本多正信", "名将", 5, 83, 43, 192, 86, 100, 100, "弓術Ⅱ", "看破Ⅲ", "猛攻Ⅰ", "知恵Ⅲ", "非常の器"],

    ["武田", "山県昌景", "名将", 7, 169, 224, 139, 162, 110, 120, "赤備え", "勇烈", "馬術Ⅲ", "気勢Ⅰ", "武田之赤備"],
    ["武田", "真田昌幸", "名将", 7, 176, 105, 231, 76, 110, 120, "老獪", "虚実", "弓砲術Ⅱ", "知恵Ⅰ", "表裏比興"],
    ["武田", "武田信玄", "名将", 7, 202, 191, 194, 139, 130, 130, "甲斐の虎", "人は城", "固守Ⅱ", "馬術Ⅱ", "風林火山"],
    ["武田", "甘利虎泰", "名将", 6, 163, 176, 94, 59, 100, 100, "槍術Ⅲ", "破敵Ⅱ", "急速Ⅱ", "武威Ⅱ", "剛の武者"],
    ["武田", "山本勘助", "名将", 6, 155, 103, 224, 117, 100, 100, "側撃", "弓槍術Ⅱ", "知謀Ⅱ", "攻勢Ⅰ", "啄木鳥"],
    ["武田", "内藤昌豊", "名将", 6, 154, 101, 189, 68, 100, 100, "牢固Ⅲ", "知恵Ⅱ", "馬術Ⅱ", "謀攻Ⅱ", "死灰復然"],
    ["武田", "馬場信春", "名将", 6, 203, 161, 170, 102, 110, 110, "不死身", "剛猛Ⅲ", "馬術Ⅱ", "防護Ⅱ", "鬼美濃"],
    ["武田", "板垣信方", "名将", 6, 165, 88, 176, 47, 100, 100, "知恵Ⅲ", "防護Ⅱ", "器術Ⅲ", "攻勢Ⅰ", "先手必勝"],
    ["武田", "飯富虎昌", "名将", 6, 136, 203, 95, 109, 100, 100, "赤備え", "馬術Ⅲ", "血気Ⅲ", "武威I", "甲山猛虎"],
    ["武田", "一条信龍", "名将", 5, 153, 156, 125, 90, 100, 100, "弓術Ⅱ", "統帥Ⅱ", "防護Ⅱ", "剛猛I", "不屈の精神"],
    ["武田", "岡部元信", "名将", 5, 131, 134, 179, 63, 100, 100, "攻勢Ⅲ", "威勢Ⅱ", "剛猛I", "知恵I", "洞察反撃"],
    ["武田", "原虎胤", "名将", 5, 108, 185, 96, 69, 100, 100, "統帥Ⅲ", "牢固Ⅱ", "剛猛I", "看破Ⅰ", "夜叉美濃"],
    ["武田", "諏訪姫", "名将", 4, 143, 75, 145, 100, 100, 100, "猛攻Ⅲ", "器術Ⅱ", "看破Ⅰ", "攻勢Ⅱ", "諏訪の光"],

    ["上杉", "柿崎景家", "名将", 7, 157, 222, 137, 135, 110, 110, "騎兵大将", "先駆け", "血気Ⅱ", "猛攻Ⅱ", "越後二天"],
    ["上杉", "上杉謙信", "名将", 7, 186, 247, 124, 138, 120, 130, "義の将", "越後の龍", "破敵Ⅱ", "馬術Ⅱ", "軍神"],
    ["上杉", "宇佐美定満", "名将", 6, 153, 112, 209, 103, 100, 100, "老功古実", "堅固Ⅲ", "弓槍術Ⅱ", "馬術Ⅰ", "越後流軍学"],
    ["上杉", "甘粕景持", "名将", 6, 147, 186, 150, 94, 100, 100, "牢固Ⅲ", "気勢Ⅱ", "急速Ⅱ", "砲術Ⅱ", "疾風怒濤"],
    ["上杉", "太田資正", "名将", 6, 159, 179, 141, 155, 100, 100, "血気Ⅲ", "急速Ⅱ", "猛攻Ⅲ", "槍術Ⅱ", "三楽犬"],
    ["上杉", "小島弥太郎", "名将", 5, 104, 193, 57, 105, 100, 100, "一番槍", "槍術Ⅱ", "血気Ⅱ", "牢固Ⅱ", "鬼小島"],
    ["上杉", "仙桃院", "名将", 5, 148, 67, 140, 94, 100, 100, "猛攻Ⅲ", "急速Ⅱ", "忍耐Ⅱ", "馬術Ⅰ", "献身"],
    ["上杉", "千坂景親", "名将", 5, 164, 161, 106, 96, 100, 100, "槍術Ⅱ", "剛猛Ⅱ", "統帥Ⅱ", "堅固Ⅰ", "耐苦鍛錬"],
    ["上杉", "樋口兼豊", "名将", 5, 139, 89, 165, 122, 100, 100, "知謀Ⅲ", "急速Ⅰ", "知恵Ⅱ", "看破Ⅱ", "密報通暁"],
    ["上杉", "河田長親", "名将", 4, 146, 69, 166, 126, 100, 100, "知謀Ⅲ", "謀攻Ⅱ", "急速Ⅱ", "馬術Ⅰ", "先制攻撃"],

    ["群雄", "今川義元", "名将", 7, 194, 174, 177, 132, 110, 120, "公家趣味", "弓兵大将", "善戦Ⅱ", "統帥Ⅱ", "海道一"],
    ["群雄", "松永久秀", "名将", 7, 173, 113, 222, 110, 110, 120, "清濁併呑", "防護Ⅱ", "砲術Ⅲ", "心尽Ⅰ", "梟雄の計"],
    ["群雄", "長宗我部元親", "名将", 7, 187, 188, 152, 96, 110, 110, "四州の雄", "足軽大将", "攻勢Ⅱ", "固守Ⅱ", "鬼若子"],
    ["群雄", "陶晴賢", "名将", 7, 166, 185, 149, 85, 110, 110, "血気Ⅲ", "看破Ⅱ", "武威Ⅲ", "馬術Ⅰ", "冷徹無情"],
    ["群雄", "北条綱成", "名将", 7, 165, 224, 155, 154, 110, 120, "騎兵大将", "血気Ⅲ", "武威Ⅱ", "牢固Ⅰ", "地黄八幡"],
    ["群雄", "本願寺顕如", "名将", 7, 182, 119, 180, 78, 110, 120, "求道", "看破Ⅲ", "知謀Ⅰ", "槍砲術Ⅱ", "一切皆空"],
    ["群雄", "毛利元就", "名将", 7, 180, 110, 247, 63, 110, 130, "謀神", "三矢家訓", "謀攻Ⅱ", "弓術Ⅱ", "百万一心"],
    ["群雄", "立花道雪", "名将", 7, 173, 193, 148, 120, 110, 110, "雷の化身", "武威Ⅱ", "槍術Ⅱ", "尽力Ⅲ", "電光雷轟"],
    ["群雄", "立花誾千代", "名将", 7, 163, 200, 136, 111, 110, 110, "近衛斉射", "姫城督", "槍砲術Ⅱ", "武威Ⅰ", "疾風迅雷"],
    ["群雄", "伊達晴宗", "名将", 6, 156, 181, 133, 112, 100, 100, "看破Ⅲ", "固守Ⅱ", "馬砲術Ⅱ", "攻勢Ⅰ", "掃疑平乱"],
    ["群雄", "高橋紹運", "名将", 6, 184, 190, 168, 107, 100, 100, "雄略絶倫", "牢固Ⅲ", "攻勢Ⅰ", "弓槍術Ⅱ", "豊後の戦陣"],
    ["群雄", "寿桂尼", "名将", 6, 148, 35, 183, 34, 100, 100, "知恵Ⅲ", "猛攻Ⅱ", "謀攻Ⅱ", "弓術Ⅱ", "尼御台"],
    ["群雄", "真柄直隆", "名将", 6, 108, 202, 112, 100, 100, 100, "槍術Ⅱ", "血気Ⅲ", "急速Ⅱ", "武威I", "怪力無双"],
    ["群雄", "浅井長政", "名将", 6, 161, 184, 129, 123, 100, 100, "槍砲術Ⅱ", "固守Ⅱ", "武威Ⅲ", "血気Ⅰ", "信義貫徹"],
    ["群雄", "大祝鶴", "名将", 6, 144, 171, 142, 75, 100, 100, "破敵Ⅲ", "統帥Ⅱ", "忍耐Ⅰ", "弓槍術Ⅰ", "月華鶴影"],
    ["群雄", "大内義隆", "名将", 6, 172, 78, 150, 73, 100, 100, "統帥Ⅲ", "謀攻Ⅱ", "砲術Ⅱ", "忍耐Ⅰ", "末世の道者"],
    ["群雄", "島津貴久", "名将", 6, 160, 100, 178, 84, 100, 100, "砲術Ⅲ", "守勢Ⅱ", "攻勢Ⅱ", "急速Ⅰ", "旋乾転坤"],
    ["群雄", "北条氏康", "名将", 6, 182, 137, 185, 100, 110, 110, "禄寿応穏", "上下一心", "堅固Ⅱ", "槍術Ⅱ", "相模の獅子"],
    ["群雄", "鈴木佐大夫", "名将", 6, 151, 179, 157, 103, 100, 100, "鉄砲大将", "牢固Ⅲ", "破敵Ⅱ", "急速Ⅱ", "弾嵐雨霰"],
    ["群雄", "安宅冬康", "名将", 5, 145, 72, 161, 84, 100, 100, "弓術Ⅲ", "固守Ⅲ", "堅固Ⅱ", "忍耐Ⅰ", "一舟軒"],
    ["群雄", "安東愛季", "名将", 5, 174, 110, 174, 70, 100, 100, "牢固Ⅲ", "看破Ⅱ", "知恵Ⅱ", "器術Ⅰ", "斗星北天"],
    ["群雄", "伊達輝宗", "名将", 5, 153, 80, 134, 88, 100, 100, "統帥Ⅲ", "馬砲術Ⅰ", "防護Ⅲ", "剛猛Ⅰ", "樽俎折衝"],
    ["群雄", "斎藤義龍", "名将", 5, 165, 163, 142, 108, 100, 100, "馬術Ⅱ", "看破Ⅱ", "堅固Ⅲ", "攻勢Ⅱ", "傲岸不遜"],
    ["群雄", "十河一存", "名将", 5, 123, 205, 104, 106, 100, 100, "槍術Ⅲ", "武威Ⅱ", "統帥Ⅰ", "血気Ⅲ", "鬼十河"],
    ["群雄", "瑞溪院", "名将", 5, 138, 45, 143, 77, 100, 100, "堅固Ⅲ", "弓術Ⅱ", "知恵Ⅲ", "馬術Ⅱ", "諸行無常"],
    ["群雄", "相馬盛胤", "名将", 5, 156, 165, 98, 107, 100, "100", "馬術Ⅲ", "攻勢Ⅱ", "統帥Ⅱ", "急速Ⅲ", "先陣鼓舞"],
    ["群雄", "津田算長", "名将", 5, 145, 156, 145, 94, 100, 100, "鉄砲大将", "武威Ⅱ", "統帥Ⅱ", "知恵Ⅱ", "津田流砲術"],
    ["群雄", "南部晴政", "名将", 5, 164, 169, 79, 152, 100, 100, "武威Ⅲ", "馬術Ⅱ", "牢固Ⅱ", "攻勢Ⅰ", "満ちゆく月"],
    ["群雄", "尼子晴久", "名将", 5, 162, 121, 162, 59, 100, 100, "馬術Ⅱ", "知恵Ⅲ", "防護Ⅱ", "急速Ⅱ", "綱紀粛正"],
    ["群雄", "毛利隆元", "名将", 5, 165, 92, 165, 56, 100, 100, "弓術Ⅱ", "知恵Ⅲ", "固守Ⅱ", "攻勢Ⅱ", "一心一徳"],
    ["群雄", "朝倉義景", "名将", 4, 110, 53, 112, 158, 100, 100, "牢固Ⅲ", "統帥Ⅱ", "忍耐Ⅰ", "急速Ⅱ", "落花啼鳥"],
    ["群雄", "里見義堯", "名将", 4, 165, 106, 165, 80, 100, 100, "弓槍術Ⅱ", "統帥Ⅱ", "防護Ⅲ", "知恵Ⅱ", "仁者の沈勇"],
]

OFFICER_DATABASE = {}
for item in RAW_OFFICER_LIST:
    faction, name, rare, cost, tousotsu, buyou, chiryaku, speed, db_s1_rate, db_s1_dmg, t_main, t_r1, t_r3, t_r5, skill_name = item
    s_attr = "計略" if chiryaku >= buyou else "兵刃"
    base_aptitudes = {"足軽": 1, "騎兵": 1, "弓兵": 1, "鉄砲": 1}
    for b_troop in parse_trait_troop_bonus(t_main):
        if b_troop in base_aptitudes:
            base_aptitudes[b_troop] += 1

    traits = [
        {"req": 0, "name": t_main, "troop": parse_trait_troop_bonus(t_main)[0] if parse_trait_troop_bonus(t_main) else None},
        {"req": 1, "name": t_r1, "troop": parse_trait_troop_bonus(t_r1)[0] if parse_trait_troop_bonus(t_r1) else None},
        {"req": 3, "name": t_r3, "troop": parse_trait_troop_bonus(t_r3)[0] if parse_trait_troop_bonus(t_r3) else None},
        {"req": 5, "name": t_r5, "troop": parse_trait_troop_bonus(t_r5)[0] if parse_trait_troop_bonus(t_r5) else None},
    ]
    OFFICER_DATABASE[name] = [buyou, chiryaku, tousotsu, speed, skill_name, db_s1_rate, db_s1_dmg, "能動", s_attr, base_aptitudes, traits, faction]

OFFICER_LIST = sorted(list(OFFICER_DATABASE.keys()))

def get_officer_data(o_name):
    return OFFICER_DATABASE.get(o_name, [100, 100, 100, 100, "汎用", 50, 100, "能動", "兵刃", {"足軽": 1, "騎兵": 1, "弓兵": 1, "鉄砲": 1}, [], "群雄"])

# --- UI構築ヘルパー ---
def input_team_data(team_prefix, team_name, default_choices, default_troop_idx):
    st.markdown(f"### {team_name}")
    selected_troop = st.radio(
        f"{team_name}の兵種", TROOP_TYPES, index=default_troop_idx, horizontal=True, key=f"{team_prefix}_troop"
    )

    roles = ["大将", "副将1", "副将2"]
    team_officers = []
    total_troop_levels = {t: 0 for t in TROOP_TYPES}

    for idx, role in enumerate(roles):
        default_idx = OFFICER_LIST.index(default_choices[idx]) if default_choices[idx] in OFFICER_LIST else 0
        
        with st.expander(f"【{role}】 {default_choices[idx]}", expanded=(idx==0)):
            col_sel1, col_sel2 = st.columns([2, 1])
            with col_sel1:
                o_name = st.selectbox(f"{role} 武将選択", OFFICER_LIST, index=default_idx, key=f"{team_prefix}_{idx}_select")
            with col_sel2:
                rank = st.selectbox("凸数", [0, 1, 2, 3, 4, 5], format_func=lambda x: "無 (★0)" if x==0 else f"★{x}", key=f"{team_prefix}_{idx}_rank")

            o_data = get_officer_data(o_name)
            o_buyou, o_chiryaku, o_tousotsu, o_speed, db_s1_name, db_s1_rate, db_s1_dmg, db_s1_type, db_s1_attr, troop_aptitudes, traits, o_faction = o_data

            st.markdown("##### 属性 / ステータス")
            
            max_pts = 50 + (rank * 10)
            pt_key = f"{team_prefix}_{idx}_remaining_pts"
            rank_cache_key = f"{team_prefix}_{idx}_last_rank"
            alloc_keys = {
                "武勇": f"{team_prefix}_{idx}_alloc_buyou",
                "統率": f"{team_prefix}_{idx}_alloc_tousotsu",
                "知略": f"{team_prefix}_{idx}_alloc_chiryaku",
                "速度": f"{team_prefix}_{idx}_alloc_speed",
            }

            for k in alloc_keys.values():
                if k not in st.session_state:
                    st.session_state[k] = 0

            if pt_key not in st.session_state or st.session_state.get(rank_cache_key) != rank:
                st.session_state[rank_cache_key] = rank
                current_allocated_sum = sum(st.session_state[k] for k in alloc_keys.values())
                if current_allocated_sum > max_pts:
                    for k in alloc_keys.values():
                        st.session_state[k] = 0
                    st.session_state[pt_key] = max_pts
                else:
                    st.session_state[pt_key] = max_pts - current_allocated_sum

            if st.button("全リセット", key=f"{team_prefix}_{idx}_reset"):
                st.session_state[pt_key] = max_pts
                for k in alloc_keys.values():
                    st.session_state[k] = 0
                st.rerun()

            base_stats = {"武勇": o_buyou, "統率": o_tousotsu, "知略": o_chiryaku, "速度": o_speed}
            allocated_stats = {}
            current_remaining = st.session_state[pt_key]

            needs_rerun = False
            for stat_name, base_val in base_stats.items():
                input_val = st.number_input(
                    f"{stat_name} 振分", min_value=0, max_value=base_val + current_remaining,
                    value=st.session_state[alloc_keys[stat_name]], step=1,
                    key=f"{team_prefix}_{idx}_input_{stat_name}"
                )
                diff = input_val - st.session_state[alloc_keys[stat_name]]
                if diff != 0:
                    if current_remaining - diff >= 0:
                        st.session_state[alloc_keys[stat_name]] = input_val
                        st.session_state[pt_key] -= diff
                        needs_rerun = True
                allocated_stats[stat_name] = base_val + st.session_state[alloc_keys[stat_name]]

            if needs_rerun:
                st.rerun()

            df_data = []
            for stat_name, base_val in base_stats.items():
                alloc_val = st.session_state[alloc_keys[stat_name]]
                total_val = base_val + alloc_val
                df_data.append({
                    "属性": stat_name,
                    "素": base_val,
                    "振分": f"+{alloc_val}",
                    "合計": total_val
                })
            df_status = pd.DataFrame(df_data)
            st.dataframe(df_status, use_container_width=True, hide_index=True)

            st.caption(f"残 **{st.session_state[pt_key]}** / {max_pts} PT (★{rank})")

            st.markdown("---")
            st.markdown("##### 特性（凸連動）")
            active_traits = []
            for t in traits:
                if rank >= t["req"]:
                    st.markdown(f"✅ **{t['req']}凸**: {t['name']}")
                    active_traits.append(t['name'])
                else:
                    st.markdown(f"🔒 `{t['req']}凸で開放`: {t['name']}")

            st.markdown("---")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                s2_name = st.selectbox("伝授/事件1 (戦法枠1)", SKILL_LIST, index=SKILL_LIST.index("有備無患") if "有備無患" in SKILL_LIST else 0, key=f"{team_prefix}_{idx}_s2")
            with col_s2:
                s3_name = st.selectbox("伝授/事件2 (戦法枠2)", SKILL_LIST, index=SKILL_LIST.index("離心の計") if "離心の計" in SKILL_LIST else 0, key=f"{team_prefix}_{idx}_s3")

            s2_data = SKILL_DATABASE[s2_name]
            s3_data = SKILL_DATABASE[s3_name]

            # 装備順（リスト上のインデックス順）をそのまま保持
            skills = [
                {"name": db_s1_name, "rate": db_s1_rate / 100.0, "dmg": db_s1_dmg / 100.0, "quality": "固有", "attr": db_s1_attr, "type": db_s1_type},
                {"name": s2_name, "rate": s2_data[0] / 100.0, "dmg": s2_data[1] / 100.0, "quality": s2_data[2], "attr": s2_data[4], "type": s2_data[3]},
                {"name": s3_name, "rate": s3_data[0] / 100.0, "dmg": s3_data[1] / 100.0, "quality": s3_data[2], "attr": s3_data[4], "type": s3_data[3]},
            ]

            team_officers.append({
                "role": role, "name": o_name, "faction": o_faction, "rank": rank,
                "buyou": allocated_stats["武勇"], "chiryaku": allocated_stats["知略"], "tousotsu": allocated_stats["統率"], "speed": allocated_stats["速度"],
                "skills": skills, "traits": active_traits
            })

            for t_type, val in troop_aptitudes.items():
                if t_type in total_troop_levels:
                    total_troop_levels[t_type] += val

    team_troop_level = total_troop_levels.get(selected_troop, 0)
    
    st.markdown("##### 連携効果設定")
    col_link1, col_link2 = st.columns(2)
    with col_link1:
        faction_bonus_lv = st.slider("連携(勢力) Lv (0-10)", 0, 10, 0, key=f"{team_prefix}_faction_lv")
    with col_link2:
        kamonn_bonus_lv = st.slider("連携(家門) Lv (0-3)", 0, 3, 0, key=f"{team_prefix}_kamonn_lv")

    st.info(f"📊 **{team_name} 合計兵種レベル ({selected_troop})**: **{team_troop_level}** (各武将の適性合計)")

    return team_officers, selected_troop, team_troop_level, faction_bonus_lv, kamonn_bonus_lv

# --- サイドバー設定 ---
st.sidebar.header("⚙️ 設定")
initial_hp_per_officer = st.sidebar.number_input("1武将あたりの兵力", min_value=1000, max_value=20000, value=10000, step=1000)
sim_trials = st.sidebar.selectbox("対戦試行回数", [1000, 5000, 10000], index=0)

# --- メインレイアウト ---
main_tab1, main_tab2 = st.tabs(["🔵 自軍（あなた）", "🔴 敵軍（対戦相手）"])

with main_tab1:
    my_team, my_troop, my_troop_lvl, my_faction_lv, my_kamonn_lv = input_team_data("my", "自軍編成", ["上杉謙信", "柿崎景家", "宇佐美定満"], 1)

with main_tab2:
    enemy_team, enemy_troop, enemy_troop_lvl, enemy_faction_lv, enemy_kamonn_lv = input_team_data("enemy", "敵軍編成", ["織田信長", "柴田勝家", "明智光秀"], 3)

base_my_adv = get_troop_advantage(my_troop, enemy_troop)
base_enemy_adv = get_troop_advantage(enemy_troop, my_troop)
my_advantage_mult = base_my_adv * (1.0 + (my_troop_lvl * 0.02))
enemy_advantage_mult = base_enemy_adv * (1.0 + (enemy_troop_lvl * 0.02))

st.write("---")

# --- ステータス計算ロジック ---
def calculate_final_attributes(officer, troop_type, team_troop_lvl, faction_lv, kamonn_lv):
    base_stats = {
        "武勇": float(officer["buyou"]),
        "統率": float(officer["tousotsu"]),
        "知略": float(officer["chiryaku"]),
        "速度": float(officer["speed"]),
        "政務": 100.0,
        "魅力": 100.0
    }
    
    troop_mult_val = team_troop_lvl * 0.02
    faction_mult = faction_lv * 0.007
    kamonn_mult = kamonn_lv * 0.01
    total_mult = 1.0 + troop_mult_val + faction_mult + kamonn_mult
    
    multiplied_stats = {}
    for k, val in base_stats.items():
        if k in ["政務", "魅力"]:
            multiplied_stats[k] = val * (1.0 + faction_mult + kamonn_mult)
        else:
            multiplied_stats[k] = val * total_mult

    if troop_type == "騎兵":
        multiplied_stats["武勇"] += 10
        multiplied_stats["知略"] += 10
    elif troop_type == "弓兵":
        multiplied_stats["速度"] += 15
    elif troop_type == "足軽":
        multiplied_stats["統率"] += 15
    elif troop_type == "鉄砲":
        multiplied_stats["武勇"] += 10
        multiplied_stats["知略"] += 10

    for t_name in officer["traits"]:
        if "人は城" in t_name:
            multiplied_stats["統率"] *= 1.05

    return multiplied_stats

# シミュレーション計算ロジック
def get_h_hp(hp):
    if hp <= 1800: return hp * 0.10
    else: return (1800 * 0.10) + ((hp - 1800) ** 0.85) * 0.15

def calc_heal_cap(skill_rate, chiryaku, current_hp, is_intel_dep=True):
    h_val = get_h_hp(current_hp)
    base_val = (1.02 * chiryaku) + h_val if is_intel_dep else h_val
    return skill_rate * base_val

def get_floor_damage(current_hp, is_skill=False, dmg_rate=1.0, troop_mult=1.0):
    if current_hp <= 600: base_floor = 11.0
    elif current_hp <= 3000: base_floor = 18.75 * (current_hp / 1000.0)
    else: base_floor = (18.75 * 3.0) + (16.0 * ((current_hp - 3000) / 1000.0))
    raw_floor = base_floor * (20.5 / 18.75) * dmg_rate if is_skill else base_floor
    return raw_floor * troop_mult

def calc_damage(atk_stat, def_stat, current_hp, dmg_rate=1.0, is_skill=False, troop_mult=1.0):
    if dmg_rate == 0: return 0
    floor_val = get_floor_damage(current_hp, is_skill=is_skill, dmg_rate=dmg_rate, troop_mult=troop_mult)
    eff_atk, eff_def = atk_stat * 1.44, def_stat * 1.44
    stat_diff = eff_atk - eff_def
    hp_scaling = (current_hp / 1000.0) ** 1.35
    stat_component = stat_diff * 0.22 * (current_hp / 1000.0)
    hp_component = 12.0 * hp_scaling
    calculated_dmg = (hp_component + stat_component) * dmg_rate
    final_dmg = max(floor_val, calculated_dmg * troop_mult)
    return int(final_dmg * random.uniform(0.96, 1.04))

def apply_damage_to_officer(officer, raw_damage):
    if raw_damage <= 0 or officer["hp"] <= 0: return
    actual_dmg = min(officer["hp"], raw_damage)
    dead_now = int(actual_dmg * 0.104)
    officer["hp"] -= actual_dmg
    officer["injured_hp"] += (actual_dmg - dead_now)
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
    if not alive_defenders: return 0, []
    total_turn_dmg = 0
    
    for off in attacker_team:
        if off["hp"] <= 0: continue
        final_attrs = off["calculated_attrs"]
        avg_def = sum(o["calculated_attrs"]["統率"] for o in alive_defenders) / len(alive_defenders)
        
        # 戦法を公式の優先順位通りにソート：
        # 優先度: 指揮(1) ＞ 能動(2) ＞ 突撃(3) ＞ 受動(4) ＞ その他(5)
        # 同系統内ではインデックス順（装備順）が維持される
        def skill_sort_key(sk):
            stype = sk.get("type", "能動")
            if "指揮" in stype: return 1
            if "能動" in stype or "固有" in sk.get("quality", ""): return 2
            if "突撃" in stype: return 3
            if "受動" in stype: return 4
            return 5

        sorted_skills = sorted(off["skills"], key=skill_sort_key)
        
        # 1. 指揮戦法の処理
        for sk in sorted_skills:
            if "指揮" in sk["type"] and sk["rate"] > 0 and sk["name"] != "（なし）":
                if random.random() < sk["rate"]:
                    ref_intel = final_attrs["知略"]
                    if "回復" in sk["attr"] or "休養" in sk["attr"]:
                        heal_cap = calc_heal_cap(sk["dmg"], ref_intel, off["hp"], True)
                        actual_heal = int(min(heal_cap, off["injured_hp"]))
                        if actual_heal > 0:
                            off["hp"] += actual_heal
                            off["injured_hp"] -= actual_heal
                    else:
                        stat_val = final_attrs["知略"] if sk["attr"] == "計略" else final_attrs["武勇"]
                        s_dmg = calc_damage(stat_val, avg_def, off["hp"], sk["dmg"], True, troop_mult)
                        total_turn_dmg += s_dmg
                        for target in alive_defenders: apply_damage_to_officer(target, s_dmg // len(alive_defenders))
                        logs.append(f"【{off['name']}】[指揮]{sk['name']} → {s_dmg:,}ダメ")

        # 2. 能動戦法の処理
        for sk in sorted_skills:
            if ("能動" in sk["type"] or "固有" in sk.get("quality", "")) and "指揮" not in sk["type"] and sk["rate"] > 0 and sk["name"] != "（なし）":
                if random.random() < sk["rate"]:
                    ref_intel = final_attrs["知略"]
                    if "回復" in sk["attr"] or "休養" in sk["attr"]:
                        heal_cap = calc_heal_cap(sk["dmg"], ref_intel, off["hp"], True)
                        actual_heal = int(min(heal_cap, off["injured_hp"]))
                        if actual_heal > 0:
                            off["hp"] += actual_heal
                            off["injured_hp"] -= actual_heal
                    else:
                        stat_val = final_attrs["知略"] if sk["attr"] == "計略" else final_attrs["武勇"]
                        s_dmg = calc_damage(stat_val, avg_def, off["hp"], sk["dmg"], True, troop_mult)
                        total_turn_dmg += s_dmg
                        for target in alive_defenders: apply_damage_to_officer(target, s_dmg // len(alive_defenders))
                        logs.append(f"【{off['name']}】[能動]{sk['name']} → {s_dmg:,}ダメ")

        # 3. 通常攻撃の処理
        normal_dmg = calc_damage(final_attrs["武勇"], avg_def, off["hp"], 1.0, False, troop_mult)
        total_turn_dmg += normal_dmg
        for target in alive_defenders: apply_damage_to_officer(target, normal_dmg // len(alive_defenders))
        normal_attack_success = (normal_dmg > 0) # 通常攻撃が不発でなければTrue

        # 4. 突撃戦法の処理（通常攻撃が成功した場合のみ発動判定）
        if normal_attack_success:
            for sk in sorted_skills:
                if "突撃" in sk["type"] and sk["rate"] > 0 and sk["name"] != "（なし）":
                    if random.random() < sk["rate"]:
                        stat_val = final_attrs["知略"] if sk["attr"] == "計略" else final_attrs["武勇"]
                        s_dmg = calc_damage(stat_val, avg_def, off["hp"], sk["dmg"], True, troop_mult)
                        total_turn_dmg += s_dmg
                        for target in alive_defenders: apply_damage_to_officer(target, s_dmg // len(alive_defenders))
                        logs.append(f"【{off['name']}】[突撃]{sk['name']} → {s_dmg:,}ダメ")

        # 5. 受動戦法の処理
        for sk in sorted_skills:
            if "受動" in sk["type"] and sk["rate"] > 0 and sk["name"] != "（なし）":
                if random.random() < sk["rate"]:
                    ref_intel = final_attrs["知略"]
                    if "回復" in sk["attr"] or "休養" in sk["attr"]:
                        heal_cap = calc_heal_cap(sk["dmg"], ref_intel, off["hp"], True)
                        actual_heal = int(min(heal_cap, off["injured_hp"]))
                        if actual_heal > 0:
                            off["hp"] += actual_heal
                            off["injured_hp"] -= actual_heal
                    else:
                        stat_val = final_attrs["知略"] if sk["attr"] == "計略" else final_attrs["武勇"]
                        s_dmg = calc_damage(stat_val, avg_def, off["hp"], sk["dmg"], True, troop_mult)
                        total_turn_dmg += s_dmg
                        for target in alive_defenders: apply_damage_to_officer(target, s_dmg // len(alive_defenders))
                        logs.append(f"【{off['name']}】[受動]{sk['name']} → {s_dmg:,}ダメ")

    return total_turn_dmg, logs

if st.button("⚔️ 対戦シミュレーション開始", type="primary", use_container_width=True):
    my_wins, enemy_wins, draws = 0, 0, 0
    end_my_dead_list, end_enemy_dead_list = [], []

    for _ in range(sim_trials):
        my_team_sim = []
        for o in my_team:
            calc_attrs = calculate_final_attributes(o, my_troop, my_troop_lvl, my_faction_lv, my_kamonn_lv)
            my_team_sim.append({**o, "hp": initial_hp_per_officer, "injured_hp": 0, "total_dead": 0, "calculated_attrs": calc_attrs})

        enemy_team_sim = []
        for o in enemy_team:
            calc_attrs = calculate_final_attributes(o, enemy_troop, enemy_troop_lvl, enemy_faction_lv, enemy_kamonn_lv)
            enemy_team_sim.append({**o, "hp": initial_hp_per_officer, "injured_hp": 0, "total_dead": 0, "calculated_attrs": calc_attrs})

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
        for o in enemy_team_sim:
            fin_dead = int(o["injured_hp"] * 0.42)
            o["total_dead"] += fin_dead

        final_my_total = sum(m["hp"] for m in my_team_sim)
        final_enemy_total = sum(e["hp"] for e in enemy_team_sim)
        end_my_dead_list.append(sum(m["total_dead"] for m in my_team_sim))
        end_enemy_dead_list.append(sum(e["total_dead"] for e in enemy_team_sim))

        if final_my_total > final_enemy_total: my_wins += 1
        elif final_enemy_total > final_my_total: enemy_wins += 1
        else: draws += 1

    st.subheader(f"📊 対戦結果サマリー ({sim_trials:,} 回対戦)")
    col1, col2, col3 = st.columns(3)
    col1.metric("自軍勝率", f"{(my_wins / sim_trials * 100):.1f}%", f"{my_wins:,}勝")
    col2.metric("引き分け", f"{(draws / sim_trials * 100):.1f}%", f"{draws:,}分")
    col3.metric("敵軍勝率", f"{(enemy_wins / sim_trials * 100):.1f}%", f"{enemy_wins:,}敗")
