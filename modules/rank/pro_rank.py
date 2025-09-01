from zlapi.models import Message, MessageStyle, MultiMsgStyle
from core.bot_sys import get_user_name_by_id
import json
from pathlib import Path

# Đuong dan toi file JSON
rank_info_path = Path.cwd() / "rank-info.json"

def read_rank_info():
    try:
        if not rank_info_path.exists():
            return {"groups": {}}
        with open(rank_info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "groups" not in data:
            data["groups"] = {}
        return data
    except Exception as e:
        print("❌ Loi khi đoc rank-info.json:", e)
        return {"groups": {}}

def handle_rank_command(message, message_object, thread_id, thread_type, author_id, client):
    user_name = get_user_name_by_id(client, author_id)
    rank_info = read_rank_info()
    group_users = rank_info.get("groups", {}).get(thread_id, {}).get("users", [])

    if not group_users:
        client.sendMessage(
            Message(text=f"📭 Chua co du lieu xep hang cho nhom nay.\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
        return

    sorted_users = sorted(group_users, key=lambda x: x["Rank"], reverse=True)
    top10_users = sorted_users[:10]

    emojis = ["🥇", "🥈", "🥉"] + [f"{i+1}." for i in range(3, 10)]
    msg_lines = ["🏆 BANG XEP HANG TUONG TAC", "━━━━━━━━━━━━━━━━━━━"]
    for idx, user in enumerate(top10_users):
        msg_lines.append(f"{emojis[idx]} {user['UserName']}: {user['Rank']} tin nhan")
    msg_lines.append("━━━━━━━━━━━━━━━━━━━")
    msg_lines.append(f"[Ask by: {user_name}]")

    msg = "\n".join(msg_lines)

    # Tinh offset đe to mau
    offsets = []
    current_offset = 0
    for line in msg_lines:
        offsets.append(current_offset)
        current_offset += len(line) + 1  # +1 vi co "\n"

    styles = []
    colors = ["#FFD700", "#C0C0C0", "#CD7F32"]  # Vang, bac, đong

    for i in range(min(3, len(top10_users))):
        name = top10_users[i]["UserName"]
        offset = offsets[i + 2] + len(emojis[i]) + 1  # offset dong + ky hieu + khoang trang
        styles.append(MessageStyle(offset=offset, length=len(name), style="color", color=colors[i]))

    multi_style = MultiMsgStyle(styles)

    client.sendMessage(Message(text=msg, style=multi_style), thread_id, thread_type)
