import json
import os
from zlapi.models import Message
from core.bot_sys import admin_cao
from config import PREFIX

LINK_FILE = 'link.json'
MAX_WARNINGS = 3

# Load / Save trạng thái antilink
def load_link_status():
    if not os.path.exists(LINK_FILE):
        return {}
    with open(LINK_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_link_status(data):
    with open(LINK_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

antilink_status = load_link_status()
warn_counts = {}

# ✅ Command handler chuẩn
def handle_antilink_command(message, message_object, thread_id, thread_type, author_id, client):
    if author_id not in admin_cao:
        client.replyMessage(Message(text="❌ Bạn không có quyền sử dụng lệnh này."), message_object, thread_id, thread_type)
        return

    args = message.strip().lower().split()
    if len(args) < 2:
        client.replyMessage(Message(text="📌 Dùng đúng cú pháp:\n/antilink on | off"), message_object, thread_id, thread_type)
        return

    status = args[1] == "on"
    antilink_status[str(thread_id)] = status
    save_link_status(antilink_status)

    msg = "✅ AntiLink đã được **bật**." if status else "🚫 AntiLink đã được **tắt**."
    client.sendMessage(Message(text=msg), thread_id, thread_type)

# Xử lý tin nhắn chứa liên kết
def detect_and_handle_link(message, message_object, thread_id, thread_type, author_id, client):
    if not antilink_status.get(str(thread_id), False):
        return

    if any(link in message.lower() for link in ["http://", "https://", "www."]):
        try:
            client.undoMessage(message_object.globalMsgId, message_object.cliMsgId, thread_id, thread_type)
        except Exception as e:
            print(f"[AntiLink] ❌ Lỗi khi thu hồi: {e}")

        key = f"{thread_id}_{author_id}"
        warn_counts[key] = warn_counts.get(key, 0) + 1
        count = warn_counts[key]

        if count < MAX_WARNINGS:
            warning = f"⚠️ Cảnh báo {count}/{MAX_WARNINGS}: Không được gửi liên kết!"
            client.sendMessage(Message(text=warning), thread_id, thread_type)
        else:
            try:
                client.removeUserFromGroup(author_id, thread_id)
                client.sendMessage(Message(text=f"MỘT THẰNG NGU {author_id} đã bị kick khỏi nhóm vì gửi link quá {MAX_WARNINGS} lần."), thread_id, thread_type)
            except Exception as e:
                print(f"[AntiLink] ❌ Lỗi khi kick: {e}")

# Hàm xử lý chung
def on_message(message, message_object, thread_id, thread_type, author_id, client):
    if message.startswith(PREFIX):
        parts = message[len(PREFIX):].strip().split()
        command = parts[0].lower()
        full_command = message[len(PREFIX):]

        if command == "antilink":
            handle_antilink_command(full_command, message_object, thread_id, thread_type, author_id, client)
            return

    # Nếu không phải command thì kiểm tra link
    detect_and_handle_link(message, message_object, thread_id, thread_type, author_id, client)
