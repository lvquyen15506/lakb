import sys
import time
import random
import string
import threading
import os

# Gia lap mot so bien, class, ham can thiet (ban thay bang ban that)
class xColor:
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WHITE = '\033[97m'

class Style:
    RESET_ALL = '\033[0m'
    BRIGHT = '\033[1m'

def _rand_name_():
    # Tra ve username ngau nhien
    return 'user' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

def _rand_email_():
    # Tra ve email ngau nhien
    prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    domain = random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])
    return f"{prefix}@{domain}"

def _rand_pw_():
    # Tra ve password ngau nhien
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def _rand_str_(length, chars=string.ascii_letters):
    return ''.join(random.choices(chars, k=length))

def excute(url, headers=None, payload=None, thread_id=None, step=None, proxies_dict=None):
    # Ham gia lap goi API, ban thay bang ham that
    # Tra ve dict hoac "proxy_dead", "too_many_requests"
    # Đe demo thi luon tra thanh cong:
    return {'result': {'status': 200}}

def get_proxy(proxy_queue, thread_id, stop_event):
    # Ham gia lap lay proxy tu queue
    # Tra ve mot proxy string hoac None neu het
    try:
        return proxy_queue.get_nowait()
    except:
        return None

def format_proxy(proxy):
    # Ham gia lap format proxy cho requests
    if proxy:
        return {"http": proxy, "https": proxy}
    return {}

def init_proxy():
    # Khoi tao queue proxy va so thread, gia lap 5 proxy, 5 thread
    import queue
    q = queue.Queue()
    for i in range(5):
        q.put(f"http://proxy{i}.example.com:8080")
    return q, 5

def typing_print(text, delay=0.01):
    for c in text:
        print(c, end='', flush=True)
        time.sleep(delay)
    print()

def _clear_():
    os.system('cls' if os.name == 'nt' else 'clear')

def _banner_():
    print(f"{xColor.CYAN}=== zLocket Tool Pro ==={Style.RESET_ALL}")

# Gia lap config class
class zLocket:
    VERSION_TOOL = "1.0"
    NAME_TOOL = "zLocketUser"
    TARGET_FRIEND_UID = "@becuachiii"
    API_BASE_URL = "https://api.locket.com"
    FIREBASE_API_KEY = "your_firebase_api_key"
    FIREBASE_APP_CHECK = True
    ACCOUNTS_PER_PROXY = 10

    def headers_locket(self):
        return {"User-Agent": "zLocketBot/1.0"}

    def _print(self, msg):
        print(msg)

    def _blinking_(self, msg, blinks=5):
        for _ in range(blinks):
            print(msg)
            time.sleep(0.3)

    def _loader_(self, msg, duration=1):
        print(msg)
        time.sleep(duration)

    def _randchar_(self, duration=1):
        time.sleep(duration)

    def _sequence_(self, msg, duration=1):
        print(msg)
        time.sleep(duration)

# Ham step2_finalize_user đa đuoc ban cho, copy lai y nguyen:
def step2_finalize_user(id_token, thread_id, proxies_dict):
    if not id_token:
        config._print(
            f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL} | {xColor.MAGENTA}Profile{Style.RESET_ALL}] {xColor.RED}[✗] Profile creation failed: Invalid token")
        return False
    first_name=config.NAME_TOOL
    last_name=' '.join(random.sample([
        '😀', '😂', '😍', '🥰', '😊', '😇', '😚', '😘', '😻', '😽', '🤗',
        '😎', '🥳', '😜', '🤩', '😢', '😡', '😴', '🙈', '🙌', '💖', '🔥', '👍',
        '✨', '🌟', '🍎', '🍕', '🚀', '🎉', '🎈', '🌈', '🐶', '🐱', '🦁',
        '😋', '😬', '😳', '😷', '🤓', '😈', '👻', '💪', '👏', '🙏', '💕', '💔',
        '🌹', '🍒', '🍉', '🍔', '🍟', '☕', '🍷', '🎂', '🎁', '🎄', '🎃', '🔔',
        '⚡', '💡', '📚', '✈️', '🚗', '🏠', '⛰️', '🌊', '☀️', '☁️', '❄️', '🌙',
        '🐻', '🐼', '🐸', '🐝', '🦄', '🐙', '🦋', '🌸', '🌺', '🌴', '🏀', '⚽', '🎸'
    ], 5))
    username=_rand_name_()
    payload={
        "data": {
            "username": username,
            "last_name": last_name,
            "require_username": True,
            "first_name": first_name
        }
    }
    headers=config.headers_locket()
    headers['Authorization']=f"Bearer {id_token}"
    result=excute(
        f"{config.API_BASE_URL}/finalizeTemporaryUser",
        headers=headers,
        payload=payload,
        thread_id=thread_id,
        step="Profile",
        proxies_dict=proxies_dict
    )
    if result:
        config._print(
            f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL} | {xColor.MAGENTA}Profile{Style.RESET_ALL}] {xColor.GREEN}[✓] Profile created: {xColor.YELLOW}{username}")
        return True
    config._print(
        f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL} | {xColor.MAGENTA}Profile{Style.RESET_ALL}] {xColor.RED}[✗] Profile creation failed")
    return False

def step3_send_friend_request(id_token, thread_id, proxies_dict):
    if not id_token:
        config._print(
            f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL} | {xColor.MAGENTA}Friend{Style.RESET_ALL}] {xColor.RED}[✗] Connection failed: Invalid token")
        return False
    payload={
        "data": {
            "user_uid": config.TARGET_FRIEND_UID,
            "source": "signUp",
            "platform": "iOS",
            "messenger": "Messages",
            "invite_variant": {"value": "1002", "@type": "type.googleapis.com/google.protobuf.Int64Value"},
            "share_history_eligible": True,
            "rollcall": False,
            "prompted_reengagement": False,
            "create_ofr_for_temp_users": False,
            "get_reengagement_status": False
        }
    }
    headers=config.headers_locket()
    headers['Authorization']=f"Bearer {id_token}"
    result=excute(
        f"{config.API_BASE_URL}/sendFriendRequest",
        headers=headers,
        payload=payload,
        thread_id=thread_id,
        step="Friend",
        proxies_dict=proxies_dict
    )
    if result:
        config._print(
            f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL} | {xColor.MAGENTA}Friend{Style.RESET_ALL}] {xColor.GREEN}[✓] Connection established with target")
        return True
    config._print(
        f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL} | {xColor.MAGENTA}Friend{Style.RESET_ALL}] {xColor.RED}[✗] Connection failed")
    return False

def _cd_(message, count=5, delay=0.2):
    for i in range(count, 0, -1):
        binary=bin(i)[2:].zfill(8)
        sys.stdout.write(
            f"\r{xColor.CYAN}[{xColor.WHITE}*{xColor.CYAN}] {xColor.GREEN}{message} {xColor.RED}{binary}")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(
        f"\r{xColor.CYAN}[{xColor.WHITE}*{xColor.CYAN}] {xColor.GREEN}{message} {xColor.GREEN}READY      \n")
    sys.stdout.flush()

def step1b_sign_in(email, password, thread_id, proxies_dict):
    # Gia lap ham đang nhap, tra ve id_token dang string neu thanh cong
    return "fake_id_token_12345"

def step1_create_account(thread_id, proxy_queue, stop_event):
    while not stop_event.is_set():
        current_proxy=get_proxy(proxy_queue, thread_id, stop_event)
        proxies_dict=format_proxy(current_proxy)
        proxy_usage_count=0
        failed_attempts=0
        max_failed_attempts=10
        if not current_proxy:
            config._print(
                f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL}] {xColor.RED}[!] Proxy pool depleted, waiting for refill (1s)")
            time.sleep(1)
            continue
        config._print(
            f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL}] {xColor.GREEN}● Thread activated with proxy: {xColor.YELLOW}{current_proxy}")
        if thread_id < 3:
            _cd_(f"Thread-{thread_id:03d} initialization", count=3)
        while not stop_event.is_set() and proxy_usage_count < config.ACCOUNTS_PER_PROXY and failed_attempts < max_failed_attempts:
            if stop_event.is_set():
                return
            if not current_proxy:
                current_proxy=get_proxy(proxy_queue, thread_id, stop_event)
                proxies_dict=format_proxy(current_proxy)
                if not current_proxy:
                    config._print(
                        f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL}] {xColor.RED}[!] Proxy unavailable, will try again")
                    break
                config._print(
                    f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL}] {xColor.GREEN}● Switching to new proxy: {xColor.YELLOW}{current_proxy}")

            prefix=f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL} | {xColor.MAGENTA}Register{Style.RESET_ALL}]"
            email=_rand_email_()
            password=_rand_pw_()
            config._print(
                f"{prefix} {xColor.CYAN}● Initializing new identity: {xColor.YELLOW}{email[:8]}...@...")
            payload={
                "data": {
                    "email": email,
                    "password": password,
                    "client_email_verif": True,
                    "client_token": _rand_str_(40, chars=string.hexdigits.lower()),
                    "platform": "ios"
                }
            }
            if stop_event.is_set():
                return
            response_data=excute(
                f"{config.API_BASE_URL}/createAccountWithEmailPassword",
                headers=config.headers_locket(),
                payload=payload,
                thread_id=thread_id,
                step="Register",
                proxies_dict=proxies_dict
            )
            if stop_event.is_set():
                return
            if response_data == "proxy_dead":
                config._print(
                    f"{prefix} {xColor.RED}[!] Proxy terminated, acquiring new endpoint")
                current_proxy=None
                failed_attempts+=1
                continue
            if response_data == "too_many_requests":
                config._print(
                    f"{prefix} {xColor.RED}[!] Connection throttled, switching endpoint")
                current_proxy=None
                failed_attempts+=1
                continue
            if isinstance(response_data, dict) and response_data.get('result', {}).get('status') == 200:
                config._print(
                    f"{prefix} {xColor.GREEN}[✓] Identity created: {xColor.YELLOW}{email}")
                proxy_usage_count+=1
                failed_attempts=0
                if stop_event.is_set():
                    return
                id_token=step1b_sign_in(
                    email, password, thread_id, proxies_dict)
                if stop_event.is_set():
                    return
                if id_token:
                    if step2_finalize_user(id_token, thread_id, proxies_dict):
                        if stop_event.is_set():
                            return
                        first_request_success=step3_send_friend_request(
                            id_token, thread_id, proxies_dict)
                        if first_request_success:
                            config._print(
                                f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL} | {xColor.MAGENTA}Boost{Style.RESET_ALL}] {xColor.YELLOW}🚀 Boosting friend requests: Sending 50 more requests")
                            for _ in range(50):
                                if stop_event.is_set():
                                    return
                                step3_send_friend_request(
                                    id_token, thread_id, proxies_dict)
                            config._print(
                                f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL} | {xColor.MAGENTA}Boost{Style.RESET_ALL}] {xColor.GREEN}[✓] Boost complete: 101 total requests sent")
                    else:
                        config._print(
                            f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL} | {xColor.MAGENTA}Profile{Style.RESET_ALL}] {xColor.RED}[✗] Skipping friend requests due to profile failure")
            else:
                config._print(
                    f"{prefix} {xColor.RED}[!] Account creation failed, retrying")
                failed_attempts+=1
        if proxy_usage_count >= config.ACCOUNTS_PER_PROXY:
            config._print(
                f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL}] {xColor.YELLOW}● Reached account limit per proxy, switching proxy")
            current_proxy=None
        if failed_attempts >= max_failed_attempts:
            config._print(
                f"[{xColor.CYAN}Thread-{thread_id:03d}{Style.RESET_ALL}] {xColor.RED}[!] Too many failures, switching proxy")
            current_proxy=None

def main():
    global config
    _clear_()
    _banner_()
    proxy_queue, number_of_threads = init_proxy()
    stop_event = threading.Event()
    config = zLocket()
    threads = []
    try:
        for thread_id in range(1, number_of_threads + 1):
            t = threading.Thread(target=step1_create_account, args=(thread_id, proxy_queue, stop_event))
            t.start()
            threads.append(t)
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt detected, stopping threads...")
        stop_event.set()
        for t in threads:
            t.join()
        print("[✓] All threads stopped. Exiting.")

if __name__ == "__main__":
    main()
