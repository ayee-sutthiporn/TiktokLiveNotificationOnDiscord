import asyncio
import json
import os
import urllib.request
import random
from typing import Optional

from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, DisconnectEvent

# Global state
tiktok_client: Optional[TikTokLiveClient] = None
live_start_time: Optional[float] = None

# ================= Discord Webhook =================
# นำลิงก์ Discord Webhook มาใส่ที่นี่ หรือจะผ่าน Environment ก็ได้
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Username ที่ต้องการตรวจสอบ (ให้ดึงจาก Environment ถ้ามี)
TIKTOK_USERNAME = os.environ.get("TIKTOK_USERNAME", "_miyoomiyo") # 🔴 ใส่ชื่อผู้ใช้ที่ต้องการ (ไม่ต้องมี @)

async def send_discord_webhook(message: str = None, embeds: list = None):
    """ส่งข้อความแจ้งเตือนเข้า Discord"""
    if not DISCORD_WEBHOOK_URL.strip():
        return
    
    def _send():
        data = {}
        if message:
            data["content"] = message
        if embeds:
            data["embeds"] = embeds
            
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "TikTokLive-Bot"}
        )
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"Discord webhook error: {e}")
            
    # ใช้ asyncio.to_thread เพื่อไม่ให้ webhook block การทำงานหลักของระบบ
    await asyncio.to_thread(_send)
# ===================================================


async def start_tiktok(unique_id: str):
    """เริ่มเชื่อมต่อ TikTok Live"""
    global tiktok_client, live_start_time

    if tiktok_client and tiktok_client.connected:
        await tiktok_client.disconnect()

    tiktok_client = TikTokLiveClient(unique_id=unique_id)

    @tiktok_client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        global live_start_time
        live_start_time = asyncio.get_event_loop().time()
        
        # Build Start Embed (อิงตาม index.js)
        # หมายเหตุ: TikTokLiveClient ไม่มี roomInfo ทันทีใน event นี้ จึงใช้ title เริ่มต้น
        start_timestamp = int(os.environ.get("START_TIME", asyncio.get_event_loop().time()))
        
        from datetime import datetime, timezone
        
        start_titles = [
            f"✿ 🔴 LIVE: @{unique_id} มาแล้วจ้า~ ✿",
            f"✿ 🔴 LIVE: @{unique_id} เริ่มสตรีมแล้วน้า ✿",
            f"✿ 🔴 LIVE: แวะมาดู @{unique_id} กันเถอะ ✿",
            f"✿ 🔴 LIVE: @{unique_id} กำลังไลฟ์สด! ✿",
        ]
        
        start_descriptions = [
            f"เมี้ยว~ **@{unique_id}** เปิดไลฟ์แล้วน้า 🐾\nแวะเข้ามาทักทายกันได้เลย~\n\nเริ่มเมื่อ: <t:{int(datetime.now(timezone.utc).timestamp())}:R>",
            f"ทุกคน! **@{unique_id}** มาแล้วจ้า 🎉\nเข้ามาพูดคุยกันเถอะ!\n\nเริ่มเมื่อ: <t:{int(datetime.now(timezone.utc).timestamp())}:R>",
            f"เย้! **@{unique_id}** เริ่มสตรีมแล้ว ✨\nอย่าลืมเข้ามาให้กำลังใจกันน้า~\n\nเริ่มเมื่อ: <t:{int(datetime.now(timezone.utc).timestamp())}:R>",
            f"ก๊อกๆ **@{unique_id}** เปิดไลฟ์แล้วน้า 💖\nมาร่วมสนุกกันเถอะ!\n\nเริ่มเมื่อ: <t:{int(datetime.now(timezone.utc).timestamp())}:R>",
        ]
        
        start_mentions = [
            f"🔔 **@{unique_id}** กำลัง LIVE แล้วค่าาา~ 😺💕",
            f"📢 มาแล้ววว **@{unique_id}** เริ่มไลฟ์แล้วจ้า! รีบเข้ามาดูเร็ว 🏃‍♀️💨",
            f"✨ พลาดไม่ได้! **@{unique_id}** สตรีมแล้วตอนนี้ ไปดูกันเลยยย 📺",
            f"🎉 **@{unique_id}** เปิดไลฟ์แล้วน้า แวะไปให้กำลังใจกันเถอะ 🎁",
        ]

        # Extract image if room_info is present
        image_url = None
        info = tiktok_client.room_info
        if info:
            if "cover" in info and "url_list" in info["cover"] and info["cover"]["url_list"]:
                image_url = info["cover"]["url_list"][0]
            elif "owner" in info and "avatar_large" in info["owner"] and "url_list" in info["owner"]["avatar_large"] and info["owner"]["avatar_large"]["url_list"]:
                image_url = info["owner"]["avatar_large"]["url_list"][0]

        embed = {
            "title": random.choice(start_titles),
            "description": random.choice(start_descriptions),
            "url": f"https://www.tiktok.com/@{unique_id}/live",
            "color": 0xffb6c1,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if image_url:
            embed["image"] = {"url": image_url}
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 {unique_id} เริ่ม Live แล้ว")
        await send_discord_webhook(
            message=random.choice(start_mentions),
            embeds=[embed]
        )

    @tiktok_client.on(DisconnectEvent)
    async def on_disconnect(event: DisconnectEvent):
        global live_start_time
        
        minutes = 0
        if live_start_time is not None:
            minutes = int((asyncio.get_event_loop().time() - live_start_time) / 60)
            
        end_titles = [
            "✿ ⚫️ ไลฟ์จบแล้ว ✿",
            "✿ 💤 สตรีมจบแล้วจ้า ✿",
            "✿ 👋 ไว้เจอกันใหม่น้า ✿",
        ]
        
        end_descriptions = [
            f"สตรีมของ **@{unique_id}** จบแล้วเมี้ยว~\nรวมเวลาไลฟ์: **{minutes} นาที** ⏱️\nขอบคุณทุกคนที่แวะมานะคะ ฅ^•ﻌ•^ฅ",
            f"**@{unique_id}** ปิดไลฟ์ไปแล้วจ้า 😴\nใช้เวลาสตรีมไปทั้งหมด: **{minutes} นาที** ⏱️\nพักผ่อนเยอะๆ น้า~",
            f"จบการสตรีมของ **@{unique_id}** แล้ว 🎉\nไลฟ์รอบนี้ความยาว: **{minutes} นาที** ⏱️\nแล้วพบกันใหม่รอบหน้านะคะ เจอกัน!",
            f"วันนี้ **@{unique_id}** ลงไลฟ์แล้วน้า 👋\nใช้เวลาไลฟ์ไป: **{minutes} นาที** ⏱️\nขอบคุณที่คอยซัพพอร์ตกันตลอดมานะคะ 💖",
        ]
            
        embed = {
            "title": random.choice(end_titles),
            "description": random.choice(end_descriptions),
            "color": 0x99aab5
        }
        from datetime import datetime, timezone
        embed["timestamp"] = datetime.now(timezone.utc).isoformat()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔴 {unique_id} หยุด Live / ตัดการเชื่อมต่อ")
        await send_discord_webhook(embeds=[embed])

    # ทดสอบ Webhook ตอนเริ่มโปรแกรม
    from datetime import datetime, timezone
    embed = {
        "title": "✿ 🟢 เริ่มระบบ ✿",
        "description": f"ระบบ TikTokLive-Bot พร้อมทำงานแล้ว!\nกำลังติดตามการแจ้งเตือนของ: **@{unique_id}** 🐾",
        "color": 0x00d26a,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await send_discord_webhook(embeds=[embed])

    print(f"กำลังเชื่อมต่อกับ {unique_id}...")
    try:
        # ลบเครื่องหมาย @ ออกจาก username ถ้ามี
        clean_id = unique_id.lstrip('@')
        # สร้างตัว client ใหม่ด้วย clean_id
        tiktok_client = TikTokLiveClient(unique_id=clean_id)
        
        # Register events again on the new client object since we overrode it
        
        @tiktok_client.on(ConnectEvent)
        async def _on_connect(event: ConnectEvent):
            await on_connect(event)
            
        @tiktok_client.on(DisconnectEvent)
        async def _on_disconnect(event: DisconnectEvent):
            await on_disconnect(event)
            
        await tiktok_client.connect(fetch_room_info=True)
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
        # ลูปให้ลองเชื่อมต่อใหม่ (Retry loop แบบง่าย)
        await asyncio.sleep(15)
        # Call start_tiktok again with the original unique_id
        await start_tiktok(unique_id)

async def main():
    if not TIKTOK_USERNAME or TIKTOK_USERNAME == "username_here":
        print("กรุณาใส่ TIKTOK_USERNAME ในไฟล์ start.py")
        return
        
    while True:
        try:
            await start_tiktok(TIKTOK_USERNAME)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("ปิดโปรแกรม...")