import pandas as pd
import random
import os

# ======================
# 1. 讀取成員 & 選 tribute
# ======================
def load_members(csv_file='members.csv'):
    if not os.path.exists(csv_file):
        print(f"錯誤：找不到 {csv_file}！請建立 CSV 檔案。")
        exit()
    df = pd.read_csv(csv_file, names=['member', 'district'])
    districts = {i: [] for i in range(1, 7)}
    for _, row in df.iterrows():
        d = int(row['district'])
        if 1 <= d <= 6:
            districts[d].append(row['member'])
    return districts

def select_tributes(districts):
    tributes = {}
    for d in range(1, 7):
        if districts[d]:
            name = random.choice(districts[d])
            tributes[name] = {
                'district': d,
                'position': random.randint(0, 23),  # 0~23 格
                'hp': 100,
                'max_hp': 100,
                'skills': None,
                'weapon': None,
                'hidden': False,
                'allies': [],
                'iq': 0, 'strength': 0, 'survival': 0, 'visibility': 0, 'sponsor_prob': 0.0
            }
    return tributes

# ======================
# 2. 分配基礎能力（平衡設計）
# ======================
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

# ======================
# 3. 選擇技能
# ======================
def choose_skill(name):
    print(f"\n=== {name} 請選擇優勢技能 ===")
    print("1. 遠程攻擊 (弓箭更強)")
    print("2. 近戰肉搏 (刀劍更猛)")
    print("3. 智取策略 (陷阱、隱身)")
    print("4. 堅韌防禦 (耐打、盾牌)")
    while True:
        try:
            choice = int(input("輸入 1-4: "))
            if choice in [1,2,3,4]:
                skills = ['far_attack', 'near_attack', 'intelligence', 'defense']
                return skills[choice-1]
        except:
            pass
        print("請輸入 1-4！")

# ======================
# 4. 抽武器（技能影響機率）
# ======================
def draw_weapon(tribute):
    base = ['bow', 'knife', 'trap', 'shield']
    bonus = []
    skill = tribute['skills']
    if skill == 'far_attack':   bonus = ['bow', 'bow', 'bow']
    elif skill == 'near_attack': bonus = ['knife', 'knife', 'knife']
    elif skill == 'intelligence': bonus = ['trap', 'trap']
    elif skill == 'defense':    bonus = ['shield', 'shield']
    all_weapons = base + bonus + ['food', 'medicine', 'random_item']
    return random.choice(all_weapons)

# ======================
# 5. 視野內敵人
# ======================
def visible_enemies(current_name, tributes):
    me = tributes[current_name]
    pos = me['position']
    vis = me['visibility']
    enemies = []
    for name, t in tributes.items():
        if name != current_name and not t.get('hidden', False):
            dist = abs(t['position'] - pos)
            if dist <= vis:
                enemies.append((name, t['position'], dist))
    return enemies

# ======================
# 6. 移動（扣 HP）
# ======================
def move(tribute, steps):
    cost = abs(steps) * 5
    tribute['hp'] -= cost
    tribute['position'] += steps * 2  # 每步 = 2 格
    tribute['position'] = max(0, min(23, tribute['position']))
    return cost

# ======================
# 7. 攻擊
# ======================
def attack(attacker, target_name, tributes):
    a = attacker
    t = tributes[target_name]
    dist = abs(a['position'] - t['position'])

    # 距離限制
    if dist > 4 and a['skills'] != 'far_attack':
        return "距離太遠，攻擊失敗！"
    if dist > 8:
        return "目標超出射程！"

    # 基礎傷害
    dmg = random.randint(15, 35)

    # 技能加成
    if a['skills'] == 'far_attack' and dist >= 4:
        dmg += 20
    if a['skills'] == 'near_attack' and dist <= 2:
        dmg += 25
    if a['skills'] == 'intelligence' and a['weapon'] == 'trap':
        dmg += 30

    # 防禦減傷
    if t['skills'] == 'defense':
        dmg = int(dmg * 0.7)

    t['hp'] -= dmg
    a['hp'] -= 10  # 攻擊耗體力

    return f"擊中！造成 {dmg} 點傷害！"

# ======================
# 8. Sponsor 檢查
# ======================
def check_sponsor(tribute):
    if random.random() < tribute['sponsor_prob']:
        heal = random.randint(15, 30)
        tribute['hp'] = min(tribute['max_hp'], tribute['hp'] + heal)
        item = random.choice(['食物', '藥品', '武器', '裝備'])
        return f"獲得贊助！恢復 {heal} HP + {item}"
    return None

# ======================
# 9. 行動選項
# ======================
def get_action_options(tribute):
    options = ['move', 'attack', 'rest', 'ally']
    if tribute['district'] <= 3:
        options.append('climb_tree')
    if tribute['skills'] == 'intelligence':
        options.append('set_trap')
    if tribute['skills'] == 'defense':
        options.append('fortify')
    return options

# ======================
# 主遊戲循環
# ======================
def run_game():
    print("飢餓遊戲 開始！")
    print("="*50)

    districts = load_members()
    tributes = select_tributes(districts)

    if len(tributes) < 2:
        print("人數不足，至少需要 2 人！")
        return

    # 選擇技能 & 抽武器
    for name, tribute in tributes.items():
        assign_base_stats(tribute, tribute['district'])
        tribute['skills'] = choose_skill(name)
        tribute['weapon'] = draw_weapon(tribute)
        print(f"{name} (District {tribute['district']}) → 技能: {tribute['skills']} | 武器: {tribute['weapon']}")

    print("\n遊戲開始！棋盤 0~23 格，每 2 格為一單位。")
    input("\n按 Enter 開始第一回合...")

    round_num = 1
    while len(tributes) > 1:
        print(f"\n{'='*20} 第 {round_num} 回合 {'='*20}")
        dead = []

        for name, tribute in list(tributes.items()):
            if tribute['hp'] <= 0:
                dead.append(name)
                continue

            print(f"\n{name} (D{tribute['district']}) | HP: {tribute['hp']}/{tribute['max_hp']} | 位置: {tribute['position']//2} 單位")
            if tribute['hidden']: print("   (隱身中)")

            # Sponsor
            sponsor_msg = check_sponsor(tribute)
            if sponsor_msg:
                print(f"   {sponsor_msg}")

            # 視野
            enemies = visible_enemies(name, tributes)
            if enemies:
                print(f"   可見敵人: {[(e[0], e[2]) for e in enemies]}")
            else:
                print("   附近無人")

            # 行動選項
            options = get_action_options(tribute)
            print(f"   可用行動: {', '.join(options)}")

            while True:
                action = input(f"\n{name} 選擇行動: ").strip().lower()
                if action in options:
                    break
                print("無效行動！")

            # 執行行動
            if action == 'move':
                try:
                    steps = int(input("移動幾步？(正右/負左): "))
                    cost = move(tribute, steps)
                    print(f"   移動 {steps} 步，消耗 {cost} HP")
                except:
                    print("   移動取消")

            elif action == 'attack' and enemies:
                print("   可攻擊目標:", [e[0] for e in enemies])
                target = input("   攻擊誰？: ").strip()
                if target in tributes and target != name:
                    result = attack(tribute, target, tributes)
                    print(f"   {result}")
                else:
                    print("   無效目標")

            elif action == 'rest':
                heal = random.randint(10, 20)
                tribute['hp'] = min(tribute['max_hp'], tribute['hp'] + heal)
                print(f"   休息恢復 {heal} HP")

            elif action == 'ally':
                allies = [n for n in tributes if n != name]
                if allies:
                    ally = input(f"   結盟對象 {allies}: ")
                    if ally in tributes:
                        tribute['allies'].append(ally)
                        print(f"   向 {ally} 發出結盟請求！")

            elif action == 'climb_tree':
                tribute['hidden'] = True
                tribute['hp'] -= 5
                print("   爬上樹隱身！下一回合敵人難發現")

            elif action == 'set_trap' and tribute['skills'] == 'intelligence':
                tribute['hp'] -= 8
                print("   設置陷阱！下次攻擊傷害 +30")
                tribute['next_attack_bonus'] = 30

            elif action == 'fortify' and tribute['skills'] == 'defense':
                tribute['hp'] = min(tribute['max_hp'] + 20, tribute['hp'] + 15)
                tribute['max_hp'] += 20
                print("   強化防禦！最大 HP +20")

            # 隱身結束
            if tribute.get('hidden', False) and random.random() < 0.7:
                tribute['hidden'] = False
                print("   隱身結束")

        # 移除死亡
        for name in dead:
            print(f"\n{name} 已陣亡！")
            del tributes[name]

        round_num += 1
        if len(tributes) > 1:
            input("\n按 Enter 繼續下一回合...")

    # 勝利
    winner = list(tributes.keys())[0]
    w = tributes[winner]
    print(f"\n{'*'*60}")
    print(f"   勝利者：{winner} (District {w['district']})")
    print(f"   最終 HP：{w['hp']}")
    print(f"{'*'*60}")

# ======================
# 啟動遊戲
# ======================
if __name__ == "__main__":
    run_game()
