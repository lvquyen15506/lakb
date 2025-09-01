from zlapi.models import Message
import requests
from core.bot_sys import get_user_name_by_id

def handle_mail10p_command(message, message_object, thread_id, thread_type, author_id, client):
    user_name = get_user_name_by_id(client, author_id)

    # Bắt nội dung tin nhắn, phòng lỗi None
    raw_text = message_object.text or ""
    text = raw_text.strip()
    args = text.split()

    # ✅ Kiểm tra lệnh chính xác (mail10p + subcommand)
    if len(args) < 2 or args[0].lower() not in ["mail10p", "10minutemail"]:
        help_text = f"""📌 Lệnh 10MinuteMail:

- `mail10p new` hoặc `more` → Tạo mail mới
- `mail10p get` → Lấy thông tin mail hiện tại
- `mail10p check` → Kiểm tra thư đến gần nhất
- `mail10p list` → Xem danh sách domain hỗ trợ

[Người yêu cầu: {user_name}]"""
        client.sendMessage(Message(text=help_text), thread_id, thread_type)
        return

    command = args[1].lower()

    try:
        # Tạo mail mới
        if command in ["new", "more"]:
            res = requests.get("https://10minutemail.net/address.api.php?more=1", timeout=10)
            data = res.json()

            email = data.get("mail_get_mail", "Không xác định")
            key = data.get("mail_get_key", "Không xác định")
            time_left = data.get("mail_left_time", "?")
            mail_list = data.get("mail_list", [])

            if mail_list:
                mail = mail_list[0]
                mail_id = mail.get("mail_id", "??")
                subject = mail.get("subject", "Không có tiêu đề")
                date = mail.get("datetime2", "Chưa rõ")
            else:
                mail_id = subject = date = "Chưa có email nào nhận được"

            msg = f"""📨 Tạo Email 10 Phút Thành Công!

📧 Email: `{email}`
🔑 Key: `{key}`
⏳ Thời gian còn lại: {time_left}s

📬 Mail ID: {mail_id}
📝 Tiêu đề: {subject}
🕒 Nhận lúc: {date}

[Người yêu cầu: {user_name}]
"""
            client.sendMessage(Message(text=msg), thread_id, thread_type)
            return

        # Lấy thông tin mail hiện tại
        elif command == "get":
            res = requests.get("https://10minutemail.net/address.api.php", timeout=10)
            data = res.json()

            email = data.get("mail_get_mail", "Không xác định")
            session_id = data.get("session_id", "?")
            permalink = data.get("permalink", {})
            key = permalink.get("key", "?")
            url = permalink.get("url", "?").replace(".", " . ")

            msg = f"""📧 Thông Tin Email Hiện Tại:

✉️ Email: `{email.replace('.', ' . ')}`
🆔 Session ID: {session_id}
🔑 Key: `{key}`
🔗 Link: {url}

[Người yêu cầu: {user_name}]
"""
            client.sendMessage(Message(text=msg), thread_id, thread_type)
            return

        # Kiểm tra thư đến gần nhất
        elif command == "check":
            res = requests.get("https://10minutemail.net/address.api.php", timeout=10)
            data = res.json()

            mail_list = data.get("mail_list", [])
            email = data.get("mail_get_mail", "Không rõ")

            if not mail_list:
                client.sendMessage(
                    Message(text=f"📭 Hộp thư của `{email}` hiện không có email nào!\n\n[Người yêu cầu: {user_name}]"),
                    thread_id, thread_type
                )
                return

            mail = mail_list[0]
            from_addr = (mail.get("from") or "Không rõ").replace(".", " . ")
            subject = mail.get("subject", "Không có tiêu đề")
            time_recv = mail.get("datetime2", "?")
            mail_id = mail.get("mail_id", "?")

            msg = f"""📬 Kiểm Tra Thư Mới

📧 Email: `{email.replace('.', ' . ')}`
📨 Từ: `{from_addr}`
🆔 Mail ID: {mail_id}
📝 Chủ đề: {subject}
🕒 Thời gian: {time_recv}

[Người yêu cầu: {user_name}]
"""
            client.sendMessage(Message(text=msg), thread_id, thread_type)
            return

        # Xem danh sách domain
        elif command == "list":
            res = requests.get("https://www.phamvandienofficial.xyz/mail10p/domain", timeout=10)
            domain_list = res.text.strip()

            msg = f"""📜 Danh sách domain email tạm thời:

{domain_list}

[Người yêu cầu: {user_name}]"""
            client.sendMessage(Message(text=msg), thread_id, thread_type)
            return

        # Không đúng subcommand
        else:
            client.sendMessage(
                Message(text=f"⚠️ Lệnh không hợp lệ. Nhập `mail10p` để xem hướng dẫn."),
                thread_id, thread_type
            )

    except Exception as e:
        client.sendMessage(
            Message(text=f"⚠️ Lỗi xảy ra: {e}\n\n[Người yêu cầu: {user_name}]"),
            thread_id, thread_type
        )
