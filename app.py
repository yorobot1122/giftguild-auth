import os
import time
import redis
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from discord import Client, Intents

# 환경 변수 불러오기
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
GUILD_ID = int(os.getenv("GUILD_ID"))
ROLE_ID = int(os.getenv("ROLE_ID"))

# Flask 앱 및 Redis 설정
app = Flask(__name__)
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Discord 클라이언트 설정
intents = Intents.default()
intents.members = True
bot = Client(intents=intents)

# 10분 유효한 토큰 생성 및 저장
def generate_token(user_id, username, avatar):
    import secrets
    token = secrets.token_urlsafe(16)
    payload = {
        "user_id": user_id,
        "username": username,
        "avatar": avatar
    }
    r.setex(token, 600, json.dumps(payload))  # 600초 = 10분
    return token

# Flask: 사용자 정보 제공
@app.route("/get_user_info")
def get_user_info():
    token = request.args.get("token")
    data = r.get(token)
    if not data:
        return jsonify({"success": False})
    user_info = json.loads(data)
    return jsonify({"success": True, **user_info})

# Flask: 인증 확인 및 역할 부여
@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    token = data.get("token")
    recaptcha = data.get("recaptcha")

    # reCAPTCHA 검증
    res = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data={"secret": RECAPTCHA_SECRET_KEY, "response": recaptcha}
    ).json()

    if not res.get("success"):
        return jsonify({"success": False, "message": "reCAPTCHA 실패"})

    # Redis에서 사용자 정보 가져오기
    user_data = r.get(token)
    if not user_data:
        return jsonify({"success": False, "message": "유효하지 않은 토큰"})

    user_info = json.loads(user_data)
    user_id = int(user_info["user_id"])

    # 역할 부여
    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(user_id)
    if not member:
        return jsonify({"success": False, "message": "서버에서 사용자를 찾을 수 없음"})

    try:
        role = guild.get_role(ROLE_ID)
        if role:
            import asyncio
            asyncio.run_coroutine_threadsafe(member.add_roles(role), bot.loop)
            r.delete(token)  # 사용 완료된 토큰 삭제
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "역할을 찾을 수 없음"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# 디스코드 봇 실행
@bot.event
async def on_ready():
    print(f"✅ Discord 봇 로그인됨: {bot.user}")

@bot.event
async def on_message(message):
    if message.content == "!동의":
        if isinstance(message.channel.type, int):  # guild 채널
            try:
                token = generate_token(str(message.author.id), str(message.author), message.author.avatar)
                url = f"https://giftguildauth.duckdns.org/?token={token}"
                await message.author.send(
                    f"🎉 인증을 위해 아래 링크를 클릭해주세요 (10분 유효)\n{url}"
                )
                await message.channel.send("DM을 확인해주세요!")
            except Exception as e:
                await message.channel.send(f"DM 전송 실패: {e}")

# Flask와 디스코드 봇 동시 실행
if __name__ == "__main__":
    import threading

    def run_flask():
        app.run(host="0.0.0.0", port=80)

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    bot.run(DISCORD_BOT_TOKEN)
