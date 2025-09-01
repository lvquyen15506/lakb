# File: bot_sys.py (Đã sửa lỗi xung đột)
import colorsys
from datetime import datetime, timedelta
import difflib
import glob
import importlib
from io import BytesIO
import os
import platform
import random
import re
import string
import sys
from threading import Thread
import threading
import time
from typing import List, Optional, Tuple
import emoji
import psutil
import pytz
import requests
from zlapi.models import *
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ============== DÒNG IMPORT GÂY LỖI VÒNG TRÒN ĐÃ BỊ XÓA KHỎI ĐÂY ==============

BACKGROUND_PATH = "background/"
CACHE_PATH = "modules/cache/"
OUTPUT_IMAGE_PATH = os.path.join(CACHE_PATH, "bot.png")
SETTING_FILE = 'setting.json'
LOG_FILE = 'logs.json'
MUTED_MESSAGES_FILE = 'muted_messages.json'

autostk_loops = {}

def sticker_loop(bot, thread_id, thread_type):
    stop_event = autostk_loops.get(thread_id)
    if not stop_event:
        return

    try:
        with open('auto_sticker.json', 'r', encoding='utf-8') as f:
            stickers = json.load(f)
        if not stickers:
            bot.sendMessage("Lỗi: Tệp auto_sticker.json trống hoặc không tồn tại. Vui lòng kiểm tra lại.", thread_id, thread_type)
            return
    except Exception as e:
        bot.sendMessage(f"Lỗi khi đọc file sticker: {e}", thread_id, thread_type)
        return

    while not stop_event.is_set():
        try:
            sticker1 = random.choice(stickers)
            bot.sendSticker(sticker1['stickerType'], sticker1['stickerId'], sticker1['cateId'], thread_id, thread_type, ttl=30000)

            time.sleep(30)

            if stop_event.is_set():
                break

            sticker2 = random.choice(stickers)
            bot.sendSticker(sticker2['stickerType'], sticker2['stickerId'], sticker2['cateId'], thread_id, thread_type)
            
            time.sleep(1)

        except Exception as e:
            print(f"[ERROR] Lỗi trong vòng lặp sticker cho thread {thread_id}: {e}")
            time.sleep(10)

def read_settings(uid):
    data_file_path = os.path.join(f"{uid}_{SETTING_FILE}")
    try:
        with open(data_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_settings(uid, settings):
    data_file_path = os.path.join(f"{uid}_{SETTING_FILE}")
    with open(data_file_path, 'w', encoding='utf-8') as file:
        json.dump(settings, file, ensure_ascii=False, indent=4)

def load_message_log(uid):
    log_file_path = os.path.join(f"{uid}_{LOG_FILE}")
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get("message_log", {})
    except FileNotFoundError:
        return {}

def save_message_log(uid, message_log):
    log_file_path = os.path.join(f"{uid}_{LOG_FILE}")
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {}
    settings["message_log"] = message_log
    with open(log_file_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def save_muted_message(uid, author_id, thread_id, message_content):
    muted_file_path = os.path.join(f"{uid}_{MUTED_MESSAGES_FILE}")
    try:
        with open(muted_file_path, 'r', encoding='utf-8') as file:
            muted_messages = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        muted_messages = {}

    if thread_id not in muted_messages:
        muted_messages[thread_id] = {}
    if author_id not in muted_messages[thread_id]:
        muted_messages[thread_id][author_id] = []

    muted_messages[thread_id][author_id].append(message_content)

    with open(muted_file_path, 'w', encoding='utf-8') as file:
        json.dump(muted_messages, file, ensure_ascii=False, indent=4)

def ban_user_from_commands(bot, author_id, mentioned_uids):
    settings = read_settings(bot.uid)
    admin_bot = settings.get("admin_bot", [])
    response = ""

    if author_id not in admin_bot:
        return "❌Ban khong phai admin bot!"

    banned_users = settings.get("banned_users", [])

    for uid in mentioned_uids:
        if uid not in banned_users:
            banned_users.append(uid)
            user_name = get_user_name_by_id(bot, uid)
            response += f"➜ Nguoi dung 👤 {user_name} đa bi cam su dung cac lenh BOT 🤖\n"
        else:
            user_name = get_user_name_by_id(bot, uid)
            response += f"➜ Nguoi dung 👤 {user_name} đa bi cam truoc đo 🤧\n"

    settings["banned_users"] = banned_users
    write_settings(bot.uid, settings)
    return response

def unban_user_from_commands(bot, author_id, mentioned_uids):
    settings = read_settings(bot.uid)
    admin_bot = settings.get("admin_bot", [])
    response = ""

    if author_id not in admin_bot:
        return "❌Ban khong phai admin bot!"

    banned_users = settings.get("banned_users", [])

    for uid in mentioned_uids:
        if uid in banned_users:
            banned_users.remove(uid)
            user_name = get_user_name_by_id(bot, uid)
            response += f"➜ Nguoi dung 👤 {user_name} đa đuoc go cam su dung cac lenh BOT 🤖\n"
        else:
            user_name = get_user_name_by_id(bot, uid)
            response += f"➜ Nguoi dung 👤 {user_name} khong co trong danh sach cam 🤧\n"

    settings["banned_users"] = banned_users
    write_settings(bot.uid, settings)
    return response

def list_banned_users(bot):
    settings = read_settings(bot.uid)
    banned_users = settings.get("banned_users", [])
    if not banned_users:
        return "➜ Khong co nguoi dung nao bi cam su dung cac lenh BOT 🤖"
    
    response = "➜ Danh sach nguoi dung bi cam su dung cac lenh BOT 🤖:\n"
    for uid in banned_users:
        user_name = get_user_name_by_id(bot, uid)
        response += f"👤 {user_name}\n"
    return response

def get_content_message(message_object):
    if message_object.msgType == 'chat.sticker':
        return ""
    
    content = message_object.content
    
    if isinstance(content, dict) and 'title' in content:
        text_to_check = content['title']
    else:
        text_to_check = content if isinstance(content, str) else ""
    return text_to_check



def is_url_in_message(message_object):
    t = _extract_all_texts(message_object)
    if not t:
        return False
    import re as _re
    patt = r"""(?xi)
        (?:https?://|www\.)\S+
        |\b(?:zalo\.me)\b(?:/\S+)?
    """
    return _re.search(patt, t) is not None


def is_admin(bot, author_id):
    settings = read_settings(bot.uid)
    admin_bot = settings.get("admin_bot", [])
    return author_id in admin_bot

def admin_cao(bot, author_id):
    settings = read_settings(bot.uid)
    high_level_admins = settings.get("high_level_admins", [])
    return author_id in high_level_admins

def handle_bot_admin(bot):
    settings = read_settings(bot.uid)
    admin_bot = settings.get("admin_bot", [])
    high_level_admins = settings.get("high_level_admins", [])

    if bot.uid not in admin_bot:
        admin_bot.append(bot.uid)
        settings['admin_bot'] = admin_bot
        write_settings(bot.uid, settings)
        print(f"Đa them 👑{get_user_name_by_id(bot, bot.uid)} 🆔 {bot.uid} cho lan đau tien khoi đong vao danh sach Admin 🤖BOT ✅")

    if bot.uid not in high_level_admins:
        high_level_admins.append(bot.uid)
        settings['high_level_admins'] = high_level_admins
        write_settings(bot.uid, settings)
        print(f"Đa them 👑{get_user_name_by_id(bot, bot.uid)} 🆔 {bot.uid} vao danh sach Admin cap cao 🤖BOT ✅")

def get_allowed_thread_ids(bot):
    settings = read_settings(bot.uid)
    return settings.get('allowed_thread_ids', [])

def bot_on_group(bot, thread_id):
    try:
        settings = read_settings(bot.uid)
        allowed_thread_ids = settings.get('allowed_thread_ids', [])
        group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]

        if thread_id not in allowed_thread_ids:
            allowed_thread_ids.append(thread_id)
            settings['allowed_thread_ids'] = allowed_thread_ids
            write_settings(bot.uid, settings)

            return f"[🤖BOT {bot.me_name} {bot.version}] đa đuoc bat trong Group: {group.name} - ID: {thread_id}\n➜ Go lenh ➡️ /help hoac {bot.prefix}bot đe xem danh sach tinh nang BOT💡"
    except Exception as e:
        print(f"Error: {e}")
        return "Đa xay ra loi gi đo🤧"

def bot_off_group(bot, thread_id):
    try:
        settings = read_settings(bot.uid)
        allowed_thread_ids = settings.get('allowed_thread_ids', [])
        group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]

        if thread_id in allowed_thread_ids:
            allowed_thread_ids.remove(thread_id)
            settings['allowed_thread_ids'] = allowed_thread_ids
            write_settings(bot.uid, settings)

            return f"[🤖BOT {bot.me_name} {bot.version}] đa đuoc tat trong Group: {group.name} - ID: {thread_id}\n➜ Chao tam biet chuc ban luon may man🍀"
    except Exception as e:
        print(f"Error: {e}")
        return "Đa xay ra loi gi đo🤧"

def add_forbidden_word(bot, author_id, word):
    if not is_admin(bot, author_id):
        return "❌Ban khong phai admin bot!"
    
    settings = read_settings(bot.uid)
    forbidden_words = settings.get('forbidden_words', [])
    
    if word not in forbidden_words:
        forbidden_words.append(word)
        settings['forbidden_words'] = forbidden_words
        write_settings(bot.uid, settings)
        return f"➜ Tu '{word}' đa đuoc them vao danh sach tu cam ✅"
    else:
        return f"➜ Tu '{word}' đa ton tai trong danh sach tu cam 🤧"

def remove_forbidden_word(bot, author_id, word):
    if not is_admin(bot, author_id):
        return "❌Ban khong phai admin bot!"
    
    settings = read_settings(bot.uid)
    forbidden_words = settings.get('forbidden_words', [])
    
    if word in forbidden_words:
        forbidden_words.remove(word)
        settings['forbidden_words'] = forbidden_words
        write_settings(bot.uid, settings)
        return f"➜ Tu '{word}' đa đuoc xoa khoi danh sach tu cam ✅"
    else:
        return f"Tu '{word}' khong co trong danh sach tu cam 🤧"

def is_forbidden_word(bot, word):
    settings = read_settings(bot.uid)
    forbidden_words = settings.get('forbidden_words', [])
    return word in forbidden_words

def setup_bot_on(bot, thread_id):
    group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
    admin_ids = group.adminIds.copy()
    if group.creatorId not in admin_ids:
        admin_ids.append(group.creatorId)
    
    if bot.uid in admin_ids:
        settings = read_settings(bot.uid)
        
        if 'group_admins' not in settings:
            settings['group_admins'] = {}
        
        settings['group_admins'][thread_id] = admin_ids
        write_settings(bot.uid, settings)
        
        return f"[🤖BOT {bot.me_name} {bot.version}]\n➜ Cau hinh thanh cong noi quy nhom: {group.name} - ID: {thread_id} ✅\n➜ Hay nhan tin mot cach van minh lich su! ✨\n➜ Chuc ban luon may man! 🍀"
    else:
        return f"[🤖BOT {bot.me_name} {bot.version}]\n➜ Cau hinh that bai cho nhom: {group.name} - ID: {thread_id} ⚠️\n➜ Ban khong co quyen quan tri nhom nay! 🤧"

def setup_bot_off(bot, thread_id):
    group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
    settings = read_settings(bot.uid)

    if 'group_admins' in settings and thread_id in settings['group_admins']:
        del settings['group_admins'][thread_id]
        write_settings(bot.uid, settings)
        return f"[🤖BOT {bot.me_name} {bot.version}]\n➜ Đa huy bo thanh cong cau hinh quan tri cho nhom: {group.name} - ID: {thread_id} ✅\n➜ Hay quay len đi! 🤣"
    else:
        return f"[🤖BOT {bot.me_name} {bot.version}]\n➜ Khong tim thay cau hinh quan tri cho nhom: {group.name} - ID: {thread_id} đe huy bo! 🤧"

def check_admin_group(bot, thread_id):
    group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
    admin_ids = group.adminIds.copy()
    if group.creatorId not in admin_ids:
        admin_ids.append(group.creatorId)
    settings = read_settings(bot.uid)
    if 'group_admins' not in settings:
        settings['group_admins'] = {}
    settings['group_admins'][thread_id] = admin_ids
    write_settings(bot.uid, settings)
    return bot.uid in admin_ids

def get_allow_link_status(bot, thread_id):
    settings = read_settings(bot.uid)
    return settings.get('allow_link', {}).get(thread_id, False)

def get_user_name_by_id(bot, author_id):
    try:
        user_info = bot.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception:
        return "Unknown User"

polls_created = {}

def is_spamming(bot, author_id, thread_id):
    max_messages = 4 
    time_window = 2
    min_interval = 0.5
    message_log = load_message_log(bot.uid)
    key = f"{thread_id}_{author_id}"
    current_time = time.time()
    if key in message_log:
        user_data = message_log[key]
        last_message_time = user_data['last_message_time']
        message_times = user_data['message_times']
        if current_time - last_message_time < min_interval:
            recent_messages = [t for t in message_times if current_time - t <= min_interval]
            if len(recent_messages) >= 6:
                return True  
        message_times = [t for t in message_times if current_time - t <= time_window]
        message_times.append(current_time)
        message_log[key] = {
            'last_message_time': current_time,
            'message_times': message_times
        }
        if len(message_times) > max_messages:
            return True  
    else:
        message_log[key] = {
            'last_message_time': current_time,
            'message_times': [current_time]
        }
    save_message_log(bot.uid, message_log)
    return False 

user_message_count = {}
def check_spam(bot, author_id, thread_id, message_object, thread_type):
    settings = read_settings(bot.uid)
    spam_enabled = settings.get('spam_enabled', False)
    
    if isinstance(spam_enabled, bool):
        if spam_enabled:
            settings['spam_enabled'] = {thread_id: True}
        else:
            settings['spam_enabled'] = {}
        write_settings(bot.uid, settings)
    spam_enabled = settings['spam_enabled']

    if not spam_enabled.get(thread_id, False):
        return

    global user_message_count
    now = time.time()

    if thread_id not in user_message_count:
        user_message_count[thread_id] = {}

    if author_id not in user_message_count[thread_id]:
        user_message_count[thread_id][author_id] = []
    user_message_count[thread_id][author_id] = [
        timestamp for timestamp in user_message_count[thread_id][author_id] if now - timestamp <= 1
    ]
    user_message_count[thread_id][author_id].append(now)
    pending_users = bot.viewGroupPending(thread_id)
    if pending_users and pending_users.users:
        if len(user_message_count[thread_id][author_id]) >= 2:
            for user in pending_users.users:
                if user['uid'] == author_id:
                    bot.changeGroupSetting(groupId=thread_id, lockSendMsg=1)
                    bot.handleGroupPending(author_id, thread_id)
                    bot.blockUsersInGroup(author_id, thread_id)
                    bot.dislink(grid=thread_id)
                    time.sleep(10)
                    bot.changeGroupSetting(groupId=thread_id, lockSendMsg=0)
                    return

    if len(user_message_count[thread_id][author_id]) >= 5:
        bot.changeGroupSetting(groupId=thread_id, lockSendMsg=1)
        bot.blockUsersInGroup(author_id, thread_id)
        bot.kickUsersInGroup(author_id, thread_id)
        time.sleep(10)
        bot.changeGroupSetting(groupId=thread_id, lockSendMsg=0)
        bot.spam = True
        return

def safe_delete_message(bot, message_object, user_author_id, thread_id):
    def delete_message():
        max_retries = 20
        retries = 0
        while retries < max_retries:
            result = bot.deleteGroupMsg(message_object.msgId, user_author_id, message_object.cliMsgId, thread_id)
            try:
                ok = (not isinstance(result, dict)) or ("error_code" not in result)
            except Exception:
                ok = True
            if ok:
                print(f"➜ Xoa tin nhan lan {retries} thanh cong:", result)
                return
            retries += 1
            time.sleep(0.8)
        print(f"➜ That bai khi xoa tin nhan sau {retries} lan thu")
        return

    save_muted_message(bot.uid, user_author_id, thread_id, message_object.content)

    delete_thread = threading.Thread(target=delete_message)
    delete_thread.start()

def handle_check_profanity(bot, author_id, thread_id, message_object, thread_type, message):
    def send_check_profanity_response():
        settings = read_settings(bot.uid)
        admin_ids = settings.get('group_admins', {}).get(thread_id, [])
        # Fallback to live group info; only return if confirmed not admin
        try:
            live = bot.fetchGroupInfo(groupId=thread_id)
            live_admins = live.gridInfoMap[thread_id]['adminIds']
            is_admin_bot = (bot.uid in admin_ids) or (bot.uid in live_admins)
        except Exception:
            is_admin_bot = (bot.uid in admin_ids)
        if not is_admin_bot:
            return
                
        skip_bot = settings.get("skip_bot", [])
        if author_id in skip_bot:
            return  
        
        group_info = bot.fetchGroupInfo(groupId=thread_id)
        admin_ids = group_info.gridInfoMap[thread_id]['adminIds']
        creator_id = group_info.gridInfoMap[thread_id]['creatorId']
        
        if author_id in admin_ids or author_id == creator_id:
            return

        spam_thread = threading.Thread(target=check_spam, args=(bot, author_id, thread_id, message_object, thread_type))
        spam_thread.start()

        if (not get_allow_link_status(bot, thread_id)) and is_url_in_message(message_object):
            bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)
            return

        ### ANTI_PAY_CONTACT_ADDED ###
        try:
            txt_all = _extract_all_texts(message_object)
        except Exception:
            txt_all = ""
        # Anti-Payment (STK/Wallet) on any message/card
        if read_settings(bot.uid).get('anti_payment', {}).get(str(thread_id), True):
            if _has_bank_or_wallet_info(txt_all):
                safe_delete_message(bot, message_object, author_id, thread_id)
                return
        # Anti-Contact (Phone) on any message/card
        if read_settings(bot.uid).get('anti_contact', {}).get(str(thread_id), True):
            if _has_phone_or_contact_info(txt_all):
                safe_delete_message(bot, message_object, author_id, thread_id)
                return
        # QR/Image heuristics (when either anti payment/contact is ON)
        if getattr(message_object, 'msgType', '') in ('chat.image','chat.file','chat.video','chat.gif'):
            ap = read_settings(bot.uid).get('anti_payment', {}).get(str(thread_id), True)
            ac = read_settings(bot.uid).get('anti_contact', {}).get(str(thread_id), True)
            if ap or ac:
                if _looks_like_qr_image(message_object):
                    safe_delete_message(bot, message_object, author_id, thread_id)
                    return
        
        muted_users = settings.get('muted_users', [])
        for muted_user in muted_users:
            if muted_user['author_id'] == author_id and muted_user['thread_id'] == thread_id:
                if muted_user['muted_until'] == float('inf') or int(time.time()) < muted_user['muted_until']:
                    for _ in range(20):
                        safe_delete_message(bot, message_object, author_id, thread_id)
                        time.sleep(0)
                    return
        
        content = message_object.content
        message_text = ""
        if isinstance(content, str):
            message_text = str(content)
        elif isinstance(content, dict) and 'title' in content:
            message_text = str(content['title'])

        forbidden_words = settings.get('forbidden_words', [])
        violations = settings.get('violations', {})
        rules = settings.get("rules", {})
        current_time = int(time.time())

        word_rule = rules.get("word", {"threshold": 3, "duration": 30})
        threshold_word = word_rule["threshold"]
        duration_word = word_rule["duration"]

        for muted_user in muted_users[:]:
            if muted_user['author_id'] == author_id and muted_user['thread_id'] == thread_id:
                if muted_user['muted_until'] == float('inf') or current_time < muted_user['muted_until']:
                    bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)
                    return
                else:
                    muted_users.remove(muted_user)
                    settings['muted_users'] = muted_users
                    if author_id in violations and thread_id in violations[author_id]:
                        violations[author_id][thread_id]['profanity_count'] = 0
                    write_settings(bot.uid, settings)
                    response = "➜ 🎉 Ban đa đuoc phep phat ngon! Hay noi chuyen 💬 lich su nhe! 😊👍"
                    bot.replyMessage(Message(text=response), message_object, thread_id=thread_id, thread_type=thread_type)
                    return

        message_words = message_text.lower().split()
        detected_profanity = any(word in forbidden_words for word in message_words)

        if detected_profanity:
            user_violations = violations.setdefault(author_id, {}).setdefault(thread_id, {'profanity_count': 0, 'spam_count': 0, 'penalty_level': 0})
            user_violations['profanity_count'] += 1
            profanity_count = user_violations['profanity_count']
            penalty_level = user_violations['penalty_level']

            if penalty_level >= 2:
                response = f"➜ ⛔ Ban đa bi loai khoi nhom do vi pham nhieu lan\n➜ 💢 Noi dung vi pham: 🤬 '{message_text}'"
                bot.replyMessage(Message(text=response), message_object, thread_id=thread_id, thread_type=thread_type)
                bot.kickUsersInGroup(author_id, thread_id)
                bot.blockUsersInGroup(author_id, thread_id)
                
                muted_users = [user for user in muted_users if not (user['author_id'] == author_id and user['thread_id'] == thread_id)]
                settings['muted_users'] = muted_users

                if author_id in violations:
                    violations[author_id].pop(thread_id, None)
                    if not violations[author_id]:
                        violations.pop(author_id, None)

                write_settings(bot.uid, settings)
                return

            if profanity_count >= threshold_word:
                penalty_level += 1
                user_violations['penalty_level'] = penalty_level

                muted_users.append({
                    'author_id': author_id,
                    'thread_id': thread_id,
                    'reason': f'{message_text}',
                    'muted_until': current_time + 60 * duration_word
                })
                settings['muted_users'] = muted_users
                write_settings(bot.uid, settings)

                response = f"➜ 🚫 Ban đa vi pham {threshold_word} lan\n➜ 🤐 Ban đa bi khoa mom trong {duration_word} phut\n➜ 💢 Noi dung vi pham: 🤬 '{message_text}'"
                bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)
                bot.replyMessage(Message(text=response), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            elif profanity_count == threshold_word - 1:
                response = f"➜ ⚠️ Canh bao: Ban đa vi pham {profanity_count}/{threshold_word} lan\n➜ 🤐 Neu ban tiep tuc vi pham, ban se bi khoa mom trong {duration_word} phut\n➜ 💢 Noi dung vi pham: 🤬 '{message_text}'"
                bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)
                bot.replyMessage(Message(text=response), message_object, thread_id=thread_id, thread_type=thread_type)
            else:
                response = f"➜ ⚠️ Ban đa vi pham {profanity_count}/{threshold_word} lan!\n➜ 💢 Noi dung vi pham: 🤬 '{message_text}'"
                bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)
                bot.replyMessage(Message(text=response), message_object, thread_id=thread_id, thread_type=thread_type)

            write_settings(bot.uid, settings)

        doodle_enabled = settings.get('doodle_enabled', True)
        if message_object.msgType == 'chat.doodle' and not doodle_enabled:
            bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)

        voice_enabled = settings.get('voice_enabled', True)
        if message_object.msgType == 'chat.voice' and not voice_enabled:
            bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)

        chat_enabled = settings.get('chat_enabled', True)
        if not chat_enabled and (message_object.content is None or not isinstance(message_object.content, str)) and message_object.msgType != 'webchat':
            bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)

        image_enabled = settings.get('image_enabled', True)
        if message_object.msgType == 'chat.photo' and not image_enabled:
            bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)

        card_enabled = settings.get('card_enabled', True)
        if message_object.msgType == 'chat.recommended' and not card_enabled:
            bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)

        # anti payment/contact on cards
        try:
            if getattr(message_object, 'msgType', '') in ('chat.recommended','chat.card'):
                txt_all = _extract_all_texts(message_object)
                if settings.get('anti_payment', {}).get(str(thread_id), True) and _has_bank_or_wallet_info(txt_all):
                    safe_delete_message(bot, message_object, author_id, thread_id)
                    return
                if settings.get('anti_contact', {}).get(str(thread_id), True) and _has_phone_or_contact_info(txt_all):
                    safe_delete_message(bot, message_object, author_id, thread_id)
                    return
        except Exception:
            pass
        file_enabled = settings.get('file_enabled', True)
        if message_object.msgType == 'share.file' and not file_enabled:
            bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)

        sticker_enabled = settings.get('sticker_enabled', True)
        if message_object.msgType == 'chat.sticker' and not sticker_enabled:
            bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)

        gif_enabled = settings.get('gif_enabled', True)
        if message_object.msgType == 'chat.gif' and not gif_enabled:
            bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)

        video_enabled = settings.get('video_enabled', True)
        if message_object.msgType == 'chat.video.msg' and not video_enabled:
            bot.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)

        anti_poll_enabled = settings.get('anti_poll', True)
        if anti_poll_enabled and message_object.msgType == 'group.poll':
            if thread_id not in polls_created:
                polls_created[thread_id] = {}
            user_polls = polls_created[thread_id].get(author_id, [])
            user_polls.append(current_time)
            polls_created[thread_id][author_id] = user_polls
            user_polls = [poll_time for poll_time in user_polls if current_time - poll_time <= 300]
            if len(user_polls) > 3:
                response = "➜ ⛔ Ban đa bi kick vi spam tao qua nhieu cuoc khao sat trong nhom."
                bot.kickUsersInGroup(author_id, thread_id)
                bot.replyMessage(Message(text=response), message_object, thread_id=thread_id, thread_type=thread_type)
                return
            polls_created[thread_id][author_id] = user_polls

    thread = Thread(target=send_check_profanity_response)
    thread.start()

def print_muted_users_in_group(bot, thread_id):
    settings = read_settings(bot.uid)
    muted_users = settings.get("muted_users", [])
    current_time = int(time.time())
    muted_users_list = []

    for user in muted_users:
        if user['thread_id'] == thread_id:
            author_id = user['author_id']
            user_name = get_user_name_by_id(bot, author_id)
            muted_until = user['muted_until']
            reason = user.get('reason', 'Khong ro ly do')

            if muted_until == float('inf'):
                minutes_left = 'Vo han'
            else:
                remaining_time = muted_until - current_time
                if remaining_time > 0:
                    minutes_left = remaining_time // 60
                else:
                    continue

            muted_users_list.append({
                "author_id": author_id,
                "name": user_name,
                "minutes_left": minutes_left,
                "reason": reason
            })

    muted_users_list.sort(key=lambda x: float('inf') if x['minutes_left'] == 'Vo han' else x['minutes_left'])

    if muted_users_list:
        result = "➜ 🚫 Danh sach cac thanh vien nhom bi khoa mom: 🤐\n"
        result += "\n".join(
            f"{i}. 😷 {user['name']} - ⏳ {user['minutes_left']} phut - ⚠️ Ly do: {user['reason']}"
            for i, user in enumerate(muted_users_list, start=1)
        )
    else:
        result = (
            "➜ 🎉 Xin chuc mung!\n"
            "➜ Nhom khong co thanh vien nao tieu cuc ❤ 🌺 🌻 🌹 🌷 🌼\n"
            "➜ Hay tiep tuc phat huy nhe 🤗"
        )

    return result

def ban_users_permanently(bot, uids, thread_id):
    settings = read_settings(bot.uid)
    muted_users = settings.get('muted_users', [])

    for uid in uids:
        user_name = get_user_name_by_id(bot, uid)
        muted_users.append({
            'author_id': uid,
            'thread_id': thread_id,
            'name': user_name,
            'reason': 'Quan tri vien cam Vinh Vien',
            'muted_until': float('inf')
        })

    settings['muted_users'] = muted_users
    write_settings(bot.uid, settings)

    usernames = [get_user_name_by_id(bot, uid) for uid in uids]
    return f"➜ 😷 Nguoi dung {', '.join(usernames)} đa bi cam phat ngon vinh vien do quan tri vien!"

def print_blocked_users_in_group(bot, thread_id):
    settings = read_settings(bot.uid)
    blocked_users_group = settings.get("block_user_group", {})

    if thread_id not in blocked_users_group:
        return "➜ 🎉 Nhom nay khong co ai bi block! 🌟"

    blocked_users = blocked_users_group[thread_id].get('blocked_users', [])
    blocked_users_list = []

    for author_id in blocked_users:
        user_name = get_user_name_by_id(bot, author_id)
        blocked_users_list.append({
            "author_id": author_id,
            "name": user_name
        })

    blocked_users_list.sort(key=lambda x: x['name'])

    if blocked_users_list:
        result = "➜ 🚫 Danh sach cac thanh vien bi block khoi nhom: 🤧\n"
        result += "\n".join(f"{i}. 🙅 {user['name']} - {user['author_id']}" for i, user in enumerate(blocked_users_list, start=1))
    else:
        result = "➜ 🎉 Nhom khong co ai bi block khoi nhom! 🌼"

    return result

def add_users_to_ban_list(bot, author_ids, thread_id, reason):
    settings = read_settings(bot.uid)
    current_time = int(time.time())
    muted_users = settings.get("muted_users", [])
    violations = settings.get("violations", {})
    duration_minutes = settings.get("rules", {}).get("word", {}).get("duration", 30)

    response = ""
    for author_id in author_ids:
        user = bot.fetchUserInfo(author_id).changed_profiles[author_id].displayName

        if not any(entry["author_id"] == author_id and entry["thread_id"] == thread_id for entry in muted_users):
            muted_users.append({
                "author_id": author_id,
                "thread_id": thread_id,
                "reason": reason,
                "muted_until": current_time + 60 * duration_minutes
            })

        if author_id not in violations:
            violations[author_id] = {}

        if thread_id not in violations[author_id]:
            violations[author_id][thread_id] = {
                "profanity_count": 0,
                "spam_count": 0,
                "penalty_level": 0
            }

        violations[author_id][thread_id]["profanity_count"] += 1
        violations[author_id][thread_id]["penalty_level"] += 1

        response += f"➜ 🚫 {user} đa bi cam phat ngon trong {duration_minutes} ⏳ phut\n"

    settings['muted_users'] = muted_users
    settings['violations'] = violations
    write_settings(bot.uid, settings)
    return response

def remove_users_from_ban_list(bot, author_ids, thread_id):
    settings = read_settings(bot.uid)
    muted_users = settings.get("muted_users", [])
    violations = settings.get("violations", {})
    response = ""

    for author_id in author_ids:
        user = bot.fetchUserInfo(author_id).changed_profiles[author_id].displayName
        initial_count = len(muted_users)
        muted_users = [entry for entry in muted_users if not (entry["author_id"] == author_id and entry["thread_id"] == thread_id)]

        removed = False
        if author_id in violations:
            if thread_id in violations[author_id]:
                del violations[author_id][thread_id]
                if not violations[author_id]:
                    del violations[author_id]
                removed = True

        if initial_count != len(muted_users) or removed:
            response += f"➜ 🎉 Chuc mung {user} đa đuoc phep phat ngon 😤\n"
        else:
            response += f"➜ 😲 {user} khong co trong danh sach cam phat ngon 🤧\n"
    
    settings['muted_users'] = muted_users
    settings['violations'] = violations
    write_settings(bot.uid, settings)
    return response

def block_users_from_group(bot, author_ids, thread_id):
    response = ''
    block_user = []
    settings = read_settings(bot.uid)

    if "block_user_group" not in settings:
        settings["block_user_group"] = {}

    if thread_id not in settings["block_user_group"]:
        settings["block_user_group"][thread_id] = {'blocked_users': []}

    for author_id in author_ids:
        user = bot.fetchUserInfo(author_id).changed_profiles[author_id].displayName
        bot.blockUsersInGroup(author_id, thread_id)
        block_user.append(user)
        if author_id not in settings["block_user_group"][thread_id]['blocked_users']:
            settings["block_user_group"][thread_id]['blocked_users'].append(author_id)

    write_settings(bot.uid, settings)

    if block_user:
        blocked_users_str = ', '.join(block_user)
        response = f"➜ :v {blocked_users_str} đa bi chan khoi nhom 🤧"
    else:
        response = "➜ Khong ai bi chan khoi nhom 🤧"
    
    return response

def unblock_users_from_group(bot, author_ids, thread_id):
    response = ''
    unblocked_users = []
    settings = read_settings(bot.uid)

    if "block_user_group" in settings and thread_id in settings["block_user_group"]:
        blocked_users = settings["block_user_group"][thread_id]['blocked_users']
        
        for author_id in author_ids:
            user = bot.fetchUserInfo(author_id).changed_profiles[author_id].displayName
            if author_id in blocked_users:
                bot.unblockUsersInGroup(author_id, thread_id)
                unblocked_users.append(user)
                blocked_users.remove(author_id)

        if not blocked_users:
            del settings["block_user_group"][thread_id]
        
        write_settings(bot.uid, settings)

    if unblocked_users:
        unblocked_users_str = ', '.join(unblocked_users)
        response = f"➜ :v {unblocked_users_str} đa đuoc bo chan khoi nhom 🎉"
    else:
        response = "➜ Khong co ai bi chan trong nhom 🤧"
    
    return response

def kick_users_from_group(bot, uids, thread_id):
    response = ""
    for uid in uids:
        try:
            bot.kickUsersInGroup(uid, thread_id)
            bot.blockUsersInGroup(uid, thread_id)
            user_name = get_user_name_by_id(bot, uid)
            response += f"➜ 💪 Đa kick nguoi dung 😫 {user_name} khoi nhom thanh cong ✅\n"
        except Exception as e:
            user_name = get_user_name_by_id(bot, uid)
            response += f"➜ 😲 Khong the kick nguoi dung 😫 {user_name} khoi nhom 🤧\n"
    
    return response

def promote_to_admin(bot, mentioned_uids, thread_id):
    try:
        bot.addGroupAdmins(mentioned_uids, thread_id)
        response = ""
        for uid in mentioned_uids:
            response += f"🎉 Đa nang quyen admin cho nguoi dung 👤 {get_user_name_by_id(bot, uid)} trong nhom! ✅\n"
        return response
    except Exception as e:
        return f"❌ Đa xay ra loi khi nang quyen admin: {str(e)}"

def remove_adminn(bot, mentioned_uids, thread_id):
    try:
        bot.removeGroupAdmins(mentioned_uids, thread_id)
        response = ""
        for uid in mentioned_uids:
            response += f"❌ Đa xoa quyen admin cua nguoi dung 👤 {get_user_name_by_id(bot, uid)} trong nhom! ✅\n"
        return response
    except Exception as e:
        return f"❌ Đa xay ra loi khi xoa quyen admin: {str(e)}"

def extract_uids_from_mentions(message_object):
    uids = []
    if message_object.mentions:
        uids = [mention['uid'] for mention in message_object.mentions if 'uid' in mention]
    return uids

def add_admin(bot, author_id, mentioned_uids):
    settings = read_settings(bot.uid)
    admin_bot = settings.get("admin_bot", [])
    high_level_admins = settings.get("high_level_admins", [])
    response = ""

    if author_id != high_level_admins[0]:
        response = "❌Ban khong phai admin bot!"
    else:
        for uid in mentioned_uids:
            if uid in admin_bot:
                user_name = get_user_name_by_id(bot, uid) if get_user_name_by_id(bot, uid) else "Nguoi dung khong ton tai"
                response += f"➜ Nguoi dung 👑 {user_name} đa co trong danh sach Admin 🤖BOT 🤧\n"
            else:
                admin_bot.append(uid)
                user_name = get_user_name_by_id(bot, uid) if get_user_name_by_id(bot, uid) else "Nguoi dung khong ton tai"
                response += f"➜ Đa them 👑 {user_name} vao danh sach Admin 🤖BOT ✅\n"

    settings['admin_bot'] = admin_bot
    write_settings(bot.uid, settings)
    return response

def remove_admin(bot, author_id, mentioned_uids):
    settings = read_settings(bot.uid)
    admin_bot = settings.get("admin_bot", [])
    high_level_admins = settings.get("high_level_admins", [])
    response = ""

    if author_id != high_level_admins[0]:
        response = "❌Ban khong phai admin bot!"
    else:
        for uid in mentioned_uids:
            if uid in admin_bot:
                user_name = get_user_name_by_id(bot, uid) if get_user_name_by_id(bot, uid) else "Nguoi dung khong ton tai"
                admin_bot.remove(uid)
                response += f"➜ Đa xoa nguoi dung 👑 {user_name} khoi danh sach Admin 🤖BOT ✅\n"
            else:
                user_name = get_user_name_by_id(bot, uid) if get_user_name_by_id(bot, uid) else "Nguoi dung khong ton tai"
                response += f"➜ Nguoi dung 👑 {user_name} khong co trong danh sach Admin 🤖BOT 🤧\n"

    settings['admin_bot'] = admin_bot
    write_settings(bot.uid, settings)
    return response

def add_skip(bot, author_id, mentioned_uids):
    if not is_admin(bot, author_id):
        return "❌Ban khong phai admin bot!"
    
    settings = read_settings(bot.uid)
    admin_bot = settings.get("skip_bot", [])
    response = ""
    for uid in mentioned_uids:
        user_name = get_user_name_by_id(bot, uid)
        if uid not in admin_bot:
            admin_bot.append(uid)
            response += f"🚦Đa them nguoi dung 👑 {user_name} vao danh sach uu tien 🤖Bot ✅\n"
        else:
            response += f"🚦Nguoi dung 👑 {user_name} đa co trong danh sach uu tien 🤖Bot 🤧\n"
    settings['skip_bot'] = admin_bot
    write_settings(bot.uid, settings)
    return response

def remove_skip(bot, author_id, mentioned_uids):
    if not is_admin(bot, author_id):
        return "❌Ban khong phai admin bot!"
    
    settings = read_settings(bot.uid)
    admin_bot = settings.get("skip_bot", [])
    response = ""
    for uid in mentioned_uids:
        if uid in admin_bot:
            admin_bot.remove(uid)
            response += f"🚦Đa xoa nguoi dung 👑 {get_user_name_by_id(bot, uid)} khoi danh sach uu tien 🤖Bot ✅\n"
        else:
            response += f"🚦Nguoi dung 👑 {get_user_name_by_id(bot, uid)} khong co trong danh sach uu tien 🤖Bot 🤧\n"
    settings['skip_bot'] = admin_bot
    write_settings(bot.uid, settings)
    return response

def get_blocked_members(bot, thread_id, page=1, count=50):
    try:
        response = bot.get_blocked_members(thread_id, page, count)
        if not response.get("success"):
            return "❌ Khong the lay danh sach bi chan."
        
        blocked_data = response.get("blocked_members", {}).get("data", {}).get("blocked_members", [])
        if not blocked_data:
            return "📌 Khong co thanh vien nao bi chan trong nhom."

        result = "🚫 Danh sach thanh vien bi chan:\n"
        for member in blocked_data:
            result += f"🔹 ID: {member['id']}\n"
            result += f"🔹 Ten hien thi: {member['dName']}\n"
            result += "----------------------\n"
        return result
    except Exception as e:
        return f"❌ Đa xay ra loi khi lay danh sach bi chan: {str(e)}"

def get_group_admins(bot, thread_id):
    try:
        group_info = bot.fetchGroupInfo(groupId=thread_id)
        admin_ids = group_info.gridInfoMap[thread_id].get('adminIds', [])
        creator_id = group_info.gridInfoMap[thread_id].get('creatorId', None)

        if not admin_ids and not creator_id:
            return "📌 Khong co admin trong nhom."

        result = "🚀 Danh sach admin trong nhom:\n"
        if creator_id:
            creator_name = get_user_name_by_id(bot, creator_id)
            result += f"👑 {creator_name}\n"

        for admin_id in admin_ids:
            if admin_id != creator_id:
                user_name = get_user_name_by_id(bot, admin_id)
                result += f"🔹 {user_name}\n"
        return result
    except Exception as e:
        return f"❌ Đa xay ra loi khi lay danh sach admin: {str(e)}"

def remove_link(bot, thread_id):
    try:
        group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        bot.dislink(grid=thread_id)
        return f"🔗 Link nhom {group.name} đa đuoc xoa! ✅"
    except Exception as e:
        return f"❌ Đa xay ra loi khi xoa link nhom: {str(e)}"

def newlink(bot, thread_id):
    try:
        group_name = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id].name
        bot.newlink(grid=thread_id)
        return f"🔗 Link nhom {group_name} đa tao moi ✅"
    except Exception as e:
        return f"❌ Đa xay ra loi khi tao link nhom: {str(e)}"

def list_bots(bot, thread_id):
    settings = read_settings(bot.uid)
    response = " "
    group_info = bot.fetchGroupInfo(thread_id)
    group_name = group_info.gridInfoMap.get(thread_id, {}).get('name', 'N/A')
    bot_name = get_user_name_by_id(bot, bot.uid)
    response += f"👥 Nhom: {group_name}\n"
    response += f"🤖 Admin: {bot_name}\n"
    
    spam_enabled = settings.get('spam_enabled', {}).get(str(thread_id), True)
    anti_poll = settings.get('anti_poll', True)
    video_enabled = settings.get('video_enabled', True)
    card_enabled = settings.get('card_enabled', True)
    file_enabled = settings.get('file_enabled', True)
    image_enabled = settings.get('image_enabled', True)
    chat_enabled = settings.get('chat_enabled', True)
    voice_enabled = settings.get('voice_enabled', True)
    sticker_enabled = settings.get('sticker_enabled', True)
    gif_enabled = settings.get('gif_enabled', True)
    doodle_enabled = settings.get('doodle_enabled', True)
    allow_link = settings.get('allow_link', {}).get(str(thread_id), True)
    sos_status = settings.get('sos_status', True)
    
    status_icon = lambda enabled: "⭕️" if enabled else "✅"

    response += (
        f"{status_icon(spam_enabled)} Anti-Spam 💢\n"
        f"{status_icon(anti_poll)} Anti-Poll 👍\n"
        f"{status_icon(video_enabled)} Anti-Video ▶️\n"
        f"{status_icon(card_enabled)} Anti-Card 🛡️\n"
        f"{status_icon(file_enabled)} Anti-File 🗂️\n"
        f"{status_icon(image_enabled)} Anti-Photo 🏖"
        f"{status_icon(chat_enabled)} SafeMode 🩹\n"
        f"{status_icon(voice_enabled)} Anti-Voice 🔊\n"
        f"{status_icon(sticker_enabled)} Anti-Sticker 😊\n"
        f"{status_icon(gif_enabled)} Anti-Gif 🖼️\n"
        f"{status_icon(doodle_enabled)} Anti-Draw ✏️\n"
        f"{status_icon(sos_status)} SOS 🆘\n"
        f"{status_icon(allow_link)} Anti-Link 🔗\n"
    )
    return response

last_reload_time = {}

def reload_modules(self, message_object, thread_id: Optional[str], thread_type: Optional[str]):
    if thread_id is None or thread_type is None:
        raise ValueError("thread_id and thread_type must be provided")

    # Kiểm tra cooldown reload
    current_time = time.time()
    if thread_id in last_reload_time:
        time_diff = current_time - last_reload_time[thread_id]
        if time_diff < 30:  # Cooldown 30 giây cho mỗi nhóm
            remaining = int(30 - time_diff)
            self.sendMessage(
                Message(text=f"⏳ Vui lòng đợi {remaining}s nữa trước khi reload lại."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

    last_reload_time[thread_id] = current_time
    
    # Thông báo bắt đầu reload
    self.sendMessage(
        Message(text="🔄 Đang tiến hành reload modules..."),
        thread_id=thread_id,
        thread_type=thread_type
    )

    current_modules = [name for name in sys.modules.keys() if name.startswith("modules.")]
    
    modules_to_reload = [m for m in current_modules if m != "modules"]
    base_modules = ["modules."]
    reload_candidates = []
    
    for module in modules_to_reload:
        similarity = difflib.SequenceMatcher(None, module, "modules.").ratio()
        if similarity > 0.5:
            reload_candidates.append(module)
    
    for name in reload_candidates:
        if name in sys.modules:
            del sys.modules[name]
    
    for module_name in reload_candidates:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            self.replyMessage(
                Message(text=f"⚠️ Loi khi reload {module_name}: {str(e)}"), 
                message_object, 
                thread_id=thread_id, 
                thread_type=thread_type
            )
            continue
    
    pass  # replyMessage block removed
    pass  # replyMessage block removed
    pass  # replyMessage block removed
    pass  # replyMessage block removed
    pass  # replyMessage block removed
    pass  # replyMessage block removed

def get_dominant_color(image_path):
    try:
        if not os.path.exists(image_path):
            print(f"File anh khong ton tai: {image_path}")
            return (0, 0, 0)

        img = Image.open(image_path).convert("RGB")
        img = img.resize((150, 150), Image.Resampling.LANCZOS)
        pixels = img.getdata()

        if not pixels:
            print(f"Khong the lay du lieu pixel tu anh: {image_path}")
            return (0, 0, 0)

        r, g, b = 0, 0, 0
        for pixel in pixels:
            r += pixel[0]
            g += pixel[1]
            b += pixel[2]
        total = len(pixels)
        if total == 0:
            return (0, 0, 0)
        r, g, b = r // total, g // total, b // total
        return (r, g, b)

    except Exception as e:
        print(f"Loi khi phan tich mau noi bat: {e}")
        return (0, 0, 0)

def get_contrasting_color(base_color, alpha=255):
    r, g, b = base_color[:3]
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return (255, 255, 255, alpha) if luminance < 0.5 else (0, 0, 0, alpha)

def random_contrast_color(base_color):
    r, g, b, _ = base_color
    box_luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    if box_luminance > 0.5:
        r = random.randint(0, 50)
        g = random.randint(0, 50)
        b = random.randint(0, 50)
    else:
        r = random.randint(200, 255)
        g = random.randint(200, 255)
        b = random.randint(200, 255)
    
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    s = min(1.0, s + 0.9)
    v = min(1.0, v + 0.7)
    
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    
    text_luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    if abs(text_luminance - box_luminance) < 0.3:
        if box_luminance > 0.5:
            r, g, b = colorsys.hsv_to_rgb(h, s, min(1.0, v * 0.4))
        else:
            r, g, b = colorsys.hsv_to_rgb(h, s, min(1.0, v * 1.7))
    
    return (int(r * 255), int(g * 255), int(b * 255), 255)

def download_avatar(avatar_url, save_path=os.path.join(CACHE_PATH, "user_avatar.png")):
    if not avatar_url:
        return None
    try:
        resp = requests.get(avatar_url, stream=True, timeout=5)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            return save_path
    except Exception as e:
        print(f"❌ Loi tai avatar: {e}")
    return None
#
def generate_menu_image(bot, author_id, thread_id, thread_type):
    images = glob.glob(os.path.join(BACKGROUND_PATH, "*.jpg")) + \
             glob.glob(os.path.join(BACKGROUND_PATH, "*.png")) + \
             glob.glob(os.path.join(BACKGROUND_PATH, "*.jpeg"))
    if not images:
        print("❌ Khong tim thay anh trong thu muc background/")
        return None

    image_path = random.choice(images)

    try:
        size = (1920, 600)
        final_size = (1280, 380)
        bg_image = Image.open(image_path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=7))
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        dominant_color = get_dominant_color(image_path)
        r, g, b = dominant_color
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

        box_colors = [
            (255, 20, 147, 90),
            (128, 0, 128, 90),
            (0, 100, 0, 90),
            (0, 0, 139, 90),
            (184, 134, 11, 90),
            (138, 3, 3, 90),
            (0, 0, 0, 90)
        ]

        box_color = random.choice(box_colors)

        box_x1, box_y1 = 90, 60
        box_x2, box_y2 = size[0] - 90, size[1] - 60
        draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=75, fill=box_color)

        font_arial_path = "arial unicode ms.otf"
        font_emoji_path = "emoji.ttf"
        
        try:
            font_text_large = ImageFont.truetype(font_arial_path, size=76)
            font_text_big = ImageFont.truetype(font_arial_path, size=68)
            font_text_small = ImageFont.truetype(font_arial_path, size=64)
            font_text_bot = ImageFont.truetype(font_arial_path, size=58)
            font_time = ImageFont.truetype(font_arial_path, size=56)
            font_icon = ImageFont.truetype(font_emoji_path, size=60)
            font_icon_large = ImageFont.truetype(font_emoji_path, size=175)
            font_name = ImageFont.truetype(font_emoji_path, size=60)
        except Exception as e:
            print(f"❌ Loi tai font: {e}")
            font_text_large = ImageFont.load_default(size=76)
            font_text_big = ImageFont.load_default(size=68)
            font_text_small = ImageFont.load_default(size=64)
            font_text_bot = ImageFont.load_default(size=58)
            font_time = ImageFont.load_default(size=56)
            font_icon = ImageFont.load_default(size=60)
            font_icon_large = ImageFont.load_default(size=175)
            font_name = ImageFont.load_default(size=60)

        def draw_text_with_shadow(draw, position, text, font, fill, shadow_color=(0, 0, 0, 250), shadow_offset=(2, 2)):
            x, y = position
            draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font, fill=shadow_color)
            draw.text((x, y), text, font=font, fill=fill)

        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        vietnam_now = datetime.now(vietnam_tz)
        hour = vietnam_now.hour
        formatted_time = vietnam_now.strftime("%H:%M")
        time_icon = "🌤️" if 6 <= hour < 18 else "🌙"
        time_text = f" {formatted_time}"
        time_x = box_x2 - 250
        time_y = box_y1 + 10
        
        box_rgb = box_color[:3]
        box_luminance = (0.299 * box_rgb[0] + 0.587 * box_rgb[1] + 0.114 * box_rgb[2]) / 255
        last_lines_color = (255, 255, 255, 220) if box_luminance < 0.5 else (0, 0, 0, 220)

        time_color = last_lines_color

        if time_x >= 0 and time_y >= 0 and time_x < size[0] and time_y < size[1]:
            try:
                icon_x = time_x - 75
                icon_color = random_contrast_color(box_color)
                draw_text_with_shadow(draw, (icon_x, time_y - 8), time_icon, font_icon, icon_color)
                draw.text((time_x, time_y), time_text, font=font_time, fill=time_color)
            except Exception as e:
                print(f"❌ Loi ve thoi gian len anh: {e}")
                draw_text_with_shadow(draw, (time_x - 75, time_y - 8), "⏰", font_icon, (255, 255, 255, 255))
                draw.text((time_x, time_y), " ??;??", font=font_time, fill=time_color)

        user_info = bot.fetchUserInfo(author_id) if author_id else None
        user_name = "Unknown"
        if user_info and hasattr(user_info, 'changed_profiles') and author_id in user_info.changed_profiles:
            user = user_info.changed_profiles[author_id]
            user_name = getattr(user, 'name', None) or getattr(user, 'displayName', None) or f"ID_{author_id}"

        greeting_name = "Chu Nhan" if str(author_id) == is_admin else user_name

        emoji_colors = {
            "🎵": random_contrast_color(box_color),
            "😁": random_contrast_color(box_color),
            "🖤": random_contrast_color(box_color),
            "💞": random_contrast_color(box_color),
            "🤖": random_contrast_color(box_color),
            "💻": random_contrast_color(box_color),
            "📅": random_contrast_color(box_color),
            "🎧": random_contrast_color(box_color),
            "🌙": random_contrast_color(box_color),
            "🌤️": (200, 150, 50, 255)
        }

        text_lines = [
            f"Hi, {greeting_name}",
            f"💞 Chao mung đen voi menu 🤖 BOT",
            f"{bot.prefix}bot on/off: 🚀 Bat/Tat tinh nang",
            "😁 Bot San Sang Phuc 🖤",
            f"🤖Bot: {bot.me_name} 💻Version: {bot.version} 📅Update {bot.date_update}"
        ]

        color1 = random_contrast_color(box_color)
        color2 = random_contrast_color(box_color)
        while color1 == color2:
            color2 = random_contrast_color(box_color)
        text_colors = [
            color1,
            color2,
            last_lines_color,
            last_lines_color,
            last_lines_color
        ]

        text_fonts = [
            font_text_large,
            font_text_big,
            font_text_bot,
            font_text_bot,
            font_text_small
        ]

        line_spacing = 85
        start_y = box_y1 + 10

        avatar_url = user_info.changed_profiles[author_id].avatar if user_info and hasattr(user_info, 'changed_profiles') and author_id in user_info.changed_profiles else None
        avatar_path = download_avatar(avatar_url)
        if avatar_path and os.path.exists(avatar_path):
            avatar_size = 200
            try:
                avatar_img = Image.open(avatar_path).convert("RGBA").resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                mask = Image.new("L", (avatar_size, avatar_size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
                border_size = avatar_size + 10
                rainbow_border = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
                draw_border = ImageDraw.Draw(rainbow_border)
                steps = 360
                for i in range(steps):
                    h = i / steps
                    r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
                    draw_border.arc([(0, 0), (border_size-1, border_size-1)], start=i, end=i + (360 / steps), fill=(int(r * 255), int(g * 255), int(b * 255), 255), width=5)
                avatar_y = (box_y1 + box_y2 - avatar_size) // 2
                overlay.paste(rainbow_border, (box_x1 + 40, avatar_y), rainbow_border)
                overlay.paste(avatar_img, (box_x1 + 45, avatar_y + 5), mask)
            except Exception as e:
                print(f"❌ Loi xu ly avatar: {e}")
                draw.text((box_x1 + 60, (box_y1 + box_y2) // 2 - 140), "🐳", font=font_icon, fill=(0, 139, 139, 255))
        else:
            draw.text((box_x1 + 60, (box_y1 + box_y2) // 2 - 140), "🐳", font=font_icon, fill=(0, 139, 139, 255))

        current_line_idx = 0
        for i, line in enumerate(text_lines):
            if not line:
                current_line_idx += 1
                continue

            parts = []
            current_part = ""
            for char in line:
                if ord(char) > 0xFFFF:
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                    parts.append(char)
                else:
                    current_part += char
            if current_part:
                parts.append(current_part)

            total_width = 0
            part_widths = []
            current_font = font_text_bot if i == 4 else text_fonts[i]
            for part in parts:
                font_to_use = font_icon if any(ord(c) > 0xFFFF for c in part) else current_font
                width = draw.textbbox((0, 0), part, font=font_to_use)[2]
                part_widths.append(width)
                total_width += width

            max_width = box_x2 - box_x1 - 300
            if total_width > max_width:
                font_size = int(current_font.getbbox("A")[3] * max_width / total_width * 0.9)
                if font_size < 60:
                    font_size = 60
                try:
                    current_font = ImageFont.truetype(font_arial_path, size=font_size) if os.path.exists(font_arial_path) else ImageFont.load_default(size=font_size)
                except Exception as e:
                    print(f"❌ Loi đieu chinh font size: {e}")
                    current_font = ImageFont.load_default(size=font_size)
                total_width = 0
                part_widths = []
                for part in parts:
                    font_to_use = font_icon if any(ord(c) > 0xFFFF for c in part) else current_font
                    width = draw.textbbox((0, 0), part, font=font_to_use)[2]
                    part_widths.append(width)
                    total_width += width

            text_x = (box_x1 + box_x2 - total_width) // 2
            text_y = start_y + current_line_idx * line_spacing + (current_font.getbbox("A")[3] // 2)

            current_x = text_x
            for part, width in zip(parts, part_widths):
                if any(ord(c) > 0xFFFF for c in part):
                    emoji_color = emoji_colors.get(part, random_contrast_color(box_color))
                    draw_text_with_shadow(draw, (current_x, text_y), part, font_icon, emoji_color)
                    if part == "🤖" and i == 4:
                        draw_text_with_shadow(draw, (current_x, text_y - 5), part, font_icon, emoji_color)
                else:
                    if i < 2:
                        draw_text_with_shadow(draw, (current_x, text_y), part, current_font, text_colors[i])
                    else:
                        draw.text((current_x, text_y), part, font=current_font, fill=text_colors[i])
                current_x += width
            current_line_idx += 1

        right_icons = ["🤖"]
        right_icon = random.choice(right_icons)
        icon_right_x = box_x2 - 225
        icon_right_y = (box_y1 + box_y2 - 180) // 2
        draw_text_with_shadow(draw, (icon_right_x, icon_right_y), right_icon, font_icon_large, emoji_colors.get(right_icon, (80, 80, 80, 255)))

        final_image = Image.alpha_composite(bg_image, overlay)
        final_image = final_image.resize(final_size, Image.Resampling.LANCZOS)
        os.makedirs(os.path.dirname(OUTPUT_IMAGE_PATH), exist_ok=True)
        final_image.save(OUTPUT_IMAGE_PATH, "PNG", quality=95)
        print(f"✅ Anh menu đa đuoc luu: {OUTPUT_IMAGE_PATH}")
        return OUTPUT_IMAGE_PATH

    except Exception as e:
        print(f"❌ Loi xu ly anh menu: {e}")
        return None

def handle_bot_command(bot, message_object, author_id, thread_id, thread_type, command):
    def send_bot_response():
        settings = read_settings(bot.uid)
        allowed_thread_ids = settings.get('allowed_thread_ids', [])
        admin_bot = settings.get("admin_bot", [])
        banned_users = settings.get("banned_users", [])
        chat_user = (thread_type == ThreadType.USER)

        if author_id in banned_users:
            return

        if not (author_id in admin_bot or thread_id in allowed_thread_ids or chat_user):
            return
        try:

            spam_enabled = settings.get('spam_enabled', {}).get(str(thread_id), True)
            anti_poll = settings.get('anti_poll', True)
            video_enabled = settings.get('video_enabled', True)
            card_enabled = settings.get('card_enabled', True)
            file_enabled = settings.get('file_enabled', True)
            image_enabled = settings.get('image_enabled', True)
            chat_enabled = settings.get('chat_enabled', True)
            voice_enabled = settings.get('voice_enabled', True)
            sticker_enabled = settings.get('sticker_enabled', True)
            gif_enabled = settings.get('gif_enabled', True)
            doodle_enabled = settings.get('doodle_enabled', True)
            allow_link = settings.get('allow_link', {}).get(str(thread_id), True)
            sos_status = settings.get('sos_status', True)

            status_icon = lambda enabled: "✅" if enabled else "⭕️"

            f"{status_icon(spam_enabled)} Anti-Spam 💢\n"
            f"{status_icon(anti_poll)} Anti-Poll 👍\n"
            f"{status_icon(video_enabled)} Anti-Video ▶️\n"
            f"{status_icon(card_enabled)} Anti-Card 🛡️\n"
            f"{status_icon(file_enabled)}Anti-File 🗂️\n"
            f"{status_icon(image_enabled)} Anti-Photo 🏖\n"
            f"{status_icon(chat_enabled)} SafeMode 🩹\n"
            f"{status_icon(voice_enabled)} Anti-Voice 🔊\n"
            f"{status_icon(sticker_enabled)} Anti-Sticker 😊\n"
            f"{status_icon(gif_enabled)} Anti-Gif 🖼️\n"
            f"{status_icon(doodle_enabled)} Anti-Draw ✏️\n"
            f"{status_icon(sos_status)}SOS 🆘\n"
            f"{status_icon(allow_link)} Anti-Link 🔗\n"



            
# NON-COMMAND moderation
            try:
                prefix = getattr(bot, 'prefix', '.')
                try:
                    content_text = get_content_message(message_object)
                except Exception:
                    content_text = ''
                if not str(content_text).strip().startswith(prefix):
                    # Anti-Link (on = cấm link)
                    if (not get_allow_link_status(bot, thread_id)) and is_url_in_message(message_object):
                        safe_delete_message(bot, message_object, author_id, thread_id)
                        return
                    # Anti-Payment (STK/Wallet)
                    if read_settings(bot.uid).get('anti_payment', {}).get(str(thread_id), True) and _has_bank_or_wallet_info(content_text):
                        safe_delete_message(bot, message_object, author_id, thread_id)
                        return
                    # Anti-Contact (SĐT)
                    if read_settings(bot.uid).get('anti_contact', {}).get(str(thread_id), True) and _has_phone_or_contact_info(content_text):
                        safe_delete_message(bot, message_object, author_id, thread_id)
                        return
                    # QR/Image heuristic
                    try:
                        if _looks_like_qr_image(message_object) and (read_settings(bot.uid).get('anti_payment', {}).get(str(thread_id), True) or read_settings(bot.uid).get('anti_contact', {}).get(str(thread_id), True)):
                            safe_delete_message(bot, message_object, author_id, thread_id)
                            return
                    except Exception:
                        pass
                    return
            except Exception:
                pass
                return


            parts = command.split()
            response = ""
            if len(parts) == 1:
                response = (
                        f"{get_user_name_by_id(bot, author_id)}\n"
                        f"➜ {bot.prefix}bot info/policy: ♨️ Thong tin/Tac gia/Thoi gian/Chinh sach BOT\n"
                        f"➜ {bot.prefix}bot setup on/off: ⚙️ Bat/Tat Noi quy BOT (OA)\n"
                        f"➜ {bot.prefix}bot anti on/off/setup: 🚦Bat/Tat Anti (OA)\n"
                        f"➜ {bot.prefix}bot newlink/dislink: 🔗 Tao/huy link nhom (OA)\n"
                        f"➜ {bot.prefix}bot fix: 🔧 Sua loi treo lenh(OA)\n"
                        f"➜ {bot.prefix}bot safemode on/off: 🩹 Che đo an toan text (OA)\n"
                        f"➜ {bot.prefix}bot on/off: ⚙️ Bat/Tat BOT (OA)\n"
                        f"➜ {bot.prefix}bot admin add/remove/list: 👑 Them/xoa Admin 🤖BOT\n"
                        f"➜ {bot.prefix}bot skip add/remove/list: 👑 Them/xoa uu tien 🤖BOT (OA)\n"
                        f"➜ {bot.prefix}bot leader add/remove/list: 👑 Them/xoa Truong/Pho (OA)\n"
                        f"➜ {bot.prefix}autosend on/off: ✉️ Gui tin nhan(OA)\n"
                        f"➜ {bot.prefix}bot noiquy: 💢 Noi quy box\n"
                        f"➜ {bot.prefix}bot ban/vv/unban list: 😷 Khoa user\n"
                        f"➜ {bot.prefix}bot kick: 💪 Kick user (OA)\n"
                        f"➜ {bot.prefix}bot sos: 🆘 Khoa box (OA)\n"
                        f"➜ {bot.prefix}bot block/unblock/list: 💪 Chan nguoi dung (OA)\n"
                        f"➜ {bot.prefix}bot link on/off: 🔗 Cam link (OA)\n"
                        f"➜ {bot.prefix}bot file on/off: 🗂️ Cam file (OA)\n"
                        f"➜ {bot.prefix}bot video on/off: ▶️ Cam video (OA)\n"
                        f"➜ {bot.prefix}bot sticker on/off: 😊 Cam sticker (OA)\n"
                        f"➜ {bot.prefix}bot gif on/off: 🖼️ Cam Gif (OA)\n"
                        f"➜ {bot.prefix}bot voice on/off: 🔊 Cam voice (OA)\n"
                        f"➜ {bot.prefix}bot photo on/off: 🏖 Cam anh (OA)\n"
                        f"➜ {bot.prefix}bot draw on/off: ✏️ Cam ve hinh (OA)\n"
                        f"➜ {bot.prefix}bot anti poll on/off: 👍 Cam binh chon (OA)\n"
                        f"➜ {bot.prefix}bot rule word [n] [m]: 📖 Cam n lan vi pham, phat m phut (OA)\n"
                        f"➜ {bot.prefix}bot word add/remove/list [tu cam]: ✍️ Them/xoa tu cam (OA)\n"
                        f" ➜ {bot.prefix}bot welcome on/off: 🎊 Welcome (OA)\n"
                        f"➜ {bot.prefix}bot card on/off: 🛡️ Cam Card (OA)\n"
                        f"🤖 BOT {get_user_name_by_id(bot, bot.uid)} luon san sang phuc vu ban! 🌸\n"
                    )
            else:
                action = parts[1].lower()
                
                if action == 'on':
                    if not admin_cao(bot, author_id):
                        response = "❌Ban khong phai admin bot!"
                    elif thread_type != ThreadType.GROUP:
                        response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                    else:
                        response = bot_on_group(bot, thread_id)
                elif action == 'off':
                    if not is_admin(bot, author_id):
                        response = "❌Ban khong phai admin bot!"
                    elif thread_type != ThreadType.GROUP:
                        response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                    else:
                        response = bot_off_group(bot, thread_id)

                elif action == 'fix':
                    response = reload_modules(bot, message_object, thread_id, thread_type)

                elif action == 'autostk':
                    if not is_admin(bot, author_id):
                        response = "❌ Ban khong phai admin bot!"
                    else:
                        sub_action = parts[2].lower() if len(parts) > 2 else None
                        if sub_action == 'start':
                            if thread_id in autostk_loops and not autostk_loops[thread_id].is_set():
                                response = "Tính năng auto sticker liên tục đã được bật từ trước."
                            else:
                                stop_event = threading.Event()
                                autostk_loops[thread_id] = stop_event
                                loop_thread = threading.Thread(target=sticker_loop, args=(bot, thread_id, thread_type))
                                loop_thread.daemon = True
                                loop_thread.start()
                                response = "✅ Đã BẬT tính năng auto sticker liên tục."
                        elif sub_action == 'stop':
                            if thread_id in autostk_loops and not autostk_loops[thread_id].is_set():
                                autostk_loops[thread_id].set()
                                response = "⏹️ Đã TẮT tính năng auto sticker liên tục."
                            else:
                                response = "Tính năng này chưa được bật."
                        else:
                            response = f"Cú pháp không hợp lệ. Sử dụng:\n{bot.prefix}bot autostk start\n{bot.prefix}bot autostk stop"
                # =================== BỔ SUNG KHỐI LỆNH BỊ THIẾU ===================
                elif action == 'autosend':
                    if not is_admin(bot, author_id):
                        response = "❌ Bạn không phải admin bot!"
                    elif len(parts) < 3:
                        response = f"➜ Vui lòng nhập [on/off] sau lệnh: {bot.prefix}bot autosend 🤧"
                    else:
                        sub_action = parts[2].lower()
                        if sub_action == 'on':
                            response = handle_autosend_on(bot, thread_id, bot.prefix)
                            # Bắt đầu luồng nếu nó chưa chạy
                            if not hasattr(bot, 'autosend_thread_started') or not bot.autosend_thread_started:
                                bot.autosend_thread = threading.Thread(target=autosend_task, args=(bot,), daemon=True)
                                bot.autosend_thread.start()
                                bot.autosend_thread_started = True
                        elif sub_action == 'off':
                            response = handle_autosend_off(bot, thread_id, bot.prefix)
                        else:
                            response = "➜ Lệnh không hợp lệ. Vui lòng chọn 'on' hoặc 'off'."
                # =====================================================================

                elif action == 'policy':
                    if thread_type != ThreadType.GROUP:
                        response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                    else:
                        response = list_bots(bot, thread_id)

                elif action == 'removelink':
                    if not is_admin(bot, author_id):
                        response = "❌Ban khong phai admin bot!"
                    else:
                        response = remove_link(bot, thread_id)
                elif action == 'newlink':
                    if not is_admin(bot, author_id):
                        response = "❌Ban khong phai admin bot!"
                    else:
                        response = newlink(bot, thread_id)
                elif action == 'skip':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [add/remove/list] sau lenh: {bot.prefix}bot skip 🤧\n➜ Vi du: {bot.prefix}bot skip add @Heoder ✅"
                    else:
                        sub_action = parts[2].lower()
                        if sub_action == 'add':
                            if len(parts) < 4:
                                response = f"➜ Vui long @tag ten nguoi dung sau lenh: {bot.prefix}bot skip add ??\n➜ Vi du: {bot.prefix}bot skip add @Heoder ✅"
                            else:
                                mentioned_uids = extract_uids_from_mentions(message_object)
                                settings = read_settings(bot.uid)
                                
                                if not is_admin(bot, author_id):
                                    response = "❌Ban khong phai admin bot!"
                                else:
                                    response = add_skip(bot, author_id, mentioned_uids)
                        elif sub_action == 'remove':
                            if len(parts) < 4:
                                response = f"➜ Vui long @tag ten nguoi dung sau lenh: {bot.prefix}bot skip remove 🤧\n➜ Vi du: {bot.prefix}bot skip remove @Heoder ✅"
                            else:
                                mentioned_uids = extract_uids_from_mentions(message_object)
                                settings = read_settings(bot.uid)
                                
                                if not is_admin(bot, author_id):
                                    response = "❌Ban khong phai admin bot!"
                                else:
                                    response = remove_skip(bot, author_id, mentioned_uids)
                        elif sub_action == 'list':
                            settings = read_settings(bot.uid)
                            skip_list = settings.get("skip_bot", [])
                            if skip_list:
                                response = "🚦 Danh sach nguoi dung đuoc uu tien: \n"
                                for uid in skip_list:
                                    response += f"👑 {get_user_name_by_id(bot, uid)} - {uid}\n"
                            else:
                                response = "🚦 Chua co nguoi dung nao trong danh sach uu tien 🤖"
                elif action == 'leader':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [add/remove] sau lenh: {bot.prefix}bot leader 🤧\n➜ Vi du: {bot.prefix}bot leader add @Hero ✅"
                    else:
                        sub_action = parts[2].lower()
                        
                      
                        if sub_action == 'add':
                            if len(parts) < 4:
                                response = f"➜ Vui long @tag ten nguoi dung sau lenh: {bot.prefix}bot leader add 🤧\n➜ Vi du: {bot.prefix}bot leader add @Hero ✅"
                            else:
                                mentioned_uids = extract_uids_from_mentions(message_object)
                                
                                if not is_admin(bot, author_id):
                                    response = "❌Ban khong phai admin bot!"
                                else:
                                    response = promote_to_admin(bot, mentioned_uids, thread_id)
                        elif sub_action == 'remove':
                            if len(parts) < 4:
                                response = f"➜ Vui long @tag ten nguoi dung sau lenh: {bot.prefix}bot admin remove 🤧\n➜ Vi du: {bot.prefix}bot admin remove @Hero ✅"
                            else:
                                mentioned_uids = extract_uids_from_mentions(message_object)
                                
                                if not is_admin(bot, author_id):
                                    response = "❌Ban khong phai admin bot!"
                                else:
                                    response = remove_adminn(bot, mentioned_uids, thread_id)
                        
                        elif sub_action == 'list':
                            
                            response = get_group_admins(bot, thread_id)

                        
                        else:
                            response = "➜ Lenh khong hop le. Vui long chon tu [add/remove/list]."
        
                elif action == 'anti':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [poll on/off] sau lenh: {bot.prefix}bot anti 🤧\n➜ Vi du: {bot.prefix}bot anti poll on ✅"
                    else:
                        sub_action = parts[2].lower()
                        if sub_action == 'poll':
                            if len(parts) < 4:
                                response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot anti poll 🤧\n➜ Vi du: {bot.prefix}bot anti poll on ✅"
                            else:
                                sub_sub_action = parts[3].lower()
                                if not is_admin(bot, author_id):
                                    response = "❌Ban khong phai admin bot!"
                                elif sub_sub_action == 'off':  
                                    settings = read_settings(bot.uid)
                                    settings["anti_poll"] = True
                                    write_settings(bot.uid, settings)
                                    response = f"{status_icon(anti_poll)} Anti-Poll 👍\n"
                                elif sub_sub_action == 'on':  
                                    settings = read_settings(bot.uid)
                                    settings["anti_poll"] = False
                                    write_settings(bot.uid, settings)
                                    response = f"{status_icon(anti_poll)} Anti-Poll 👍\n"
                                else:
                                    response = "➜ Lenh khong hop le. Vui long chon 'on' hoac 'off' sau lenh anti poll 🤧"
                                
                elif action == 'safemode':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot chat 🤧\n➜ Vi du: {bot.prefix}bot chat on hoac {bot.prefix}bot chat off ✅"
                    else:
                        chat_action = parts[2].lower()
                        settings = read_settings(bot.uid)

                        if chat_action == 'off':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['chat_enabled'] = True  
                                response = f"{status_icon(chat_enabled)} SafeMode 🩹\n"
                        elif chat_action == 'on':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['chat_enabled'] = False  
                                response = f"{status_icon(chat_enabled)} SafeMode 🩹\n"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot chat {chat_action} khong hop le 🤧"
                        
                        write_settings(bot.uid, settings)  

                elif action == 'sticker':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot sticker 🤧\n➜ Vi du: {bot.prefix}bot sticker on hoac {bot.prefix}bot sticker off ✅"
                    else:
                        sticker_action = parts[2].lower()
                        settings = read_settings(bot.uid)

                        if sticker_action == 'off':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['sticker_enabled'] = True  
                                response = f"{status_icon(sticker_enabled)} Anti-Sticker 😊\n"
                                
                        elif sticker_action == 'on':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['sticker_enabled'] = False  
                                response = f"{status_icon(sticker_enabled)} Anti-Sticker 😊\n"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot sticker {sticker_action} khong hop le 🤧"
                        
                        write_settings(bot.uid, settings)

                elif action == 'draw':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot draw 🤧\n➜ Vi du: {bot.prefix}bot draw on hoac {bot.prefix}bot draw off ✅"
                    else:
                        draw_action = parts[2].lower()
                        settings = read_settings(bot.uid)

                        if draw_action == 'off':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['doodle_enabled'] = True  
                                response = f"{status_icon(doodle_enabled)} Anti-Draw ✏️\n"
                        elif draw_action == 'on':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['doodle_enabled'] = False  
                                response = f"{status_icon(doodle_enabled)} Anti-Draw ✏️\n"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot draw {draw_action} khong hop le 🤧"
                        
                        write_settings(bot.uid, settings)

                elif action == 'gif':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot gif 🤧\n➜ Vi du: {bot.prefix}bot gif on hoac {bot.prefix}bot gif off ✅"
                    else:
                        gif_action = parts[2].lower()
                        settings = read_settings(bot.uid)

                        if gif_action == 'off':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['gif_enabled'] = True  
                                response = f"{status_icon(gif_enabled)} Anti-Gif 🖼️\n"
                        elif gif_action == 'on':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['gif_enabled'] = False  
                                response = f"{status_icon(gif_enabled)} Anti-Gif 🖼️\n"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot gif {gif_action} khong hop le 🤧"
                        
                        write_settings(bot.uid, settings)

                elif action == 'video':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot video 🤧\n➜ Vi du: {bot.prefix}bot video on hoac {bot.prefix}bot video off ✅"
                    else:
                        video_action = parts[2].lower()
                        settings = read_settings(bot.uid)

                        if video_action == 'off':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['video_enabled'] = True  
                                response = f"{status_icon(video_enabled)} Anti-Video ▶️\n"
                        elif video_action == 'on':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['video_enabled'] = False  
                                response = f"{status_icon(video_enabled)} Anti-Video ▶️\n"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot video {video_action} khong hop le 🤧"
                        
                        write_settings(bot.uid, settings)

                elif action == 'photo':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot image 🤧\n➜ Vi du: {bot.prefix}bot image on hoac {bot.prefix}bot image off ✅"
                    else:
                        image_action = parts[2].lower()
                        settings = read_settings(bot.uid)

                        if image_action == 'off':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['image_enabled'] = True  
                                response = f"{status_icon(image_enabled)} Anti-Photo 🏖\n"
                        elif image_action == 'on':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['image_enabled'] = False  
                                response = f"{status_icon(image_enabled)} Anti-Photo 🏖\n"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot video {image_action} khong hop le 🤧"
                        
                        write_settings(bot.uid, settings)

                elif action == 'voice':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot voice 🤧\n➜ Vi du: {bot.prefix}bot voice on hoac {bot.prefix}bot voice off ✅"
                    else:
                        voice_action = parts[2].lower()
                        settings = read_settings(bot.uid)

                        if voice_action == 'off':
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['voice_enabled'] = True  
                                response = f"{status_icon(voice_enabled)} Anti-Voice 🔊\n"
                        elif voice_action == 'on':
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['voice_enabled'] = False  
                                response = f"{status_icon(voice_enabled)} Anti-Voice 🔊\n"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot video {voice_action} khong hop le 🤧"
                        
                        write_settings(bot.uid, settings)

                elif action == 'file':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot file 🤧\n➜ Vi du: {bot.prefix}bot file on hoac {bot.prefix}bot file off ✅"
                    else:
                        file_action = parts[2].lower()
                        settings = read_settings(bot.uid)

                        if file_action == 'off':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['file_enabled'] = True  
                                response = f"{status_icon(file_enabled)} Anti-File 🗂️\n"
                                
                        elif file_action == 'on':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['file_enabled'] = False  
                                response = f"{status_icon(file_enabled)} Anti-File 🗂️\n"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot video {file_action} khong hop le 🤧"
                        
                        write_settings(bot.uid, settings)

                elif action == 'card':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot card 🤧\n➜ Vi du: {bot.prefix}bot card on hoac {bot.prefix}bot card off ✅"
                    else:
                        card_action = parts[2].lower()
                        settings = read_settings(bot.uid)

                        if card_action == 'on':
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['card_enabled'] = False  
                                response = f"{status_icon(card_enabled)} Anti-Card 🛡️\n"
                        elif card_action == 'off':  
                            if not is_admin(bot, author_id):  
                                response = "❌Ban khong phai admin bot!"
                            else:
                                settings['card_enabled'] = True  
                                response = f"{status_icon(card_enabled)} Anti-Card 🛡️\n"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot card {card_action} khong hop le 🤧"
                        
                        write_settings(bot.uid, settings)

                elif action == 'welcome':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot welcome 🤧\n➜ Vi du: {bot.prefix}bot welcome on hoac {bot.prefix}bot welcome off ✅"
                    else:
                        settings = read_settings(bot.uid)
                        setup_action = parts[2].lower()
                        if setup_action == 'on':
                            if not is_admin(bot, author_id):
                                response = "❌Ban khong phai admin bot!"
                            elif thread_type != ThreadType.GROUP:
                                response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                            else:
                                response = handle_welcome_on(bot, thread_id)
                        elif setup_action == 'off':
                            if not is_admin(bot, author_id):
                                response = "❌Ban khong phai admin bot!"
                            elif thread_type != ThreadType.GROUP:
                                response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                            else:
                                response = handle_welcome_off(bot, thread_id)
                        else:
                            response = f"➜ Lenh {bot.prefix}bot welcome {setup_action} khong đuoc ho tro 🤧"
                
                elif action == 'spam':
                    if not is_admin(bot, author_id):
                        response = "❌Ban khong phai admin bot!"
                    elif len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot spam 🤧\n➜ Vi du: {bot.prefix}bot spam on hoac {bot.prefix}bot spam off ✅"
                    else:
                        spam_action = parts[2].lower()
                        settings = read_settings(bot.uid)

                        if 'spam_enabled' not in settings:
                            settings['spam_enabled'] = {}

                        if spam_action == 'on':
                            settings['spam_enabled'][thread_id] = True  
                            response = f"{status_icon(spam_enabled)} Anti-Spam 💢\n"
                        elif spam_action == 'off':
                            settings['spam_enabled'][thread_id] = False  
                            response = f"{status_icon(spam_enabled)} Anti-Spam 💢\n"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot spam {spam_action} khong hop le 🤧"
                        
                        write_settings(bot.uid, settings)
                elif action == 'info':
                    response = (
    "╭────────────────────────────╮\n"
    f"│ 🤖 Bot phien ban: {bot.version}\n"
    f"│ 📅 Cap nhat lan cuoi: {bot.date_update}\n"
    f"│ 👨‍💻 Nha phat trien: {bot.me_name}\n"
    f"│ 📖 Huong dan: Dung lenh [{bot.prefix}bot/help]\n"
    "│ ⏳ Thoi gian phan hoi: 1 giay\n"
    "│ ⚡ Tinh nang noi bat:\n"
    "│  ├➜ 🛡️ Anti-spam,anti-radi, chan link, tu cam\n"
    "│  ├➜ 🤬 Kiem soat noi dung chui the\n"
    "│  ├➜ 🚫 Tu đong duyet & chan spammer\n"
    "│  ├➜ 🔊 Quan ly giong noi & sticker\n"
    "│  ├➜ 🖼️ Ho tro hinh anh, GIF, video\n"
    "│  ├➜ 🗳️ Kiem soat cuoc khao sat\n"
    "│  ├➜ 🔗 Bao ve nhom khoi link đoc hai\n"
    "│  └➜ 🔍 Kiem tra & phan tich tin nhan\n"
    "╰────────────────────────────╯"
)

                elif action == 'admin':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [list/add/remove] sau lenh: {bot.prefix}bot admin 🤧\n➜ Vi du: {bot.prefix}bot admin list hoac {bot.prefix}bot admin add @Heoder hoac {bot.prefix}bot admin remove @Heoder ✅"
                    else:
                        settings = read_settings(bot.uid)
                        admin_bot = settings.get("admin_bot", [])  
                        sub_action = parts[2].lower()
                        if sub_action == 'add':
                            if len(parts) < 4:
                                response = f"➜ Vui long @tag ten nguoi dung sau lenh: {bot.prefix}bot admin add 🤧\n➜ Vi du: {bot.prefix}bot admin add @Heoder ✅"
                            else:
                                if not admin_cao(bot, author_id):
                                    response = "❌Ban khong phai admin bot!"
                                else:
                                    mentioned_uids = extract_uids_from_mentions(message_object)
                                    response = add_admin(bot, author_id, mentioned_uids)
                        elif sub_action == 'remove':
                            if len(parts) < 4:
                                response = f"➜ Vui long @tag ten nguoi dung sau lenh: {bot.prefix}bot admin remove 🤧\n➜ Vi du: {bot.prefix}bot admin remove @Heoder ✅"
                            else:
                                if not admin_cao(bot, author_id):
                                    response = "❌Ban khong phai admin bot!"
                                else:
                                    mentioned_uids = extract_uids_from_mentions(message_object)
                                    response = remove_admin(bot, author_id, mentioned_uids)
                        elif sub_action == 'list':
                            if admin_bot:
                                response = f"🚦🧑‍💻 Danh sach Admin 🤖BOT {get_user_name_by_id(bot, bot.uid)}\n"
                                for idx, uid in enumerate(admin_bot, start=1):
                                    response += f"➜   {idx}. {get_user_name_by_id(bot, uid)} - {uid}\n"
                            else:
                                response = "➜ Khong co Admin BOT nao trong danh sach 🤧"
                        else:
                            response = f"➜ Lenh {bot.prefix}bot admin {sub_action} khong đuoc ho tro 🤧"


                elif action == 'setup':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot setup 🤧\n➜ Vi du: {bot.prefix}bot setup on hoac {bot.prefix}bot setup off ✅"
                    else:
                        setup_action = parts[2].lower()
                        if setup_action == 'on':
                            if not is_admin(bot, author_id):
                                response = "❌Ban khong phai admin bot!"
                            elif thread_type != ThreadType.GROUP:
                                response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                            else:
                                response = setup_bot_on(bot, thread_id)
                        elif setup_action == 'off':
                            if not is_admin(bot, author_id):
                                response = "❌Ban khong phai admin bot!"
                            elif thread_type != ThreadType.GROUP:
                                response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                            else:
                                response = setup_bot_off(bot,thread_id)
                        else:
                            response = f"➜ Lenh {bot.prefix}bot setup {setup_action} khong đuoc ho tro 🤧"
                elif action == 'link':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [on/off] sau lenh: {bot.prefix}bot link 🤧\n➜ Vi du: {bot.prefix}bot link on hoac {bot.prefix}bot link off ✅"
                    else:
                        link_action = parts[2].lower()
                        if not is_admin(bot, author_id):
                            response = "❌Ban khong phai admin bot!"
                        elif thread_type != ThreadType.GROUP:
                            response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                        else:
                            settings = read_settings(bot.uid)

                            if 'allow_link' not in settings:
                                settings['allow_link'] = {}

                            
                            if link_action == 'on':
                                settings['allow_link'][thread_id] = True
                                response = f"{status_icon(allow_link)} Anti-Link 🔗\n"
                            elif link_action == 'off':
                                settings['allow_link'][thread_id] = False
                                response = f"{status_icon(allow_link)} Anti-Link 🔗\n"
                            else:
                                response = f"➜ Lenh {bot.prefix}bot link {link_action} khong đuoc ho tro 🤧"
                        write_settings(bot.uid, settings)
                elif action == 'word':
                    if len(parts) < 4:
                        response = f"➜ Vui long nhap [add/reomve] [tu khoa] sau lenh: {bot.prefix}bot word 🤧\n➜ Vi du: {bot.prefix}bot word add [tu khoa] hoac {bot.prefix}bot word remove [tu khoa] ✅"
                    else:
                        if not is_admin(bot, author_id):
                            response = "❌Ban khong phai admin bot!"
                        elif thread_type != ThreadType.GROUP:
                            response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                        else:
                            word_action = parts[2].lower()
                            word = ' '.join(parts[3:]) 
                            if word_action == 'add':
                                response = add_forbidden_word(bot, author_id, word)
                            elif word_action == 'remove':
                                response = remove_forbidden_word(bot, author_id, word)
                            else:
                                response = f"➜ Lenh [{bot.prefix}bot word {word_action}] khong đuoc ho tro 🤧\n➜ Vi du: {bot.prefix}bot word add [tu khoa] hoac {bot.prefix}bot word remove [tu khoa] ✅"
                elif action == 'noiquy':
                    settings = read_settings(bot.uid)
                    rules=settings.get("rules", {})
                    word_rule = rules.get("word", {"threshold": 3, "duration": 30})
                    threshold_word = word_rule["threshold"]
                    duration_word = word_rule["duration"]
                    group_admins = settings.get('group_admins', {})
                    admins = group_admins.get(thread_id, [])
                    group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
                    if admins:
                        response = (
                            f"➜ 💢 Noi quy 🤖BOT {bot.me_name} đuoc ap dung cho nhom: {group.name} - ID: {thread_id} ✅\n"
                            f"➜ 🚫 Cam su dung cac tu ngu tho tuc 🤬 trong nhom\n"
                            f"➜ 💢 Vi pham {threshold_word} lan se bi 😷 khoa mom {duration_word} phut\n"
                            f"➜ ⚠️ Neu tai pham 2 lan se bi 💪 kick khoi nhom 🤧"
                        )
                    else:
                        response = (
                            f"➜ 💢 Noi quy khong ap dung cho nhom: {group.name} - ID: {thread_id} 💔\n➜ Ly do: 🤖BOT {bot.me_name} chua đuoc setup hoac BOT khong co quyen cam key quan tri nhom 🤧"
                        )
                elif action == 'ban':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap 'list' hoac 'ban @tag' sau lenh: {bot.prefix}bot 🤧\n➜ Vi du: {bot.prefix}bot ban list hoac {bot.prefix}bot ban @user ✅"
                    else:
                        sub_action = parts[2].lower()

                        if sub_action == 'list':
                            response = print_muted_users_in_group(bot, thread_id)
                        elif sub_action == 'vv':
                            if not is_admin(bot, author_id):
                                response = "➜ Lenh nay chi kha thi voi quan tri vien 🤧"
                            elif thread_type != ThreadType.GROUP:
                                response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                            elif not check_admin_group(bot, thread_id):
                                response = "➜ 🤖BOT khong co quyen quan tri nhom đe thuc hien lenh nay 🤧"
                            else:
                                uids = extract_uids_from_mentions(message_object)
                                if not uids:
                                    response = f"➜ Vui long tag nguoi can ban sau lenh: {bot.prefix}bot ban vv @username 🤧"
                                else:
                                    response = ban_users_permanently(bot, uids, thread_id)
                        else:
                            if not is_admin(bot, author_id):
                                response = "➜ Lenh nay chi kha thi voi quan tri vien 🤧"
                            elif thread_type != ThreadType.GROUP:
                                response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                            elif not check_admin_group(bot, thread_id):
                                response = "➜ Lenh nay khong kha thi do 🤖BOT khong co quyen quan tri nhom 🤧"
                            else:
                                uids = extract_uids_from_mentions(message_object)
                                response = add_users_to_ban_list(bot, uids, thread_id, "Quan tri vien cam")


                elif action == 'unban':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap @tag ten sau lenh: {bot.prefix}bot unban 🤧\n➜ Vi du: {bot.prefix}bot unban @Heoder ✅"
                    else:
                        if not is_admin(bot, author_id):
                            response = "❌Ban khong phai admin bot!"
                        elif thread_type != ThreadType.GROUP:
                            response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                        else:
                            
                            uids = extract_uids_from_mentions(message_object)
                            response = remove_users_from_ban_list(bot, uids, thread_id)
                elif action == 'block':
                      
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap @tag ten sau lenh: {bot.prefix}bot block 🤧\n➜ Vi du: {bot.prefix}bot block @Heoder ✅"
                    else:
                        s_action = parts[2]  
                      
                        if s_action == 'list':
                            response = print_blocked_users_in_group(bot, thread_id)
                        else:
                         
                            if not is_admin(bot, author_id):
                                response = "❌Ban khong phai admin bot!"
                            elif thread_type != ThreadType.GROUP:
                                response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                            elif check_admin_group(bot,thread_id)==False:
                                response = "➜ Lenh nay khong kha thi do 🤖BOT khong co quyen cam 🔑 key nhom 🤧"
                            else:
                              
                                uids = extract_uids_from_mentions(message_object)
                                response = block_users_from_group(bot, uids, thread_id)
                elif action == 'sos':
                    if not is_admin(bot, author_id):
                        response = "❌Ban khong phai admin bot!"
                    else:
                        settings = read_settings(bot.uid)
                        sos_status = settings.get("sos_status", False)

                        if sos_status:
                            bot.changeGroupSetting(groupId=thread_id, lockSendMsg=0)
                            settings["sos_status"] = False
                            response = f"{status_icon(sos_status)}SOS 🆘\n"
                        else:
                            bot.changeGroupSetting(groupId=thread_id, lockSendMsg=1)
                            settings["sos_status"] = True
                            response = f"{status_icon(sos_status)}SOS 🆘\n"

                        write_settings(bot.uid, settings)
  
                elif action == 'unblock':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap UID sau lenh: {bot.prefix}bot unblock 🤧\n➜ Vi du: {bot.prefix}bot unblock 8421834556970988033, 842183455697098804... ✅"
                    else:
                        if not is_admin(bot, author_id):
                            response = "❌Ban khong phai admin bot!"
                        elif thread_type != ThreadType.GROUP:
                            response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                        else:
                           
                            ids_str = parts[2]  
                            print(f"Chuoi UIDs: {ids_str}")

                            uids = [uid.strip() for uid in ids_str.split(',') if uid.strip()]
                            print(f"Danh sach UIDs: {uids}")

                            if uids:
                              
                                response = unblock_users_from_group(bot, uids, thread_id)
                            else:
                                response = "➜ Khong co UID nao hop le đe bo chan 🤧"

                elif action == 'kick':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap @tag ten sau lenh: {bot.prefix}bot kick 🤧\n➜ Vi du: {bot.prefix}bot kick @Heoder ✅"
                    else:
                        if not is_admin(bot, author_id):
                            response = "❌Ban khong phai admin bot!"
                        elif thread_type != ThreadType.GROUP:
                            response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                        elif check_admin_group(bot,thread_id)==False:
                                response = "➜ Lenh nay khong kha thi do 🤖BOT khong co quyen cam 🔑 key nhom 🤧"
                        else:
                            uids = extract_uids_from_mentions(message_object)
                            response = kick_users_from_group(bot, uids, thread_id)
                
                elif action == 'rule':
                    if len(parts) < 5:
                        response = f"➜ Vui long nhap word [n lan] [m phut] sau lenh: {bot.prefix}bot rule 🤧\n➜ Vi du: {bot.prefix}bot rule word 3 30 ✅"
                    else:
                        rule_type = parts[2].lower()
                        try:
                            threshold = int(parts[3])
                            duration = int(parts[4])
                        except ValueError:
                            response = "➜ So lan va phut phat phai la so nguyen 🤧"
                        else:
                            settings = read_settings(bot.uid)
                            if rule_type not in ["word", "spam"]:
                                response = f"➜ Lenh {bot.prefix}bot rule {rule_type} khong đuoc ho tro 🤧\n➜ Vi du: {bot.prefix}bot rule word 3 30✅"
                            else:
                                if not is_admin(bot, author_id):
                                    response = "❌Ban khong phai admin bot!"
                                elif thread_type != ThreadType.GROUP:
                                    response = "➜ Lenh nay chi kha thi trong nhom 🤧"
                                else:
                                    settings.setdefault("rules", {})
                                    settings["rules"][rule_type] = {
                                        "threshold": threshold,
                                        "duration": duration
                                    }
                                    write_settings(bot.uid, settings)
                                    response = f"➜ 🔄 Đa cap nhat noi quy cho {rule_type}: Neu vi pham {threshold} lan se bi phat {duration} phut ✅"
                elif action == 'cam':
                    if len(parts) < 3:
                        response = f"➜ Vui long nhap [add/remove] sau lenh: {bot.prefix}bot cam 🤧\n➜ Vi du: {bot.prefix}bot cam add @Heoder ✅"
                    else:
                        sub_action = parts[2].lower()
                        if sub_action == 'add':
                            if len(parts) < 4:
                                response = f"➜ Vui long @tag ten nguoi dung sau lenh: {bot.prefix}bot cam add 🤧\n➜ Vi du: {bot.prefix}bot cam add @Heoder ✅"
                            if not admin_cao(bot, author_id):
                                response = "❌Ban khong phai admin bot!"
                            else:
                                mentioned_uids = extract_uids_from_mentions(message_object)
                                response = ban_user_from_commands(bot, author_id, mentioned_uids)
                        elif sub_action == 'remove':
                            if len(parts) < 4:
                                response = f"➜ Vui long @tag ten nguoi dung sau lenh: {bot.prefix}bot cam remove 🤧\n➜ Vi du: {bot.prefix}bot cam remove @Heoder ✅"
                            if not admin_cao(bot, author_id):
                                response = "❌Ban khong phai admin bot!"
                            else:
                                mentioned_uids = extract_uids_from_mentions(message_object)
                                response = unban_user_from_commands(bot, author_id, mentioned_uids)
                        elif sub_action == 'list':
                            response = list_banned_users(bot)

                else:
                    bot.sendReaction(message_object, "❌", thread_id, thread_type)
            
            if response:
                if len(parts) == 1:
                    os.makedirs(CACHE_PATH, exist_ok=True)
    
                    image_path = generate_menu_image(bot, author_id, thread_id, thread_type)
                    if not image_path:
                        bot.sendMessage("❌ Khong the tao anh menu!", thread_id, thread_type)
                        return
                    reaction = [
                        "❌", "🤧", "🐞", "😊", "🔥", "👍", "💖", "🚀",
                        "😍", "😂", "😢", "😎", "🙌", "💪", "🌟", "🍀",
                        "🎉", "🦁", "🌈", "🍎", "⚡", "🔔", "🎸", "🍕",
                        "🏆", "📚", "🦋", "🌍", "⛄", "🎁", "💡", "🐾",
                        "😺", "🐶", "🐳", "🦄", "🌸", "🍉", "🍔", "🎄",
                        "🎃", "👻", "☃️", "🌴", "🏀", "⚽", "🎾", "🏈",
                        "🚗", "✈️", "🚢", "🌙", "☀️", "⭐", "⛅", "☔",
                        "⌛", "⏰", "💎", "💸", "📷", "🎥", "🎤", "🎧",
                        "🍫", "🍰", "🍩", "☕", "🍵", "🍷", "🍹", "🥐",
                        "🐘", "🦒", "🐍", "🦜", "🐢", "🦀", "🐙", "🦈",
                        "🍓", "🍋", "🍑", "🥥", "🥪", "🍝", "🍣",
                        "🎲", "🎯", "🎱", "🎮", "🎰", "🧩", "🧸", "🎡",
                        "🏰", "🗽", "🗼", "🏔️", "🏝️", "🏜️", "🌋", "⛲",
                        "📱", "💻", "🖥️", "🖨️", "⌨️", "🖱️", "📡", "🔋",
                        "🔍", "🔎", "🔑", "🔒", "🔓", "📩", "📬", "📮",
                        "💢", "💥", "💫", "💦", "💤", "🚬", "💣", "🔫",
                        "🩺", "💉", "🩹", "🧬", "🔬", "🔭", "🧪", "🧫",
                        "🧳", "🎒", "👓", "🕶️", "👔", "👗", "👠", "🧢",
                        "🦷", "🦴", "👀", "👅", "👄", "👶", "👩", "👨",
                        "🚶", "🏃", "💃", "🕺", "🧘", "🏄", "🏊", "🚴",
                        "🍄", "🌾", "🌻", "🌵", "🌿", "🍂", "🍁", "🌊",
                        "🛠️", "🔧", "🔨", "⚙️", "🪚", "🪓", "🧰", "⚖️",
                        "🧲", "🪞", "🪑", "🛋️", "🛏️", "🪟", "🚪", "🧹"
                    ]

                    num_reactions = random.randint(2, 3)
                    selected_reactions = random.sample(reaction, num_reactions)

                    for emoji in selected_reactions:
                        bot.sendReaction(message_object, emoji, thread_id, thread_type)
                    bot.sendLocalImage(
                        imagePath=image_path,
                        message=Message(text=response, mention=Mention(author_id, length=len(f"{get_user_name_by_id(bot, author_id)}"), offset=0)),
                        thread_id=thread_id,
                        thread_type=thread_type,
                        width=1920,
                        height=600,
                        ttl=240000
                    )
                    
                    try:
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    except Exception as e:
                        print(f"❌ Loi khi xoa anh: {e}")
                else:
                    reaction = [
                        "❌", "🤧", "🐞", "😊", "🔥", "👍", "💖", "🚀",
                        "😍", "😂", "😢", "😎", "🙌", "💪", "🌟", "🍀",
                        "🎉", "🦁", "🌈", "🍎", "⚡", "🔔", "🎸", "🍕",
                        "🏆", "📚", "🦋", "🌍", "⛄", "🎁", "💡", "🐾",
                        "😺", "🐶", "🐳", "🦄", "🌸", "🍉", "🍔", "🎄",
                        "🎃", "👻", "☃️", "🌴", "🏀", "⚽", "🎾", "🏈",
                        "🚗", "✈️", "🚢", "🌙", "☀️", "⭐", "⛅", "☔",
                        "⌛", "⏰", "💎", "💸", "📷", "🎥", "🎤", "🎧",
                        "🍫", "🍰", "🍩", "☕", "🍵", "🍷", "🍹", "🥐",
                        "🐘", "🦒", "🐍", "🦜", "🐢", "🦀", "🐙", "🦈",
                        "🍓", "🍋", "🍑", "🥥", "🥪", "🍝", "🍣",
                        "🎲", "🎯", "🎱", "🎮", "🎰", "🧩", "🧸", "🎡",
                        "🏰", "🗽", "🗼", "🏔️", "🏝️", "🏜️", "🌋", "⛲",
                        "📱", "💻", "🖥️", "🖨️", "⌨️", "🖱️", "📡", "🔋",
                        "🔍", "🔎", "🔑", "🔒", "🔓", "📩", "📬", "📮",
                        "💢", "💥", "💫", "💦", "💤", "🚬", "💣", "🔫",
                        "🩺", "💉", "🩹", "🧬", "🔬", "🔭", "🧪", "🧫",
                        "🧳", "🎒", "👓", "🕶️", "👔", "👗", "👠", "🧢",
                        "🦷", "🦴", "👀", "👅", "👄", "👶", "👩", "👨",
                        "🚶", "🏃", "💃", "🕺", "🧘", "🏄", "🏊", "🚴",
                        "🍄", "🌾", "🌻", "🌵", "🌿", "🍂", "🍁", "🌊",
                        "🛠️", "🔧", "🔨", "⚙️", "🪚", "🪓", "🧰", "⚖️",
                        "🧲", "🪞", "🪑", "🛋️", "🛏️", "🪟", "🚪", "🧹"
                    ]

                    num_reactions = random.randint(2, 3)
                    selected_reactions = random.sample(reaction, num_reactions)

                    for emoji in selected_reactions:
                        bot.sendReaction(message_object, emoji, thread_id, thread_type)
                    bot.replyMessage(Message(text=response),message_object, thread_id=thread_id, thread_type=thread_type,ttl=9000)
        
        except Exception as e:
            print(f"Error: {e}")
            bot.replyMessage(Message(text="➜ 🐞 Đa xay ra loi gi đo 🤧"), message_object, thread_id=thread_id, thread_type=thread_type)

    thread = Thread(target=send_bot_response)
    thread.start()

font_path_emoji = os.path.join("emoji.ttf")
font_path_arial = os.path.join("arial unicode ms.otf")

def create_gradient_colors(num_colors: int) -> List[Tuple[int, int, int]]:
    return [(random.randint(30, 255), random.randint(30, 255), random.randint(30, 255)) for _ in range(num_colors)]

def interpolate_colors(colors: List[Tuple[int, int, int]], text_length: int, change_every: int) -> List[Tuple[int, int, int]]:
    gradient = []
    num_segments = len(colors) - 1
    steps_per_segment = max((text_length // change_every) + 1, 1)

    for i in range(num_segments):
        for j in range(steps_per_segment):
            if len(gradient) < text_length:
                ratio = j / steps_per_segment
                interpolated_color = (
                    int(colors[i][0] * (1 - ratio) + colors[i + 1][0] * ratio),
                    int(colors[i][1] * (1 - ratio) + colors[i + 1][1] * ratio),
                    int(colors[i][2] * (1 - ratio) + colors[i + 1][2] * ratio)
                )
                gradient.append(interpolated_color)

    while len(gradient) < text_length:
        gradient.append(colors[-1])

    return gradient[:text_length]

def is_emoji(character: str) -> bool:
    return character in emoji.EMOJI_DATA

def create_text(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont, 
                emoji_font: ImageFont.FreeTypeFont, text_position: Tuple[int, int], 
                gradient_colors: List[Tuple[int, int, int]]):
    gradient = interpolate_colors(gradient_colors, text_length=len(text), change_every=4)
    current_x = text_position[0]

    for i, char in enumerate(text):
        color = tuple(gradient[i])
        try:
            selected_font = emoji_font if is_emoji(char) and emoji_font else font
            draw.text((current_x, text_position[1]), char, fill=color, font=selected_font)
            text_bbox = draw.textbbox((current_x, text_position[1]), char, font=selected_font)
            text_width = text_bbox[2] - text_bbox[0]
            current_x += text_width
        except Exception as e:
            print(f"Loi khi ve ky tu '{char}': {e}. Bo qua ky tu nay.")
            continue

def draw_gradient_border(draw: ImageDraw.Draw, center_x: int, center_y: int, 
                        radius: int, border_thickness: int, 
                        gradient_colors: List[Tuple[int, int, int]]):
    num_segments = 80
    gradient = interpolate_colors(gradient_colors, num_segments, change_every=10)

    for i in range(num_segments):
        start_angle = i * (360 / num_segments)
        end_angle = (i + 1) * (360 / num_segments)
        color = tuple(gradient[i])
        draw.arc(
            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
            start=start_angle, end=end_angle, fill=color, width=border_thickness
        )

def load_image_from_url(url: str) -> Image.Image:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert('RGBA')
    except Exception as e:
        print(f"Loi khi tai anh tu URL {url}: {e}")
        return Image.new('RGBA', (100, 100), (0, 0, 0, 0))

def generate_short_filename(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def load_random_background(background_dir: str = "background") -> Image.Image:
    if not os.path.exists(background_dir):
        print(f"Error: Background folder '{background_dir}' does not exist.")
        return None
    background_files = [os.path.join(background_dir, f) for f in os.listdir(background_dir) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not background_files:
        print(f"Error: No valid image files found in '{background_dir}'")
        return None
    background_path = random.choice(background_files)
    try:
        return Image.open(background_path).convert("RGBA")
    except Exception as e:
        print(f"Error loading image {background_path}: {e}")
        return None

def create_default_background(width: int, height: int) -> Image.Image:
    return Image.new('RGBA', (width, height), (0, 100, 0, 255))

def create_default_avatar(name: str) -> Image.Image:
    avatar = Image.new('RGBA', (170, 170), (200, 200, 200, 255))
    draw = ImageDraw.Draw(avatar)
    draw.ellipse((0, 0, 170, 170), fill=(100, 100, 255, 255))
    initials = (name[:2].upper() if name else "??")
    font = ImageFont.truetype(font_path_arial, 60)
    text_bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    draw.text(
        ((170 - text_width) // 2, (170 - text_height) // 2),
        initials,
        font=font,
        fill=(255, 255, 255, 255)
    )
    return avatar

def create_banner(bot, uid: str, thread_id: str, group_name: str = None, 
                 avatar_url: str = None, event_type: str = None, 
                 event_data = None, background_dir: str = "background") -> str:
    try:
        settings = read_settings(bot.uid)
        if not settings.get("welcome", {}).get(thread_id, False):
            return None
            
        member_info = bot.fetchUserInfo(uid).changed_profiles.get(uid)
        if not member_info:
            print(f"[ERROR] Khong tim thay thong tin user {uid}")
            return None
            
        avatar_url = member_info.avatar if not avatar_url else avatar_url
        user_name = getattr(member_info, 'zaloName', f"User{uid}")

        group_info = bot.group_info_cache.get(thread_id, {})
        group_name = group_info.get('name', "Nhom khong xac đinh") if not group_name else group_name
        total_members = group_info.get('total_member', 0)
        thread_type = ThreadType.GROUP

        ow_name = ""
        ow_avatar_url = ""
        if event_data and hasattr(event_data, 'sourceId'):
            try:
                ow_info = bot.fetchUserInfo(event_data.sourceId).changed_profiles.get(event_data.sourceId)
                ow_name = getattr(ow_info, 'zaloName', f"Admin{event_data.sourceId}") if ow_info else "Quan tri vien"
                ow_avatar_url = ow_info.avatar if ow_info else ""
            except Exception as e:
                print(f"[WARNING] Loi khi lay thong tin admin: {e}")
                ow_name = "Quan tri vien"

        event_config = {
            GroupEventType.JOIN: {
                'main_text': f'Chao mung, {user_name} 💜',
                'group_name_text': group_name,
                'credit_text': "Đa đuoc duyet vao nhom",
                'msg': f"✨ {user_name}",
                'mention': None
            },
            GroupEventType.LEAVE: {
                'main_text': f'Tam biet, {user_name} 💔',
                'group_name_text': group_name,
                'credit_text': "Đa roi khoi nhom",
                'msg': f'💔 {user_name}',
                'mention': None
            },
            GroupEventType.ADD_ADMIN: {
                'main_text': f'Chuc mung, {user_name}',
                'group_name_text': group_name,
                'credit_text': f"bo nhiem lam pho nhom🔑",
                'msg': f'🎉 {user_name}',
                'mention': None
            },
            GroupEventType.REMOVE_ADMIN: {
                'main_text': f'Rat tiec, {user_name}',
                'group_name_text': group_name,
                'credit_text': f"Đa bi xoa vai tro nhom❌",
                'msg': f'⚠️ {user_name}',
                'mention': None
            },
            GroupEventType.REMOVE_MEMBER: {
                'main_text': f'Nhay nay, {user_name}',
                'group_name_text': group_name,
                'credit_text': f"Đa bi kick khoi nhom🚫",
                'msg': f'🚫 {user_name}',
                'mention': None
            },
            GroupEventType.JOIN_REQUEST: {
                'main_text': f'Yeu cau tham gia ✋',
                'group_name_text': group_name,
                'credit_text': f"{user_name}",
                'msg': f'✋ {user_name}',
                'mention': None
            }
        }

        config = event_config.get(event_type)
        if not config:
            print(f"[ERROR] Su kien {event_type} khong đuoc ho tro")
            return None
        
        banner_width, banner_height = 980, 350
        
        try:
            background = load_random_background(background_dir) or create_default_background(banner_width, banner_height)
            background = background.resize((banner_width, banner_height), Image.LANCZOS)
            background_blurred = background.filter(ImageFilter.GaussianBlur(radius=5))
        except Exception as e:
            print(f"[ERROR] Loi background: {e}")
            background = create_default_background(banner_width, banner_height)
            background_blurred = background

        overlay = Image.new("RGBA", (banner_width, banner_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        glass_color = (
            random.randint(30, 80),
            random.randint(30, 80), 
            random.randint(30, 80),
            random.randint(170, 220)
        )
        
        rect_margin = 60
        rect_x0, rect_y0 = rect_margin, 30
        rect_x1, rect_y1 = banner_width - rect_margin, banner_height - 30
        draw.rounded_rectangle([rect_x0, rect_y0, rect_x1, rect_y1], radius=30, fill=glass_color)

        member_circle_radius = 25
        member_circle_x = rect_x1 - member_circle_radius - 20 
        member_circle_y = rect_y0 + member_circle_radius + 15
        
        circle_border_color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255),
            255 
        )
        
        draw.ellipse(
            [member_circle_x - member_circle_radius, 
             member_circle_y - member_circle_radius,
             member_circle_x + member_circle_radius, 
             member_circle_y + member_circle_radius],
            outline=circle_border_color,
            width=6
        )
        
        member_font = ImageFont.truetype(font_path_arial, 20)
        member_count_text = str(total_members)
        member_bbox = draw.textbbox((0, 0), member_count_text, font=member_font)
        member_text_width = member_bbox[2] - member_bbox[0]
        member_text_height = member_bbox[3] - member_bbox[1]
        
        member_text_x = member_circle_x - (member_text_width // 2)
        member_text_y = member_circle_y - (member_text_height // 2 + 10)
        draw.text(
            (member_text_x, member_text_y),
            member_count_text,
            font=member_font,
            fill=(255, 255, 255, 255)
        )

        banner = Image.alpha_composite(background_blurred, overlay)

        try:
            avatar = load_image_from_url(avatar_url) or create_default_avatar(user_name)
            avatar_size = 135
            mask = Image.new('L', (avatar_size, avatar_size), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            
            avatar = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)
            avatar_x = rect_x0 + 25
            avatar_y = rect_y1 - avatar_size - 70
            banner.paste(avatar, (avatar_x, avatar_y), mask)
            
            border_size = 4
            border = Image.new('RGBA', (avatar_size + border_size*2, avatar_size + border_size*2), (255, 255, 255, 255))
            border_mask = Image.new('L', (avatar_size + border_size*2, avatar_size + border_size*2), 0)
            border_draw = ImageDraw.Draw(border_mask)
            border_draw.ellipse((0, 0, avatar_size + border_size*2, avatar_size + border_size*2), fill=255)
            banner.paste(border, (avatar_x - border_size, avatar_y - border_size), border_mask)
            banner.paste(avatar, (avatar_x, avatar_y), mask)
        except Exception as e:
            print(f"[WARNING] Loi avatar nguoi dung: {e}")

        if ow_avatar_url:
            try:
                ow_avatar = load_image_from_url(ow_avatar_url) or create_default_avatar(ow_name)
                ow_avatar = ow_avatar.resize((avatar_size, avatar_size), Image.LANCZOS)
                ow_avatar_x = rect_x1 - avatar_size - 25
                ow_avatar_y = avatar_y
                banner.paste(ow_avatar, (ow_avatar_x, ow_avatar_y), mask)
                
                banner.paste(border, (ow_avatar_x - border_size, ow_avatar_y - border_size), border_mask)
                banner.paste(ow_avatar, (ow_avatar_x, ow_avatar_y), mask)
            except Exception as e:
                print(f"[WARNING] Loi avatar nguoi thuc hien: {e}")

        draw = ImageDraw.Draw(banner)
        
        def get_vibrant_color():
            colors = [
                (255, 90, 90), (90, 255, 90), (90, 90, 255),
                (255, 255, 90), (255, 90, 255), (90, 255, 255)
            ]
            return random.choice(colors)
        
        font_main = ImageFont.truetype(font_path_arial, 50)
        main_text = config['main_text']
        main_bbox = draw.textbbox((0, 0), main_text, font=font_main)
        main_width = main_bbox[2] - main_bbox[0]
        main_x = rect_x0 + (rect_x1 - rect_x0 - main_width) // 2
        main_y = rect_y0 + 10
        draw.text((main_x, main_y), main_text, font=font_main, fill=get_vibrant_color())

        font_group = ImageFont.truetype(font_path_arial, 48)
        group_text = config['group_name_text']
        group_bbox = draw.textbbox((0, 0), group_text, font=font_group)
        group_width = group_bbox[2] - group_bbox[0]
        group_x = rect_x0 + (rect_x1 - rect_x0 - group_width) // 2
        group_y = main_y + main_bbox[3] + 15
        max_width = rect_x1 - rect_x0 - 20
        if group_width > max_width:
            while group_bbox[2] - group_bbox[0] > max_width and len(group_text) > 0:
                group_text = group_text[:-1]
                group_bbox = draw.textbbox((0, 0), group_text + "...", font=font_group)
            group_text += "..."
        draw.text((group_x, group_y), group_text, font=font_group, fill=get_vibrant_color())

        font_credit = ImageFont.truetype(font_path_arial, 38)
        credit_text = config['credit_text']
        credit_bbox = draw.textbbox((0, 0), credit_text, font=font_credit)
        credit_width = credit_bbox[2] - credit_bbox[0]
        credit_x = rect_x0 + (rect_x1 - rect_x0 - credit_width) // 2
        credit_y = group_y + group_bbox[3] + 15
        draw.text((credit_x, credit_y), credit_text, font=font_credit, fill=(255, 255, 255))

        time_text = f"📅 {time.strftime('%d/%m/%Y')}  ⏰ {time.strftime('%H:%M:%S')}    🔑 Executed by {ow_name}" if ow_name else f"📅 {time.strftime('%d/%m/%Y')}     ⏰ {time.strftime('%H:%M:%S')}"
        font_footer = ImageFont.truetype(font_path_arial, 22)
        footer_bbox = draw.textbbox((0, 0), time_text, font=font_footer)
        footer_x = rect_x0 + (rect_x1 - rect_x0 - footer_bbox[2]) // 2 + 20
        footer_y = rect_y1 - footer_bbox[3] - 15
        draw.text((footer_x, footer_y), time_text, font=font_footer, fill=(220, 220, 220))

        file_name = f"banner_{int(time.time())}.jpg"
        try:
            banner.convert('RGB').save(file_name, quality=95)
            if event_type:
                bot.sendMultiLocalImage(
                    [file_name],
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=banner_width,
                    height=banner_height,
                    message=Message(text=config['msg'], mention=config.get('mention')),
                    ttl=60000 * 60
                )
        except Exception as e:
            print(f"[ERROR] Loi khi luu/gui banner: {e}")
            return None
        finally:
            try:
                delete_file(file_name)
            except:
                pass

        return file_name

    except Exception as e:
        print(f"[CRITICAL] Loi nghiem trong: {str(e)}")
        return None

def delete_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Đa xoa tep: {file_path}")
    except Exception as e:
        print(f"Loi khi xoa tep: {e}")

def load_emoji_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        if os.path.exists(font_path_emoji):
            return ImageFont.truetype(font_path_emoji, size)
        if os.name == 'nt':
            return ImageFont.truetype("seguiemj.ttf", size)
        elif os.path.exists("/System/Library/Fonts/Apple Color Emoji.ttc"):
            return ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", size)
    except Exception:
        return None

def handle_event(client, event_data, event_type):
    try:
        if not hasattr(event_data, 'groupId'):
            print(f"Du lieu su kien khong co groupId: {event_data}")
            return

        thread_id = event_data.groupId
        thread_type = ThreadType.GROUP
        
        settings = read_settings(client.uid)
        if not settings.get("welcome", {}).get(thread_id, False):
            return
            
        group_info = client.fetchGroupInfo(thread_id)
        group_name = group_info.gridInfoMap.get(str(thread_id), {}).get('name', 'nhom')
        total_member = group_info.gridInfoMap[str(thread_id)]['totalMember']

        client.group_info_cache[thread_id] = {
            "name": group_name,
            "member_list": group_info.gridInfoMap[str(thread_id)]['memVerList'],
            "total_member": total_member
        }

        for member in event_data.updateMembers:
            member_id = member['id']
            member_name = member['dName']
            user_info = client.fetchUserInfo(member_id)
            avatar_url = user_info.changed_profiles[member_id].avatar

            banner_path = create_banner(
                client, 
                member_id, 
                thread_id, 
                group_name=group_name, 
                avatar_url=avatar_url, 
                event_type=event_type, 
                event_data=event_data
            )

            if not banner_path or not os.path.exists(banner_path):
                print(f"Khong tao đuoc banner cho {member_name} voi event {event_type}")
                continue

            if event_type == GroupEventType.JOIN:
                msg = Message(
                    text=f"🚦 {member_name}",
                    mention=Mention(uid=member_id, length=len(member_name), offset=3)
                )
                client.sendLocalImage(banner_path, thread_id=thread_id, thread_type=thread_type, 
                                    width=980, height=350, message=msg, ttl=60000 * 60)
            elif event_type == GroupEventType.LEAVE:
                client.sendLocalImage(banner_path, thread_id=thread_id, thread_type=thread_type, 
                                    width=980, height=350, ttl=60000 * 60)
            else:
                print(f"Su kien {event_type} khong đuoc ho tro")

            delete_file(banner_path)

    except Exception as e:
        print(f"Loi khi xu ly event {event_type}: {e}")

def handle_welcome_on(bot, thread_id: str) -> str:
    settings = read_settings(bot.uid)
    if "welcome" not in settings:
        settings["welcome"] = {}
    settings["welcome"][thread_id] = True
    write_settings(bot.uid, settings)
    return f"🚦Che đo welcome đa 🟢 Bat 🎉"

def handle_welcome_off(bot, thread_id: str) -> str:
    settings = read_settings(bot.uid)
    if "welcome" in settings and thread_id in settings["welcome"]:
        settings["welcome"][thread_id] = False
        write_settings(bot.uid, settings)
        return f"🚦Che đo welcome đa 🔴 Tat 🎉"
    return "🚦Nhom chua co thong tin cau hinh welcome đe 🔴 Tat 🤗"

def get_allow_welcome(bot, thread_id: str) -> bool:
    settings = read_settings(bot.uid)
    return settings.get("welcome", {}).get(thread_id, False)

def initialize_group_info(bot, allowed_thread_ids: List[str]):
    for thread_id in allowed_thread_ids:
        group_info = bot.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id, None)
        if group_info:
            bot.group_info_cache[thread_id] = {
                "name": group_info['name'],
                "member_list": group_info['memVerList'],
                "total_member": group_info['totalMember']
            }
        else:
            print(f"Bo qua nhom {thread_id}")

def check_member_changes(bot, thread_id: str) -> Tuple[set, set]:
    current_group_info = bot.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id, None)
    cached_group_info = bot.group_info_cache.get(thread_id, None)

    if not cached_group_info or not current_group_info:
        return set(), set()

    old_members = set([member.split('_')[0] for member in cached_group_info["member_list"]])
    new_members = set([member.split('_')[0] for member in current_group_info['memVerList']])

    joined_members = new_members - old_members
    left_members = old_members - new_members

    bot.group_info_cache[thread_id] = {
        "name": current_group_info['name'],
        "member_list": current_group_info['memVerList'],
        "total_member": current_group_info['totalMember']
    }

    return joined_members, left_members

def handle_group_member(bot, message_object, author_id: str, thread_id: str, thread_type: str):
    if not get_allow_welcome(bot, thread_id):
        return
        
    current_group_info = bot.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id, None)
    cached_group_info = bot.group_info_cache.get(thread_id, None)

    if not cached_group_info or not current_group_info:
        print(f"Khong co thong tin nhom cho thread_id {thread_id}")
        return

    old_members = set([member.split('_')[0] for member in cached_group_info["member_list"]])
    new_members = set([member.split('_')[0] for member in current_group_info['memVerList']])

    joined_members = new_members - old_members
    left_members = old_members - new_members

    for member_id in joined_members:
        banner = create_banner(bot, member_id, thread_id, event_type=GroupEventType.JOIN, 
                             event_data=type('Event', (), {'sourceId': author_id or bot.uid})())
        if banner and os.path.exists(banner):
            try:
                user_name = bot.fetchUserInfo(member_id).changed_profiles[member_id].zaloName
                bot.sendLocalImage(
                    banner,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=980,
                    height=350,
                    message=Message(
                        text=f"🚦 {user_name}",
                        mention=Mention(uid=member_id, length=len(user_name), offset=3)
                    ),
                    ttl=86400000
                )
                delete_file(banner)
            except Exception as e:
                print(f"Loi khi gui banner cho {member_id} (JOIN): {e}")
                if os.path.exists(banner):
                    delete_file(banner)

    for member_id in left_members:
        banner = create_banner(bot, member_id, thread_id, event_type=GroupEventType.LEAVE, 
                             event_data=type('Event', (), {'sourceId': author_id or bot.uid})())
        if banner and os.path.exists(banner):
            try:
                bot.sendLocalImage(
                    banner,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=980,
                    height=350,
                    ttl=86400000
                )
                delete_file(banner)
            except Exception as e:
                print(f"Loi khi gui banner cho {member_id} (LEAVE): {e}")
                if os.path.exists(banner):
                    delete_file(banner)

    bot.group_info_cache[thread_id] = {
        "name": current_group_info['name'],
        "member_list": current_group_info['memVerList'],
        "total_member": current_group_info['totalMember']
    }

def start_member_check_thread(bot, allowed_thread_ids: List[str]):
    def check_members_loop():
        while True:
            for thread_id in allowed_thread_ids:
                if not get_allow_welcome(bot, thread_id):
                    continue
                handle_group_member(bot, None, None, thread_id, ThreadType.GROUP)
            time.sleep(2)

    thread = threading.Thread(target=check_members_loop, daemon=True)
    thread.start()

def _extract_all_texts(message_object) -> str:
    """
    Gom mọi text có thể (title/desc/description/url/href/caption/filename) để detector dễ bắt.
    """
    parts = []
    try:
        base = get_content_message(message_object)
        if base:
            parts.append(str(base))
    except Exception:
        pass
    try:
        c = getattr(message_object, 'content', '')
        if isinstance(c, dict):
            for k in ('title','desc','description','subtitle','text','caption','url','href','fileName','name'):
                v = c.get(k)
                if v:
                    parts.append(str(v))
        elif isinstance(c, str):
            parts.append(c)
    except Exception:
        pass
    # Also consider preview URLs in cards
    try:
        preview = getattr(message_object, 'preview', None)
        if isinstance(preview, dict):
            for k in ('title','desc','description','subtitle','text','url','href'):
                v = preview.get(k)
                if v:
                    parts.append(str(v))
    except Exception:
        pass
    return "\n".join([p for p in parts if p])

def _normalize_text_simple(s: str) -> str:
    import re as _re
    return _re.sub(r"\s+", " ", (s or "").lower())

def _has_phone_or_contact_info(text: str) -> bool:
    import re as _re
    if not text:
        return False
    # Normalize
    t = _normalize_text_simple(text)
    # Simple Vietnamese phone patterns: +84 or 0 followed by 9-11 digits with separators allowed
    if _re.search(r"(\+?84|0)(?:\D*\d){9,11}\b", text):
        return True
    # Raw digits check
    digits = _re.sub(r"\D", "", text)
    return 9 <= len(digits) <= 12

def _has_bank_or_wallet_info(text: str) -> bool:
    import re as _re
    if not text:
        return False
    t = _normalize_text_simple(text)
    keywords = [
        "stk", "số tài khoản", "so tai khoan", "vietqr", "qrpay", "qr pay",
        "momo", "zalo pay", "zalopay", "vnpay", "nap tien", "thanh toan",
        "chuyen khoan", "ck", "donate", "mbbank", "techcombank", "vcb",
        "vietcombank", "bidv", "acb", "agribank", "tpbank", "vpbank"
    ]
    if any(k in t for k in keywords):
        return True
    digits = _re.sub(r"\D", "", text)
    # Many digits often imply account/QR context; be conservative
    return len(digits) >= 12



def _looks_like_qr_image(message_object) -> bool:
    """
    Heuristic: ảnh/file có chữ 'qr' hoặc từ khóa ví/thanh toán trong caption/filename.
    Không OCR được ảnh, nên dùng tên/caption/metadata.
    """
    mt = getattr(message_object, 'msgType', '')
    if mt not in ('chat.image','chat.file','chat.video','chat.gif'):
        return False
    t = _normalize_text_simple(_extract_all_texts(message_object))
    if not t:
        return False
    kw = ['qr', 'vietqr', 'qrpay', 'momo', 'zalo pay', 'zalopay', 'vnpay', 'payment', 'pay', 'thanh toan', 'nap tien', 'donate', 'bank', 'stk', 'so tai khoan']
    if any(k in t for k in kw):
        return True
    # many digits hint
    import re as _re
    digits = _re.sub(r'[^0-9]', '', t)
    if len(digits) >= 10:
        return True
    return False