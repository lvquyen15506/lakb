import sys
import requests
import logging
import base64
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_next_api_key():
    return "AIzaSyAjfdo8Wxk25p7nsJPL2wG65z6R4UZos3E"

def generate_image(prompt):
    api_key = get_next_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    headers = {"Content-Type": "application/json"}

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Image generation failed: {e}")
        return None

def save_image_from_result(result_json, output_path="generated_image.png"):
    try:
        for part in result_json["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                base64_data = part["inlineData"]["data"]
                image_bytes = base64.b64decode(base64_data)
                image_stream = BytesIO(image_bytes)
                img = Image.open(image_stream).convert("RGB")
                img = img.filter(ImageFilter.SHARPEN)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(2.0)
                img.save(output_path)
                width, height = img.size
                logging.info(f"Image saved to: {output_path}, Size: {width}x{height}")
                return output_path, (width, height)
        logging.error("No inlineData found in response parts.")
        return None, None
    except Exception as e:
        logging.error(f"Error decoding or saving image: {e}")
        return None, None

def create_image(prompt, output_path="generated_image.png"):
    if not prompt:
        logging.error("No prompt provided.")
        return None, None

    result_json = generate_image(prompt)
    if not result_json or "candidates" not in result_json or "content" not in result_json["candidates"][0]:
        logging.error(f"Failed to generate image for prompt '{prompt}'")
        return None, None

    return save_image_from_result(result_json, output_path)

def main():
    # Lay prompt tu dong lenh, noi cac argument thanh chuoi
    if len(sys.argv) < 2:
        print("Vui long nhap mo ta anh sau lenh, vi du:\n  python3 img.py con cho")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    output_path = "generated_image.png"

    image_path, image_size = create_image(prompt, output_path)
    if image_path and image_size:
        width, height = image_size
        print(f"Anh đa đuoc luu tai: {image_path}, Kich thuoc: {width}x{height}")
    else:
        print(f"Khong the tao anh tu mo ta '{prompt}'. Vui long thu lai!")

if __name__ == "__main__":
    main()
