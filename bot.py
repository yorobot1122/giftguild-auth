# bot.py (예시)
import discord
import redis
import secrets
import asyncio

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
REDIS = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
AUTH_BASE_URL = "https://giftguildauth.duckdns.org/auth"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.content.strip() == "!동의":
        token = secrets.token_urlsafe(32)
        REDIS.setex(token, 600, str(message.author.id))  # 10분간 유효
        auth_url = f"{AUTH_BASE_URL}?token={token}"
        try:
            await message.author.send(f"🔐 아래 링크를 클릭하여 인증을 완료해주세요!\n\n{auth_url}")
            await message.channel.send("📬 DM으로 인증 링크를 보냈어요!")
        except discord.Forbidden:
            await message.channel.send("❌ DM을 보낼 수 없습니다. DM 허용 설정을 확인해주세요.")

client.run(TOKEN)
