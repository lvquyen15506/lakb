from zlapi.models import Message
import requests
import os
from PIL import Image
from io import BytesIO
from core.bot_sys import get_user_name_by_id

def handle_doff_command(message, message_object, thread_id, thread_type, author_id, client):
    user_name = get_user_name_by_id(client, author_id)
    parts = message.strip().split()

    if len(parts) < 2:
        client.sendMessage(
            Message(text=f"❌ Thieu UID!\n\n📌 **Cach dung:**\n`doff <uid>`\n\nVi du: `doff 12345678`\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
        return

    uid = parts[1]
    region = "sg"
    api_key = "AYAxAPI"

    try:
        outfit_url = f"https://aya-outfit-version1.vercel.app/outfit-image?uid={uid}&region={region}&key={api_key}"

        response = requests.get(outfit_url, stream=True)
        if response.status_code != 200:
            client.sendMessage(
                Message(text=f"❌ Khong the lay anh outfit. UID sai hoac server loi.\n\n[Ask by: {user_name}]"),
                thread_id, thread_type
            )
            return

        image = Image.open(BytesIO(response.content)).convert("RGB")
        temp_path = f"modules/cache/outfit_{uid}.jpg"
        image.save(temp_path, format='JPEG')

        client.sendLocalImage(
            temp_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=image.width,
            height=image.height
        )

        if os.path.exists(temp_path):
            os.remove(temp_path)

    except Exception as e:
        client.sendMessage(
            Message(text=f"⚠️ Co loi xay ra khi xu ly: {e}\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
