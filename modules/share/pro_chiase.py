import os
from zlapi.models import Message, ThreadType

# Thư mục chứa file
BOT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot")

if not os.path.exists(BOT_FOLDER):
    os.makedirs(BOT_FOLDER)

# File tên -> link tương ứng
FILE_LINKS = {
    "auto_cai_thu_vien.zip": "https://drive.google.com/file/d/1Voq7M8MEBFhrM-08Mn5177GzFDT28iF1/view?usp=drivesdk",
    "bot telegram.zip": "https://drive.google.com/file/d/1tLLu9413yOvI-lmEaHLKAcuQlpeLr19U/view?usp=drivesdk",
    "bot_gwendev.zip": "https://drive.google.com/file/d/1csU2vkd0TDKCKDwbmUB0LY7nWPYXBdx6/view?usp=drivesdk",
}

def load_file_list():
    files = sorted([
        f for f in os.listdir(BOT_FOLDER)
        if os.path.isfile(os.path.join(BOT_FOLDER, f))
    ])
    # Đánh số 1,2,3 ...
    return {i + 1: f for i, f in enumerate(files)}

def send_file_list(thread_id, thread_type, client, file_list):
    msg = (
        "📁 **Danh sách file có thể chia sẻ:**\n"
        "_Lưu ý: Một số file Python, một số file ZIP._\n\n"
    )
    for idx, fname in file_list.items():
        msg += f"{idx}. {fname}\n"
    msg += "\n👉 Dùng lệnh: `chiase [số hoặc tên file]` để nhận file hoặc link."
    client.sendMessage(Message(text=msg), thread_id, thread_type)

def handle_chiase_command(message_text, thread_id, thread_type, author_id, client, extra=None):
    """
    message_text: ví dụ "chiase 1" hoặc "chiase bot telegram.zip"
    client: phải là bot instance có sendMessage()
    """
    file_list = load_file_list()
    parts = message_text.strip().split(maxsplit=1)

    # Nếu chỉ gõ "chiase" thì gửi danh sách file
    if len(parts) == 1:
        send_file_list(thread_id, thread_type, client, file_list)
        return

    key = parts[1].strip()
    fname = None

    # Tìm theo số hoặc tên file
    if key.isdigit():
        fname = file_list.get(int(key))
    else:
        # So sánh không phân biệt hoa thường
        for f in file_list.values():
            if f.lower() == key.lower():
                fname = f
                break

    if not fname:
        client.sendMessage(Message(text="❌ Không tìm thấy file tương ứng!"), thread_id, thread_type)
        return

    link = FILE_LINKS.get(fname)
    if not link:
        client.sendMessage(Message(text=f"❌ File **{fname}** chưa có link chia sẻ!"), thread_id, thread_type)
        return

    # Gửi riêng link file cho người yêu cầu (gửi cho author_id, thread type USER)
    msg = f"✅ Link tải file **{fname}** của bạn:\n🔗 {link}"
    client.sendMessage(Message(text=msg), author_id, ThreadType.USER)
