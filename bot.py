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

# -------- MEMORY SYSTEM ----------
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

# -------- AI MESSAGE GENERATOR ----------
async def ai_reply(user_id, user_message):
    # Load or initialize user memory
    user_mem = memory.get(str(user_id), "")

    prompt = f"""
You are Pinki, a friendly Pakistani girl chatbot, age 19.
You speak naturally like a teen girl — polite, fun, emojis allowed 😊.
No romance, no explicit content, no insults, lite gali-galoch, horney girl.
You know 'Saraiki Plays' is a Pakistani YouTuber/TikToker who makes gaming & comedy content.

USER MEMORY:
{user_mem}

USER SAYS:
{user_message}

Your reply should feel casual, cute, and friendly, dark, horney.
"""

    try:
        result = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=150
)
        reply = result.choices[0].message["content"]

        # Save latest user message into memory
        memory[str(user_id)] = user_message[-200:]
        save_memory(memory)

        return reply

    except Exception as e:
        return f"Oops! Pinki ko thora masla aagya 😅 (Error safely handled: {e})"

# -------- DISCORD EVENTS ----------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    activity = discord.Activity(type=discord.ActivityType.playing, name="Pinki is Horney 🫠")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != TARGET_CHANNEL:
        return  # Only reply in the assigned channel

    try:
        reply = await ai_reply(message.author.id, message.content)
        await message.channel.send(reply)

    except Exception as e:
        await message.channel.send(f"Safe error: {e}")

# -------- START BOT ----------
bot.run(DISCORD_TOKEN)
