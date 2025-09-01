from zlapi.models import Message
import json
import urllib.parse
import requests
import os
import time
import ffmpeg
from PIL import Image

des = {
    'version': "1.4.1",
    'credits': "Nguyen Đuc Tai x TRBAYK (NGSON)",
    'description': "Scan QRCODE",
    'power': "Thanh vien"
}

luu_anh = "modules/cache"
ten_anh = os.path.join(luu_anh, "qr_img.jpg")
os.makedirs(luu_anh, exist_ok=True)

def handle_scanqr_command(message, message_object, thread_id, thread_type, author_id, client):
    msg_obj = message_object
    if msg_obj.msgType == "chat.photo":
        img_url = urllib.parse.unquote(msg_obj.content.href.replace("\\/", "/"))
        handle_scan_command(img_url, thread_id, thread_type, client, message_object)
    elif msg_obj.quote:
        attach = msg_obj.quote.attach
        if attach:
            try:
                attach_data = json.loads(attach)
                image_url = attach_data.get('hdUrl') or attach_data.get('href')
                if image_url:
                    handle_scan_command(image_url, thread_id, thread_type, client, message_object)
                else:
                    send_error_message(thread_id, thread_type, client)
            except json.JSONDecodeError as e:
                print(f"Loi JSON: {str(e)}")
                send_error_message(thread_id, thread_type, client)
        else:
            send_error_message(thread_id, thread_type, client)
    else:
        send_error_message(thread_id, thread_type, client)

def handle_scan_command(image_url, thread_id, thread_type, client, message_object):
    client.replyMessage(Message(text="Đoi bo ti"), message_object, thread_id=thread_id, thread_type=thread_type)
    if download_image(image_url, ten_anh):
        api_url = "http://api.qrserver.com/v1/read-qr-code/"
        try:
            with open(ten_anh, "rb") as img_file:
                files = {"file": img_file}
                response = requests.post(api_url, files=files)
            try:
                data = response.json()
                datascan = "Khong thay du lieu."
                if data and isinstance(data, list) and len(data) > 0:
                    if data[0].get("symbol") and isinstance(data[0]["symbol"], list) and len(data[0]["symbol"]) > 0:
                        symbol_data = data[0]["symbol"][0]
                        if symbol_data.get("error"):
                            datascan = f"Loi tu QR API: {symbol_data.get('error')}"
                        elif symbol_data.get("data"):
                            datascan = symbol_data["data"]
                if "http" in datascan.lower()[:5]:
                    file_extension = datascan.lower().split(".")[-1] if "." in datascan else None
                    if file_extension in ["png", "jpg", "jpeg", "bmp", "webp"]:
                        if download_image(datascan, ten_anh):
                            try:
                                img = Image.open(ten_anh)
                                width, height = img.size
                                client.sendLocalImage(
                                    imagePath=ten_anh,
                                    thread_id=thread_id,
                                    thread_type=thread_type,
                                    width=width,
                                    height=height
                                )
                            except Exception as pil_e:
                                print(f"Loi PIL: {str(pil_e)}")
                                send_error_message(thread_id, thread_type, client, "Khong the xu ly anh tu QR Code.")
                            finally:
                                os.remove(ten_anh)
                        else:
                            send_error_message(thread_id, thread_type, client, "Khong the tai xuong anh tu QR Code.")
                    elif file_extension == "gif":
                        gif_path = "modules/baucua/VxkZaloBot.gif"
                        if download_image(datascan, gif_path):
                            size = get_gif_size(gif_path) or (300, 300)
                            client.sendLocalGif(
                                gifPath=gif_path,
                                thumbnailUrl=None,
                                thread_id=thread_id,
                                thread_type=thread_type,
                                width=size[0],
                                height=size[1]
                            )
                            os.remove(gif_path)
                        else:
                            send_error_message(thread_id, thread_type, client, "Khong the tai xuong GIF tu QR Code.")
                    elif file_extension == "mp4" or file_extension is None:
                        try:
                            image_url = "https://xuankien.dev"
                            duration, width, height = get_video_info(datascan)
                            client.sendRemoteVideo(
                                datascan,
                                image_url,
                                duration=int(duration),
                                message=None,
                                thread_id=thread_id,
                                thread_type=thread_type,
                                width=width,
                                height=height
                            )
                        except Exception as e:
                            print(f"Loi khi gui video: {str(e)}")
                            send_error_message(thread_id, thread_type, client, "Khong the tai hoac gui video.")
                    else:
                        client.replyMessage(Message(text=f"{datascan}"), message_object, thread_id=thread_id, thread_type=thread_type)
                else:
                    client.replyMessage(Message(text=datascan), message_object, thread_id=thread_id, thread_type=thread_type)
            except Exception as e:
                print(f"Loi xu ly JSON tu API: {str(e)}")
                send_error_message(thread_id, thread_type, client, "Loi khi scan QR Code.")
        except FileNotFoundError:
            send_error_message(thread_id, thread_type, client, "Khong tim thay file anh sau khi tai.")
        except Exception as e:
            print(f"Loi khi mo hoac xu ly file anh: {str(e)}")
            send_error_message(thread_id, thread_type, client, "Loi khi xu ly file anh.")
        finally:
            try:
                os.remove(ten_anh)
            except Exception as e:
                print(f"Loi xoa anh: {str(e)}")
    else:
        send_error_message(thread_id, thread_type, client, "Khong the tai xuong anh QR Code.")

def download_image(url, save_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return True
    except Exception as e:
        print(f"Loi tai anh: {str(e)}")
        return False

def get_gif_size(gif_path):
    try:
        with Image.open(gif_path) as img:
            return img.size
    except Exception as e:
        print(f"Loi khi lay kich thuoc GIF: {str(e)}")
        return None

def get_video_info(video_url, max_retries=3):
    for attempt in range(max_retries):
        try:
            probe = ffmpeg.probe(video_url)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if not video_stream:
                raise ValueError("Khong tim thay luong video trong URL")

            duration = float(video_stream['duration']) * 1000
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            return duration, width, height
        except Exception as e:
            print(f"Loi khi lay thong tin video (lan {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise Exception(f"Khong the lay thong tin video sau nhieu lan thu: {str(e)}") from e

def send_error_message(thread_id, thread_type, client, error_message="Vui long reply anh Qr Code can scan"):
    client.send(Message(text=error_message), thread_id=thread_id, thread_type=thread_type)
