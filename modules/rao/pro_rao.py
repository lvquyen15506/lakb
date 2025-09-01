#==================HTT=========================
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle
import threading
import time
from datetime import datetime, timedelta
import pytz
from core.bot_sys import admin_cao

vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")

rao_started = False
rao_enabled = False
rao_message = ""
rao_interval = 15 

def start_rao_loop(client):
    global rao_enabled, rao_message, rao_interval

    all_group = client.fetchAllGroups()
    allowed_thread_ids = list(all_group.gridVerMap.keys())

    last_sent_time = None

    while True:
        now = datetime.now(vn_tz)
        if rao_enabled and (last_sent_time is None or now - last_sent_time >= timedelta(minutes=rao_interval)):
            for thread_id in allowed_thread_ids:
                try:
                    text = f"{rao_message}"
                    styles = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(text), style="color", color="#DB342E", auto_format=False),
                        MessageStyle(offset=0, length=len(text), style="bold", size="15", auto_format=False)
                    ])

                    client.sendMessage(
                        message=Message(text=text, style=styles),
                        thread_id=thread_id,
                        thread_type=ThreadType.GROUP,
                        ttl=120000 
                    )
                    time.sleep(1) 
                except Exception as e:
                    print(f"[RAO] ❌ Loi gui toi nhom {thread_id}: {e}")
            last_sent_time = now
        time.sleep(5)

def start_rao_handle(message, message_object, thread_id, thread_type, author_id, client):
    global rao_started, rao_enabled, rao_message, rao_interval

    if not admin_cao(client, author_id):
        client.replyMessage(
            Message(text="🚫 Ban khong co quyen su dung lenh nay."),
            message_object, thread_id, thread_type, ttl=72000
        )
        return

    parts = [p.strip() for p in message.split("|") if p.strip()]

    if len(parts) < 4:
        client.replyMessage(
            Message(text="❗ Sai cu phap. Dung:\nrao | noi dung | phut | on/off"),
            message_object, thread_id, thread_type, ttl=72000
        )
        return

    _, raw_content, raw_minutes, raw_status = parts[:4]

    try:
        rao_interval = max(1, int(raw_minutes))
    except ValueError:
        client.replyMessage(
            Message(text="❗ So phut khong hop le."),
            message_object, thread_id, thread_type, ttl=72000
        )
        return

    rao_message = raw_content
    rao_enabled = raw_status.lower() == "on"

    if not rao_started:
        rao_started = True
        threading.Thread(target=start_rao_loop, args=(client,), daemon=True).start()

   
    preview_text = f"🔴 {rao_message} 🔴"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(preview_text), style="color", color="#DB342E", auto_format=False),
        MessageStyle(offset=0, length=len(preview_text), style="bold", size="15", auto_format=False)
    ])

    status_text = "✅ Đa **BAT** gui đinh ky." if rao_enabled else "⛔ Đa **TAT** gui đinh ky."
    reply_text = f"{status_text}\n🕒 Moi {rao_interval} phut\n📩 Noi dung se gui:\n{preview_text}"

    client.replyMessage(
        Message(text=reply_text, style=styles),
        message_object, thread_id, thread_type, ttl=72000
    )
