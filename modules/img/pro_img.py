import subprocess
import os
from PIL import Image
from zlapi.models import Message
from core.bot_sys import get_user_name_by_id

def handle_img_command(message, message_object, thread_id, thread_type, author_id, client):
    user_name = get_user_name_by_id(client, author_id)
    parts = message.strip().split(" ", 1)

    if len(parts) < 2 or not parts[1].strip():
        client.replyMessage(
            Message(text=(
                f"❌ Ban chua nhap mo ta anh.\n\n"
                f"📌 Cach dung:\n`>img <mo ta>`\n\n"
                f"Vi du: `>img con cho đang bay`\n\n"
                f"[Ask by: {user_name}]"
            )),
            thread_id=thread_id,
            thread_type=thread_type,
            replyMsg=message_object
        )
        return

    prompt = parts[1].strip()
    output_path = "generated_image.png"

    try:
        subprocess.run(
            ["python3", "img.py", prompt, output_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        client.replyMessage(
            Message(text=(
                f"❌ Loi khi tao anh tu mo ta: \"{prompt}\"\n"
                f"Chi tiet loi: {e}\n"
                f"Vui long thu lai sau.\n\n"
                f"[Ask by: {user_name}]"
            )),
            thread_id=thread_id,
            thread_type=thread_type,
            replyMsg=message_object
        )
        return

    if os.path.exists(output_path):
        if os.path.getsize(output_path) == 0:
            client.replyMessage(
                Message(text=(
                    f"❌ File anh tao ra bi rong.\n"
                    f"Vui long thu lai.\n\n"
                    f"[Ask by: {user_name}]"
                )),
                thread_id=thread_id,
                thread_type=thread_type,
                replyMsg=message_object
            )
            return

        try:
            with Image.open(output_path) as img:
                width, height = img.size

            client.sendLocalImage(
                output_path,
                thread_id=thread_id,
                thread_type=thread_type
            )

            client.replyMessage(
                Message(text=(
                    f"🖼️ Anh đuoc tao tu mo ta: \"{prompt}\"\n"
                    f"📐 Kich thuoc: {width}x{height}\n"
                    f"[Ask by: {user_name}]"
                )),
                thread_id=thread_id,
                thread_type=thread_type,
                replyMsg=message_object
            )

            os.remove(output_path)

        except Exception as e:
            client.replyMessage(
                Message(text=(
                    f"❌ Đa co loi khi mo anh vua tao.\n"
                    f"Chi tiet loi: {e}\n"
                    f"Vui long thu lai sau.\n\n"
                    f"[Ask by: {user_name}]"
                )),
                thread_id=thread_id,
                thread_type=thread_type,
                replyMsg=message_object
            )
    else:
        client.replyMessage(
            Message(text=(
                f"❌ Khong tim thay anh đuoc tao tu mo ta: \"{prompt}\"\n"
                f"Vui long thu lai!\n\n"
                f"[Ask by: {user_name}]"
            )),
            thread_id=thread_id,
            thread_type=thread_type,
            replyMsg=message_object
        )
