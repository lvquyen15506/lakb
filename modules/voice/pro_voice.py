from zlapi.models import Message, MessageStyle, MultiMsgStyle
from gtts import gTTS
import os
import threading
import tempfile
import requests

CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

def upload_to_uguu(file_path):
    url = "https://uguu.se/upload"
    try:
        with open(file_path, 'rb') as f:
            files = {'files[]': (os.path.basename(file_path), f)}
            resp = requests.post(url, files=files, headers=get_headers())
            resp.raise_for_status()
        data = resp.json()
        if 'files' in data and len(data['files']) > 0:
            return data['files'][0]['url']
        return None
    except Exception as e:
        print(f"Loi upload Uguu: {e}")
        return None

def handle_voice_command(message, message_object, thread_id, thread_type, author_id, client):
    # Kiem tra tin nhan reply
    quote = getattr(message_object, 'quote', None)
    if not quote or not isinstance(quote, dict):
        client.sendMessage(
            Message(text="❌ Vui long reply vao mot tin nhan co noi dung van ban đe bot đoc."),
            thread_id, thread_type
        )
        return

    text_to_speak = quote.get('msg', None)
    if not text_to_speak:
        client.sendMessage(
            Message(text="❌ Tin nhan ban reply khong co noi dung van ban đe đoc."),
            thread_id, thread_type
        )
        return

    def create_and_send_voice():
        try:
            # Gui tin nhan thong bao kieu xanh đam
            voice_text = "🎙️ Voice cua ban đay!"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(voice_text), style="color", color="#15A85F", auto_format=False),
                MessageStyle(offset=0, length=len(voice_text), style="bold", auto_format=False)
            ])
            client.sendMessage(Message(text=voice_text, style=styles), thread_id, thread_type)

            # Tao file mp3 tam
            with tempfile.NamedTemporaryFile(suffix=".mp3", dir=CACHE_DIR, delete=False) as tmpfile:
                audio_path = tmpfile.name
            tts = gTTS(text=text_to_speak, lang='vi')
            tts.save(audio_path)

            # Upload len Uguu
            audio_url = upload_to_uguu(audio_path)
            if audio_url:
                # Gui voice qua URL (client phai ho tro sendRemoteVoice)
                if hasattr(client, 'sendRemoteVoice'):
                    client.sendRemoteVoice(voiceUrl=audio_url, thread_id=thread_id, thread_type=thread_type)
                else:
                    client.sendMessage(Message(text="❌ Bot khong ho tro gui voice qua URL."), thread_id, thread_type)
            else:
                client.sendMessage(Message(text="❌ Khong upload đuoc file am thanh."), thread_id, thread_type)

            # Xoa file tam
            if os.path.exists(audio_path):
                os.remove(audio_path)

        except Exception as e:
            client.sendMessage(Message(text=f"❌ Loi khi tao hoac gui am thanh: {str(e)}"), thread_id, thread_type)

    threading.Thread(target=create_and_send_voice).start()
