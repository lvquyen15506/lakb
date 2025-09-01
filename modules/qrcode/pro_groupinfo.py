import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import requests
import base64
import emoji
from datetime import datetime
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
    lh = int(th * 1.5)
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
                           ImageFont.truetype("modules/cache/font/BeVietnamPro-Bold.ttf", 12), icon_font,
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

def process_image_with_info(avatar_url, cover_path, group_name, group_info_text):
    dw, dh = 2000, 1000
    f = get_font_size()
    text_height = calculate_text_height(group_info_text, f, dw)
    avatar_size = 350
    avatar_x = int(dw * 0.03)
    avatar_y = int(dh * 0.5 - avatar_size * 0.5)
    separator_x = avatar_x * 2 + avatar_size
    try:
        ci = Image.open(cover_path).convert("RGB")
        cover_width, cover_height = 2000, 1000
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
        mi = ImageEnhance.Brightness(mi).enhance(0.4)
        image.paste(mi.resize((iw, ih)), (0, 0))
        dw, dh = iw, ih
    ai = fetch_image(avatar_url)
    if ai:
        draw_stylized_avatar(image, ai, (avatar_x, avatar_y), (avatar_size, avatar_size), border_color=(220, 220, 220))
        draw = ImageDraw.Draw(image)
        draw.line((separator_x, avatar_y, separator_x, avatar_y + avatar_size), fill=(150, 150, 150), width=8)
    draw = ImageDraw.Draw(image)
    f = get_font_size(70)
    ef = ImageFont.truetype("NotoEmoji-Bold.ttf", f.size)
    text_x = separator_x
    text_y = ih // 2
    draw_text(draw, group_info_text, (text_x, text_y), f, ef, iw, separator_x)
    return image

def truncate_text(text, max_length=100):
    if isinstance(text, str) and len(text) > max_length:
        return text[:max_length] + "..."
    return text

def get_group_info_text(group, get_name):
    msg = f"📋 Ten nhom: {truncate_text(group.name)}\n"
    msg += f"👤 Truong nhom: {truncate_text(get_name(group.creatorId))}\n"
    admin_ids = group.adminIds
    num_admins = len(admin_ids)
    msg += f"👤 So pho nhom: {num_admins}\n"
    group_type = "Cong Đong" if group.type == 2 else "Nhom"
    msg += f"💼 Phan loai: {group_type}\n"
    if group.updateMems:
        update_mems_info = ', '.join([get_name(member) for member in group.updateMems])
    else:
        update_mems_info = ""
    msg += f"📜 Tong {group.totalMember} thanh vien\n"
    createdTime = group.createdTime
    formatted_time = datetime.fromtimestamp(createdTime / 1000).strftime('%H:%M %d/%m/%Y')
    msg += f"📆 Thoi gian tao: {formatted_time}\n"
    return msg

def handle_groupinfo_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        def get_name(id):
            try:
                return client.fetchUserInfo(id).changed_profiles[id].zaloName
            except:
                return "Khong tim thay"

        group = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        group_info_text = get_group_info_text(group, get_name)
        avatar_url = group.fullAvt
        cover_path = "modules/cache/vxkiue.jpg"
        group_name = group.name
        image = process_image_with_info(avatar_url, cover_path, group_name, group_info_text)
        op = "modules/cache/VXKZALOBOT.jpg"
        image.save(op)
        try:
            if os.path.exists(op):
                client.sendLocalImage(op, thread_id=thread_id, thread_type=thread_type, width=image.width, height=image.height)
        finally:
            if os.path.exists(op):
                os.remove(op)
    except Exception as e:
        print(f"Error handling groupinfo command: {e}")
