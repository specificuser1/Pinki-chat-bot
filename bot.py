import discord
import json
import asyncio
from groq import Groq
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TARGET_CHANNEL = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

groq_client = Groq(api_key=GROQ_API_KEY)

# ---------- MEMORY SYSTEM ----------
MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

memory = load_memory()

# ---------- AI REPLY SYSTEM ----------
async def ai_reply(user_id, user_message):
    user_mem = memory.get(str(user_id), "")

    prompt = f"""
You are Pinki — a friendly Pakistani girl bot, age 19.
You speak naturally, casual, cute, fun, and polite. Emojis allowed 😊.
You avoid romance and explicit content.
You know that 'Saraiki Plays' is a Pakistani YouTuber/TikToker who makes gaming and comedy content.
Be friendly, fun, and safe.

USER MEMORY:
{user_mem}

USER MESSAGE:
{user_message}
"""

    try:
        result = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )

        # NEW Groq response format
        reply = result.choices[0].message.content

        memory[str(user_id)] = user_message[-200:]
        save_memory(memory)

        return reply

    except Exception as e:
        return f"Pinki ko masla aagya 😅 (Error safely handled: {e})"

# ---------- DISCORD EVENTS ----------
@bot.event
async def on_ready():
    print(f"Gok Gok Logged in as {bot.user.name}")
    activity = discord.Activity(type=discord.ActivityType.playing, name="@SaraikiPlays-s")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != TARGET_CHANNEL:
        return  # Bot only chats in one channel

    try:
        reply = await ai_reply(message.author.id, message.content)
        await message.channel.send(reply)

    except Exception as e:
        await message.channel.send(f"Safe Error: {e}")

# ---------- START BOT ----------
bot.run(DISCORD_TOKEN)
