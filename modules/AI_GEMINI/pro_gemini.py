from datetime import datetime, timedelta
import json
from core.bot_sys import *
from zlapi.models import *
import requests
import threading
import re
import random
import math
import heapq
import os
import logging

GEMINI_API_KEY = 'AIzaSyC5VvVGBk3T0TzfF_JCaDTDPAW97oRhdrc'
last_message_times = {}
conversation_states = {}
default_language = "vi"

def get_user_name_by_id(bot, author_id):
    try:
        user_info = bot.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception:
        return "ban bi an"

def detect_language(text):
    if re.search(r'[aaaaaaaaaaaaaaaaađeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyy]', text.lower()):
        return "vi"
    elif re.search(r'[a-zA-Z]', text):
        return "en"
    return default_language

def translate_response(text, target_lang):
    return text  # Giu nguyen neu chua tich hop dich

def handle_chat_on(bot, thread_id):
    settings = read_settings(bot.uid)
    if "chat" not in settings:
        settings["chat"] = {}
    settings["chat"][thread_id] = True
    write_settings(bot.uid, settings)
    return "Ok, bat chat roi nha, gio thi quay tung bung voi Shin đay! 😎"

def handle_chat_off(bot, thread_id):
    settings = read_settings(bot.uid)
    if "chat" in settings and thread_id in settings["chat"]:
        settings["chat"][thread_id] = False
        write_settings(bot.uid, settings)
        return "Tat chat roi, buon thiet chu, nhung can Shin thi cu reo nhe! 😌"
    return "Nhom nay chua bat chat ma, tat gi noi đau đai ca! 😂"

def handle_chat_command(message, message_object, thread_id, thread_type, author_id, client):
    settings = read_settings(client.uid)
    user_message = message.replace(f"{client.prefix}chat ", "").strip()
    current_time = datetime.now()

    if user_message.lower() == "on":
        if not is_admin(client, author_id):
            response = "❌Ban khong phai admin bot!"
        else:
            response = handle_chat_on(client, thread_id)
        client.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object)
        return

    elif user_message.lower() == "off":
        if not is_admin(client, author_id):
            response = "❌Ban khong phai admin bot!"
        else:
            response = handle_chat_off(client, thread_id)
        client.replyMessage(Message(text=response), thread_id=thread_id, thread_type=thread_type, replyMsg=message_object)
        return

    if not settings.get("chat", {}).get(thread_id, False):
        return

    # Kiem tra spam
    if author_id in last_message_times:
        time_diff = current_time - last_message_times[author_id]
        if time_diff < timedelta(seconds=5):
            user_name = get_user_name_by_id(client, author_id)
            client.replyMessage(
                Message(text=f"Oi {user_name}, tu tu thoi nha! Shin khong phai sieu may tinh đau 😅\n\n[Ask by: {user_name}]"),
                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
            )
            return

    last_message_times[author_id] = current_time
    threading.Thread(target=handle_gemini_chat, args=(user_message, message_object, thread_id, thread_type, author_id, client)).start()

def handle_gemini_chat(user_message, message_object, thread_id, thread_type, author_id, client):
    asker_name = get_user_name_by_id(client, author_id)
    conversation_state = conversation_states.get(thread_id, {'history': []})
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    prompt = f"Ban la tro ly AI cua nguoi dung ten {asker_name}, tao ra boi Hoang Thang Tung, thoi gian hien tai la {current_time}.\n"
    prompt += "Lich su cuoc tro chuyen:\n"
    for item in conversation_state['history'][-10:]:
        prompt += f"{item['role']}: {item['text']}\n"
    prompt += f"user: {user_message}\n>"

    headers = {'Content-Type': 'application/json'}
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    json_data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, json=json_data, timeout=15)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result and result['candidates']:
            for candidate in result['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            reply_text = part['text'].replace("*", "")
                            conversation_state['history'].append({'role': 'user', 'text': user_message})
                            conversation_state['history'].append({'role': 'gemini', 'text': reply_text})
                            conversation_states[thread_id] = conversation_state

                            reply_text += f"\n\n[Ask by: {asker_name}]"
                            client.replyMessage(
                                Message(text=reply_text),
                                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
                            )
                            return
        else:
            client.replyMessage(
                Message(text=f"Oops, he thong dang ban. Thu lai sau nhe! 😅\n\n[Ask by: {asker_name}]"),
                thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
            )
    except requests.exceptions.Timeout:
        client.replyMessage(
            Message(text=f"Shin cham qua, doi xiu nha! ⏳\n\n[Ask by: {asker_name}]"),
            thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
        )
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        client.replyMessage(
            Message(text=f"Oi loi roi: {str(e)} 😓\n\n[Ask by: {asker_name}]"),
            thread_id=thread_id, thread_type=thread_type, replyMsg=message_object
        )
