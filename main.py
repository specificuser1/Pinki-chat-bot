import discord
from discord.ext import commands
from discord import app_commands
from groq import Groq
import os, json, time
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
CHANNEL_ID = int(os.getenv("ALLOWED_CHANNEL_ID"))

client_ai = Groq(api_key=GROQ_KEY)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

MEMORY_FILE = "memory.json"
start_time = time.time()

# -------- Memory System --------
def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

memory = load_memory()

# -------- Level System --------
def add_xp(user_id):
    if user_id not in memory:
        memory[user_id] = {
            "name": "",
            "messages": [],
            "xp": 0,
            "level": 0,
            "notes": ""
        }

    memory[user_id]["xp"] += 10
    memory[user_id]["level"] = memory[user_id]["xp"] // 100

# -------- Admin Check --------
def is_admin(interaction):
    return interaction.user.guild_permissions.administrator

# -------- Control Panel --------
class ControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📊 Status", style=discord.ButtonStyle.primary)
    async def status(self, interaction, button):
        if not is_admin(interaction):
            return await interaction.response.send_message("Only Admin 😌", ephemeral=True)

        uptime = round(time.time() - start_time)
        await interaction.response.send_message(
            f"💖 Pinki Online\nLatency: {round(bot.latency*1000)}ms\nUsers: {len(memory)}\nUptime: {uptime}s"
        )

    @discord.ui.button(label="🧠 Reset Memory", style=discord.ButtonStyle.danger)
    async def reset_memory(self, interaction, button):
        if not is_admin(interaction):
            return await interaction.response.send_message("Only Admin 😌", ephemeral=True)

        memory.clear()
        save_memory(memory)
        await interaction.response.send_message("Memory Reset Done 💖")

# -------- Slash Panel --------
@bot.tree.command(name="panel")
async def panel(interaction: discord.Interaction):
    if not is_admin(interaction):
        return await interaction.response.send_message("Admin Only 💖", ephemeral=True)

    await interaction.response.send_message("🎀 Pinki Control Panel", view=ControlPanel())

# -------- Message Event --------
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id != CHANNEL_ID:
        return

    user_id = str(message.author.id)
    user_name = message.author.name

    if user_id not in memory:
        memory[user_id] = {
            "name": user_name,
            "messages": [],
            "xp": 0,
            "level": 0,
            "notes": ""
        }

    memory[user_id]["name"] = user_name
    memory[user_id]["messages"].append(message.content)
    memory[user_id]["messages"] = memory[user_id]["messages"][-5:]

    add_xp(user_id)
    save_memory(memory)

    # Level Up
    if memory[user_id]["xp"] % 100 == 0:
        await message.reply(f"🎉 {user_name} Level Up! Ab tum level {memory[user_id]['level']} ho 💖")

    # Special Saraiki Plays Reply
    if "saraiki plays" in message.content.lower():
        await message.reply(
            "Saraiki Plays ak Content Creator ha 💖\n"
            "Funny gaming content banata ha 😂\n"
            "TikTok 100k jaldi complete kiye 🔥\n"
            "Age 19-20\nReal name Adeel\nMultan Pakistan"
        )
        return

    # Pinki AI Reply
    try:
        response = client_ai.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": f"""
Tum Pinki ho 💖
Cute Pakistani girl
Urdu me short reply do
Emojis use karo kabi kabi
Funny dark Jokes bee kabi kabi reply kry
User ka naam {user_name}
Level {memory[user_id]['level']}
"""
                },
                {
                    "role": "user",
                    "content": message.content
                }
            ]
        )

        reply = response.choices[0].message.content[:400]
        await message.reply(reply)

    except:
    await message.reply("Pinki thora mood me nahi 😒💔")
    
    await bot.process_commands(message)

bot.run(TOKEN)
