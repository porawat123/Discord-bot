import os
import random
import time
import discord
from discord import app_commands
from pymongo import MongoClient
from keep_alive import keep_alive

# ── MongoDB Setup ──────────────────────────────────────────────
_client = MongoClient(os.environ["MONGODB_URI"])
_db = _client["chokun_bot"]
users_col = _db["users"]

DEFAULT_USER = {
    "coins": 0, "xp": 0, "level": 1,
    "last_work": 0, "last_fish": 0, "last_mine": 0, "last_checkin": 0,
    "warnings": 0, "title": "", "inventory": []
}

def get_user(user_id):
    uid = str(user_id)
    user = users_col.find_one({"_id": uid})
    if user is None:
        user = {"_id": uid, **DEFAULT_USER}
        users_col.insert_one(user)
    else:
        changed = False
        for k, v in DEFAULT_USER.items():
            if k not in user:
                user[k] = v
                changed = True
        if changed:
            users_col.replace_one({"_id": uid}, user)
    return user

def save_user(user):
    users_col.replace_one({"_id": user["_id"]}, user, upsert=True)

def xp_for_level(level):
    return level * 100

def add_xp(user, amount):
    user["xp"] += amount
    leveled_up = False
    while user["xp"] >= xp_for_level(user["level"]):
        user["xp"] -= xp_for_level(user["level"])
        user["level"] += 1
        leveled_up = True
    return leveled_up

# ── Shop Items ────────────────────────────────────────────────
SHOP_ITEMS = [
    {"id": "vip",   "name": "👑 VIP",       "desc": "ตำแหน่ง VIP แสดงในโปรไฟล์",    "price": 500},
    {"id": "pro",   "name": "⚡ Pro",        "desc": "ตำแหน่ง Pro แสดงในโปรไฟล์",    "price": 300},
    {"id": "rich",  "name": "💎 เศรษฐี",     "desc": "ตำแหน่งเศรษฐีแสดงในโปรไฟล์",  "price": 1000},
    {"id": "lucky", "name": "🍀 โชคดี",      "desc": "ตำแหน่งโชคดีแสดงในโปรไฟล์",   "price": 200},
    {"id": "boost", "name": "🚀 XP Booster", "desc": "รับ XP x2 จาก /งาน 10 ครั้ง",  "price": 400},
]

# ── Cooldowns ─────────────────────────────────────────────────
WORK_COOLDOWN    = 90
FISH_COOLDOWN    = 60
MINE_COOLDOWN    = 120
CHECKIN_COOLDOWN = 86400

# ── Response Lists ────────────────────────────────────────────
HELLO_RESPONSES = [
    "สวัสดีครับ 👋", "หวัดดีครับ! มีอะไรให้ช่วยไหม? 😊",
    "ยินดีต้อนรับครับ 🎉", "อ้าว มาแล้วหรอ! สวัสดีครับ 😄",
]
HUNGRY_RESPONSES = [
    "ไปหาอะไรกินในตู้เย็นไหมครับ 🍱", "หิวแล้วหรอ? สั่ง Grab Food เลยครับ 🛵",
    "มาม่าไม่เคยทำให้ผิดหวังนะครับ 🍜", "ออกไปซื้อข้าวข้างนอกก็ได้ครับ 🌤️",
]
FORTUNE_RESPONSES = [
    "ดวงวันนี้ดีมากครับ ⭐ มีโชคลาภรออยู่!", "ระวังเรื่องการเงินหน่อยนะครับ 💸",
    "วันนี้ดวงความรักมาแรงครับ ❤️", "โชคดีมากครับวันนี้! 🍀",
]
TIRED_RESPONSES = [
    "พักก่อนนะครับ ร่างกายสำคัญกว่างาน 💙", "เหนื่อยก็หยุดพักได้ครับ ไม่ต้องสู้คนเดียว 🫂",
    "ดื่มน้ำ นอนหลับ พรุ่งนี้ค่อยสู้ใหม่ครับ 😴", "คุณทำได้ดีมากแล้วครับ 🌟",
]
WORK_RESPONSES = [
    "คุณไปส่งพัสดุและได้รับ {coins} เหรียญ 📦",
    "คุณขายของออนไลน์และได้รับ {coins} เหรียญ 🛒",
    "คุณรับจ้างเขียนโค้ดและได้รับ {coins} เหรียญ 💻",
    "คุณออกไปตัดหญ้าและได้รับ {coins} เหรียญ 🌿",
    "คุณไปสอนพิเศษและได้รับ {coins} เหรียญ 📚",
    "คุณรับงานฟรีแลนซ์และได้รับ {coins} เหรียญ 🎨",
]
SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎"]

FISH_RESULTS  = [
    ("🐟 ปลาทอง",     80,  150),
    ("🐠 ปลาการ์ตูน", 120, 200),
    ("🐡 ปลาปักเป้า",  50,  100),
    ("🦈 ฉลาม",       200, 400),
    ("🦑 หมึก",        60,  130),
    ("👢 รองเท้าเก่า",  5,   10),
    ("🪨 ก้อนหิน",     1,    5),
    ("🎣 ไม่ได้อะไร",   0,    0),
]
FISH_WEIGHTS  = [20, 15, 20, 5, 15, 10, 10, 5]

MINE_RESULTS  = [
    ("🪨 หินธรรมดา",  10,  30),
    ("🥈 เหล็ก",       50, 100),
    ("🪙 ทองแดง",      70, 130),
    ("💛 ทอง",        150, 300),
    ("💎 เพชร",       300, 600),
    ("🔥 ทับทิม",     200, 400),
]
MINE_WEIGHTS  = [30, 25, 20, 15, 5, 5]

RPS_MAP = {"ค้อน": "✊", "กระดาษ": "✋", "กรรไกร": "✌️"}
RPS_WIN = {"ค้อน": "กรรไกร", "กระดาษ": "ค้อน", "กรรไกร": "กระดาษ"}

# ── Bot Setup ─────────────────────────────────────────────────
intents = discord.Intents.default()
client  = discord.Client(intents=intents)
tree    = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"บอทออนไลน์แล้ว: {client.user}")

# ── General Commands ──────────────────────────────────────────

@tree.command(name="hello", description="ทักทายบอท")
async def hello(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    leveled_up = add_xp(user, 5)
    save_user(user)
    msg = random.choice(HELLO_RESPONSES)
    if leveled_up:
        msg += f"\n🎉 **เลเวลอัพ!** ตอนนี้คุณเป็น Level {user['level']} แล้ว!"
    await interaction.response.send_message(msg)

@tree.command(name="หิว", description="บอทแนะนำอาหาร")
async def hiw(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(HUNGRY_RESPONSES))

@tree.command(name="ดวง", description="เช็คดวงวันนี้")
async def fortune(interaction: discord.Interaction):
    await interaction.response.send_message(f"🔮 ดวงของคุณวันนี้: {random.choice(FORTUNE_RESPONSES)}")

@tree.command(name="เหนื่อย", description="บอทให้กำลังใจ")
async def tired(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(TIRED_RESPONSES))

@tree.command(name="ทาย", description="ให้บอททายว่าใช่หรือไม่ใช่")
async def guess(interaction: discord.Interaction, คำถาม: str):
    options = ["ใช่ครับ ✅", "ไม่ใช่ครับ ❌", "ยังบอกไม่ได้ครับ 🤔", "ลองถามใหม่อีกทีครับ 🔄", "แน่นอนเลยครับ! 💯"]
    await interaction.response.send_message(f"❓ **{คำถาม}**\n→ {random.choice(options)}")

@tree.command(name="สุ่มเลข", description="สุ่มตัวเลข")
async def random_number(interaction: discord.Interaction, ต่ำสุด: int = 1, สูงสุด: int = 100):
    result = random.randint(ต่ำสุด, สูงสุด)
    await interaction.response.send_message(f"🎲 สุ่มเลขระหว่าง {ต่ำสุด}-{สูงสุด} ได้: **{result}**")

# ── Economy ───────────────────────────────────────────────────

@tree.command(name="งาน", description="ทำงานเพื่อรับเหรียญ (cooldown 1 นาที 30 วินาที)")
async def work(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    now = time.time()
    remaining = WORK_COOLDOWN - (now - user["last_work"])
    if remaining > 0:
        mins = int(remaining // 60); secs = int(remaining % 60)
        await interaction.response.send_message(f"⏳ ยังทำงานได้อีกใน **{mins} นาที {secs} วินาที** ครับ")
        return
    has_boost = "boost" in user.get("inventory", [])
    earned = random.randint(50, 200)
    xp_earn = 40 if has_boost else 20
    if has_boost:
        earned *= 2
        user["inventory"].remove("boost")
    user["coins"] += earned
    user["last_work"] = now
    leveled_up = add_xp(user, xp_earn)
    save_user(user)
    msg = random.choice(WORK_RESPONSES).format(coins=earned)
    if has_boost: msg += " *(XP Booster ใช้แล้ว!)*"
    msg += f"\n💰 ยอดเหรียญรวม: **{user['coins']}** เหรียญ"
    if leveled_up: msg += f"\n🎉 **เลเวลอัพ!** ตอนนี้คุณเป็น Level {user['level']} แล้ว!"
    await interaction.response.send_message(msg)

@tree.command(name="เหรียญ", description="ดูยอดเหรียญของตัวเอง")
async def coins_cmd(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    await interaction.response.send_message(f"🪙 **{interaction.user.display_name}** มีเหรียญ **{user['coins']}** เหรียญ")

@tree.command(name="โอน", description="โอนเหรียญให้สมาชิกคนอื่น")
async def transfer(interaction: discord.Interaction, สมาชิก: discord.Member, จำนวน: int):
    if จำนวน <= 0:
        await interaction.response.send_message("❌ จำนวนต้องมากกว่า 0 ครับ"); return
    if สมาชิก.id == interaction.user.id:
        await interaction.response.send_message("❌ โอนให้ตัวเองไม่ได้ครับ"); return
    sender   = get_user(interaction.user.id)
    receiver = get_user(สมาชิก.id)
    if sender["coins"] < จำนวน:
        await interaction.response.send_message(f"❌ เหรียญไม่พอครับ! คุณมีแค่ **{sender['coins']}** เหรียญ"); return
    sender["coins"]   -= จำนวน
    receiver["coins"] += จำนวน
    save_user(sender); save_user(receiver)
    await interaction.response.send_message(
        f"💸 **{interaction.user.display_name}** โอน **{จำนวน}** เหรียญให้ **{สมาชิก.display_name}** สำเร็จ!\n"
        f"💰 ยอดเหรียญของคุณเหลือ: **{sender['coins']}** เหรียญ"
    )

# ── Profile & Leaderboard ─────────────────────────────────────

@tree.command(name="โปรไฟล์", description="ดูโปรไฟล์และ Level ของตัวเอง")
async def profile(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    needed = xp_for_level(user["level"])
    bar_filled = int((user["xp"] / needed) * 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)
    title_str = f" {user['title']}" if user.get("title") else ""
    inventory_str = ", ".join(user.get("inventory", [])) or "ว่างเปล่า"
    embed = discord.Embed(title=f"📋 โปรไฟล์ของ {interaction.user.display_name}{title_str}", color=0x5865F2)
    embed.add_field(name="⭐ Level",     value=str(user["level"]),         inline=True)
    embed.add_field(name="✨ XP",        value=f"{user['xp']}/{needed}",   inline=True)
    embed.add_field(name="🪙 เหรียญ",   value=str(user["coins"]),          inline=True)
    embed.add_field(name="📊 Progress",  value=f"`{bar}`",                  inline=False)
    embed.add_field(name="🎒 ไอเทม",    value=inventory_str,               inline=False)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@tree.command(name="อันดับ", description="ดู Leaderboard เหรียญของ Server")
async def leaderboard(interaction: discord.Interaction):
    top = list(users_col.find().sort("coins", -1).limit(10))
    if not top:
        await interaction.response.send_message("ยังไม่มีข้อมูลผู้เล่นครับ"); return
    embed  = discord.Embed(title="🏆 อันดับเศรษฐีของ Server", color=0xFFD700)
    medals = ["🥇", "🥈", "🥉"]
    lines  = []
    for i, udata in enumerate(top):
        medal = medals[i] if i < 3 else f"`{i+1}.`"
        try:
            member = interaction.guild.get_member(int(udata["_id"]))
            name   = member.display_name if member else f"User#{udata['_id'][-4:]}"
        except Exception:
            name = f"User#{udata['_id'][-4:]}"
        lines.append(f"{medal} **{name}** — {udata.get('coins', 0)} 🪙")
    embed.description = "\n".join(lines)
    await interaction.response.send_message(embed=embed)

# ── Shop ──────────────────────────────────────────────────────

@tree.command(name="ร้านค้า", description="ดูของที่ขายในร้าน")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 ร้านค้า", description="ใช้ `/ซื้อ` เพื่อซื้อสินค้าครับ", color=0x57F287)
    for item in SHOP_ITEMS:
        embed.add_field(name=f"{item['name']} — {item['price']} 🪙", value=item["desc"], inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ซื้อ", description="ซื้อสินค้าจากร้านค้า")
@app_commands.choices(สินค้า=[app_commands.Choice(name=f"{i['name']} ({i['price']} เหรียญ)", value=i["id"]) for i in SHOP_ITEMS])
async def buy(interaction: discord.Interaction, สินค้า: str):
    item = next((i for i in SHOP_ITEMS if i["id"] == สินค้า), None)
    if not item:
        await interaction.response.send_message("❌ ไม่พบสินค้านี้ครับ"); return
    user = get_user(interaction.user.id)
    if user["coins"] < item["price"]:
        await interaction.response.send_message(
            f"❌ เหรียญไม่พอครับ! ต้องการ **{item['price']}** เหรียญ (มีอยู่ **{user['coins']}** เหรียญ)"); return
    user["coins"] -= item["price"]
    if สินค้า in ["vip", "pro", "rich", "lucky"]:
        user["title"] = item["name"]
    else:
        if สินค้า not in user["inventory"]:
            user["inventory"].append(สินค้า)
    save_user(user)
    await interaction.response.send_message(
        f"✅ ซื้อ **{item['name']}** สำเร็จ!\n💰 เหรียญเหลือ: **{user['coins']}** เหรียญ"
    )

# ── Extra Earn Commands ───────────────────────────────────────

@tree.command(name="ตกปลา", description="ตกปลาเพื่อรับเหรียญ (cooldown 1 นาที)")
async def fishing(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    now = time.time()
    remaining = FISH_COOLDOWN - (now - user["last_fish"])
    if remaining > 0:
        await interaction.response.send_message(f"🎣 ยังตกปลาได้อีกใน **{int(remaining)} วินาที** ครับ"); return
    catch = random.choices(FISH_RESULTS, weights=FISH_WEIGHTS, k=1)[0]
    name, min_c, max_c = catch
    earned = random.randint(min_c, max_c) if max_c > 0 else 0
    user["coins"] += earned
    user["last_fish"] = now
    leveled_up = add_xp(user, 15)
    save_user(user)
    if earned == 0:
        msg = f"🎣 {name}... วันนี้ปลาไม่กัดเลยครับ 😔"
    else:
        msg = f"🎣 ได้ **{name}**! ขายได้ **{earned}** เหรียญ 💰\n🪙 ยอดรวม: **{user['coins']}** เหรียญ"
    if leveled_up: msg += f"\n🎉 **เลเวลอัพ!** Level {user['level']} แล้ว!"
    await interaction.response.send_message(msg)

@tree.command(name="ขุด", description="ขุดแร่เพื่อรับเหรียญ (cooldown 2 นาที)")
async def mining(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    now = time.time()
    remaining = MINE_COOLDOWN - (now - user["last_mine"])
    if remaining > 0:
        mins = int(remaining // 60); secs = int(remaining % 60)
        await interaction.response.send_message(f"⛏️ ยังขุดได้อีกใน **{mins} นาที {secs} วินาที** ครับ"); return
    ore = random.choices(MINE_RESULTS, weights=MINE_WEIGHTS, k=1)[0]
    name, min_c, max_c = ore
    earned = random.randint(min_c, max_c)
    user["coins"] += earned
    user["last_mine"] = now
    leveled_up = add_xp(user, 20)
    save_user(user)
    msg = f"⛏️ ขุดได้ **{name}**! ขายได้ **{earned}** เหรียญ 💰\n🪙 ยอดรวม: **{user['coins']}** เหรียญ"
    if leveled_up: msg += f"\n🎉 **เลเวลอัพ!** Level {user['level']} แล้ว!"
    await interaction.response.send_message(msg)

@tree.command(name="เช็คอิน", description="เช็คอินรายวัน รับเหรียญ+XP (วันละครั้ง)")
async def checkin(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    now = time.time()
    remaining = CHECKIN_COOLDOWN - (now - user["last_checkin"])
    if remaining > 0:
        hrs = int(remaining // 3600); mins = int((remaining % 3600) // 60)
        await interaction.response.send_message(f"📅 เช็คอินได้อีกใน **{hrs} ชั่วโมง {mins} นาที** ครับ"); return
    bonus_coins = random.randint(150, 350)
    bonus_xp    = random.randint(50, 100)
    user["coins"] += bonus_coins
    user["last_checkin"] = now
    leveled_up = add_xp(user, bonus_xp)
    save_user(user)
    msg = (f"📅 **เช็คอินสำเร็จ!**\n"
           f"🪙 ได้รับ **{bonus_coins}** เหรียญ\n"
           f"✨ ได้รับ **{bonus_xp}** XP\n"
           f"💰 ยอดรวม: **{user['coins']}** เหรียญ")
    if leveled_up: msg += f"\n🎉 **เลเวลอัพ!** Level {user['level']} แล้ว!"
    await interaction.response.send_message(msg)

# ── Mini Games ────────────────────────────────────────────────

@tree.command(name="เป่ายิ้งฉุบ", description="เล่นเป่ายิ้งฉุบกับบอท (เดิมพันเหรียญได้)")
@app_commands.choices(ตัวเลือก=[
    app_commands.Choice(name="✊ ค้อน",    value="ค้อน"),
    app_commands.Choice(name="✋ กระดาษ", value="กระดาษ"),
    app_commands.Choice(name="✌️ กรรไกร", value="กรรไกร"),
])
async def rps(interaction: discord.Interaction, ตัวเลือก: str, เดิมพัน: int = 0):
    user = get_user(interaction.user.id)
    if เดิมพัน < 0:
        await interaction.response.send_message("❌ เดิมพันต้องมากกว่า 0 ครับ"); return
    if เดิมพัน > user["coins"]:
        await interaction.response.send_message(f"❌ เหรียญไม่พอครับ! คุณมีแค่ **{user['coins']}** เหรียญ"); return
    bot_choice = random.choice(list(RPS_MAP.keys()))
    player = ตัวเลือก
    if player == bot_choice:
        result, coins_change = "เสมอกันครับ 🤝", 0
    elif RPS_WIN[player] == bot_choice:
        result, coins_change = "**คุณชนะครับ!** 🎉", เดิมพัน
    else:
        result, coins_change = "**บอทชนะครับ!** 😈", -เดิมพัน
    user["coins"] += coins_change
    leveled_up = add_xp(user, 10)
    save_user(user)
    msg = f"{RPS_MAP[player]} vs {RPS_MAP[bot_choice]}\n{result}"
    if เดิมพัน > 0:
        sign = "+" if coins_change >= 0 else ""
        msg += f"\n🪙 เหรียญ: {sign}{coins_change} (รวม: **{user['coins']}** เหรียญ)"
    if leveled_up: msg += f"\n🎉 **เลเวลอัพ!** ตอนนี้คุณเป็น Level {user['level']} แล้ว!"
    await interaction.response.send_message(msg)

@tree.command(name="สล็อต", description="เล่นสล็อตเดิมพันเหรียญ")
async def slots(interaction: discord.Interaction, เดิมพัน: int = 50):
    user = get_user(interaction.user.id)
    if เดิมพัน <= 0:
        await interaction.response.send_message("❌ เดิมพันต้องมากกว่า 0 ครับ"); return
    if เดิมพัน > user["coins"]:
        await interaction.response.send_message(f"❌ เหรียญไม่พอครับ! คุณมีแค่ **{user['coins']}** เหรียญ"); return
    reels = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
    display = " | ".join(reels)
    if reels[0] == reels[1] == reels[2]:
        if reels[0] == "💎":
            mult, result = 10, "**JACKPOT!! 💎💎💎** ได้ x10!"
        else:
            mult, result = 5, f"**ชนะ! {reels[0]}{reels[0]}{reels[0]}** ได้ x5!"
        winnings = เดิมพัน * mult
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        mult, result = 2, "**ชนะนิดหน่อย!** ได้ x2"
        winnings = เดิมพัน * mult
    else:
        result   = "**แพ้แล้วครับ 😢**"
        winnings = 0
    user["coins"] += winnings - เดิมพัน
    leveled_up = add_xp(user, 15)
    save_user(user)
    msg = f"🎰 **[ {display} ]**\n{result}\n"
    if winnings > 0:
        msg += f"🪙 ได้รับ **{winnings}** เหรียญ! (รวม: **{user['coins']}** เหรียญ)"
    else:
        msg += f"💸 เสีย **{เดิมพัน}** เหรียญ (รวม: **{user['coins']}** เหรียญ)"
    if leveled_up: msg += f"\n🎉 **เลเวลอัพ!** ตอนนี้คุณเป็น Level {user['level']} แล้ว!"
    await interaction.response.send_message(msg)

# ── Moderation ────────────────────────────────────────────────

@tree.command(name="เตือน", description="[Admin] เตือนสมาชิก")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, สมาชิก: discord.Member, เหตุผล: str = "ไม่ระบุ"):
    user = get_user(สมาชิก.id)
    user["warnings"] += 1
    save_user(user)
    await interaction.response.send_message(
        f"⚠️ **{สมาชิก.display_name}** ได้รับการเตือนครั้งที่ {user['warnings']}\n📝 เหตุผล: {เหตุผล}"
    )

@tree.command(name="คิก", description="[Admin] คิกสมาชิกออกจาก Server")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, สมาชิก: discord.Member, เหตุผล: str = "ไม่ระบุ"):
    await สมาชิก.kick(reason=เหตุผล)
    await interaction.response.send_message(f"👢 **{สมาชิก.display_name}** ถูกคิกออกแล้วครับ\n📝 เหตุผล: {เหตุผล}")

@tree.command(name="แบน", description="[Admin] แบนสมาชิกออกจาก Server")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, สมาชิก: discord.Member, เหตุผล: str = "ไม่ระบุ"):
    await สมาชิก.ban(reason=เหตุผล)
    await interaction.response.send_message(f"🔨 **{สมาชิก.display_name}** ถูกแบนแล้วครับ\n📝 เหตุผล: {เหตุผล}")

@warn.error
@kick.error
@ban.error
async def mod_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้ครับ", ephemeral=True)

keep_alive()
client.run(os.environ["DISCORD_BOT_TOKEN"])
