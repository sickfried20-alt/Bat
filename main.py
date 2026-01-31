import flet as ft
import requests
import time
import re
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor

# Konfiguration
DOMAIN_LABEL = "sondiservice!"
PROXIES_FILE = "proxies.txt"

def main(page: ft.Page):
    page.title = DOMAIN_LABEL
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    # Counter
    stats = {"u": 0, "v": 0}
    
    # UI Elemente
    log_view = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    status_text = ft.Text("U: (0)  V: (0)", size=20, color=ft.colors.CYAN, weight="bold")
    num_input = ft.TextField(label="Anzahl Accounts", value="1", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    
    def ui_log(msg, color=ft.colors.WHITE):
        ts = time.strftime("%H:%M:%S")
        log_view.controls.append(ft.Text(f"[{ts}] {msg}", color=color, font_family="monospace", size=12))
        page.update()

    def update_stats():
        status_text.value = f"U: ({stats['u']})  V: ({stats['v']})"
        page.update()

    # Bot Logik (vereinfacht für Stabilität)
    def worker(task_id):
        try:
            # Hier deine TunnelBear Logik einfügen
            stats["u"] += 1
            update_stats()
            ui_log(f"Task {task_id}: Starte...", ft.colors.YELLOW)
            
            # Beispiel-Request zum Testen der Verbindung
            requests.get("https://google.com", timeout=5)
            
            time.sleep(3) # Simuliert Arbeit
            
            stats["u"] -= 1
            stats["v"] += 1
            update_stats()
            ui_log(f"Task {task_id}: Erfolg!", ft.colors.GREEN)
        except Exception as e:
            ui_log(f"Fehler Task {task_id}: {str(e)}", ft.colors.RED)

    def start_gen(e):
        try:
            n = int(num_input.value)
            ui_log(f"Starte Generierung für {n} Accounts...")
            threading.Thread(target=lambda: [worker(i) for i in range(1, n+1)], daemon=True).start()
        except:
            ui_log("Bitte gültige Zahl eingeben", ft.colors.RED)

    start_btn = ft.ElevatedButton("Start", on_click=start_gen)

    page.add(
        ft.Text(DOMAIN_LABEL, size=30, weight="bold"),
        status_text,
        ft.Row([num_input, start_btn]),
        ft.Container(content=log_view, height=400, bgcolor=ft.colors.BLACK, padding=10, border_radius=10)
    )

if __name__ == "__main__":
    ft.app(target=main)
