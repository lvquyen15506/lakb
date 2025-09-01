from zlapi.models import Message, ThreadType, MessageStyle, MultiMsgStyle
import requests
from datetime import datetime
from core.bot_sys import get_user_name_by_id

des = {
    'version': "1.0.0",
    'credits': "Hoang Thanh Tung",
    'description': "Lay thong tin tai khoan Free Fire tu UID",
    'power': "✅ Ai cung dung đuoc"
}

def handle_ff_command(message, message_object, thread_id, thread_type, author_id, client):
    user_name = get_user_name_by_id(client, author_id)
    parts = message.strip().split()

    if len(parts) < 2:
        client.sendMessage(
            Message(text=f"❌ Thieu UID!\n\n📌 **Cach dung:**\n`/ff <uid>`\n\nVi du: `/ff 12345678`\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
        return

    uid = parts[1]
    region = "SG"

    try:
        url = f"https://accinfo.vercel.app/player-info?region={region}&uid={uid}"
        res = requests.get(url)

        if res.status_code != 200 or not res.json().get("basicInfo"):
            client.sendMessage(
                Message(text=f"❌ Khong tim thay tai khoan hoac UID sai.\n\n[Ask by: {user_name}]"),
                thread_id, thread_type
            )
            return

        data = res.json()
        basic = data["basicInfo"]
        clan = data.get("clanBasicInfo", {})
        pet = data.get("petInfo", {})
        social = data.get("socialInfo", {})

        nickname = basic.get("nickname", "Khong ro")
        level = basic.get("level", 0)
        rank = basic.get("rank", 0)
        cs_rank = basic.get("csRank", 0)
        liked = basic.get("liked", 0)
        clan_name = clan.get("clanName", "Khong co")
        pet_name = pet.get("name", "Khong co")
        pet_lv = pet.get("level", 0)
        signature = social.get("signature", "Chua co")
        created_at = datetime.fromtimestamp(int(basic.get("createAt", 0))).strftime("%d/%m/%Y")

        # Soan tin nhan chia dong đe tinh offset chinh xac
        msg_lines = [
            f"📦 [Thong Tin Free Fire]",
            "━━━━━━━━━━━━━━━━━━━",
            f"👤 Nickname: {nickname}",
            f"🆔 UID: {uid} ({region})",
            f"📈 Cap đo: {level}",
            f"🏆 Rank BR: {rank} | CS: {cs_rank}",
            f"❤️ Luot thich: {liked:,}",
            f"👑 Clan: {clan_name}",
            f"🐾 Pet chinh: {pet_name} (Lv.{pet_lv})",
            f"📅 Ngay tao tai khoan: {created_at}",
            f"📝 Tieu su: {signature if signature else 'Khong co'}",
            "━━━━━━━━━━━━━━━━━━━",
            f"[Ask by: {user_name}]"
        ]
        msg = "\n".join(msg_lines)

        # Tinh offset cho tung dong
        offsets = []
        current_offset = 0
        for line in msg_lines:
            offsets.append(current_offset)
            current_offset += len(line) + 1  # +1 cho \n

        # Tao danh sach style
        style_list = [
            # Tieu đe
            MessageStyle(offset=offsets[0], length=len(msg_lines[0]), style="bold"),
            MessageStyle(offset=offsets[0], length=len(msg_lines[0]), style="color", color="#15A85F"),

            # Nickname
            MessageStyle(offset=offsets[2] + 13, length=len(nickname), style="color", color="#3498DB"),

            # UID
            MessageStyle(offset=offsets[3] + 9, length=len(uid), style="color", color="#E67E22"),

            # Level
            MessageStyle(offset=offsets[4] + 13, length=len(str(level)), style="color", color="#2ECC71"),

            # Rank BR
            MessageStyle(offset=offsets[5] + 13, length=len(str(rank)), style="color", color="#9B59B6"),

            # Rank CS
            MessageStyle(offset=offsets[5] + 24, length=len(str(cs_rank)), style="color", color="#8E44AD"),

            # Likes
            MessageStyle(offset=offsets[6] + 15, length=len(f"{liked:,}"), style="color", color="#E74C3C"),

            # Clan
            MessageStyle(offset=offsets[7] + 9, length=len(clan_name), style="color", color="#F1C40F"),

            # Pet
            MessageStyle(offset=offsets[8] + 14, length=len(pet_name), style="color", color="#1ABC9C"),

            # Ngay tao
            MessageStyle(offset=offsets[9] + 23, length=len(created_at), style="color", color="#95A5A6"),
        ]

        # Them style cho tieu su neu co
        if signature:
            style_list.append(
                MessageStyle(offset=offsets[10] + 13, length=len(signature), style="color", color="#7F8C8D")
            )

        # Gui tin nhan co đinh dang mau
        styles = MultiMsgStyle(style_list)
        client.sendMessage(Message(text=msg, style=styles), thread_id, thread_type)

    except Exception as e:
        client.sendMessage(
            Message(text=f"⚠️ Co loi xay ra khi xu ly: {e}\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
