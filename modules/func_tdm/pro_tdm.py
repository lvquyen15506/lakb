import speedtest
import random
import colorsys
from datetime import datetime, timedelta, timezone
import glob
from io import BytesIO
import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core.bot_sys import is_admin
from modules.AI_GEMINI.pro_gemini import get_user_name_by_id
from zlapi.models import *

BACKGROUND_PATH = "background/"
CACHE_PATH = "modules/cache/"
OUTPUT_IMAGE_PATH = os.path.join(CACHE_PATH, "menu.png")

# Ham lay ten nguoi dung tu ID (Can đieu chinh theo cach lay ten trong bot cua ban)
def get_user_name_by_id(bot, user_id):
    return "Nguoi Dung"  # Đoi phan nay đe lay ten that cua nguoi dung tu bot API

# Ham thuc hien đo toc đo mang
def run_speedtest_tag(bot, author_id, thread_id, thread_type, mention_id=None):
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download = round(st.download() / 1_000_000, 2)  # Toc đo download (Mbps)
        upload = round(st.upload() / 1_000_000, 2)  # Toc đo upload (Mbps)
        ping = round(st.results.ping, 2)  # Ping (ms)

        # Tag nguoi neu co mention
        if mention_id:
            mention_name = get_user_name_by_id(bot, mention_id)
            msg = f"📡 Ket qua đo mang cho @{mention_name}:\n⬇️ Download: {download} Mbps\n⬆️ Upload: {upload} Mbps\n📶 Ping: {ping} ms"
            mention_obj = Mention(mention_id, length=len(f"@{mention_name}"), offset=25)
        else:
            mention_name = get_user_name_by_id(bot, author_id)
            msg = f"📡 Ket qua đo mang cho @{mention_name}:\n⬇️ Download: {download} Mbps\n⬆️ Upload: {upload} Mbps\n📶 Ping: {ping} ms"
            mention_obj = Mention(author_id, length=len(f"@{mention_name}"), offset=25)

        bot.sendMessage(msg, thread_id, thread_type, mentions=[mention_obj])
    except Exception as e:
        bot.sendMessage(f"❌ Loi khi đo toc đo mang: {e}", thread_id, thread_type)

# Ham xu ly lenh -> tdm va cac chuc nang lien quan
def handle_tdm_command(self, thread_type, message, message_object, author_id, client):
    author_id = message.author
    text = message.text.lower().strip()
    mentions = message.mentions or []

    # Toggle đo mang
    if text.startswith("-> tdm check"):
        status = toggle_speedtest(thread_id)
        msg = "✅ Đa BAT đo toc đo mang!" if status else "❌ Đa TAT đo toc đo mang!"
        bot.sendMessage(msg, thread_id, thread_type)
        return

    # Chi hien thi ket qua đo mang cho nguoi goi
    if text == "-> tdm":
        bot.sendMessage("⏳ Đang đo toc đo mang cho ban...", thread_id, thread_type)
        run_speedtest_tag(bot, author_id, thread_id, thread_type)
        return

    # Neu co tag nguoi khac: đo mang va tag ho
    if text.startswith("-> tdm") and mentions:
        target_id = mentions[0].id
        bot.sendMessage("⏳ Đang đo mang cho nguoi đuoc tag...", thread_id, thread_type)
        run_speedtest_tag(bot, author_id, thread_id, thread_type, mention_id=target_id)
        return

    # Neu nhap sai đinh dang
    bot.sendMessage("❌ Sai cu phap! Dung:\n-> tdm\n-> tdm check\n-> tdm @user", thread_id, thread_type)

# Ham bat/tat chuc nang đo toc đo mang (gia lap)
def toggle_speedtest(thread_id):
    # Gia lap bat/tat. Thuc te ban co the luu trang thai vao database hoac file.
    status = random.choice([True, False])
    return status

# Phan menu va cac chuc nang lien quan
def handle_menu_commands(message, message_object, thread_id, thread_type, author_id, bot):
    command_names = "".join([
        f"{get_user_name_by_id(bot, author_id)}\n"
        "➜ ☁️ Tdm ({bot.prefix}tdm)\n"
        "➜ 🐳 Tdm @user ({bot.prefix}tdm)\n"
    ])
    
    image_path = generate_menu_image(bot, author_id, thread_id, thread_type)
    
    reaction = [
        "❌", "🤧", "🐞", "😊", "🔥", "👍", "💖", "🚀", "😍", "😂", "😢", "😎", "🙌", "💪", "🌟", "🍀", "🎉", "🦁", "🌈", "🍎", 
        # Them cac bieu tuong cam xuc o đay
    ]
    
    bot.sendReaction(message_object, random.choice(reaction), thread_id, thread_type)
    bot.sendLocalImage(
        imagePath=image_path,
        message=Message(text=command_names, mention=Mention(author_id, length=len(f"{get_user_name_by_id(bot, author_id)}"), offset=0)),
        thread_id=thread_id,
        thread_type=thread_type,
        width=1920, height=600,
        ttl=60000
    )
    
    try:
        os.remove(image_path)
    except Exception as e:
        print(f"❌ Loi khi xoa anh: {e}")

# Cac ham xu ly anh va mau sac
def get_dominant_color(image_path):
    try:
        if not os.path.exists(image_path):
            print(f"File anh khong ton tai: {image_path}")
            return (0, 0, 0)
        
        img = Image.open(image_path).convert("RGB")
        img = img.resize((150, 150), Image.Resampling.LANCZOS)
        pixels = img.getdata()

        if not pixels:
            print(f"Khong the lay du lieu pixel tu anh: {image_path}")
            return (0, 0, 0)

        r, g, b = 0, 0, 0
        for pixel in pixels:
            r += pixel[0]
            g += pixel[1]
            b += pixel[2]

        total = len(pixels)
        if total == 0:
            return (0, 0, 0)
        
        r, g, b = r // total, g // total, b // total
        return (r, g, b)
    except Exception as e:
        print(f"Loi khi phan tich mau noi bat: {e}")
        return (0, 0, 0)

def generate_menu_image(bot, author_id, thread_id, thread_type):
    images = glob.glob(BACKGROUND_PATH + "*.jpg") + glob.glob(BACKGROUND_PATH + "*.png") + glob.glob(BACKGROUND_PATH + "*.jpeg")
    
    if not images:
        print("❌ Khong tim thay anh trong thu muc background/")
        return None
    
    image_path = random.choice(images)
    
    try:
        size = (1920, 600)
        final_size = (1280, 380)
        bg_image = Image.open(image_path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=7))
        
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        dominant_color = get_dominant_color(image_path)
        r, g, b = dominant_color
        
        # Ve len overlay hoac thuc hien cac thao tac voi anh
        
        final_image = Image.alpha_composite(bg_image, overlay)
        final_image_path = os.path.join(CACHE_PATH, "final_menu_image.png")
        final_image.save(final_image_path)
        return final_image_path
    
    except Exception as e:
        print(f"Loi khi tao anh menu: {e}")
        return None

# Cac ham khac xu ly download anh avatar, mau sac tuong phan, v.v. co the giu lai tuong tu.
