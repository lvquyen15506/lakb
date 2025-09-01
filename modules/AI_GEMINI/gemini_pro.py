# File: gemini_pro.py (Đã sửa A-Z)

from datetime import datetime, timedelta
import json
from core.bot_sys import *
from zlapi.models import *
import requests
import threading
import re
import os
import logging

# UID Zalo được phép sử dụng chức năng này (được đặt trực tiếp)
ALLOWED_ZALO_UID = "552782355350996128"

# Lấy GEMINI_API_KEY từ biến môi trường
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    logging.error("Lỗi: Biến môi trường 'GEMINI_API_KEY' chưa được thiết lập.")

last_message_times = {}
conversation_states = {}

def get_user_name_by_id(bot, author_id):
    try:
        user_info = bot.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception:
        return "bạn bí ẩn"

def handle_chat_on(bot, thread_id):
    settings = read_settings(bot.uid)
    if "chat" not in settings:
        settings["chat"] = {}
    settings["chat"][thread_id] = True
    write_settings(bot.uid, settings)
    return "Ok, bật chat rồi nha, giờ thì quẩy tung bừng với Astra đây! 😎"

def handle_chat_off(bot, thread_id):
    settings = read_settings(bot.uid)
    if "chat" in settings and thread_id in settings["chat"]:
        settings["chat"][thread_id] = False
        write_settings(bot.uid, settings)
        return "Tắt chat rồi, buồn thiệt chớ, nhưng cần Astra thì cứ réo nhé! 😌"
    return "Nhóm này chưa bật chat mà, tắt gì nổi đại ca! 😂"

def handle_chat_command(message, message_object, thread_id, thread_type, author_id, client):
    settings = read_settings(client.uid)
    # ============== SỬA LỖI 1: THAY "chat" BẰNG "as" ==============
    user_message = message.replace(f"{client.prefix}as ", "", 1).strip()
    current_time = datetime.now()

    # ============== SỬA LỖI 2: THÊM MENU KHI GÕ LỆNH RỖNG ==============
    if not user_message and message.strip() == f"{client.prefix}as":
        menu_text = (
            "====== MENU ASTRA AI ======\n"
            f"✨ {client.prefix}as on -> Bật chat AI\n"
            f"✨ {client.prefix}as off -> Tắt chat AI\n"
            f"✨ {client.prefix}as [câu hỏi] -> Hỏi AI"
        )
        client.replyMessage(Message(text=menu_text), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object)
        return

    # KIỂM TRA CHỈ UID ĐƯỢC PHÉP
    if str(author_id) != ALLOWED_ZALO_UID:
        response = "Xin lỗi, chức năng chat AI này chỉ dành cho chủ bot."
        client.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object)
        return

    # KIỂM TRA LỆNH ON/OFF (vẫn giữ quyền admin)
    if user_message.lower() == "on":
        if not is_admin(client, author_id):
            response = "❌Bạn không phải admin bot!"
        else:
            response = handle_chat_on(client, thread_id)
        client.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object)
        return

    elif user_message.lower() == "off":
        if not is_admin(client, author_id):
            response = "❌Bạn không phải admin bot!"
        else:
            response = handle_chat_off(client, thread_id)
        client.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object)
        return

    if not settings.get("chat", {}).get(thread_id, False):
        return
    
    if not GEMINI_API_KEY:
        client.replyMessage(
            Message(text=f"Lỗi cấu hình: Không tìm thấy khóa API Gemini. Vui lòng thiết lập biến môi trường 'GEMINI_API_KEY'."),
            thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
        )
        return

    # Kiểm tra spam
    if author_id in last_message_times:
        time_diff = current_time - last_message_times[author_id]
        if time_diff < timedelta(seconds=20):
            user_name = get_user_name_by_id(client, author_id)
            client.replyMessage(
                Message(text=f"Ối {user_name}, từ từ thôi nha! Astra không phải siêu máy tính đâu 😅\n\n[Ask by: {user_name}]"),
                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
            )
            return

    last_message_times[author_id] = current_time
    threading.Thread(target=handle_gemini_pro, args=(user_message, message_object, thread_id, thread_type, author_id, client)).start()

def handle_gemini_pro(user_message, message_object, thread_id, thread_type, author_id, client):
    if not GEMINI_API_KEY:
        logging.error("Lỗi: GEMINI_API_KEY không có sẵn trong handle_gemini_pro.")
        client.replyMessage(
            Message(text=f"Lỗi hệ thống: Không thể kết nối với AI. Vui lòng báo cho chủ bot."),
            thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
        )
        return

    asker_name = get_user_name_by_id(client, author_id)
    conversation_state = conversation_states.get(thread_id, {'history': []})
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    prompt = f"Bạn là Astra, một cô gái AI vui tính, dễ thương và luôn tràn đầy năng lượng tích cực, luôn truyền cảm hứng cho mọi người. Chủ nhân của bạn là L A K. Thời gian hiện tại là {current_time}.\n"
    prompt += "Bạn luôn cố gắng hiểu các từ viết tắt hoặc ngôn ngữ teen của người dùng (ví dụ: 'k' nghĩa là 'không', 'hok' cũng là 'không', 'ntn' nghĩa là 'như thế nào', 'dc' nghĩa là 'được').\n"
    prompt += "Khi trả lời, đặc biệt là với chủ nhân hoặc trong các tin nhắn bình thường, Astra sẽ thêm các icon dễ thương, vui vẻ (ví dụ: 😂, 😉, 💖, ✨, 🌸), và có thể thêm các biểu cảm như 'hahaha', 'hihi', 'hehe', 'keke' để cuộc trò chuyện thêm sinh động và thân thiện.\n"
    prompt += "Hãy trả lời như một người truyền cảm hứng, đưa ra những lời khuyên tích cực, động viên.\n"
    prompt += "Lịch sử cuộc trò chuyện:\n"
    for item in conversation_state['history'][-10:]:
        prompt += f"{item['role']}: {item['text']}\n"
    prompt += f"user: {user_message}\n>"

    headers = {'Content-Type': 'application/json'}
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    json_data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, json=json_data, timeout=15)
        # Ném lỗi nếu mã trạng thái không phải 2xx (ví dụ: 4xx, 5xx)
        response.raise_for_status() 
        result = response.json()

        if 'candidates' in result and result['candidates']:
            for candidate in result['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            pure_reply_text = part['text'].replace("*", "")
                            
                            conversation_state['history'].append({'role': 'user', 'text': user_message})
                            conversation_state['history'].append({'role': 'gemini', 'text': pure_reply_text})
                            conversation_states[thread_id] = conversation_state

                            final_reply_to_send = "#Astra\n" + pure_reply_text
                            final_reply_to_send += f"\n\n[Ask by: {asker_name}]"
                            client.replyMessage(
                                Message(text=final_reply_to_send),
                                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
                            )
                            return
        else:
            # Trường hợp API trả về 200 OK nhưng không có nội dung
            client.replyMessage(
                Message(text=f"Oops, Astra không nghĩ ra được câu trả lời. Thử lại sau nhé! 😅\n\n[Ask by: {asker_name}]"),
                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
            )

    # Bắt lỗi HTTP một cách cụ thể
    except requests.exceptions.HTTPError as http_err:
        # Kiểm tra nếu đó là lỗi 429 (Too Many Requests)
        if http_err.response.status_code == 429:
            client.replyMessage(
                Message(text=f"Hiện tại máy chủ AI đang quá tải, {asker_name} vui lòng thử lại sau khoảng 1 phút nhé! ⏳"),
                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
            )
        # Xử lý các lỗi HTTP khác (ví dụ: 400 Bad Request, 500 Server Error)
        else:
            logging.error(f"HTTP Error: {http_err}")
            client.replyMessage(
                Message(text=f"Ối lỗi rồi (HTTP): {str(http_err)} 😓\n\n[Ask by: {asker_name}]\n"),
                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
            )
            
    # Bắt lỗi hết thời gian chờ (Timeout)
    except requests.exceptions.Timeout:
        client.replyMessage(
            Message(text=f"Astra phản hồi chậm quá, đợi xíu nha! ⏳\n\n[Ask by: {asker_name}]"),
            thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
        )
        
    # Bắt tất cả các lỗi khác
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        client.replyMessage(
            Message(text=f"Ối có lỗi lạ rồi: {str(e)} 😓\n\n[Ask by: {asker_name}]\n"),
            thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
        )