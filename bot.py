import discord
from discord.ext import commands
from discord import app_commands
from groq import Groq
import json, os, time, requests
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot Alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROQ_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

start_time = time.time()

MEMORY_FILE = "memory.json"

# ---------- MEMORY ----------
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    return json.load(open(MEMORY_FILE))

def save_memory(data):
    json.dump(data, open(MEMORY_FILE, "w"), indent=4)

memory = load_memory()
modes = {}

# ---------- AI ----------
async def ai_reply(user_id, msg):

    history = memory.get(str(user_id), [])
    history.append({"role": "user", "content": msg})

    mode = modes.get(user_id, "friendly")

    system_prompt = f"""
You are a safe, friendly AI assistant.
Personality mode: {mode}
Reply short, fun, helpful.
Speak English, Roman Urdu, or Banglish based on user message.
"""

    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":system_prompt}] + history[-12:]
    )

    reply = chat.choices[0].message.content

    history.append({"role":"assistant","content":reply})
    memory[str(user_id)] = history[-25:]
    save_memory(memory)

    return reply

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    await tree.sync()
    print("ULTRA PRO BOT READY")

# ---------- SLASH COMMANDS ----------

@tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Latency: {round(bot.latency*1000)}ms")

@tree.command(name="mode")
@app_commands.describe(type="friendly / funny / teacher / gamer")
async def mode(interaction: discord.Interaction, type: str):
    modes[interaction.user.id] = type
    await interaction.response.send_message(f"Mode changed to {type}")

@tree.command(name="reset")
async def reset(interaction: discord.Interaction):
    memory[str(interaction.user.id)] = []
    save_memory(memory)
    await interaction.response.send_message("Memory cleared")

@tree.command(name="status")
async def status(interaction: discord.Interaction):

    uptime = int(time.time() - start_time)

    embed = discord.Embed(title="ULTRA AI STATUS", color=0xff69b4)
    embed.add_field(name="Latency", value=f"{round(bot.latency*1000)}ms")
    embed.add_field(name="Users", value=str(len(memory)))
    embed.add_field(name="Uptime", value=f"{uptime}s")
    embed.add_field(name="Channel Lock", value=f"<#{CHANNEL_ID}>")

    await interaction.response.send_message(embed=embed)

# ---------- IMAGE GENERATOR ----------
@tree.command(name="imagine")
@app_commands.describe(prompt="Describe image")
async def imagine(interaction: discord.Interaction, prompt: str):

    await interaction.response.defer()

    url = f"https://image.pollinations.ai/prompt/{prompt}"
    await interaction.followup.send(url)

# ---------- MESSAGE ----------
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    # Allow DM chat
    if isinstance(message.channel, discord.DMChannel) or message.channel.id == CHANNEL_ID:

        async with message.channel.typing():
            reply = await ai_reply(message.author.id, message.content)

        await message.reply(reply)

    await bot.process_commands(message)

bot.run(TOKEN)
