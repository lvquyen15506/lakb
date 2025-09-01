from core.bot_sys import admin_cao
from zlapi.models import Message, MessageStyle, MultiMsgStyle
import time

des = {
    'version': "1.0.1",
    'credits': "Vu Xuan Kien",
    'description': "Duyet tat ca thanh vien",
    'power': "Quan tri vien Bot / Quan tri vien Nhom"
}

def handle_duyetmem_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # Kiem tra quyen admin
        if not admin_cao(client, author_id):
            client.replyMessage(
                Message(text="🚫 Ban khong co quyen su dung lenh nay!"),
                message_object, thread_id, thread_type, ttl=12000
            )
            return

        group_info = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        pending_members = group_info.pendingApprove.get('uids', [])

        command_parts = message.strip().split()
        if len(command_parts) < 2:
            client.replyMessage(
                Message(text="Nhap lenh đung nhe:\nduyetmem [all|list]"),
                message_object, thread_id, thread_type, ttl=12000
            )
            return

        action = command_parts[1]

        if action == "list":
            if not pending_members:
                client.replyMessage(
                    Message(text="Hien tai khong co thanh vien nao đang cho duyet."),
                    message_object, thread_id, thread_type, ttl=12000
                )
            else:
                client.replyMessage(
                    Message(text=f"So thanh vien đang cho duyet: {len(pending_members)}"),
                    message_object, thread_id, thread_type, ttl=12000
                )
        elif action == "all":
            if not pending_members:
                client.replyMessage(
                    Message(text="Hien tai khong co thanh vien nao đang cho duyet."),
                    message_object, thread_id, thread_type, ttl=12000
                )
                return

            for member_id in pending_members:
                if hasattr(client, 'handleGroupPending'):
                    client.handleGroupPending(member_id, thread_id)
                else:
                    break

            client.replyMessage(
                Message(text="Đa hoan tat duyet tat ca thanh vien."),
                message_object, thread_id, thread_type, ttl=12000
            )
        else:
            client.replyMessage(
                Message(text="Nhap lenh đung nhe:\nduyetmem [all|list]"),
                message_object, thread_id, thread_type, ttl=12000
            )

    except Exception as e:
        print(f"Loi: {e}")
        client.replyMessage(
            Message(text=f"Đa xay ra loi khi duyet.\n{e}"),
            message_object, thread_id, thread_type, ttl=12000
        )
