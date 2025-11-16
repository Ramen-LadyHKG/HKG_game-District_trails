import pandas as pd
import random
import os
import json
from datetime import datetime

SAVE_FILE = 'hunger_games_save.json'

# ======================
# SAVE/LOAD 系統
# ======================
def save_game(tributes, round_num, volunteers=None):
    """完整儲存遊戲狀態"""
    save_data = {
        'round_num': round_num,
        'tributes': tributes,
        'volunteers': volunteers or {},
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'version': '2.0'
    }
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    print(f"💾 已自動儲存 → 第 {round_num} 回合")

def load_game():
    """載入遊戲狀態"""
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

# ======================
# 初始化（每個區抽2人 + 自願者）
# ======================
def load_members(csv_file='members.csv'):
    if not os.path.exists(csv_file):
        print(f"錯誤：找不到 {csv_file}！")
        exit()
    df = pd.read_csv(csv_file, names=['member', 'district'])
    districts = {i: [] for i in range(1, 7)}
    for _, row in df.iterrows():
        d = int(row['district'])
        if 1 <= d <= 6:
            districts[d].append(row['member'])
    return districts

def select_tributes(districts):
    """每個區隨機抽2人"""
    tributes = {}
    for d in range(1, 7):
        if len(districts[d]) >= 2:
            selected = random.sample(districts[d], 2)
            for name in selected:
                tributes[name] = {
                    'district': d,
                    'position': random.randint(0, 23),
                    'hp': 100, 'max_hp': 100,
                    'skills': None, 'weapon': None,
                    'hidden': False, 'allies': [],
                    'iq': 0, 'strength': 0, 'survival': 0,
                    'visibility': 0, 'sponsor_prob': 0.0,
                    'is_volunteer': False  # 標記是否自願者
                }
    return tributes

def volunteer_tribute(tributes):
    """自願者取代指定tribute"""
    print(f"\n{'='*50}")
    print("🗣️  自願者階段！")
    print("輸入 '區號 會員名' 取代該區tribute（例如：1 司徒老賊）")
    print("輸入 'done' 結束")
    print(f"{'='*50}")

    volunteers = {}
    while True:
        cmd = input("自願者 > ").strip()
        if cmd.lower() == 'done':
            break
        try:
            district, name = cmd.split(maxsplit=1)
            district = int(district)
            if district in range(1, 7) and name not in tributes:
                # 找該區現有tribute取代
                district_tributes = [n for n, t in tributes.items() if t['district'] == district]
                if district_tributes:
                    old_tribute = random.choice(district_tributes)
                    tributes[name] = tributes.pop(old_tribute)
                    tributes[name]['is_volunteer'] = True
                    volunteers[f"{district}區"] = f"{old_tribute} → {name}"
                    print(f"✅ {name} 取代 {old_tribute}")
                else:
                    print("❌ 該區無tribute")
            else:
                print("❌ 格式錯誤或已存在")
        except:
            print("❌ 輸入格式：區號 會員名")

    if volunteers:
        print(f"\n自願者總結：")
        for d, change in volunteers.items():
            print(f"  {d}: {change}")
    return volunteers

def assign_base_stats(tribute, district):
    stats = {
        1: {'iq': 50, 'strength': 50, 'survival': 80, 'visibility': 12, 'sponsor_prob': 0.10},
        2: {'iq': 50, 'strength': 70, 'survival': 70, 'visibility': 10, 'sponsor_prob': 0.20},
        3: {'iq': 60, 'strength': 60, 'survival': 60, 'visibility': 8,  'sponsor_prob': 0.30},
        4: {'iq': 70, 'strength': 50, 'survival': 40, 'visibility': 6,  'sponsor_prob': 0.40},
        5: {'iq': 80, 'strength': 40, 'survival': 30, 'visibility': 4,  'sponsor_prob': 0.50},
        6: {'iq': 40, 'strength': 30, 'survival': 20, 'visibility': 2,  'sponsor_prob': 0.60}
    }
    tribute.update(stats[district])
    return tribute

def choose_skill(name, tributes):
    district = tributes[name]['district']
    print(f"\n{'='*35}")
    print(f"=== {name} (D{district}) 請選擇優勢技能 ===")
    print("1. 遠程攻擊 (弓箭更強)  2. 近戰肉搏 (刀劍更猛)")
    print("3. 智取策略 (陷阱、隱身)  4. 堅韌防禦 (耐打、盾牌)")
    print(f"{'='*35}")
    while True:
        try:
            choice = int(input("輸入 1-4: "))
            if 1 <= choice <= 4:
                return ['far_attack', 'near_attack', 'intelligence', 'defense'][choice-1]
        except: pass
        print("請輸入 1-4！")

def draw_weapon(tribute):
    base = ['bow', 'knife', 'trap', 'shield']
    bonus = []
    if tribute['skills'] == 'far_attack': bonus = ['bow']*3
    elif tribute['skills'] == 'near_attack': bonus = ['knife']*3
    elif tribute['skills'] == 'intelligence': bonus = ['trap']*2
    elif tribute['skills'] == 'defense': bonus = ['shield']*2
    return random.choice(base + bonus + ['food', 'medicine'])

# ======================
# 遊戲邏輯
# ======================
def visible_enemies(name, tributes):
    me = tributes[name]
    enemies = []
    for t_name, t in tributes.items():
        if t_name != name and not t.get('hidden', False) and t['hp'] > 0:
            dist = abs(t['position'] - me['position'])
            if dist <= me['visibility']:
                enemies.append((t_name, t['position'], dist))
    return enemies

def move(tribute, steps):
    cost = abs(steps) * 5
    tribute['hp'] = max(0, tribute['hp'] - cost)
    tribute['position'] = max(0, min(23, tribute['position'] + steps * 2))
    return cost

def attack(attacker, target_name, tributes):
    a, t = attacker, tributes[target_name]
    dist = abs(a['position'] - t['position'])
    if dist > 8 or (dist > 4 and a['skills'] != 'far_attack'):
        return None, 0

    dmg = random.randint(20, 40)
    if a['skills'] == 'far_attack' and dist >= 4: dmg += 20
    if a['skills'] == 'near_attack' and dist <= 2: dmg += 25
    if t['skills'] == 'defense': dmg *= 0.7

    old_hp = t['hp']
    t['hp'] = max(0, t['hp'] - dmg)
    a['hp'] -= 10
    return target_name, dmg, old_hp

def check_sponsor(tribute):
    if random.random() < tribute['sponsor_prob']:
        heal = random.randint(15, 25)
        tribute['hp'] = min(tribute['max_hp'], tribute['hp'] + heal)
        return f"贊助！恢復 {heal} HP"
    return None

def get_action_options(tribute):
    opts = ['move', 'attack', 'rest', 'save']
    if tribute['district'] <= 3: opts.append('climb_tree')
    if tribute['skills'] == 'intelligence': opts.append('set_trap')
    if tribute['skills'] == 'defense': opts.append('fortify')
    return opts

# ======================
# 輸出格式函數
# ======================
def print_round_summary(tributes, round_num, round_actions):
    """第N回合簡述"""
    print("====================")
    print(f"[u]第{round_num}回合簡述[/u]：")

    alive_before = {n: t['hp'] for n, t in tributes.items() if t['hp'] > 0}
    for name, actions in round_actions.items():
        if name not in alive_before: continue

        line = f"> [u]{name}[/u] (D{tributes[name]['district']})："
        if actions:
            for act in actions:
                if act['type'] == 'attack':
                    target, dmg, old_hp = act['data']
                    line += f"攻擊[u]{target}[/u]造成{dmg}傷（[u]HP[/u]{old_hp}->[u]{tributes[target]['hp']}[/u]）"
                elif act['type'] == 'move':
                    line += f"移動（[u]位置[/u]{act['data']}，[u]HP[/u]{tributes[name]['hp']}）"
                elif act['type'] == 'hidden_end':
                    line += f"[u]隱身[/u]結束"
                elif act['type'] == 'fortify':
                    line += f"[u]fortify[/u]強化防禦！最大[u]HP[/u]+20"
        else:
            line += "（[u]死亡[/u]）"
        print(line)

    print("====================\n")

def print_live_status(tributes, round_num):
    """第N回合實時戰況"""
    print("=========================")
    print(f"[u]第 {round_num} 回合 實時戰況[/u]")
    print("=========================")
    alive = sorted([n for n in tributes if tributes[n]['hp'] > 0],
                   key=lambda x: (-tributes[x]['district'], tributes[x]['position']))
    for name in alive:
        t = tributes[name]
        status = "[u]生[/u]"
        pos = f"{t['position']//2}單位"
        hp = f"[u]HP[/u]: {t['hp']}/{t['max_hp']}"
        print(f"{status} [u]{name}[/u] (D{t['district']}) {hp} [u]位置[/u]: {pos}")
    print("=================\n")

# ======================
# 主遊戲
# ======================
def run_game():
    print("🎤 Welcome, Welcome! Happy Hunger Games!")
    print("May the odds be ever in your favor!")

    # 載入或新遊戲
    saved = load_game()
    if saved and input("\n發現存檔！1=載入 2=新遊戲: ").strip() == '1':
        tributes, round_num, volunteers = saved['tributes'], saved['round_num'], saved.get('volunteers', {})
        print(f"載入第 {round_num} 回合")
    else:
        districts = load_members()
        tributes = select_tributes(districts)
        volunteers = volunteer_tribute(tributes)  # 自願者階段
        round_num = 1

        # 初始化技能武器
        for name in sorted(tributes, key=lambda x: tributes[x]['district']):
            t = tributes[name]
            assign_base_stats(t, t['district'])
            t['skills'] = choose_skill(name, tributes)
            t['weapon'] = draw_weapon(t)
            print(f"{name} (D{t['district']}) 技能:{t['skills']} 武器:{t['weapon']}")

        save_game(tributes, round_num, volunteers)

    input(f"\n按Enter開始第{round_num}回合...")

    while len([t for t in tributes.values() if t['hp'] > 0]) > 1:
        print_live_status(tributes, round_num)

        round_actions = {name: [] for name in tributes if tributes[name]['hp'] > 0}
        dead_this_round = []

        # 每個tribute行動
        for name in list(tributes.keys()):
            t = tributes[name]
            if t['hp'] <= 0: continue

            print(f"\n=== {name} (D{t['district']}) ===")
            print(f"HP: {t['hp']}/{t['max_hp']} 位置: {t['position']//2}")

            sponsor = check_sponsor(t)
            if sponsor:
                round_actions[name].append({'type': 'sponsor', 'data': sponsor})
                print(sponsor)

            enemies = visible_enemies(name, tributes)
            print("可見敵人:", [e[0] for e in enemies])

            opts = get_action_options(t)
            print("行動:", ', '.join(opts))

            action = input(f"{name} 行動: ").strip().lower()
            if action not in opts: continue

            if action == 'save':
                save_game(tributes, round_num, volunteers)
                continue
            elif action == 'move':
                steps = int(input("步數: "))
                old_pos = t['position']//2
                cost = move(t, steps)
                new_pos = t['position']//2
                round_actions[name].append({'type': 'move', 'data': new_pos})
            elif action == 'attack' and enemies:
                target = input("攻擊誰: ").strip()
                if target in tributes:
                    result = attack(t, target, tributes)
                    if result:
                        tgt, dmg, old_hp = result
                        round_actions[name].append({'type': 'attack', 'data': (tgt, dmg, old_hp)})
                        if tributes[target]['hp'] <= 0:
                            dead_this_round.append(target)
            elif action == 'rest':
                heal = random.randint(10, 20)
                t['hp'] = min(t['max_hp'], t['hp'] + heal)
            elif action == 'climb_tree':
                t['hidden'] = True
                t['hp'] -= 5
            elif action == 'fortify' and t['skills'] == 'defense':
                t['max_hp'] += 20
                t['hp'] = min(t['max_hp'], t['hp'] + 15)
                round_actions[name].append({'type': 'fortify'})
            # ... 其他行動簡化

            # 隱身結束
            if t.get('hidden', False) and random.random() < 0.5:
                t['hidden'] = False
                round_actions[name].append({'type': 'hidden_end'})

        # 回合結束：顯示簡述 + 存檔
        print_round_summary(tributes, round_num, round_actions)
        save_game(tributes, round_num + 1, volunteers)
        round_num += 1

        input("\n按Enter下一回合...")

    # 勝利
    winner = next(n for n in tributes if tributes[n]['hp'] > 0)
    print(f"\n🏆 勝利者: {winner} (D{tributes[winner]['district']})!")

if __name__ == "__main__":
    run_game()
