from zlapi.models import Message
import requests
import urllib.parse
import json
import os

des = {
    'version': "1.9.2",
    'credits': "Nguyen Đuc Tai",
    'description': "Tao qrcode tu text hoac media URL",
    'power': "Thanh vien"
}

def handle_qrcode_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message.split()
    content = None

    if hasattr(message_object, 'msgType') and message_object.msgType in ["chat.photo", "chat.video.msg"]:
        media_url = message_object.content.get('href', '').replace("\\/", "/")
        if media_url:
            content = media_url

    elif getattr(message_object, 'quote', None):
        attach = getattr(message_object.quote, 'attach', None)
        if attach:
            try:
                attach_data = json.loads(attach)
            except json.JSONDecodeError:
                error_message = Message(text="Loi: Khong the phan tich JSON tu file đinh kem.")
                client.replyMessage(error_message, message_object, thread_id, thread_type)
                return

            media_url = attach_data.get('hdUrl') or attach_data.get('href')
            if media_url:
                content = media_url

    if not content:
        if len(text) < 2 or not text[1].strip():
            error_message = Message(text="Vui long nhap noi dung hoac reply anh/video đe tao QR code.")
            client.replyMessage(error_message, message_object, thread_id, thread_type)
            return
        content = " ".join(text[1:])

    encoded_text = urllib.parse.quote(content, safe='')

    try:
        apiqrcode = f'https://api.qrserver.com/v1/create-qr-code/?size=4820x4820&data={encoded_text}'
        image_response = requests.get(apiqrcode)
        image_path = 'modules/cache/temp_image1.jpeg'
        with open(image_path, 'wb') as f:
            f.write(image_response.content)

        if os.path.exists(image_path):
            client.sendLocalImage(
                image_path, 
                message=None,
                thread_id=thread_id,
                thread_type=thread_type,
                width=1600,
                height=1600
            )
            os.remove(image_path)

    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"Đa xay ra loi khi goi API: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except KeyError as e:
        error_message = Message(text=f"Du lieu tu API khong đung cau truc: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
    except Exception as e:
        error_message = Message(text=f"Đa xay ra loi khong xac đinh: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type)
