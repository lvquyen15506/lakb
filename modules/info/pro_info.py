import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import requests
import base64
import emoji
from datetime import datetime
import json
from zlapi.models import *

des = {'version': "1.3.0", 'credits': "Vu Xuan Kien", 'description': "weo cam", 'power': "Thanh vien"}

def draw_text_line(draw, text, x, y, font, emoji_font, text_color):
    for char in text:
        f = emoji_font if emoji.emoji_count(char) else font
        draw.text((x, y), char, fill=text_color, font=f)
        x += f.getlength(char)

def split_text_into_lines(text, font, emoji_font, max_width):
    lines = []
    for paragraph in text.splitlines():
        words = paragraph.split()
        line = ""
        for word in words:
            temp_line = line + word + " "
            width = sum(emoji_font.getlength(c) if emoji.emoji_count(c) else font.getlength(c) for c in temp_line)
            if width <= max_width:
                line = temp_line
            else:
                if line:
                    lines.append(line.strip())
                line = word + " "
        if line:
            lines.append(line.strip())
    return lines

def draw_text(draw, text, position, font, emoji_font, image_width, separator_x):
    x, y = position
    max_width = image_width - separator_x - 50
    lines = split_text_into_lines(text, font, emoji_font, max_width)
    th = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    lh = int(th * 1.6)
    yh = len(lines) * lh
    yo = y - yh // 2
    yo += lh // 8
    start_x = separator_x + 50
    for line in lines:
        draw_text_line(draw, line, start_x, yo, font, emoji_font, (255, 255, 255))
        yo += lh

def get_font_size(size=50):
    return ImageFont.truetype("BeVietnamPro-SemiBold.ttf", size)

def make_circle_mask(size, border_width=0):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((border_width, border_width, size[0] - border_width, size[1] - border_width), fill=255)
    return mask

def draw_stylized_avatar(image, avatar_image, position, size, border_color=(220, 220, 220), border_thickness=15,
                         is_active_pc=False, is_active_web=False):
    scale = 7
    scaled_size = (size[0] * scale, size[1] * scale)
    scaled_border_thickness = border_thickness * scale
    inner_scaled_size = (scaled_size[0] - 2 * scaled_border_thickness, scaled_size[1] - 2 * scaled_border_thickness)
    avatar_scaled = avatar_image.resize(inner_scaled_size, resample=Image.LANCZOS)
    mask_scaled = make_circle_mask(inner_scaled_size)
    border_img = Image.new("RGBA", scaled_size, (0, 0, 0, 0))
    draw_obj = ImageDraw.Draw(border_img)
    draw_obj.ellipse((0, 0, scaled_size[0] - 1, scaled_size[1] - 1), fill=border_color + (255,))
    border_img.paste(avatar_scaled, (scaled_border_thickness, scaled_border_thickness), mask=mask_scaled)
    border_img = border_img.resize(size, resample=Image.LANCZOS)
    image.paste(border_img, position, mask=border_img)
    icon_size = int(size[0] * 0.15)
    icon_font = ImageFont.truetype("NotoEmoji-Bold.ttf", icon_size)
    icon_y = position[1] + size[1] + 10
    icon_x = position[0] + size[0] // 2
    status_icons = []
    if is_active_pc:
        status_icons.append("💻")
    if is_active_web:
        status_icons.append("🌐")
    if status_icons:
        total_icon_width = sum(icon_font.getlength(icon) for icon in status_icons)
        total_icon_width += 5 * (len(status_icons) - 1)
        start_x = icon_x - total_icon_width // 2
        draw_obj = ImageDraw.Draw(image)
        for icon in status_icons:
            draw_text_line(draw_obj, icon, start_x, icon_y,
                           ImageFont.truetype("BeVietnamPro-Bold.ttf", 12), icon_font,
                           (255, 255, 255))
            start_x += icon_font.getlength(icon) + 5

def calculate_text_height(content, font, image_width):
    lines = split_text_into_lines(content, font, ImageFont.truetype("NotoEmoji-Bold.ttf", font.size),
                                  int(image_width * 0.6))
    th = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    lh = int(th * 1.2)
    return len(lines) * lh

def fetch_image(url):
    if not url:
        return None
    try:
        if url.startswith('data:image'):
            h, e = url.split(',', 1)
            try:
                i = base64.b64decode(e)
            except:
                return None
            return Image.open(BytesIO(i)).convert("RGB")
        r = requests.get(url, stream=True, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except:
        return None

def process_image_with_info(avatar_url, cover_url, author_name, user_info_text, is_active_pc, is_active_web):
    dw, dh = 2000, 900
    f = get_font_size()
    text_height = calculate_text_height(user_info_text, f, dw)
    avatar_size = 350
    avatar_x = int(dw * 0.03)
    avatar_y = int(dh * 0.5 - avatar_size * 0.5)
    try:
        if cover_url == "https://cover-talk.zadn.vn/default" and os.path.exists("modules/cache/vxkiue.jpg"):
            ci = Image.open("vxkiue.jpg").convert("RGB")
            cover_width, cover_height = 2000, 900
        else:
            ci = fetch_image(cover_url)
            if ci:
                cover_width, cover_height = ci.size
    except:
        ci = None
    if ci:
        ci = ci.resize((cover_width, cover_height))
    text_region_height = text_height + 20
    min_height = max(avatar_y + avatar_size + 50, 280 + text_region_height)
    ih = max(min_height, dh)
    iw = dw
    image = Image.new("RGB", (iw, ih), color=(50, 50, 50))
    if ci:
        mi = ci.copy()
        mi = ImageEnhance.Brightness(mi).enhance(0.5)
        image.paste(mi.resize((iw, ih)), (0, 0))
        dw, dh = iw, ih
    ai = fetch_image(avatar_url)
    if ai:
        draw_stylized_avatar(image, ai, (avatar_x, avatar_y), (avatar_size, avatar_size), border_color=(220, 220, 220),
                             is_active_pc=is_active_pc, is_active_web=is_active_web)
        draw = ImageDraw.Draw(image)
        separator_x = avatar_x * 2 + avatar_size
        draw.line((separator_x, avatar_y, separator_x, avatar_y + avatar_size), fill=(150, 150, 150), width=8)
    draw = ImageDraw.Draw(image)
    f = get_font_size(63)
    ef = ImageFont.truetype("NotoEmoji-Bold.ttf", f.size)
    text_x = separator_x
    text_y = ih // 2
    draw_text(draw, user_info_text, (text_x, text_y), f, ef, iw, separator_x)
    return image

def truncate_text(text, max_length=100):
    if isinstance(text, str) and len(text) > max_length:
        return text[:max_length] + "..."
    return text

def get_user_info_text(user):
    dob = user.dob or user.sdob or "An"
    if isinstance(dob, int):
        dob = datetime.fromtimestamp(dob).strftime("%d/%m/%Y")
    business = user.bizPkg.label if hasattr(user, 'bizPkg') and hasattr(user.bizPkg, 'label') else None
    business = "Co" if business else "Khong co"
    createTime = user.createdTs
    if isinstance(createTime, int):
        createTime = datetime.fromtimestamp(createTime).strftime("%H:%M %d/%m/%Y")
    else:
        createTime = "Undefined"
    lastAction = user.lastActionTime
    if isinstance(lastAction, int):
        lastAction = lastAction / 1000
        timeAction = datetime.fromtimestamp(lastAction)
        lastAction = timeAction.strftime("%H:%M %d/%m/%Y")
    else:
        lastAction = "Undefined"

    gender_string = {
        0: 'Nam',
        1: 'Nu',
    }.get(user.gender, 'Khong xac đinh') if hasattr(user, 'gender') else 'Khong xac đinh'

    user_info_text = (
        f"🆔 Username: {truncate_text(user.username) if hasattr(user, 'username') else 'Khong co'}\n"
        f"👤 Ten: {truncate_text(user.zaloName) if hasattr(user, 'zaloName') else 'Khong co'}\n"
        f"🚻 Gioi tinh: {truncate_text(gender_string)}\n"
        f"💼 Tai khoan Business: {truncate_text(business)}\n"
        f"🎂 Ngay sinh: {truncate_text(dob)}\n"
        f"📆 Ngay tao tai khoan: {truncate_text(createTime)}\n"
        f"📜 Lan cuoi hoat đong: {truncate_text(lastAction)}\n"
    )

    return user_info_text

def handle_info_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        input_value = message.split()[1].lower() if len(message.split()) > 1 else author_id
        if message_object.mentions:
            input_value = message_object.mentions[0]['uid']
        user_id_data = client.fetchPhoneNumber(input_value, language="en") or {}
        user_id_to_fetch = user_id_data.get('uid', input_value)
        user_info = client.fetchUserInfo(user_id_to_fetch) or {}
        user_data = user_info.get('changed_profiles', {}).get(user_id_to_fetch, {})
        user = client.fetchUserInfo(user_id_to_fetch).changed_profiles[user_id_to_fetch]
        user_info_text = get_user_info_text(user)
        ud = user_info.get('changed_profiles', {}).get(user_id_to_fetch, {})
        av, cv = ud.get('avatar'), ud.get('cover')
        an = user.zaloName
        is_active_pc = user.isActivePC == 1
        is_active_web = user.isActiveWeb == 1
        image = process_image_with_info(av, cv, an, user_info_text, is_active_pc, is_active_web)
        op = "modules/VXKZALOBOT.jpg"
        image.save(op, quality=100)
        try:
            if os.path.exists(op):
                client.sendLocalImage(op, thread_id=thread_id, thread_type=thread_type, width=image.width,
                                      height=image.height)
        finally:
            if os.path.exists(op):
                os.remove(op)
    except Exception as e:
        print(f"Error handling info command: {e}")
