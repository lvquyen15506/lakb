from zlapi.models import Message, ThreadType
import time

des = {
    'version': "1.0.2",
    'credits': "Vu Xuan Kien",
    'description': "uptime card bot",
    'power': "Thanh vien"
}

start_time = time.time()

def handle_cardinfo_command(message, message_object, thread_id, thread_type, author_id, client):
    userId = message_object.mentions[0]['uid'] if message_object.mentions else author_id

    if not userId:
        client.send(
            Message(text="Khong tim thay nguoi dung."),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return
    user_info = client.fetchUserInfo(userId).changed_profiles.get(userId)
    if not user_info:
        client.send(
            Message(text="Khong the lay thong tin nguoi dung."),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return

    avatarUrl = user_info.avatar
    
    if not avatarUrl:
        client.send(
            Message(text="Nguoi dung nay khong co anh đai dien."),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return

    current_time = time.time()
    uptime_seconds = int(current_time - start_time)

    days = uptime_seconds // (24 * 3600)
    uptime_seconds %= (24 * 3600)
    hours = uptime_seconds // 3600
    uptime_seconds %= 3600
    minutes = uptime_seconds // 60
    seconds = uptime_seconds % 60

    uptime_text = f"⤷Uptime: {days}d {hours}h {minutes}m {seconds}s!"

    client.sendBusinessCard(
        userId=userId,
        qrCodeUrl=None,
        thread_id=thread_id,
        thread_type=thread_type,
        phone=f"{uptime_text}"
    )
