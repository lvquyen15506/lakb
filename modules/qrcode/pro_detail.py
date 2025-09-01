# File: pro_detail.py - Optimized Version
# Author: L A K
# Description: Hiển thị thông tin thiết bị đang chạy bot với giao diện đẹp

from zlapi.models import *
import platform
import psutil
import time
import socket
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess
import io
import colorsys
import random
import glob
import requests
from datetime import datetime, timedelta, timezone
from core.bot_sys import is_admin
from modules.AI_GEMINI.pro_gemini import get_user_name_by_id

# Config
bot_name = "BOT"
cre = "L A K"
description = "Hiển thị thông tin thiết bị đang chạy bot"
start_time = time.time()

BACKGROUND_PATH = "background/"
CACHE_PATH = "modules/cache/"
OUTPUT_IMAGE_PATH = os.path.join(CACHE_PATH, "system_detail.png")

def get_uptime():
    """Lấy thời gian bot đã chạy"""
    try:
        uptime_sec = int(time.time() - start_time)
        hours = uptime_sec // 3600
        minutes = (uptime_sec % 3600) // 60
        seconds = uptime_sec % 60
        return f"{hours}h {minutes}m {seconds}s"
    except Exception: 
        return "N/A"

def get_ram():
    """Lấy thông tin RAM"""
    try:
        mem = psutil.virtual_memory()
        used = round(mem.used / (1024 ** 3), 2)
        total = round(mem.total / (1024 ** 3), 2)
        available = round(mem.available / (1024 ** 3), 2)
        percent = round(mem.percent, 1)
        return f"{used}/{total} GB ({percent}%)|Available: {available} GB"
    except Exception: 
        return "N/A"

def get_cpu():
    """Lấy thông tin CPU với xử lý lỗi tốt hơn"""
    try:
        cpu_name = platform.processor()
        
        # Nếu không lấy được tên CPU, thử các cách khác
        if not cpu_name or cpu_name.strip() == "":
            if os.name == 'nt':  # Windows
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                       r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                    cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                    winreg.CloseKey(key)
                except:
                    cpu_name = "Unknown Windows CPU"
            else:  # Linux/Unix
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if line.startswith('model name'):
                                cpu_name = line.split(':', 1)[1].strip()
                                break
                    if not cpu_name:
                        cpu_name = "Unknown Linux CPU"
                except:
                    cpu_name = "Unknown CPU"
        
        # Lấy thông tin sử dụng CPU
        cpu_percent = round(psutil.cpu_percent(interval=1), 1)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False) or cpu_count_logical
        
        # Lấy thông tin tần số
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq and cpu_freq.current:
                current_freq = round(cpu_freq.current, 0)
                max_freq = round(cpu_freq.max, 0) if cpu_freq.max else current_freq
                freq_info = f"{current_freq}/{max_freq} MHz"
            else:
                freq_info = "N/A MHz"
        except: 
            freq_info = "N/A MHz"
            
        # Cắt tên CPU nếu quá dài
        cpu_name_short = cpu_name[:45] if len(cpu_name) > 45 else cpu_name
        
        return f"{cpu_name_short}|{cpu_count_physical}C/{cpu_count_logical}T • {cpu_percent}%|{freq_info}"
    except Exception as e:
        print(f"Lỗi get_cpu: {e}")
        return "N/A"

def get_gpu():
    """Lấy thông tin GPU với hỗ trợ đa nền tảng"""
    try:
        if os.name == 'nt':  # Windows
            # Thử NVIDIA-SMI trước
            try:
                result = subprocess.run([
                    'nvidia-smi', 
                    '--query-gpu=name,memory.total,temperature.gpu', 
                    '--format=csv,noheader,nounits'
                ], capture_output=True, text=True, timeout=8)
                
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    gpu_data = lines[0].split(', ')
                    if len(gpu_data) >= 3:
                        name, memory, temp = gpu_data[0], gpu_data[1], gpu_data[2]
                        return f"{name[:40]}|{memory}MB VRAM • {temp}°C"
            except Exception as e:
                print(f"NVIDIA-SMI error: {e}")
            
            # Thử WMI
            try:
                import wmi
                c = wmi.WMI()
                gpus = c.Win32_VideoController()
                if gpus and len(gpus) > 0:
                    gpu_name = gpus[0].Name or "Unknown GPU"
                    return f"{gpu_name[:40]}|Windows GPU"
            except Exception as e:
                print(f"WMI error: {e}")
                
            return "Không tìm thấy GPU"
            
        else:  # Linux/Unix
            try:
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
                for line in result.stdout.splitlines():
                    if "VGA compatible controller" in line or "3D controller" in line:
                        gpu_info = line.split(': ')[1] if ': ' in line else line
                        return f"{gpu_info[:40]}|Linux GPU"
                return "Không tìm thấy GPU"
            except Exception as e:
                print(f"lspci error: {e}")
                return "Lỗi lấy thông tin GPU"
                
    except Exception as e:
        print(f"get_gpu error: {e}")
        return "Lỗi lấy thông tin GPU"

def get_disk():
    """Lấy thông tin ổ đĩa"""
    try:
        disk = psutil.disk_usage('/') if os.name != 'nt' else psutil.disk_usage('C:')
        used = round(disk.used / (1024 ** 3), 2)
        total = round(disk.total / (1024 ** 3), 2)
        free = round(disk.free / (1024 ** 3), 2)
        percent = round(disk.percent, 1)
        return f"{used}/{total} GB ({percent}%)|Free: {free} GB"
    except Exception: 
        return "N/A"

def get_os():
    """Lấy thông tin hệ điều hành"""
    try:
        system = platform.system()
        release = platform.release()
        arch = platform.architecture()[0]
        
        if system == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                product_name = winreg.QueryValueEx(key, "ProductName")[0]
                build = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
                winreg.CloseKey(key)
                return f"{product_name}|Build {build} • {arch}"
            except:
                return f"Windows {release}|{arch}"
                
        elif system == "Linux":
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            distro = line.split('=')[1].strip().strip('"')
                            return f"{distro}|Kernel {release} • {arch}"
            except:
                pass
            return f"Linux {release}|{arch}"
        else:
            return f"{system} {release}|{arch}"
    except Exception: 
        return platform.platform()

def get_python_ver():
    """Lấy thông tin Python"""
    try:
        impl = platform.python_implementation()
        version = platform.python_version()
        compiler = platform.python_compiler()
        compiler_short = compiler[:50] if len(compiler) > 50 else compiler
        return f"{impl} {version}|{compiler_short}"
    except Exception:
        return "N/A"

def get_boot_time():
    """Lấy thời gian khởi động hệ thống"""
    try:
        boot_dt = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_dt
        days = uptime.days
        hours, rem = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(rem, 60)
        uptime_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"
        return f"{boot_dt.strftime('%d/%m %H:%M')}|System uptime: {uptime_str}"
    except Exception: 
        return "N/A"

def get_loadavg():
    """Lấy thông tin tải hệ thống"""
    try:
        if hasattr(os, 'getloadavg'):  # Unix/Linux
            loads = os.getloadavg()
            return f"1min: {loads[0]:.2f}|5min: {loads[1]:.2f} • 15min: {loads[2]:.2f}"
        else:  # Windows
            load = (psutil.cpu_percent(interval=0.1) / 100) * psutil.cpu_count()
            return f"Est. Load: {load:.2f}|Windows approximation"
    except Exception: 
        return "N/A"

def get_username():
    """Lấy tên người dùng hệ thống"""
    try:
        return os.getenv('USER') or os.getenv('USERNAME') or "Unknown User"
    except:
        return "Unknown User"

def detect_environment():
    """Phát hiện môi trường đang chạy (Termux, WSL, Docker, etc.)"""
    try:
        env_info = []
        
        # Kiểm tra Termux (Android)
        if ('com.termux' in os.environ.get('PREFIX', '')) or os.path.exists('/data/data/com.termux'):
            env_info.append("Termux")
        
        # Kiểm tra WSL (Windows Subsystem for Linux)
        if 'microsoft' in platform.release().lower():
            env_info.append("WSL")
        elif os.path.exists('/proc/version'):
            try:
                with open('/proc/version', 'r') as f:
                    if 'microsoft' in f.read().lower():
                        env_info.append("WSL")
            except:
                pass
        
        # Kiểm tra Docker
        if os.path.exists('/.dockerenv'):
            env_info.append("Docker")
        
        # Kiểm tra shell environment
        shell = os.environ.get('SHELL', '').lower()
        if 'bash' in shell:
            env_info.append("Bash")
        elif 'zsh' in shell:
            env_info.append("Zsh")
        elif 'fish' in shell:
            env_info.append("Fish")
        
        # Kiểm tra Windows Terminal
        if os.name == 'nt':
            comspec = os.environ.get('COMSPEC', '').lower()
            if 'powershell' in comspec or os.environ.get('PSModulePath'):
                env_info.append("PowerShell")
            elif 'cmd' in comspec:
                env_info.append("CMD")
        
        # Kiểm tra distribution Linux
        if os.path.exists('/etc/lsb-release'):
            try:
                with open('/etc/lsb-release', 'r') as f:
                    content = f.read().lower()
                    if 'ubuntu' in content:
                        env_info.append("Ubuntu")
                    elif 'debian' in content:
                        env_info.append("Debian")
            except:
                pass
        
        # Kiểm tra cloud environment
        if os.environ.get('GOOGLE_CLOUD_PROJECT'):
            env_info.append("GCP")
        elif os.environ.get('AWS_EXECUTION_ENV'):
            env_info.append("AWS")
        elif os.environ.get('AZURE_CLIENT_ID'):
            env_info.append("Azure")
        
        return " + ".join(env_info) if env_info else "Standard Environment"
    except Exception as e:
        print(f"detect_environment error: {e}")
        return "Unknown Environment"

def get_app():
    """Lấy thông tin ứng dụng và môi trường"""
    try:
        env = detect_environment()
        return f"ZaloBot|Environment: {env}"
    except:
        return "ZaloBot|Environment: Unknown"

def get_network_info():
    """Lấy thông tin mạng"""
    try:
        # Kiểm tra kết nối internet
        status = "Offline"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(3)
            s.connect(('8.8.8.8', 80))
            status = "Connected"
            s.close()
        except:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(3)
                s.connect(('1.1.1.1', 80))
                status = "Connected"
                s.close()
            except:
                status = "Offline"
        
        # Lấy thông tin network I/O
        try:
            net_io = psutil.net_io_counters()
            sent = round(net_io.bytes_sent / (1024**2), 1)
            recv = round(net_io.bytes_recv / (1024**2), 1)
            return f"Status: {status}|↑{sent}MB ↓{recv}MB"
        except:
            return f"Status: {status}|I/O: N/A"
            
    except Exception: 
        return "N/A"

def download_avatar(avatar_url, save_path=None):
    """Tải avatar người dùng"""
    if not save_path:
        save_path = os.path.join(CACHE_PATH, "user_avatar_detail.png")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(avatar_url, stream=True, timeout=10, headers=headers)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(1024): 
                    if chunk:
                        f.write(chunk)
            return save_path
    except Exception as e:
        print(f"⚠ Lỗi tải avatar: {e}")
    return None

def safe_get_user_info(bot, author_id):
    """Lấy thông tin user một cách an toàn với nhiều phương pháp"""
    user_name = "User"
    avatar_url = None
    
    try:
        # Phương pháp 1: get_user_name_by_id
        try:
            name = get_user_name_by_id(bot, author_id)
            if name and isinstance(name, str) and name.strip():
                user_name = name.strip()[:30]  # Giới hạn độ dài
        except Exception as e:
            print(f"⚠ get_user_name_by_id lỗi: {e}")
        
        # Phương pháp 2: fetchUserInfo
        try:
            user_info = bot.fetchUserInfo(author_id)
            if user_info and hasattr(user_info, 'changed_profiles'):
                if author_id in user_info.changed_profiles:
                    profile = user_info.changed_profiles.get(author_id)
                    if profile:
                        # Lấy tên
                        if hasattr(profile, 'name') and profile.name:
                            user_name = str(profile.name).strip()[:30]
                        elif hasattr(profile, 'displayName') and profile.displayName:
                            user_name = str(profile.displayName).strip()[:30]
                        
                        # Lấy avatar
                        if hasattr(profile, 'avatar') and profile.avatar:
                            avatar_obj = profile.avatar
                            if isinstance(avatar_obj, str):
                                avatar_url = avatar_obj
                            elif isinstance(avatar_obj, dict):
                                avatar_url = (avatar_obj.get('normalUrl') or 
                                            avatar_obj.get('thumbnailUrl') or
                                            avatar_obj.get('url'))
        except Exception as e:
            print(f"⚠ fetchUserInfo lỗi: {e}")
        
        # Phương pháp 3: fetchThreadInfo (backup)
        try:
            if user_name == "User":  # Chỉ thử nếu chưa có tên
                thread_info = bot.fetchThreadInfo(author_id)
                if thread_info and hasattr(thread_info, 'name') and thread_info.name:
                    user_name = str(thread_info.name).strip()[:30]
        except Exception as e:
            print(f"⚠ fetchThreadInfo lỗi: {e}")
            
    except Exception as e:
        print(f"⚠ safe_get_user_info lỗi tổng quát: {e}")
    
    # Fallback cuối cùng
    if not user_name or user_name.strip() == "":
        user_name = f"User_{str(author_id)[-4:]}"
    
    return user_name, avatar_url

def generate_system_detail_image(bot, author_id, thread_id, thread_type):
    """Tạo ảnh thông tin hệ thống với layout tối ưu"""
    
    # Tìm ảnh background
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    images = []
    for ext in image_extensions:
        images.extend(glob.glob(os.path.join(BACKGROUND_PATH, ext)))
        images.extend(glob.glob(os.path.join(BACKGROUND_PATH, ext.upper())))
    
    if not images:
        print("⚠ Không tìm thấy ảnh background. Tạo ảnh mặc định...")
        # Tạo background đơn giản nếu không có ảnh
        bg_color = (random.randint(20, 60), random.randint(20, 60), random.randint(60, 100))
        bg_image = Image.new("RGBA", (4800, 3600), bg_color + (255,))
    else:
        image_path = random.choice(images)
        try:
            bg_image = Image.open(image_path).convert("RGBA")
        except Exception as e:
            print(f"⚠ Lỗi mở ảnh {image_path}: {e}")
            bg_color = (30, 30, 60, 255)
            bg_image = Image.new("RGBA", (4800, 3600), bg_color)

    try:
        # Kích thước canvas và output
        canvas_size = (4800, 3600)  # Kích thước làm việc
        final_size = (3000, 2250)  # Kích thước xuất ra (4:3)

        # Resize và blur background
        bg_image = bg_image.resize(canvas_size, Image.Resampling.LANCZOS)
        bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=12))
        
        # Tạo overlay
        overlay = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Box chính với padding hợp lý
        padding = 80
        box_x1, box_y1 = padding, padding
        box_x2, box_y2 = canvas_size[0] - padding, canvas_size[1] - padding
        box_color = (12, 12, 12, 170)  # Màu nền box
        
        # Vẽ box chính với border radius
        draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], 
                              radius=60, fill=box_color)

        # Load fonts
        font_paths = {
            'arial': ['arial unicode ms.otf', 'arial.ttf', 'DejaVuSans.ttf'],
            'emoji': ['emoji.ttf', 'NotoColorEmoji.ttf', 'seguiemj.ttf']
        }
        
        def load_font_safe(font_list, size):
            for font_name in font_list:
                try:
                    return ImageFont.truetype(font_name, size)
                except:
                    continue
            return ImageFont.load_default()

        # Định nghĩa fonts
        font_title = load_font_safe(font_paths['arial'], 140)
        font_label = load_font_safe(font_paths['arial'], 90) 
        font_value = load_font_safe(font_paths['arial'], 75)
        font_time = load_font_safe(font_paths['arial'], 85)
        font_icon = load_font_safe(font_paths['emoji'], 100)
        font_icon_large = load_font_safe(font_paths['emoji'], 180)

        def draw_text_with_shadow(draw, position, text, font, fill, shadow_color=(0,0,0,200), offset=2):
            """Vẽ text với shadow"""
            x, y = position
            # Shadow
            draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
            # Text chính  
            draw.text((x, y), text, font=font, fill=fill)

        # Hiển thị thời gian ở góc phải
        vietnam_now = datetime.now(timezone(timedelta(hours=7)))
        time_icon = "🌤️" if 6 <= vietnam_now.hour < 18 else "🌙"
        time_text = vietnam_now.strftime('%H:%M')
        date_text = vietnam_now.strftime('%d/%m')
        
        time_x, time_y = box_x2 - 350, box_y1 + 30
        time_color = (255, 255, 255, 255)
        
        draw_text_with_shadow(draw, (time_x - 120, time_y), time_icon, font_icon, (255, 215, 0))
        draw_text_with_shadow(draw, (time_x, time_y), time_text, font_time, time_color)
        draw_text_with_shadow(draw, (time_x, time_y + 60), date_text, font_value, (200, 200, 200))

        # Lấy thông tin user
        user_name, avatar_url = safe_get_user_info(bot, author_id)
        greeting_name = "Chủ Nhân" if is_admin(bot, author_id) else user_name
        
        # Xử lý avatar
        avatar_displayed = False
        if avatar_url:
            avatar_path = download_avatar(avatar_url)
            if avatar_path and os.path.exists(avatar_path):
                try:
                    avatar_size = 220
                    avatar_img = Image.open(avatar_path).convert("RGBA")
                    avatar_img = avatar_img.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                    
                    # Tạo mask tròn
                    mask = Image.new("L", (avatar_size, avatar_size), 0)
                    ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    
                    # Border cho avatar
                    border_size = avatar_size + 16
                    border_image = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
                    draw_border = ImageDraw.Draw(border_image)
                    draw_border.ellipse([(0, 0), (border_size, border_size)], 
                                      fill=(255, 255, 255, 100))
                    
                    # Paste avatar
                    avatar_x, avatar_y = box_x1 + 60, box_y1 + 60
                    overlay.paste(border_image, (avatar_x, avatar_y), border_image)
                    overlay.paste(avatar_img, (avatar_x + 8, avatar_y + 8), mask)
                    avatar_displayed = True
                    
                except Exception as e:
                    print(f"⚠ Lỗi xử lý avatar: {e}")
        
        # Title và subtitle
        title_text = "THÔNG TIN HỆ THỐNG"
        title_x = box_x1 + (350 if avatar_displayed else 60)
        title_y = box_y1 + 80
        
        draw_text_with_shadow(draw, (title_x, title_y), title_text, font_title, (255, 255, 102))
        
        subtitle_text = f"Xin chào {greeting_name}, đây là thông tin chi tiết hệ thống"
        draw_text_with_shadow(draw, (title_x, title_y + 160), subtitle_text, font_value, (173, 216, 230))

        # Thu thập thông tin hệ thống
        system_info = [
            ("👤", "User", get_username()),
            ("📱", "App", get_app()), 
            ("🧠", "Memory", get_ram()),
            ("⚡", "CPU", get_cpu()),
            ("🎮", "GPU", get_gpu()),
            ("💽", "Storage", get_disk()),
            ("🖥️", "OS", get_os()),
            ("📊", "Load Average", get_loadavg()),
            ("🐍", "Python", get_python_ver()),
            ("🌐", "Network", get_network_info()),
            ("🚀", "Boot Time", get_boot_time()),
            ("⏰", "Bot Uptime", get_uptime())
        ]
        
        # Chia thành 2 cột
        items_per_col = 6
        col1_items = system_info[:items_per_col]
        col2_items = system_info[items_per_col:]

        # Vị trí các cột
        start_y = box_y1 + 320
        line_height = 220  # Khoảng cách giữa các dòng
        col1_x = box_x1 + 100
        col2_x = box_x1 + 2400
        
        # Màu sắc
        label_color = (135, 206, 250, 255)  # Light blue
        value_color = (255, 255, 255, 255)  # White
        icon_color = (255, 182, 193, 255)   # Light pink

        # Vẽ cột 1
        for i, (emoji, label, value) in enumerate(col1_items):
            y = start_y + i * line_height
            
            # Icon
            draw_text_with_shadow(draw, (col1_x, y), emoji, font_icon, icon_color)
            
            # Label
            draw_text_with_shadow(draw, (col1_x + 120, y), f"{label}:", font_label, label_color)
            
            # Values - split bởi ký tự |
            value_lines = value.split('|')
            for j, line in enumerate(value_lines):
                if line.strip():  # Chỉ vẽ dòng không rỗng
                    draw_text_with_shadow(draw, (col1_x + 120, y + 90 + j * 55), 
                                        line.strip(), font_value, value_color)

        # Vẽ cột 2  
        for i, (emoji, label, value) in enumerate(col2_items):
            y = start_y + i * line_height
            
            # Icon
            draw_text_with_shadow(draw, (col2_x, y), emoji, font_icon, icon_color)
            
            # Label
            draw_text_with_shadow(draw, (col2_x + 120, y), f"{label}:", font_label, label_color)
            
            # Values
            value_lines = value.split('|') 
            for j, line in enumerate(value_lines):
                if line.strip():
                    draw_text_with_shadow(draw, (col2_x + 120, y + 90 + j * 55), 
                                        line.strip(), font_value, value_color)
        
        # Icon trang trí góc phải
        decoration_icons = ["🎧", "🎵", "📊", "💻", "⚙️", "🔧", "📡", "🌟", "⚡"]
        right_icon = random.choice(decoration_icons)
        icon_x = box_x2 - 250
        icon_y = (box_y1 + box_y2 - 180) // 2
        draw_text_with_shadow(draw, (icon_x, icon_y), right_icon, font_icon_large, (144, 238, 144))
        
        # Vẽ border ngoài
        border_color = (255, 255, 255, 100)
        draw.rounded_rectangle([(box_x1-2, box_y1-2), (box_x2+2, box_y2+2)], 
                              radius=62, outline=border_color, width=4)

        # Tạo ảnh cuối cùng
        final_image = Image.alpha_composite(bg_image, overlay)
        final_image = final_image.resize(final_size, Image.Resampling.LANCZOS)
        
        # Lưu ảnh
        os.makedirs(CACHE_PATH, exist_ok=True)
        final_image.save(OUTPUT_IMAGE_PATH, "PNG", quality=95, optimize=True)
        
        print(f"✅ Ảnh system detail đã được tạo: {OUTPUT_IMAGE_PATH}")
        return OUTPUT_IMAGE_PATH

    except Exception as e:
        print(f"❌ Lỗi tạo ảnh system detail: {e}")
        import traceback
        traceback.print_exc()
        return None

def handle_detail_command(message, message_object, thread_id, thread_type, author_id, bot):
    """Xử lý lệnh detail - hiển thị thông tin hệ thống"""
    
    try:
        print(f"🔄 Bắt đầu tạo system detail cho user {author_id}")
        
        # Tạo ảnh thông tin hệ thống
        image_path = generate_system_detail_image(bot, author_id, thread_id, thread_type)
        
        if not image_path or not os.path.exists(image_path):
            print("⚠ Không thể tạo ảnh, sử dụng text fallback")
            
            # Fallback text format nếu không tạo được ảnh
            system_info = f"""
╭─╌「 🖥️ THÔNG TIN HỆ THỐNG 」
│
├─ 👤 User: {get_username()}
├─ 📱 App: {get_app().split('|')[0]}  
├─ 🧠 Memory: {get_ram().split('|')[0]}
├─ ⚡ CPU: {get_cpu().split('|')[0]}
├─ 🎮 GPU: {get_gpu().split('|')[0]}
├─ 💽 Storage: {get_disk().split('|')[0]}
├─ 🖥️ OS: {get_os().split('|')[0]}
├─ 📊 Load: {get_loadavg().split('|')[0]}
├─ 🐍 Python: {get_python_ver().split('|')[0]}
├─ 🌐 Network: {get_network_info().split('|')[0]}
├─ 🚀 Boot: {get_boot_time().split('|')[0]}
├─ ⏰ Uptime: {get_uptime()}
│
╰─╌「 Generated by {bot_name} | {cre} 」
            """
            
            bot.replyMessage(
                Message(text=system_info.strip()), 
                message_object, 
                thread_id=thread_id, 
                thread_type=thread_type
            )
            return

        # React tích cực
        positive_reactions = ["👍", "💖", "🚀", "😎", "💪", "🌟", "⚡", "🔥", "✨", "👌"]
        try:
            bot.sendReaction(message_object, random.choice(positive_reactions), thread_id, thread_type)
        except Exception as e:
            print(f"⚠ Không thể gửi reaction: {e}")
        
        # Lấy tên user và chuẩn bị message
        user_name, _ = safe_get_user_info(bot, author_id)
        message_text = f"{user_name}\n📊 Thông tin chi tiết hệ thống của bạn đây!"

        # Thử gửi ảnh với kích thước gốc
        try:
            print("📤 Đang gửi ảnh system detail...")
            
            send_result = bot.sendLocalImage(
                imagePath=image_path,
                message=Message(
                    text=message_text, 
                    mention=Mention(uid=author_id, length=len(user_name), offset=0)
                ),
                thread_id=thread_id,
                thread_type=thread_type,
                width=3000,
                height=2250
            )
            
            if send_result:
                print("✅ Gửi ảnh thành công!")
            else:
                raise Exception("sendLocalImage returned None")
                
        except Exception as e:
            print(f"⚠ Lỗi gửi ảnh gốc: {e}, thử gửi ảnh nhỏ hơn...")
            
            # Thử resize ảnh nhỏ hơn nếu gửi lỗi
            try:
                smaller_image = Image.open(image_path)
                smaller_image = smaller_image.resize((2000, 1500), Image.Resampling.LANCZOS)
                smaller_path = image_path.replace('.png', '_compressed.png')
                smaller_image.save(smaller_path, "PNG", quality=85, optimize=True)
                
                send_result = bot.sendLocalImage(
                    imagePath=smaller_path,
                    message=Message(text=message_text),
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=2000,
                    height=1500
                )
                
                if send_result:
                    print("✅ Gửi ảnh nén thành công!")
                else:
                    raise Exception("Compressed image also failed")
                    
                # Xóa ảnh nén tạm
                try:
                    if os.path.exists(smaller_path):
                        os.remove(smaller_path)
                except:
                    pass
                    
            except Exception as e2:
                print(f"❌ Cả 2 cách gửi ảnh đều lỗi: {e2}")
                bot.replyMessage(
                    Message(text="⚠ Lỗi gửi ảnh hệ thống. Vui lòng thử lại sau."), 
                    message_object, 
                    thread_id=thread_id, 
                    thread_type=thread_type
                )

        # Dọn dẹp files tạm
        cleanup_files = [
            image_path,
            os.path.join(CACHE_PATH, "user_avatar_detail.png"),
            image_path.replace('.png', '_compressed.png')
        ]
        
        for file_path in cleanup_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🗑️ Đã xóa file tạm: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"⚠ Lỗi xóa file {file_path}: {e}")
            
    except Exception as e:
        print(f"❌ Lỗi trong handle_detail_command: {e}")
        import traceback
        traceback.print_exc()
        
        # Gửi thông báo lỗi cho user
        error_msg = f"⚠ Đã xảy ra lỗi khi tạo thông tin hệ thống: {str(e)[:100]}..."
        try:
            bot.replyMessage(
                Message(text=error_msg), 
                message_object, 
                thread_id=thread_id, 
                thread_type=thread_type
            )
        except:
            print("❌ Không thể gửi thông báo lỗi")

# ============ CÁC HÀM HỖ TRỢ THÊM ============

def get_system_summary():
    """Lấy tóm tắt hệ thống để debug"""
    return {
        'os': platform.system(),
        'python': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_gb': round(psutil.virtual_memory().total / (1024**3), 1),
        'disk_gb': round(psutil.disk_usage('/').total / (1024**3), 1) if os.name != 'nt' else round(psutil.disk_usage('C:').total / (1024**3), 1),
        'uptime_hours': round((time.time() - start_time) / 3600, 1),
        'environment': detect_environment()
    }

def test_system_info():
    """Test function để kiểm tra các thông tin hệ thống"""
    print("🧪 Testing system information functions...")
    
    functions_to_test = [
        ("Username", get_username),
        ("App Info", get_app),
        ("RAM", get_ram), 
        ("CPU", get_cpu),
        ("GPU", get_gpu),
        ("Disk", get_disk),
        ("OS", get_os),
        ("Python", get_python_ver),
        ("Load Avg", get_loadavg),
        ("Network", get_network_info),
        ("Boot Time", get_boot_time),
        ("Uptime", get_uptime),
    ]
    
    for name, func in functions_to_test:
        try:
            result = func()
            status = "✅" if result != "N/A" else "⚠️"
            print(f"{status} {name}: {result}")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
    
    print(f"\n📋 System Summary: {get_system_summary()}")

# Test khi chạy trực tiếp file
if __name__ == "__main__":
    test_system_info()
    
