import os
import random
import json
import time
import discord
from discord import app_commands
from keep_alive import keep_alive

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"coins": 0, "xp": 0, "level": 1, "last_work": 0, "warnings": 0, "title": "", "inventory": []}
    if "title" not in data[uid]:
        data[uid]["title"] = ""
    if "inventory" not in data[uid]:
        data[uid]["inventory"] = []
    return data[uid]

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

SHOP_ITEMS = [
    {"id": "vip",   "name": "👑 VIP",       "desc": "ตำแหน่ง VIP แสดงในโปรไฟล์",   "price": 500},
    {"id": "pro",   "name": "⚡ Pro",        "desc": "ตำแหน่ง Pro แสดงในโปรไฟล์",   "price": 300},
    {"id": "rich",  "name": "💎 เศรษฐี",     "desc": "ตำแหน่งเศรษฐีแสดงในโปรไฟล์", "price": 1000},
    {"id": "lucky", "name": "🍀 โชคดี",      "desc": "ตำแหน่งโชคดีแสดงในโปรไฟล์",  "price": 200},
    {"id": "boost", "name": "🚀 XP Booster", "desc": "รับ XP x2 จาก /งาน 10 ครั้ง", "price": 400},
]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

HELLO_RESPONSES = ["สวัสดีครับ 👋","หวัดดีครับ! มีอะไรให้ช่วยไหม? 😊","ยินดีต้อนรับครับ 🎉","อ้าว มาแล้วหรอ! สวัสดีครับ 😄","เฮ้! ดีใจที่เห็นครับ 🙌"]
HUNGRY_RESPONSES = ["ไปหาอะไรกินในตู้เย็นไหมครับ 🍱","ข้าวกล่องอยู่ในตู้เย็นนะครับ ลองเปิดดูสิ 🥡","หิวแล้วหรอ? สั่ง Grab Food เลยครับ 🛵","มาม่าไม่เคยทำให้ผิดหวังนะครับ 🍜","ขนมถุงอยู่ตรงไหนก็ไปหาดูนะครับ 🍪","ออกไปซื้อข้าวข้างนอกก็ได้ครับ 🌤️"]
FORTUNE_RESPONSES = ["ดวงวันนี้ดีมากครับ ⭐ มีโชคลาภรออยู่!","ระวังเรื่องการเงินหน่อยนะครับ 💸 แต่โดยรวมโอเค","วันนี้ดวงความรักมาแรงครับ ❤️ เปิดใจไว้เลย","ดวงวันนี้กลางๆ ครับ ขึ้นอยู่กับตัวเองเลย","โชคดีมากครับวันนี้! 🍀","ดวงการงานดีครับ วันนี้เหมาะทำสิ่งใหม่ๆ 🚀"]
TIRED_RESPONSES = ["พักก่อนนะครับ ร่างกายสำคัญกว่างาน 💙","เหนื่อยก็หยุดพักได้ครับ ไม่ต้องสู้คนเดียว 🫂","ดื่มน้ำ นอนหลับ พรุ่งนี้ค่อยสู้ใหม่ครับ 😴","คุณทำได้ดีมากแล้วครับ 🌟","ทุกอย่างจะผ่านไปได้ครับ สู้ๆ นะ 💪","เหนื่อยแล้วก็พักได้เลยครับ 🤗"]
WORK_RESPONSES = ["คุณไปส่งพัสดุและได้รับ {coins} เหรียญ 📦","คุณขายของออนไลน์และได้รับ {coins} เหรียญ 🛒","คุณรับจ้างเขียนโค้ดและได้รับ {coins} เหรียญ 💻","คุณออกไปตัดหญ้าและได้รับ {coins} เหรียญ 🌿","คุณช่วยพ่อค้าแบกของและได้รับ {coins} เหรียญ 💪","คุณไปสอนพิเศษและได้รับ {coins} เหรียญ 📚","คุณรับงานฟรีแลนซ์และได้รับ {coins} เหรียญ 🎨"]
SLOT_SYMBOLS = ["🍒","🍋","🍊","🍇","⭐","💎"]
WORK_COOLDOWN = 90

@client.event
async def on_ready():
    await tree.sync()
    print(f"บอทออนไลน์แล้ว: {client.user}")

@tree.command(name="hello", description="ทักทายบอท")
async def hello(interaction: discord.Interaction):
    data = load_data(); user = get_user(data, interaction.user.id)
    leveled_up = add_xp(user, 5); save_data(data)
    msg = random.choice(HELLO_RESPONSES)
    if leveled_up: msg += f"\n🎉 **เลเวลอัพ!** ตอนนี้คุณเป็น Level {user['level']} แล้ว!"
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
    options = ["ใช่ครับ ✅","ไม่ใช่ครับ ❌","ยังบอกไม่ได้ครับ 🤔","ลองถามใหม่อีกทีครับ 🔄","แน่นอนเลยครับ! 💯","อาจจะครับ... 50/50 🎲"]
    await interaction.response.send_message(f"❓ **{คำถาม}**\n→ {random.choice(options)}")

@tree.command(name="สุ่มเลข", description="สุ่มตัวเลข")
async def random_number(interaction: discord.Interaction, ต่ำสุด: int = 1, สูงสุด: int = 100):
    await interaction.response.send_message(f"🎲 สุ่มเลขระหว่าง {ต่ำสุด}-{สูงสุด} ได้: **{random.randint(ต่ำสุด, สูงสุด)}**")

@tree.command(name="งาน", description="ทำงานเพื่อรับเหรียญ (cooldown 1 นาที 30 วินาที)")
async def work(interaction: discord.Interaction):
    data = load_data(); user = get_user(data, interaction.user.id); now = time.time()
    remaining = WORK_COOLDOWN - (now - user["last_work"])
    if remaining > 0:
        await interaction.response.send_message(f"⏳ ยังทำงานได้อีกใน **{int(remaining//60)} นาที {int(remaining%60)} วินาที** ครับ"); return
    has_boost = "boost" in user.get("inventory", [])
    earned = random.randint(50, 200) * (2 if has_boost else 1)
    if has_boost: user["inventory"].remove("boost")
    user["coins"] += earned; user["last_work"] = now
    leveled_up = add_xp(user, 40 if has_boost else 20); save_data(data)
    msg = random.choice(WORK_RESPONSES).format(coins=earned)
    msg += f"\n💰 ยอดเหรียญรวม: **{user['coins']}** เหรียญ"
    if leveled_up: msg += f"\n🎉 **เลเวลอัพ!** ตอนนี้คุณเป็น Level {user['level']} แล้ว!"
    await interaction.response.send_message(msg)

@tree.command(name="เหรียญ", description="ดูยอดเหรียญของตัวเอง")
async def coins(interaction: discord.Interaction):
    data = load_data(); user = get_user(data, interaction.user.id)
    await interaction.response.send_message(f"🪙 **{interaction.user.display_name}** มีเหรียญ **{user['coins']}** เหรียญ")

@tree.command(name="โอน", description="โอนเหรียญให้สมาชิกคนอื่น")
async def transfer(interaction: discord.Interaction, สมาชิก: discord.Member, จำนวน: int):
    if จำนวน <= 0: await interaction.response.send_message("❌ จำนวนต้องมากกว่า 0 ครับ"); return
    if สมาชิก.id == interaction.user.id: await interaction.response.send_message("❌ โอนให้ตัวเองไม่ได้ครับ"); return
    data = load_data(); sender = get_user(data, interaction.user.id); receiver = get_user(data, สมาชิก.id)
    if sender["coins"] < จำนวน: await interaction.response.send_message(f"❌ เหรียญไม่พอครับ! มีแค่ **{sender['coins']}** เหรียญ"); return
    sender["coins"] -= จำนวน; receiver["coins"] += จำนวน; save_data(data)
    await interaction.response.send_message(f"💸 โอน **{จำนวน}** เหรียญให้ **{สมาชิก.display_name}** สำเร็จ!\n💰 เหลือ: **{sender['coins']}** เหรียญ")

@tree.command(name="โปรไฟล์", description="ดูโปรไฟล์และ Level ของตัวเอง")
async def profile(interaction: discord.Interaction):
    data = load_data(); user = get_user(data, interaction.user.id)
    needed = xp_for_level(user["level"]); bar_filled = int((user["xp"]/needed)*10)
    bar = "█"*bar_filled + "░"*(10-bar_filled)
    title_str = f" {user['title']}" if user.get("title") else ""
    embed = discord.Embed(title=f"📋 โปรไฟล์ของ {interaction.user.display_name}{title_str}", color=0x5865F2)
    embed.add_field(name="⭐ Level", value=str(user["level"]), inline=True)
    embed.add_field(name="✨ XP", value=f"{user['xp']}/{needed}", inline=True)
    embed.add_field(name="🪙 เหรียญ", value=str(user["coins"]), inline=True)
    embed.add_field(name="📊 Progress", value=f"`{bar}`", inline=False)
    embed.add_field(name="🎒 ไอเทม", value=", ".join(user.get("inventory",[])) or "ว่างเปล่า", inline=False)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@tree.command(name="อันดับ", description="ดู Leaderboard เหรียญของ Server")
async def leaderboard(interaction: discord.Interaction):
    data = load_data()
    if not data: await interaction.response.send_message("ยังไม่มีข้อมูลผู้เล่นครับ"); return
    sorted_users = sorted(data.items(), key=lambda x: x[1].get("coins",0), reverse=True)[:10]
    medals = ["🥇","🥈","🥉"]
    lines = []
    for i,(uid,udata) in enumerate(sorted_users):
        medal = medals[i] if i < 3 else f"`{i+1}.`"
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"User#{uid[-4:]}"
        lines.append(f"{medal} **{name}** — {udata.get('coins',0)} 🪙")
    embed = discord.Embed(title="🏆 อันดับเศรษฐีของ Server", description="\n".join(lines), color=0xFFD700)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ร้านค้า", description="ดูของที่ขายในร้าน")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 ร้านค้า", description="ใช้ `/ซื้อ` เพื่อซื้อสินค้าครับ", color=0x57F287)
    for item in SHOP_ITEMS: embed.add_field(name=f"{item['name']} — {item['price']} 🪙", value=item["desc"], inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ซื้อ", description="ซื้อสินค้าจากร้านค้า")
@app_commands.choices(สินค้า=[app_commands.Choice(name=f"{i['name']} ({i['price']} เหรียญ)", value=i["id"]) for i in SHOP_ITEMS])
async def buy(interaction: discord.Interaction, สินค้า: str):
    item = next((i for i in SHOP_ITEMS if i["id"] == สินค้า), None)
    if not item: await interaction.response.send_message("❌ ไม่พบสินค้านี้ครับ"); return
    data = load_data(); user = get_user(data, interaction.user.id)
    if user["coins"] < item["price"]: await interaction.response.send_message(f"❌ เหรียญไม่พอครับ! ต้องการ **{item['price']}** เหรียญ"); return
    user["coins"] -= item["price"]
    if สินค้า in ["vip","pro","rich","lucky"]: user["title"] = item["name"]
    elif สินค้า not in user["inventory"]: user["inventory"].append(สินค้า)
    save_data(data)
    await interaction.response.send_message(f"✅ ซื้อ **{item['name']}** สำเร็จ!\n💰 เหรียญเหลือ: **{user['coins']}** เหรียญ")

RPS_MAP = {"ค้อน":"✊","กระดาษ":"✋","กรรไกร":"✌️"}
RPS_WIN = {"ค้อน":"กรรไกร","กระดาษ":"ค้อน","กรรไกร":"กระดาษ"}

@tree.command(name="เป่ายิ้งฉุบ", description="เล่นเป่ายิ้งฉุบกับบอท (เดิมพันเหรียญได้)")
@app_commands.choices(ตัวเลือก=[app_commands.Choice(name="✊ ค้อน",value="ค้อน"),app_commands.Choice(name="✋ กระดาษ",value="กระดาษ"),app_commands.Choice(name="✌️ กรรไกร",value="กรรไกร")])
async def rps(interaction: discord.Interaction, ตัวเลือก: str, เดิมพัน: int = 0):
    data = load_data(); user = get_user(data, interaction.user.id)
    if เดิมพัน > user["coins"]: await interaction.response.send_message(f"❌ เหรียญไม่พอครับ!"); return
    bot_choice = random.choice(list(RPS_MAP.keys())); player = ตัวเลือก
    if player == bot_choice: result, coins_change = "เสมอกันครับ 🤝", 0
    elif RPS_WIN[player] == bot_choice: result, coins_change = "**คุณชนะครับ!** 🎉", เดิมพัน
    else: result, coins_change = "**บอทชนะครับ!** 😈", -เดิมพัน
    user["coins"] += coins_change; leveled_up = add_xp(user, 10); save_data(data)
    msg = f"{RPS_MAP[player]} vs {RPS_MAP[bot_choice]}\n{result}"
    if เดิมพัน > 0: msg += f"\n🪙 {'+' if coins_change>=0 else ''}{coins_change} (รวม: **{user['coins']}** เหรียญ)"
    if leveled_up: msg += f"\n🎉 **เลเวลอัพ!** Level {user['level']}!"
    await interaction.response.send_message(msg)

@tree.command(name="สล็อต", description="เล่นสล็อตเดิมพันเหรียญ")
async def slots(interaction: discord.Interaction, เดิมพัน: int = 50):
    data = load_data(); user = get_user(data, interaction.user.id)
    if เดิมพัน <= 0 or เดิมพัน > user["coins"]: await interaction.response.send_message(f"❌ เหรียญไม่พอหรือจำนวนไม่ถูกต้องครับ"); return
    reels = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
    if reels[0]==reels[1]==reels[2]: mult,result = (10,"**JACKPOT!! 💎💎💎** x10!") if reels[0]=="💎" else (5,f"**ชนะ! {reels[0]*3}** x5!")
    elif reels[0]==reels[1] or reels[1]==reels[2] or reels[0]==reels[2]: mult,result = 2,"**ชนะนิดหน่อย!** x2"
    else: mult,result = 0,"**แพ้แล้วครับ 😢**"
    winnings = เดิมพัน*mult; user["coins"] += winnings-เดิมพัน; leveled_up = add_xp(user,15); save_data(data)
    msg = f"🎰 **[ {' | '.join(reels)} ]**\n{result}\n"
    msg += f"🪙 ได้รับ **{winnings}** เหรียญ! (รวม: **{user['coins']}**)" if winnings > 0 else f"💸 เสีย **{เดิมพัน}** เหรียญ (รวม: **{user['coins']}**)"
    if leveled_up: msg += f"\n🎉 **เลเวลอัพ!** Level {user['level']}!"
    await interaction.response.send_message(msg)

@tree.command(name="เตือน", description="[Admin] เตือนสมาชิก")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, สมาชิก: discord.Member, เหตุผล: str = "ไม่ระบุ"):
    data = load_data(); user = get_user(data, สมาชิก.id); user["warnings"] += 1; save_data(data)
    await interaction.response.send_message(f"⚠️ **{สมาชิก.display_name}** ได้รับการเตือนครั้งที่ {user['warnings']}\n📝 เหตุผล: {เหตุผล}")

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