import psutil
import datetime
from ping3 import ping
import speedtest
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from zlapi.models import Message

FONT_PATH = "BeVietnamPro-SemiBold.ttf"
FONT_SIZE = 20
CANVAS_WIDTH = 700
CANVAS_HEIGHT = 400
AVT_SIZE = 100

def gather_info():
    now = datetime.datetime.now()
    uptime = now - datetime.datetime.fromtimestamp(psutil.boot_time())
    cpu = psutil.cpu_percent(interval=1)
    cores = psutil.cpu_count()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    gping = ping('8.8.8.8', timeout=1)
    cping = ping('1.1.1.1', timeout=1)
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        dl = st.download()/1e6
        ul = st.upload()/1e6
    except:
        dl = ul = 0
    return {
        "uptime": str(uptime).split('.')[0],
        "cpu": f"{cpu:.1f}%",
        "cores": cores,
        "ram": f"{ram.used//2**20}/{ram.total//2**20} MB ({ram.percent}%)",
        "disk": f"{disk.used//2**30}/{disk.total//2**30} GB ({disk.percent}%)",
        "gping": f"{gping*1000:.1f} ms" if gping else "–",
        "cping": f"{cping*1000:.1f} ms" if cping else "–",
        "dl": f"{dl:.1f} Mbps",
        "ul": f"{ul:.1f} Mbps"
    }

def draw_canvas(info, user_avatar_url, username):
    # Tao canvas
    img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "#1e1e2e")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    # Tai avatar
    try:
        response = requests.get(user_avatar_url)
        avatar = Image.open(BytesIO(response.content)).resize((AVT_SIZE, AVT_SIZE)).convert("RGB")
        avatar_circle = Image.new("L", (AVT_SIZE, AVT_SIZE), 0)
        draw_circle = ImageDraw.Draw(avatar_circle)
        draw_circle.ellipse((0, 0, AVT_SIZE, AVT_SIZE), fill=255)
        img.paste(avatar, (30, 30), avatar_circle)
    except Exception:
        pass

    # Tieu đe
    draw.text((150, 30), f"📊 Bot System Snapshot", font=font, fill="white")
    draw.text((150, 65), f"👤 Nguoi goi: {username}", font=font, fill="#dddddd")

    # Noi dung he thong
    lines = [
        f"🧠 CPU: {info['cpu']} - {info['cores']} cores",
        f"💾 RAM: {info['ram']}",
        f"🗄️ Disk: {info['disk']}",
        f"🌐 Ping Google: {info['gping']}",
        f"🌐 Ping Cloudflare: {info['cping']}",
        f"⬇️ Download: {info['dl']}  |  ⬆️ Upload: {info['ul']}",
        f"🕒 Uptime: {info['uptime']}"
    ]

    y = 120
    for line in lines:
        draw.text((150, y), line, font=font, fill="white")
        y += 35

    return img

def handle_ping_command(message, message_object, thread_id, thread_type, author_id, client):
    # Gui tin nhan tam
    client.replyMessage(Message("⏳ Đang kiem tra he thong..."), message_object, thread_id, thread_type)

    # Lay info nguoi dung
    user = client.fetchUserInfo(author_id)[author_id]
    username = f"{user.name}"
    avatar_url = user.photo  # URL anh đai dien

    info = gather_info()
    canvas_img = draw_canvas(info, avatar_url, username)

    # Luu anh tam va gui
    tmp = "/tmp/status_canvas.png"
    canvas_img.save(tmp)

    client.send(thread_id=thread_id, thread_type=thread_type, message=Message("", attachment=tmp))
