from zlapi.models import *
import threading
import time
from core.bot_sys import admin_cao

spam_threads = {}

def read_noidung():
    try:
        with open("noidung.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def send_spam_loop(thread_id, thread_type, client, message_object, ttl=0):
    try:
        noidung_list = read_noidung()
        if not noidung_list:
            client.replyMessage(
                Message(text="⚠️ File `noidung.txt` không có nội dung để gửi."),
                message_object, thread_id, thread_type
            )
            return

        start_time = time.time()

        while spam_threads.get(thread_id, False):
            # Dừng nếu quá TTL (nếu được truyền)
            if ttl > 0 and time.time() - start_time > ttl:
                spam_threads[thread_id] = False
                break

            group_info = client.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id)
            if not group_info:
                break

            members = group_info.get('memVerList', [])
            if not members:
                break

            for line in noidung_list:
                if not spam_threads.get(thread_id, False):
                    break

                text = f"<b>{line}</b>"
                mentions = []
                offset = len(text)

                for member in members:
                    parts = member.split('_', 1)
                    if len(parts) != 2:
                        continue
                    user_id, user_name = parts
                    mentions.append(
                        Mention(uid=user_id, offset=offset, length=len(user_name)+1, auto_format=False)
                    )
                    offset += len(user_name) + 2

                multi_mention = MultiMention(mentions)

                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(text), style="color", color="#DB342E", auto_format=False),
                    MessageStyle(offset=0, length=len(text), style="bold", size="15", auto_format=False)
                ])

                client.replyMessage(
                    Message(text=text, style=styles, mention=multi_mention, parse_mode="HTML"),
                    message_object,
                    thread_id,
                    thread_type
                )

                time.sleep(0.5)

    except Exception as e:
        print(f"[SPAM ERROR] {e}")

def handle_spaman_command(message, message_object, thread_id, thread_type, author_id, client):
    if not admin_cao(client, author_id):
        client.replyMessage(
            Message(text="🚫 Bạn không có quyền sử dụng lệnh này."),
            message_object, thread_id, thread_type
        )
        return

    parts = message.strip().split()
    if len(parts) < 2:
        client.replyMessage(
            Message(text="❗ Vui lòng dùng đúng cú pháp: `spaman on` hoặc `spaman off`"),
            message_object, thread_id, thread_type
        )
        return

    cmd = parts[1].lower()

    if cmd == "on":
        if spam_threads.get(thread_id, False):
            client.replyMessage(
                Message(text="⚠️ Spam đã được bật trước đó."),
                message_object, thread_id, thread_type
            )
            return

        spam_threads[thread_id] = True
        client.replyMessage(
            Message(text="✅ Đã bật spam message!"),
            message_object, thread_id, thread_type
        )

        # Khởi chạy spam loop — nếu muốn TTL thì truyền kwargs
        threading.Thread(
            target=send_spam_loop,
            args=(thread_id, thread_type, client, message_object),
            kwargs={'ttl': 5000},  # Bật dòng này nếu muốn TTL 5 giây
            daemon=True
        ).start()

    elif cmd == "off":
        if not spam_threads.get(thread_id, False):
            client.replyMessage(
                Message(text="⚠️ Spam chưa được bật hoặc đã tắt rồi."),
                message_object, thread_id, thread_type
            )
            return

        spam_threads[thread_id] = False
        client.replyMessage(
            Message(text="🛑 Đã tắt spam message!"),
            message_object, thread_id, thread_type
        )

    else:
        client.replyMessage(
            Message(text="❗ Lệnh không hợp lệ. Dùng: `spaman on` hoặc `spaman off`"),
            message_object, thread_id, thread_type
        )
