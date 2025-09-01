from zlapi.models import Message
import json
import urllib.parse
import os

des = {
    'version': "1.0.0",
    'credits': "Nguyen Đuc Tai x TRBAYK X Quoc Khanh",
    'description': "Lenh lay va luu link hinh anh, video, file.",
    'power': "Thanh vien"
}
def handle_save_command(message, message_object, thread_id, thread_type, author_id, client):
    msg_obj = message_object

    if msg_obj.msgType == "chat.photo":
        img_url = msg_obj.content.href.replace("\\/", "/")
        img_url = urllib.parse.unquote(img_url)
        save_link_to_file(img_url) 
        send_image_link(img_url, thread_id, thread_type, client)

    elif msg_obj.quote:
        attach = msg_obj.quote.attach
        if attach:
            try:
                attach_data = json.loads(attach)  # Phan tich du lieu tep đinh kem
            except json.JSONDecodeError as e:
                print(f"Loi khi phan tich JSON: {str(e)}")
                return

          
            media_url = attach_data.get('hdUrl') or attach_data.get('href')
            if media_url:
                save_link_to_file(media_url) 
                send_image_link(media_url, thread_id, thread_type, client)
            else:
                send_error_message(thread_id, thread_type, client)
        else:
            send_error_message(thread_id, thread_type, client)
    else:
        send_error_message(thread_id, thread_type, client)

def save_link_to_file(link):
    try:
        # Kiem tra neu thu muc data chua ton tai thi tao moi
        if not os.path.exists('data'):
            os.makedirs('data')

        # Mo file vdgai.txt va ghi link vao cuoi file
        with open("data/vdgai.txt", "a") as file:
            file.write(link + "\n")
        print(f"Đa luu link: {link}")
    except Exception as e:
        print(f"Loi khi luu link: {str(e)}")

def send_image_link(media_url, thread_id, thread_type, client):
    if media_url:
        message_text = f"{media_url}\n\n[✅ Đa luu vao file vdgai.txt]"
        
        message_to_send = Message(
            text=message_text,
        )
        
        if hasattr(client, 'send'):
            client.send(message_to_send, thread_id, thread_type)
        else:
            print("Client khong ho tro gui tin nhan.")

def send_error_message(thread_id, thread_type, client):
    error_message = Message(
        text="Vui long reply (phan hoi) hinh anh, video, hoac file đe lay link.",
    )
    
    if hasattr(client, 'send'):
        client.send(error_message, thread_id, thread_type)
    else:
        print("Client khong ho tro gui tin nhan.")
