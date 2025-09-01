import colorsys
from datetime import datetime
import glob
from io import BytesIO
import json
import random
import threading
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from core.bot_sys import extract_uids_from_mentions, get_user_name_by_id, is_admin
from zlapi.models import *
import os
import time
import pytz
from threading import Thread

WAR_TXT_DIR = "modules/func_war/war_txt/"
os.makedirs(WAR_TXT_DIR, exist_ok=True)

war_config = {
    'reo': {
        'file': os.path.join(WAR_TXT_DIR, "choc.txt"),
        'delay': 0.6
    },
    'spam': {
        'file': os.path.join(WAR_TXT_DIR, "noidung.txt"),
        'delay': 0.6
    },
    'poll': {
        'file': os.path.join(WAR_TXT_DIR, "noidung.txt"),
        'delay': 0.6
    },
    'todo': {
        'file': os.path.join(WAR_TXT_DIR, "noidung.txt"),
        'delay': 0.6
    }
}

sticker_file = os.path.join(WAR_TXT_DIR, "sticker.json")
is_reo_running = False
reo_lock = threading.Lock()
is_spam_running = False
spam_lock = threading.Lock()
is_polling = False
is_todo_active = False
BACKGROUND_PATH = "background/"
CACHE_PATH = "modules/cache/"
OUTPUT_IMAGE_PATH = os.path.join(CACHE_PATH, "war.png")

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

def get_contrasting_color(base_color, alpha=255):
    r, g, b = base_color[:3]
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return (255, 255, 255, alpha) if luminance < 0.5 else (0, 0, 0, alpha)

def random_contrast_color(base_color):
    r, g, b, _ = base_color
    box_luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    if box_luminance > 0.5:
        r = random.randint(0, 50)
        g = random.randint(0, 50)
        b = random.randint(0, 50)
    else:
        r = random.randint(200, 255)
        g = random.randint(200, 255)
        b = random.randint(200, 255)
    
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    s = min(1.0, s + 0.9)
    v = min(1.0, v + 0.7)
    
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    
    text_luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    if abs(text_luminance - box_luminance) < 0.3:
        if box_luminance > 0.5:
            r, g, b = colorsys.hsv_to_rgb(h, s, min(1.0, v * 0.4))
        else:
            r, g, b = colorsys.hsv_to_rgb(h, s, min(1.0, v * 1.7))
    
    return (int(r * 255), int(g * 255), int(b * 255), 255)

def download_avatar(avatar_url, save_path=os.path.join(CACHE_PATH, "user_avatar.png")):
    if not avatar_url:
        return None
    try:
        resp = requests.get(avatar_url, stream=True, timeout=5)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            return save_path
    except Exception as e:
        print(f"❌ Loi tai avatar: {e}")
    return None

def generate_menu_image(bot, author_id, thread_id, thread_type):
    images = glob.glob(os.path.join(BACKGROUND_PATH, "*.jpg")) + \
             glob.glob(os.path.join(BACKGROUND_PATH, "*.png")) + \
             glob.glob(os.path.join(BACKGROUND_PATH, "*.jpeg"))
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
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

        box_colors = [
            (255, 20, 147, 90),
            (128, 0, 128, 90),
            (0, 100, 0, 90),
            (0, 0, 139, 90),
            (184, 134, 11, 90),
            (138, 3, 3, 90),
            (0, 0, 0, 90)
        ]

        box_color = random.choice(box_colors)

        box_x1, box_y1 = 90, 60
        box_x2, box_y2 = size[0] - 90, size[1] - 60
        draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=75, fill=box_color)

        font_arial_path = "arial unicode ms.otf"
        font_emoji_path = "emoji.ttf"
        
        try:
            font_text_large = ImageFont.truetype(font_arial_path, size=76)
            font_text_big = ImageFont.truetype(font_arial_path, size=68)
            font_text_small = ImageFont.truetype(font_arial_path, size=64)
            font_text_bot = ImageFont.truetype(font_arial_path, size=58)
            font_time = ImageFont.truetype(font_arial_path, size=56)
            font_icon = ImageFont.truetype(font_emoji_path, size=60)
            font_icon_large = ImageFont.truetype(font_emoji_path, size=175)
            font_name = ImageFont.truetype(font_emoji_path, size=60)
        except Exception as e:
            print(f"❌ Loi tai font: {e}")
            font_text_large = ImageFont.load_default(size=76)
            font_text_big = ImageFont.load_default(size=68)
            font_text_small = ImageFont.load_default(size=64)
            font_text_bot = ImageFont.load_default(size=58)
            font_time = ImageFont.load_default(size=56)
            font_icon = ImageFont.load_default(size=60)
            font_icon_large = ImageFont.load_default(size=175)
            font_name = ImageFont.load_default(size=60)

        def draw_text_with_shadow(draw, position, text, font, fill, shadow_color=(0, 0, 0, 250), shadow_offset=(2, 2)):
            x, y = position
            draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font, fill=shadow_color)
            draw.text((x, y), text, font=font, fill=fill)

        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        vietnam_now = datetime.now(vietnam_tz)
        hour = vietnam_now.hour
        formatted_time = vietnam_now.strftime("%H:%M")
        time_icon = "🌤️" if 6 <= hour < 18 else "🌙"
        time_text = f" {formatted_time}"
        time_x = box_x2 - 250
        time_y = box_y1 + 10
        
        box_rgb = box_color[:3]
        box_luminance = (0.299 * box_rgb[0] + 0.587 * box_rgb[1] + 0.114 * box_rgb[2]) / 255
        last_lines_color = (255, 255, 255, 220) if box_luminance < 0.5 else (0, 0, 0, 220)

        time_color = last_lines_color

        if time_x >= 0 and time_y >= 0 and time_x < size[0] and time_y < size[1]:
            try:
                icon_x = time_x - 75
                icon_color = random_contrast_color(box_color)
                draw_text_with_shadow(draw, (icon_x, time_y - 8), time_icon, font_icon, icon_color)
                draw.text((time_x, time_y), time_text, font=font_time, fill=time_color)
            except Exception as e:
                print(f"❌ Loi ve thoi gian len anh: {e}")
                draw_text_with_shadow(draw, (time_x - 75, time_y - 8), "⏰", font_icon, (255, 255, 255, 255))
                draw.text((time_x, time_y), " ??;??", font=font_time, fill=time_color)

        user_info = bot.fetchUserInfo(author_id) if author_id else None
        user_name = "Unknown"
        if user_info and hasattr(user_info, 'changed_profiles') and author_id in user_info.changed_profiles:
            user = user_info.changed_profiles[author_id]
            user_name = getattr(user, 'name', None) or getattr(user, 'displayName', None) or f"ID_{author_id}"

        greeting_name = "Chu Nhan" if str(author_id) == is_admin else user_name

        emoji_colors = {
            "🎵": random_contrast_color(box_color),
            "😁": random_contrast_color(box_color),
            "🖤": random_contrast_color(box_color),
            "💞": random_contrast_color(box_color),
            "🤖": random_contrast_color(box_color),
            "💻": random_contrast_color(box_color),
            "📅": random_contrast_color(box_color),
            "🎧": random_contrast_color(box_color),
            "🌙": random_contrast_color(box_color),
            "🌤️": (200, 150, 50, 255)
        }

        text_lines = [
            f"Hi, {greeting_name}",
            f"💞 Chao mung đen menu 🧨 war",
            f" ",
            "😁 Bot San Sang Phuc 🖤",
            f"🤖Bot: {bot.me_name} 💻Version: {bot.version} 📅Update {bot.date_update}"
        ]

        color1 = random_contrast_color(box_color)
        color2 = random_contrast_color(box_color)
        while color1 == color2:
            color2 = random_contrast_color(box_color)
        text_colors = [
            color1,
            color2,
            last_lines_color,
            last_lines_color,
            last_lines_color
        ]

        text_fonts = [
            font_text_large,
            font_text_big,
            font_text_bot,
            font_text_bot,
            font_text_small
        ]

        line_spacing = 85
        start_y = box_y1 + 10

        avatar_url = user_info.changed_profiles[author_id].avatar if user_info and hasattr(user_info, 'changed_profiles') and author_id in user_info.changed_profiles else None
        avatar_path = download_avatar(avatar_url)
        if avatar_path and os.path.exists(avatar_path):
            avatar_size = 200
            try:
                avatar_img = Image.open(avatar_path).convert("RGBA").resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                mask = Image.new("L", (avatar_size, avatar_size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
                border_size = avatar_size + 10
                rainbow_border = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
                draw_border = ImageDraw.Draw(rainbow_border)
                steps = 360
                for i in range(steps):
                    h = i / steps
                    r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
                    draw_border.arc([(0, 0), (border_size-1, border_size-1)], start=i, end=i + (360 / steps), fill=(int(r * 255), int(g * 255), int(b * 255), 255), width=5)
                avatar_y = (box_y1 + box_y2 - avatar_size) // 2
                overlay.paste(rainbow_border, (box_x1 + 40, avatar_y), rainbow_border)
                overlay.paste(avatar_img, (box_x1 + 45, avatar_y + 5), mask)
            except Exception as e:
                print(f"❌ Loi xu ly avatar: {e}")
                draw.text((box_x1 + 60, (box_y1 + box_y2) // 2 - 140), "🐳", font=font_icon, fill=(0, 139, 139, 255))
        else:
            draw.text((box_x1 + 60, (box_y1 + box_y2) // 2 - 140), "🐳", font=font_icon, fill=(0, 139, 139, 255))

        current_line_idx = 0
        for i, line in enumerate(text_lines):
            if not line:
                current_line_idx += 1
                continue

            parts = []
            current_part = ""
            for char in line:
                if ord(char) > 0xFFFF:
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                    parts.append(char)
                else:
                    current_part += char
            if current_part:
                parts.append(current_part)

            total_width = 0
            part_widths = []
            current_font = font_text_bot if i == 4 else text_fonts[i]
            for part in parts:
                font_to_use = font_icon if any(ord(c) > 0xFFFF for c in part) else current_font
                width = draw.textbbox((0, 0), part, font=font_to_use)[2]
                part_widths.append(width)
                total_width += width

            max_width = box_x2 - box_x1 - 300
            if total_width > max_width:
                font_size = int(current_font.getbbox("A")[3] * max_width / total_width * 0.9)
                if font_size < 60:
                    font_size = 60
                try:
                    current_font = ImageFont.truetype(font_arial_path, size=font_size) if os.path.exists(font_arial_path) else ImageFont.load_default(size=font_size)
                except Exception as e:
                    print(f"❌ Loi đieu chinh font size: {e}")
                    current_font = ImageFont.load_default(size=font_size)
                total_width = 0
                part_widths = []
                for part in parts:
                    font_to_use = font_icon if any(ord(c) > 0xFFFF for c in part) else current_font
                    width = draw.textbbox((0, 0), part, font=font_to_use)[2]
                    part_widths.append(width)
                    total_width += width

            text_x = (box_x1 + box_x2 - total_width) // 2
            text_y = start_y + current_line_idx * line_spacing + (current_font.getbbox("A")[3] // 2)

            current_x = text_x
            for part, width in zip(parts, part_widths):
                if any(ord(c) > 0xFFFF for c in part):
                    emoji_color = emoji_colors.get(part, random_contrast_color(box_color))
                    draw_text_with_shadow(draw, (current_x, text_y), part, font_icon, emoji_color)
                    if part == "🤖" and i == 4:
                        draw_text_with_shadow(draw, (current_x, text_y - 5), part, font_icon, emoji_color)
                else:
                    if i < 2:
                        draw_text_with_shadow(draw, (current_x, text_y), part, current_font, text_colors[i])
                    else:
                        draw.text((current_x, text_y), part, font=current_font, fill=text_colors[i])
                current_x += width
            current_line_idx += 1

        right_icons = ["🧨"]
        right_icon = random.choice(right_icons)
        icon_right_x = box_x2 - 225
        icon_right_y = (box_y1 + box_y2 - 180) // 2
        draw_text_with_shadow(draw, (icon_right_x, icon_right_y), right_icon, font_icon_large, emoji_colors.get(right_icon, (80, 80, 80, 255)))

        final_image = Image.alpha_composite(bg_image, overlay)
        final_image = final_image.resize(final_size, Image.Resampling.LANCZOS)
        os.makedirs(os.path.dirname(OUTPUT_IMAGE_PATH), exist_ok=True)
        final_image.save(OUTPUT_IMAGE_PATH, "PNG", quality=95)
        print(f"✅ Anh menu đa đuoc luu: {OUTPUT_IMAGE_PATH}")
        return OUTPUT_IMAGE_PATH

    except Exception as e:
        print(f"❌ Loi xu ly anh menu: {e}")
        return None

def get_user_name_by_id(bot, author_id):
    try:
        user_info = bot.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception as e:
        return "Unknown User"

def set_war_delay(war_type, delay_value):
    try:
        delay = float(delay_value)
        if delay >= 0:
            war_config[war_type]['delay'] = delay
            return True
    except (ValueError, KeyError):
        return False
    return False

def set_war_file(war_type, filename):
    if not filename.endswith('.txt'):
        filename += '.txt'
    
    filepath = os.path.join(WAR_TXT_DIR, filename)
    if os.path.exists(filepath):
        war_config[war_type]['file'] = filepath
        return True
    return False

def list_text_files():
    try:
        txt_files = [f for f in os.listdir(WAR_TXT_DIR) if f.endswith('.txt')]
        return txt_files
    except FileNotFoundError:
        return []

def stop_all_wars(client, message_object, thread_id, thread_type):
    global is_reo_running, is_spam_running, is_polling, is_todo_active
    
    with reo_lock:
        is_reo_running = False
    with spam_lock:
        is_spam_running = False
    is_polling = False
    is_todo_active = False
    
    client.replyMessage(
        Message(text="⚠️ Đa dung tat ca che đo war."),
        message_object, thread_id, thread_type
    )

def handle_reo_war(message_object, thread_id, thread_type, author_id, client, count=-1):
    global is_reo_running
    
    tagged_users = message_object.mentions[0]['uid']

    try:
        with open(war_config['reo']['file'], 'r', encoding='utf-8') as file:
            content = file.readlines()
    except FileNotFoundError:
        client.replyMessage(Message(text=f"❌Khong tim thay file {war_config['reo']['file']}."), message_object, thread_id, thread_type)
        return

    if not content:
        client.replyMessage(Message(text=f"❌File {war_config['reo']['file']} trong."), message_object, thread_id, thread_type)
        return

    with reo_lock:
        is_reo_running = True

    def reo_loop():
        global is_reo_running
        executed = 0
        while is_reo_running and (count == -1 or executed < count):
            for line in content:
                if not is_reo_running or (count != -1 and executed >= count):
                    break
                mention = Mention(tagged_users, length=0, offset=4)
                client.send(Message(text=f" {line.strip()}", mention=mention), thread_id, thread_type)
                executed += 1
                time.sleep(war_config['reo']['delay'])

        with reo_lock:
            is_reo_running = False

    Thread(target=reo_loop, daemon=True).start()

def handle_spam_war(message_object, thread_id, thread_type, author_id, client, count=-1):
    global is_spam_running
    
    tagged_users = message_object.mentions[0]['uid']

    try:
        with open(war_config['spam']['file'], 'r', encoding='utf-8') as file:
            content = file.readlines()
    except FileNotFoundError:
        client.replyMessage(Message(text=f"❌Khong tim thay file {war_config['spam']['file']}."), message_object, thread_id, thread_type)
        return

    if not content:
        client.replyMessage(Message(text=f"❌File {war_config['spam']['file']} trong."), message_object, thread_id, thread_type)
        return

    try:
        with open(sticker_file, 'r', encoding='utf-8') as file:
            stickers = json.load(file)
    except:
        client.replyMessage(Message(text="❗️ Khong the đoc file sticker.json!"), message_object, thread_id, thread_type)
        return

    with spam_lock:
        is_spam_running = True

    def spam_loop():
        global is_spam_running
        executed = 0
        while is_spam_running and (count == -1 or executed < count):
            for line in content:
                if not is_spam_running or (count != -1 and executed >= count):
                    break
                mention = Mention(tagged_users, length=0, offset=4)
                client.send(Message(text=f"{line.strip()}", mention=mention), thread_id, thread_type)
                sticker = random.choice(stickers)
                client.sendSticker(
                    stickerType=sticker['stickerType'],
                    stickerId=sticker['stickerId'],
                    cateId=sticker['cateId'],
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                executed += 1
                time.sleep(war_config['spam']['delay'])
        with spam_lock:
            is_spam_running = False

    Thread(target=spam_loop, daemon=True).start()

def handle_poll_war(message_object, thread_id, thread_type, author_id, client, count=-1):
    global is_polling
    
    user_id = message_object.mentions[0]['uid']

    try:
        author_info = client.fetchUserInfo(user_id)
        username = author_info['changed_profiles'][user_id].get('zaloName', 'khong xac đinh')
    except Exception:
        username = "Nguoi dung khong xac đinh"

    try:
        with open(war_config['poll']['file'], "r", encoding="utf-8") as file:
            captions = [caption.strip() for caption in file.readlines() if caption.strip()]
    except FileNotFoundError:
        client.replyMessage(Message(text=f"Khong tim thay file {war_config['poll']['file']}"), message_object, thread_id, thread_type)
        return

    if not captions:
        client.replyMessage(Message(text=f"File {war_config['poll']['file']} trong."), message_object, thread_id, thread_type)
        return

    is_polling = True

    def poll_loop():
        global is_polling
        executed = 0
        while is_polling and (count == -1 or executed < count):
            question = f"{username} {captions[executed % len(captions)]}"
            try:
                client.createPoll(question=question, options=["Trum war."], groupId=thread_id)
                executed += 1
                time.sleep(war_config['poll']['delay'])
            except Exception as e:
                client.replyMessage(Message(text=f"Loi khi tao poll: {str(e)}"), message_object, thread_id, thread_type)
                break
        is_polling = False

    Thread(target=poll_loop).start()

def handle_todo_war(message_object, thread_id, thread_type, author_id, client, count=-1):
    global is_todo_active
    
    user_id = message_object.mentions[0]['uid']
    is_todo_active = True

    def send_todo():
        global is_todo_active
        try:
            with open(war_config['todo']['file'], "r", encoding="utf-8") as file:
                captions = [caption.strip() for caption in file.readlines() if caption.strip()]

            if not captions:
                client.replyMessage(Message(text=f"❗️ File {war_config['todo']['file']} trong."), message_object, thread_id, thread_type)
                return

            executed = 0
            while is_todo_active and (count == -1 or executed < count):
                content = captions[executed % len(captions)]
                client.sendToDo(message_object, content, [user_id], thread_id, thread_type, -1, "Nhiem vu tu đong")
                executed += 1
                time.sleep(war_config['todo']['delay'])
            is_todo_active = False

        except Exception as e:
            client.replyMessage(Message(text=f"Loi khi tao todo: {str(e)}"), message_object, thread_id, thread_type)
            is_todo_active = False

    Thread(target=send_todo).start()

def handle_random_war(message_object, thread_id, thread_type, author_id, client, count=-1):
    war_type = random.choice(['reo', 'spam', 'poll', 'todo'])
    response = f"🎲 Đa chon ngau nhien: {war_type} - Delay: {war_config[war_type]['delay']}s - File: {os.path.basename(war_config[war_type]['file'])} - So lan: {count if count >= 0 else '∞'}"
    client.replyMessage(Message(text=response), message_object, thread_id, thread_type)
    
    if war_type == 'reo':
        handle_reo_war(message_object, thread_id, thread_type, author_id, client, count)
    elif war_type == 'spam':
        handle_spam_war(message_object, thread_id, thread_type, author_id, client, count)
    elif war_type == 'poll':
        handle_poll_war(message_object, thread_id, thread_type, author_id, client, count)
    elif war_type == 'todo':
        handle_todo_war(message_object, thread_id, thread_type, author_id, client, count)

def create_new_txt(filename, content):
    try:
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        filepath = os.path.join(WAR_TXT_DIR, filename)
        
        if os.path.exists(filepath):
            return False, "File already exists!"
        
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return True, f"File {filename} created successfully!"
    except Exception as e:
        return False, f"Error creating file: {str(e)}"

def handle_allwar_command(bot, message_object, author_id, thread_id, thread_type, command):
    def send_response():
        try:
            parts = command.split()
            if len(parts) == 1:
                response = (
                    f"{get_user_name_by_id(bot, author_id)}\n"
                    f"➤ 🎯 Bat đau war: {bot.prefix}war [reo/spam/poll/todo/random] [so lan] @tag\n"
                    f"➤ ⚙️ Cai đat delay: {bot.prefix}war [reo/spam/poll/todo] delay [thoi gian]\n"
                    f"➤ 📝 Đat file text: {bot.prefix}war [reo/spam/poll/todo] set [ten file]\n"
                    f"➤ 📋 Danh sach file: {bot.prefix}war txt list\n"
                    f"➤ ⭕️ Tat war: {bot.prefix}war off\n"
                    f"🔹 reo: Gui tin nhan cham (delay: {war_config['reo']['delay']}s, file: {os.path.basename(war_config['reo']['file'])})\n"
                    f"🔹 spam: Tin nhan + sticker (delay: {war_config['spam']['delay']}s, file: {os.path.basename(war_config['spam']['file'])})\n"
                    f"🔹 poll: Tao binh chon (delay: {war_config['poll']['delay']}s, file: {os.path.basename(war_config['poll']['file'])})\n"
                    f"🔹 todo: Giao nhiem vu (delay: {war_config['todo']['delay']}s, file: {os.path.basename(war_config['todo']['file'])})\n"
                    f"🔹 random: Chon ngau nhien\n"
                    f"📌 Vi du:\n"
                    f"- {bot.prefix}war spam 5 @bot\n"
                    f"- {bot.prefix}war reo delay 0.5\n"
                    f"- {bot.prefix}war spam set noidung\n"
                    f"- {bot.prefix}war txt list\n"
                    f"- {bot.prefix}war off"
                )
                
                os.makedirs(CACHE_PATH, exist_ok=True)
    
                image_path = generate_menu_image(bot, author_id, thread_id, thread_type)
                if not image_path:
                    bot.sendMessage("❌ Khong the tao anh menu!", thread_id, thread_type)
                    return

                reaction = [
                    "❌", "🤧", "🐞", "😊", "🔥", "👍", "💖", "🚀",
                    "😍", "😂", "😢", "😎", "🙌", "💪", "🌟", "🍀",
                    "🎉", "🦁", "🌈", "🍎", "⚡", "🔔", "🎸", "🍕",
                    "🏆", "📚", "🦋", "🌍", "⛄", "🎁", "💡", "🐾",
                    "😺", "🐶", "🐳", "🦄", "🌸", "🍉", "🍔", "🎄",
                    "🎃", "👻", "☃️", "🌴", "🏀", "⚽", "🎾", "🏈",
                    "🚗", "✈️", "🚢", "🌙", "☀️", "⭐", "⛅", "☔",
                    "⌛", "⏰", "💎", "💸", "📷", "🎥", "🎤", "🎧",
                    "🍫", "🍰", "🍩", "☕", "🍵", "🍷", "🍹", "🥐",
                    "🐘", "🦒", "🐍", "🦜", "🐢", "🦀", "🐙", "🦈",
                    "🍓", "🍋", "🍑", "🥥", "🥐", "🥪", "🍝", "🍣",
                    "🎲", "🎯", "🎱", "🎮", "🎰", "🧩", "🧸", "🎡",
                    "🏰", "🗽", "🗼", "🏔️", "🏝️", "🏜️", "🌋", "⛲",
                    "📱", "💻", "🖥️", "🖨️", "⌨️", "🖱️", "📡", "🔋",
                    "🔍", "🔎", "🔑", "🔒", "🔓", "📩", "📬", "📮",
                    "💢", "💥", "💫", "💦", "💤", "🚬", "💣", "🔫",
                    "🩺", "💉", "🩹", "🧬", "🔬", "🔭", "🧪", "🧫",
                    "🧳", "🎒", "👓", "🕶️", "👔", "👗", "👠", "🧢",
                    "🦷", "🦴", "👀", "👅", "👄", "👶", "👩", "👨",
                    "🚶", "🏃", "💃", "🕺", "🧘", "🏄", "🏊", "🚴",
                    "🍄", "🌾", "🌻", "🌵", "🌿", "🍂", "🍁", "🌊",
                    "🛠️", "🔧", "🔨", "⚙️", "🪚", "🪓", "🧰", "⚖️",
                    "🧲", "🪞", "🪑", "🛋️", "🛏️", "🪟", "🚪", "🧹"
                ]
                
                bot.sendReaction(message_object, random.choice(reaction), thread_id, thread_type)
                bot.sendLocalImage(
                    imagePath=image_path,
                    message=Message(text=response, mention=Mention(author_id, length=len(f"{get_user_name_by_id(bot, author_id)}"), offset=0)),
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=1920,
                    height=600,
                    ttl=240000
                )
                
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    print(f"❌ Loi khi xoa anh: {e}")
                return  # Them return đe tranh loi tiep tuc xu ly
            
            action = parts[1].lower()
            
            if action == 'off':
                stop_all_wars(bot, message_object, thread_id, thread_type)
                return
                
            if action == 'txt' and len(parts) > 2 and parts[2].lower() == 'list':
                files = list_text_files()
                if files:
                    response = "📋 Danh sach file txt co san:\n" + "\n".join(f"• {f}" for f in files)
                else:
                    response = f"❌ Khong co file txt nao trong thu muc {WAR_TXT_DIR}!"
                bot.replyMessage(Message(text=response), message_object, thread_id, thread_type)
                return
                
            if not is_admin(bot, author_id):
                bot.replyMessage(Message(text="❌ Ban khong phai admin!"), message_object, thread_id, thread_type)
                return
                
            if len(parts) >= 3 and parts[2].lower() == 'delay':
                if len(parts) < 4:
                    bot.replyMessage(Message(text="❌ Thieu thoi gian delay!"), message_object, thread_id, thread_type)
                    return
                    
                if action in war_config:
                    if set_war_delay(action, parts[3]):
                        bot.replyMessage(Message(text=f"✅ Đa đat delay {action} thanh {parts[3]} giay"), 
                                       message_object, thread_id, thread_type)
                    else:
                        bot.replyMessage(Message(text="❌ Thoi gian delay khong hop le!"), 
                                       message_object, thread_id, thread_type)
                else:
                    bot.replyMessage(Message(text="❌ Loai war khong hop le!"), message_object, thread_id, thread_type)
                return
            
            if action == 'newtxt':
                if not is_admin(bot, author_id):
                    bot.replyMessage(Message(text="❌ Ban khong phai admin!"), message_object, thread_id, thread_type)
                    return
                
                if len(parts) < 4:
                    bot.replyMessage(Message(text="❌ Thieu ten file hoac noi dung!\nVi du: /war newtxt tenfile noidung"), 
                                   message_object, thread_id, thread_type)
                    return
                
                filename = parts[2]
                content = ' '.join(parts[3:])
                
                success, message = create_new_txt(filename, content)
                if success:
                    bot.replyMessage(Message(text=f"✅ {message}"), message_object, thread_id, thread_type)
                else:
                    bot.replyMessage(Message(text=f"❌ {message}"), message_object, thread_id, thread_type)
                return
                
            if not is_admin(bot, author_id):
                bot.replyMessage(Message(text="❌ Ban khong phai admin!"), message_object, thread_id, thread_type)
                return
                
            if len(parts) >= 3 and parts[2].lower() == 'set':
                if len(parts) < 4:
                    bot.replyMessage(Message(text="❌ Thieu ten file!"), message_object, thread_id, thread_type)
                    return
                    
                if action in war_config:
                    if set_war_file(action, parts[3]):
                        bot.replyMessage(Message(text=f"✅ Đa đat file {action} thanh {os.path.basename(war_config[action]['file'])}"), 
                                       message_object, thread_id, thread_type)
                    else:
                        bot.replyMessage(Message(text=f"❌ File {parts[3]}.txt khong ton tai!"), 
                                       message_object, thread_id, thread_type)
                else:
                    bot.replyMessage(Message(text="❌ Loai war khong hop le!"), message_object, thread_id, thread_type)
                return
                
            if thread_type != ThreadType.GROUP:
                bot.replyMessage(Message(text="❌ Chi dung trong nhom!"), message_object, thread_id, thread_type)
                return
                
            if not message_object.mentions and action not in ['delay', 'set']:
                bot.replyMessage(Message(text="❌ Vui long tag nguoi muon war!"), message_object, thread_id, thread_type)
                return
                
            count = -1
            if len(parts) > 2 and parts[2].isdigit():
                count = int(parts[2])
                if count < 0:
                    bot.replyMessage(Message(text="❌ So lan phai ≥ 0!"), message_object, thread_id, thread_type)
                    return
                
            if action == 'reo':
                handle_reo_war(message_object, thread_id, thread_type, author_id, bot, count)
            elif action == 'spam':
                handle_spam_war(message_object, thread_id, thread_type, author_id, bot, count)
            elif action == 'poll':
                handle_poll_war(message_object, thread_id, thread_type, author_id, bot, count)
            elif action == 'todo':
                handle_todo_war(message_object, thread_id, thread_type, author_id, bot, count)
            elif action == 'random':
                handle_random_war(message_object, thread_id, thread_type, author_id, bot, count)
            else:
                bot.replyMessage(Message(text=f"❌ Lenh khong hop le!"), message_object, thread_id, thread_type)

        except Exception as e:
            bot.replyMessage(Message(text=f"❌ Loi: {str(e)}"), message_object, thread_id, thread_type)

    Thread(target=send_response).start()