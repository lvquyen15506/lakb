from zlapi.models import Message, MessageStyle, MultiMsgStyle
import os
import threading
import tempfile
from zalo_tts import ZaloTTS  # pip install zalo-tts

CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def handle_voice_command(message, message_object, thread_id, thread_type, author_id, client):
    # Kiểm tra reply có quote kèm tin nhắn văn bản không
    quote = getattr(message_object, 'quote', None)
    if not quote or not isinstance(quote, dict):
        client.sendMessage(
            Message(text="❌ Vui lòng reply vào một tin nhắn có nội dung văn bản để bot đọc."),
            thread_id, thread_type
        )
        return

    text_to_speak = quote.get('msg', None)
    if not text_to_speak:
        client.sendMessage(
            Message(text="❌ Tin nhắn bạn reply không có nội dung văn bản để đọc."),
            thread_id, thread_type
        )
        return

    def create_and_send_voice():
        try:
            # Thông báo kiểu xanh đậm
            voice_text = "🎙️ Voice của bạn đây!"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(voice_text), style="color", color="#15A85F", auto_format=False),
                MessageStyle(offset=0, length=len(voice_text), style="bold", auto_format=False)
            ])
            client.sendMessage(Message(text=voice_text, style=styles), thread_id, thread_type)

            # Tạo giọng nói mp3 từ text bằng ZaloTTS
            tts = ZaloTTS(speaker=ZaloTTS.SOUTH_WOMEN)  # Giọng nữ miền Nam, đổi giọng nếu muốn
            audio_data = tts.text_to_speech(text_to_speak, encode_type='mp3')

            # Lưu file tạm
            with tempfile.NamedTemporaryFile(suffix=".mp3", dir=CACHE_DIR, delete=False) as tmpfile:
                tmpfile.write(audio_data)
                audio_path = tmpfile.name

            # Gửi trực tiếp file voice nếu client hỗ trợ
            if hasattr(client, 'sendVoice'):
                client.sendVoice(file_path=audio_path, thread_id=thread_id, thread_type=thread_type)
            else:
                client.sendMessage(Message(text="❌ Bot không hỗ trợ gửi file voice trực tiếp."), thread_id, thread_type)

            # Xóa file tạm
            if os.path.exists(audio_path):
                os.remove(audio_path)

        except Exception as e:
            client.sendMessage(Message(text=f"❌ Lỗi khi tạo hoặc gửi âm thanh: {str(e)}"), thread_id, thread_type)

    threading.Thread(target=create_and_send_voice).start()
