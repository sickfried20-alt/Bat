import flet as ft
import requests
import time
import re
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor

# --- Globale Variablen & Konfiguration ---
DOMAIN_LABEL = "sondiservice!"
PROXIES_FILE = "proxies.txt"
write_lock = threading.Lock()
counter_lock = threading.Lock()

class BotApp:
    def __init__(self):
        self.unverified_count = 0
        self.verified_count = 0
        self.proxies = self.load_proxies()

    def load_proxies(self):
        try:
            with open(PROXIES_FILE, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except:
            return []

    def save_credentials(self, email, password):
        with write_lock:
            with open("accs.txt", "a") as f:
                f.write(f"{email}:{password}\n")

    # --- Logik Funktionen (Original) ---
    def create_temp_inbox(self, session):
        try:
            r = session.post('https://api.tempmail.lol/v2/inbox/create',
                             json={"captcha": None, "domain": None, "prefix": ""}, timeout=10)
            return r.json()
        except: return None

    def check_inbox(self, session, token):
        try:
            r = session.get(f'https://api.tempmail.lol/v2/inbox?token={token}', timeout=10)
            return r.json()
        except: return None

    def send_tunnelbear_create_account(self, session, email, password):
        try:
            r = session.post("https://prod-api-core.tunnelbear.com/core/web/createAccount",
                             data={"email": email, "password": password, "json": "1", "v": "web-1.0"}, timeout=10)
            return r.json()
        except: return None

    def process_verification_link(self, session, link):
        try:
            r = session.get(link, timeout=10)
            return r.status_code == 200
        except: return False

def main(page: ft.Page):
    bot = BotApp()
    
    # UI Setup
    page.title = DOMAIN_LABEL
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 700
    page.scroll = ft.ScrollMode.ADAPTIVE

    # UI Komponenten
    log_view = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    status_text = ft.Text(f"U: (0)  V: (0)", size=20, weight="bold", color=ft.colors.CYAN)
    num_input = ft.TextField(label="Anzahl Accounts", value="1", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    start_btn = ft.ElevatedButton("Start Account Gen", icon=ft.icons.PLAY_ARROW, on_click=lambda _: start_gen())

    def append_log(message, color=ft.colors.GREEN):
        ts = time.strftime("%H:%M:%S")
        log_view.controls.append(
            ft.Text(f"[{ts}] -> {message}", color=color, font_family="monospace", size=12)
        )
        page.update()

    def update_stats():
        status_text.value = f"U: ({bot.unverified_count})  V: ({bot.verified_count})"
        page.update()

    def worker(task_id):
        session = requests.Session()
        if bot.proxies:
            p = random.choice(bot.proxies)
            session.proxies = {"http": f"socks5h://{p}", "https": f"socks5h://{p}"}
            append_log(f"Task {task_id}: Proxy {p[:15]}...", ft.colors.BLUE_GREY_400)

        temp = bot.create_temp_inbox(session)
        if not temp:
            append_log(f"Task {task_id}: Inbox Error", ft.colors.RED)
            return

        email = temp.get("address")
        token = temp.get("token")
        
        with counter_lock: bot.unverified_count += 1
        update_stats()
        
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        bot.send_tunnelbear_create_account(session, email, pwd)
        bot.save_credentials(email, pwd)
        append_log(f"Task {task_id}: Reg gesendet ({email})", ft.colors.YELLOW)

        verified = False
        while not verified:
            inbox = bot.check_inbox(session, token)
            if inbox and inbox.get("emails"):
                for e in inbox["emails"]:
                    content = e.get("html") or ""
                    links = re.findall(r'https://api\.tunnelbear\.com/core/verifyEmail\?key=[\w-]+', content)
                    if links:
                        if bot.process_verification_link(session, links[0]):
                            verified = True
                            with counter_lock:
                                bot.unverified_count -= 1
                                bot.verified_count += 1
                            update_stats()
                            append_log(f"VERIFIZIERT: {email}", ft.colors.GREEN_ACCENT_700)
                            break
            time.sleep(3)

    def start_gen():
        try:
            n = int(num_input.value)
            start_btn.disabled = True
            page.update()
            
            def run():
                with ThreadPoolExecutor(max_workers=5) as executor:
                    executor.map(worker, range(1, n + 1))
                append_log("ALLE TASKS FERTIG", ft.colors.CYAN)
                start_btn.disabled = False
                page.update()

            threading.Thread(target=run, daemon=True).start()
        except Exception as e:
            append_log(f"Fehler: {e}", ft.colors.RED)

    # Layout
    page.add(
        ft.Text(DOMAIN_LABEL, size=30, weight="bold", color=ft.colors.CYAN_ACCENT),
        status_text,
        ft.Row([num_input, start_btn], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        ft.Container(
            content=log_view,
            height=400,
            bgcolor=ft.colors.BLACK,
            border_radius=10,
            padding=10,
            border=ft.border.all(1, ft.colors.GREY_800)
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
                        
