import requests
from zlapi.models import Message
import ffmpeg
import json
import io
import os
from PIL import Image

def get_video_info(video_url):
    try:
        probe = ffmpeg.probe(video_url)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream:
            duration = float(video_stream.get('duration', 0)) * 1000
            width = int(video_stream.get('width', 1200))
            height = int(video_stream.get('height', 1600))
            return duration, width, height
        else:
            return 0, 1200, 1600
    except Exception as e:
        return 0, 1200, 1600

def handle_vdtiktok_command(message, message_object, thread_id, thread_type, author_id, client):
    content = message.strip().split()
    if len(content) < 2:
        client.replyMessage(Message(text="Vui long nhap mot đuong link hop le."), message_object, thread_id, thread_type, ttl=60000)
        return

    video_link = content[1].strip()

    if not (video_link.startswith("https://vt.tiktok.com/") or video_link.startswith("https://www.tiktok.com/")):
        client.replyMessage(Message(text="Vui long nhap mot link TikTok hop le."), message_object, thread_id, thread_type, ttl=60000)
        return

    api_url = f"http://taitiktok.x10.mx/taivideo.php?url={video_link}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()["data"]

        user_info = client.fetchUserInfo(author_id)
        user_name = user_info.changed_profiles[author_id].zaloName

        title = data.get('title', 'Khong co tieu đe')
        author_name = data.get('author', {}).get('nickname', 'Khong ro')
        thumbnail_url = data.get('cover')
        video_url = data.get('play')
        image_urls = data.get('images', [])
        audio_url = data.get('music')

        messagesend = Message(text=f"[ {user_name} ]\n\n• 🎬 Nen tang: TikTok\n• 👤 Tac gia: {author_name}\n• 💻 Tieu đe: {title}")

        if video_url and not image_urls:
            video_duration, video_width, video_height = get_video_info(video_url)
            client.sendRemoteVideo(
                video_url,
                thumbnail_url,
                duration=video_duration,
                message=messagesend,
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=86400000,
                width=video_width,
                height=video_height
            )

        elif image_urls:
            if len(image_urls) > 1:
                image_paths = []
                for idx, url in enumerate(image_urls):
                    img_response = requests.get(url)
                    img_response.raise_for_status()
                    img_path = f"temp_image_{idx}.jpg"
                    with open(img_path, 'wb') as f:
                        f.write(img_response.content)
                    image_paths.append(img_path)

                client.sendMultiLocalImage(
                    imagePathList=image_paths,
                    message=messagesend,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=86400000
                )

                if audio_url:
                    client.sendRemoteVoice(voiceUrl=audio_url, thread_id=thread_id, thread_type=thread_type, ttl=86400000)

                for path in image_paths:
                    os.remove(path)

            else:
                img_response = requests.get(image_urls[0])
                img_response.raise_for_status()
                output_path = "temp_image.jpg"
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)

                with Image.open(output_path) as img:
                    width, height = img.size

                client.sendLocalImage(
                    output_path,
                    message=messagesend,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=width,
                    height=height,
                    ttl=200000
                )

                if audio_url:
                    client.sendRemoteVoice(voiceUrl=audio_url, thread_id=thread_id, thread_type=thread_type, ttl=86400000)
                os.remove(output_path)

    except requests.exceptions.RequestException as e:
        client.replyMessage(Message(text=f"Loi khi goi API: {str(e)}"), message_object, thread_id, thread_type, ttl=60000)
    except Exception as e:
        client.replyMessage(Message(text=f"Loi xu ly: {str(e)}"), message_object, thread_id, thread_type, ttl=60000)
