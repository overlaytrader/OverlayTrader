# overlay_trader_fixed.py
import os
import sys
import threading
import time
import logging
import json
from typing import Dict, List, Tuple
import webbrowser
import winreg
import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser
from dotenv import load_dotenv
from PIL import Image
import pystray
from pystray import MenuItem as item
import keyboard

# 3rd-party exchange SDKs
try:
    from binance.client import Client as BinanceClient
    from pybit.unified_trading import HTTP as BybitClient
except ImportError:
    print("Critical Error: Missing libraries. Run: pip install python-binance pybit")
    sys.exit(1)

# ------------------------------------------------------------
# Localization Mock (Встроена, чтобы код работал без внешнего файла)
# ------------------------------------------------------------
class LocalizationManager:
    def __init__(self):
        self.lang = "ru"
        self.translations = {
            "en": {
                "app_title": "Overlay Trader AI",
                "general_tab": "General",
                "settings_tab": "Settings",
                "exchange_connection": "Exchange Connection",
                "exchange": "Exchange:",
                "disconnected": "Disconnected",
                "connected": "Connected",
                "api_key": "API Key:",
                "enter_api_key": "Enter API Key",
                "api_secret": "API Secret:",
                "enter_api_secret": "Enter API Secret",
                "connect_to_exchange": "Connect to Exchange",
                "auto_connect_startup": "Auto connect on startup",
                "hide_from_taskbar": "Hide from taskbar when minimized",
                "auto_start_windows": "Start with Windows",
                "minimize_to_tray": "Minimize to Tray",
                "donate_text": "Support the developer",
                "wallet_usdt": "USDT (BEP20):",
                "copy": "Copy",
                "join_community": "Join Community:",
                "telegram_group": "Telegram Group",
                "for_updates_support": "for updates & support",
                "dev_text": "Developed with AI assistance",
                "overlay_balance_font_size": "Balance Font Size",
                "overlay_positions_font_size": "Positions Font Size",
                "overlay_balance_font_family": "Balance Font Family",
                "overlay_positions_font_family": "Positions Font Family",
                "overlay_fields_to_show": "Fields to Show:",
                "balance": "Balance",
                "pnl_percent": "PnL %",
                "pnl_usd": "PnL $",
                "overlay_colors": "Overlay Colors",
                "balance_color": "Balance Color",
                "positive_position_color": "Positive PnL Color",
                "negative_position_color": "Negative PnL Color",
                "change": "Change",
                "language_settings": "Language",
                "select_language": "Select Language:",
                "language_change_restart": "Please restart the application to apply language changes.",
                "show_app": "Show Application",
                "show_hide_overlay": "Show/Hide Overlay",
                "exit": "Exit",
                "choose_balance_color": "Choose Balance Color",
                "choose_positive_pnl_color": "Choose Positive PnL Color",
                "choose_negative_pnl_color": "Choose Negative PnL Color"
            },
            "ru": {
                "app_title": "Overlay Trader AI",
                "general_tab": "Главная",
                "settings_tab": "Настройки",
                "exchange_connection": "Подключение к бирже",
                "exchange": "Биржа:",
                "disconnected": "Отключено",
                "connected": "Подключено",
                "api_key": "API Key:",
                "enter_api_key": "Введите API Key",
                "api_secret": "API Secret:",
                "enter_api_secret": "Введите API Secret",
                "connect_to_exchange": "Подключиться",
                "auto_connect_startup": "Авто-подключение при запуске",
                "hide_from_taskbar": "Скрывать из панели задач при сворачивании",
                "auto_start_windows": "Запускать вместе с Windows",
                "minimize_to_tray": "Свернуть в трей",
                "donate_text": "Поддержать разработчика",
                "wallet_usdt": "USDT (BEP20):",
                "copy": "Коп.",
                "join_community": "Сообщество:",
                "telegram_group": "Telegram Группа",
                "for_updates_support": "для обновлений и поддержки",
                "dev_text": "Разработано с помощью ИИ",
                "overlay_balance_font_size": "Размер шрифта баланса",
                "overlay_positions_font_size": "Размер шрифта позиций",
                "overlay_balance_font_family": "Шрифт баланса",
                "overlay_positions_font_family": "Шрифт позиций",
                "overlay_fields_to_show": "Отображать:",
                "balance": "Баланс",
                "pnl_percent": "PnL %",
                "pnl_usd": "PnL $",
                "overlay_colors": "Цвета оверлея",
                "balance_color": "Цвет баланса",
                "positive_position_color": "Цвет плюс. PnL",
                "negative_position_color": "Цвет минус. PnL",
                "change": "Изменить",
                "language_settings": "Язык",
                "select_language": "Выберите язык:",
                "language_change_restart": "Пожалуйста, перезапустите приложение для смены языка.",
                "show_app": "Показать окно",
                "show_hide_overlay": "Показать/Скрыть оверлей",
                "exit": "Выход",
                "choose_balance_color": "Выбрать цвет баланса",
                "choose_positive_pnl_color": "Выбрать цвет плюс. PnL",
                "choose_negative_pnl_color": "Выбрать цвет минус. PnL"
            }
        }

    def get_text(self, key):
        return self.translations.get(self.lang, self.translations["en"]).get(key, key)

    def set_language(self, lang_code):
        if lang_code in self.translations:
            self.lang = lang_code

    def get_available_languages(self):
        return {"ru": "Русский", "en": "English"}

# Initialize localization
loc_manager = LocalizationManager()
get_text = loc_manager.get_text
set_language = loc_manager.set_language
get_available_languages = loc_manager.get_available_languages

# ------------------------------------------------------------
# Logging and environment
# ------------------------------------------------------------
log_dir = os.path.join(os.path.expanduser("~"), ".overlay_trader")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "overlay.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
load_dotenv()
SETTINGS_FILE = os.path.join(log_dir, "settings.json")

# ------------------------------------------------------------
# Helper: Resource Path for PyInstaller
# ------------------------------------------------------------
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# ------------------------------------------------------------
# Windows Autostart Functions
# ------------------------------------------------------------
def get_autostart_registry_path():
    return r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"

def is_autostart_enabled():
    try:
        wow64_64 = getattr(winreg, "KEY_WOW64_64KEY", 0)
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            get_autostart_registry_path(),
            0,
            winreg.KEY_READ | wow64_64,
        ) as key:
            try:
                val, _ = winreg.QueryValueEx(key, "OverlayTrader")
                return bool(val)
            except FileNotFoundError:
                return False
    except Exception as e:
        logging.error(f"Error checking autostart: {e}")
        return False

def set_autostart(enabled: bool):
    try:
        wow64_64 = getattr(winreg, "KEY_WOW64_64KEY", 0)
        key = winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            get_autostart_registry_path(),
            0,
            winreg.KEY_SET_VALUE | wow64_64,
        )
        try:
            if enabled:
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                else:
                    exe_path = os.path.abspath(__file__)
                    python_exe = sys.executable if sys.executable else os.path.join(os.path.dirname(os.__file__), 'python.exe')
                    # Wrap paths in quotes to handle spaces
                    exe_path = f'"{python_exe}" "{exe_path}"'
                    winreg.SetValueEx(key, "OverlayTrader", 0, winreg.REG_SZ, exe_path)
                    return
                
                command = f'"{exe_path}"'
                winreg.SetValueEx(key, "OverlayTrader", 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, "OverlayTrader")
                except FileNotFoundError:
                    pass
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        logging.error(f"Error setting autostart: {e}")

# ------------------------------------------------------------
# Exchange API abstractions
# ------------------------------------------------------------
class ExchangeAPI:
    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise ValueError("API key and secret cannot be empty")
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.connected = False
        self.client = None
        self.balance: Dict[str, float] = {}
        self.positions: List[dict] = []
        self.last_update_time = 0.0

    def connect(self) -> bool:
        raise NotImplementedError

    def fetch_data(self) -> None:
        raise NotImplementedError

class BinanceAPI(ExchangeAPI):
    def connect(self) -> bool:
        try:
            self.client = BinanceClient(self.api_key, self.api_secret)
            # Test connection
            self.client.futures_account_balance()
            self.connected = True
            logging.info("Binance connected successfully")
            return True
        except Exception as e:
            logging.error(f"Binance connect error: {e}")
            self.connected = False
            return False

    def fetch_data(self) -> None:
        if not self.connected: return
        try:
            # Using futures endpoints
            account = self.client.futures_account_balance()
            usdt = next((a for a in account if a and a.get("asset") == "USDT"), None)
            if usdt:
                self.balance = {
                    "total": float(usdt.get("balance", 0)),
                    "available": float(usdt.get("availableBalance", 0)),
                    "unrealized_pnl": float(usdt.get("crossUnPnl", 0)),
                }
            
            positions_raw = self.client.futures_position_information()
            self.positions = []
            if positions_raw:
                for pos in positions_raw:
                    try:
                        amt = float(pos.get("positionAmt", 0))
                        if amt != 0:
                            self.positions.append(
                                {
                                    "symbol": pos.get("symbol", ""),
                                    "side": "LONG" if amt > 0 else "SHORT",
                                    "amount": abs(amt),
                                    "entry": float(pos.get("entryPrice", 0)),
                                    "mark": float(pos.get("markPrice", 0)),
                                    "pnl": float(pos.get("unRealizedProfit", 0)),
                                }
                            )
                    except Exception:
                        continue
            self.last_update_time = time.time()
        except Exception as e:
            logging.error(f"Binance fetch error: {e}")
            # Don't disconnect immediately on one error (timeout), just log
            pass

class BybitAPI(ExchangeAPI):
    def connect(self) -> bool:
        try:
            self.client = BybitClient(
                testnet=False,
                api_key=self.api_key,
                api_secret=self.api_secret,
                recv_window=5000
            )
            self.client.get_wallet_balance(accountType="UNIFIED", coin="USDT")
            self.connected = True
            logging.info("Bybit connected successfully")
            return True
        except Exception as e:
            logging.error(f"Bybit connect error: {e}")
            self.connected = False
            return False

    def fetch_data(self) -> None:
        if not self.connected: return
        try:
            balance = self.client.get_wallet_balance(accountType="UNIFIED", coin="USDT")
            if (balance.get("retCode") == 0 and 
                balance.get("result", {}).get("list") and 
                balance["result"]["list"][0].get("coin")):
                usdt = balance["result"]["list"][0]["coin"][0]
                self.balance = {
                    "total": float(usdt.get("walletBalance", 0)),
                    "available": float(usdt.get("availableToWithdraw", 0)),
                    "unrealized_pnl": float(usdt.get("unrealisedPnl", 0)),
                }
            
            positions = self.client.get_positions(category="linear", settleCoin="USDT")
            self.positions = []
            if positions and positions.get("retCode") == 0:
                for pos in positions.get("result", {}).get("list", []):
                    try:
                        size = float(pos.get("size", 0))
                        if size > 0:
                            self.positions.append(
                                {
                                    "symbol": pos.get("symbol", "N/A"),
                                    "side": pos.get("side", "N/A"),
                                    "amount": size,
                                    "entry": float(pos.get("avgPrice", 0)),
                                    "mark": float(pos.get("markPrice", 0)),
                                    "pnl": float(pos.get("unrealisedPnl", 0)),
                                }
                            )
                    except Exception:
                        continue
            self.last_update_time = time.time()
        except Exception as e:
            logging.error(f"Bybit fetch error: {e}")

# ------------------------------------------------------------
# Background Data Fetcher (FIX for GUI Freezing)
# ------------------------------------------------------------
class DataFetcher(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.running = True
        self.daemon = True  # Ensure thread dies with main app

    def run(self):
        while self.running:
            if self.app.exchanges:
                # Fetch data for all connected exchanges
                for name, ex in list(self.app.exchanges.items()):
                    if ex.connected:
                        ex.fetch_data()
                
                # Calculate total and notify UI
                # We use app.after to interact with GUI thread safely
                self.app.after(0, self.app.refresh_overlay_data)
            
            # Wait 2 seconds before next update
            time.sleep(2)

    def stop(self):
        self.running = False

# ------------------------------------------------------------
# Native tkinter OverlayWindow
# ------------------------------------------------------------
class OverlayWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Chroma key transparency (color removal)
        self._transparent_color = "#010102"
        self.configure(bg=self._transparent_color)
        try:
            self.attributes("-transparentcolor", self._transparent_color)
        except Exception:
            pass
            
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        
        bal_font = (getattr(parent, "overlay_balance_font_family", "Segoe UI"), getattr(parent, "overlay_balance_font_size", 16))
        bal_color = getattr(parent, "overlay_balance_color", "#FFFFFF")
        
        self.balance_label = tk.Label(self, text="Loading...", bg=self._transparent_color, fg=bal_color, font=bal_font)
        self.positions_frame = tk.Frame(self, bg=self._transparent_color)
        
        self.balance_label.pack(anchor="w", padx=6, pady=(6,2))
        self.positions_frame.pack(anchor="w", padx=6, pady=(0,6))
        
        # Dragging bindings
        for widget in (self.balance_label, self.positions_frame, self):
            widget.bind("<ButtonPress-1>", self._start_move)
            widget.bind("<B1-Motion>", self._on_move)

    def _start_move(self, event):
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y

    def _on_move(self, event):
        x = self.winfo_x() + event.x - self._drag_offset_x
        y = self.winfo_y() + event.y - self._drag_offset_y
        self.geometry(f"+{x}+{y}")
        self.parent_app.set_overlay_position(x, y)

    def _side_to_abbrev(self, side_raw: str, amount: float) -> str:
        s = str(side_raw).upper()
        if 'Buy' in s or 'Long' in s: return 'L'
        if 'Sell' in s or 'Short' in s: return 'S'
        return 'L' if amount > 0 else 'S'

    def update_data(self, total_balance: float, positions: list):
        # Read preferences
        app = self.parent_app
        
        # Update Balance
        if app.overlay_show_balance:
            font = (app.overlay_balance_font_family, app.overlay_balance_font_size)
            self.balance_label.config(
                text=f"${total_balance:,.2f}", 
                fg=app.overlay_balance_color, 
                font=font
            )
            if not self.balance_label.winfo_ismapped():
                self.balance_label.pack(anchor="w", padx=6, pady=(6,2), before=self.positions_frame)
        else:
            self.balance_label.pack_forget()

        # Update Positions
        # Clear old widgets
        for child in self.positions_frame.winfo_children():
            child.destroy()

        pos_font = (app.overlay_positions_font_family, app.overlay_positions_font_size)

        for pos in positions:
            symbol = pos.get('symbol', '')
            side = self._side_to_abbrev(pos.get('side', ''), pos.get('amount', 0))
            pnl_usd = pos.get('pnl', 0.0)
            
            # Calculate PnL % fallback
            entry = pos.get('entry', 0)
            mark = pos.get('mark', 0)
            pnl_percent = 0.0
            if entry > 0:
                if side == 'L':
                    pnl_percent = (mark - entry) / entry * 100
                else:
                    pnl_percent = (entry - mark) / entry * 100

            parts = [f"{symbol} {side}"]
            if app.overlay_show_pnl_percent:
                parts.append(f"{pnl_percent:+.2f}%")
            if app.overlay_show_pnl_usd:
                parts.append(f"${pnl_usd:+,.2f}")
            
            text_str = "  ".join(parts)
            color = app.overlay_pos_color_positive if pnl_usd >= 0 else app.overlay_pos_color_negative
            
            lbl = tk.Label(self.positions_frame, text=text_str, bg=self._transparent_color, 
                           fg=color, font=pos_font, anchor="w")
            lbl.pack(anchor="w")
            
            # Add drag binding to new labels
            lbl.bind("<ButtonPress-1>", self._start_move)
            lbl.bind("<B1-Motion>", self._on_move)

# ------------------------------------------------------------
# Main application class
# ------------------------------------------------------------
class OverlayTrader(ctk.CTk):
    WALLET_ADDRESS = "0x1ea179e669e2347d43d53a79aba4e8b539d478ce"
    TELEGRAM_URL = "https://t.me/OverlayTrader"

    def __init__(self):
        super().__init__()
        self.title(get_text("app_title"))
        self.geometry("900x750")
        self.minsize(900, 750)

        # Set icon
        try:
            icon_path = resource_path("favic.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        # Data structures
        self.exchanges: Dict[str, ExchangeAPI] = {}
        self.overlay_position = None
        
        # Defaults
        self.overlay_balance_font_size = 24
        self.overlay_positions_font_size = 14
        self.overlay_balance_font_family = "Segoe UI"
        self.overlay_positions_font_family = "Segoe UI"
        self.overlay_balance_color = "#FFFFFF"
        self.overlay_pos_color_positive = "#00C853"
        self.overlay_pos_color_negative = "#FF3B30"
        self.overlay_show_balance = True
        self.overlay_show_pnl_percent = True
        self.overlay_show_pnl_usd = True
        self.auto_connect = True
        self.auto_start_windows = False
        self.hide_from_taskbar = True
        self.current_language = "ru"

        self.load_settings()
        
        # Create Overlay (hidden initially)
        self.overlay = OverlayWindow(self)
        self.overlay.withdraw()
        if self.overlay_position:
            self.overlay.geometry(f"+{self.overlay_position[0]}+{self.overlay_position[1]}")

        # Build UI
        self.build_ui()
        
        # Setup Tray & Hotkeys
        self.setup_system_tray()
        keyboard.add_hotkey("F12", self.toggle_overlay)

        # Start Data Fetcher Thread
        self.data_thread = DataFetcher(self)
        self.data_thread.start()

        # Auto Connect
        if self.auto_connect:
            self.after(1000, self.try_auto_connect)

        # Protocol handlers
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

    def build_ui(self):
        self.notebook = ctk.CTkTabview(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.general_tab = self.notebook.add(get_text("general_tab"))
        self.settings_tab = self.notebook.add(get_text("settings_tab"))

        # --- General Tab ---
        gen_frame = ctk.CTkFrame(self.general_tab)
        gen_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Connection Area
        conn_frame = ctk.CTkFrame(gen_frame)
        conn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(conn_frame, text=get_text("exchange_connection"), font=("", 16, "bold")).pack(anchor="w", padx=15, pady=10)
        
        grid = ctk.CTkFrame(conn_frame, fg_color="transparent")
        grid.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkLabel(grid, text=get_text("exchange")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.exchange_var = ctk.StringVar(value="Binance")
        ctk.CTkOptionMenu(grid, values=["Binance", "Bybit"], variable=self.exchange_var, command=self.change_exchange).grid(row=0, column=1, sticky="w", padx=5)
        
        self.status_icon = ctk.CTkLabel(grid, text="●", text_color="red", font=("", 20))
        self.status_icon.grid(row=0, column=2, padx=10)
        self.status_text = ctk.CTkLabel(grid, text=get_text("disconnected"))
        self.status_text.grid(row=0, column=3, sticky="w")

        ctk.CTkLabel(grid, text=get_text("api_key")).grid(row=1, column=0, sticky="w", padx=5)
        self.api_key_entry = ctk.CTkEntry(grid, width=300)
        self.api_key_entry.grid(row=1, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        self.bind_paste(self.api_key_entry)

        ctk.CTkLabel(grid, text=get_text("api_secret")).grid(row=2, column=0, sticky="w", padx=5)
        self.api_secret_entry = ctk.CTkEntry(grid, width=300, show="•")
        self.api_secret_entry.grid(row=2, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        self.bind_paste(self.api_secret_entry)

        self.connection_switch = ctk.CTkSwitch(grid, text=get_text("connect_to_exchange"), command=self.toggle_connection)
        self.connection_switch.grid(row=3, column=0, columnspan=4, pady=10)

        # Checkboxes
        self.auto_connect_var = tk.BooleanVar(value=self.auto_connect)
        ctk.CTkCheckBox(grid, text=get_text("auto_connect_startup"), variable=self.auto_connect_var, command=self.save_settings).grid(row=4, column=0, columnspan=4, sticky="w", padx=5, pady=2)
        
        self.hide_taskbar_var = tk.BooleanVar(value=self.hide_from_taskbar)
        ctk.CTkCheckBox(grid, text=get_text("hide_from_taskbar"), variable=self.hide_taskbar_var, command=self.on_hide_taskbar_change).grid(row=5, column=0, columnspan=4, sticky="w", padx=5, pady=2)

        self.autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        ctk.CTkCheckBox(grid, text=get_text("auto_start_windows"), variable=self.autostart_var, command=self.on_autostart_change).grid(row=6, column=0, columnspan=4, sticky="w", padx=5, pady=2)

        ctk.CTkButton(grid, text=get_text("minimize_to_tray"), command=self.minimize_to_tray).grid(row=7, column=0, columnspan=4, pady=10)

        # Donation & Info
        info_frame = ctk.CTkFrame(gen_frame, fg_color="#2B2B2B")
        info_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(info_frame, text=get_text("donate_text"), font=("", 18, "bold"), text_color="#4682B4").pack(pady=5)
        
        w_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        w_frame.pack()
        ctk.CTkLabel(w_frame, text=self.WALLET_ADDRESS, text_color="#00a1ff").pack(side="left", padx=5)
        ctk.CTkButton(w_frame, text=get_text("copy"), width=50, command=self.copy_wallet).pack(side="left")

        # --- Settings Tab ---
        set_frame = ctk.CTkFrame(self.settings_tab)
        set_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Font sliders
        self.create_slider_setting(set_frame, 0, get_text("overlay_balance_font_size"), self.overlay_balance_font_size, self.change_bal_size)
        self.create_slider_setting(set_frame, 1, get_text("overlay_positions_font_size"), self.overlay_positions_font_size, self.change_pos_size)

        # Visibility Toggles
        ctk.CTkLabel(set_frame, text=get_text("overlay_fields_to_show")).grid(row=2, column=0, sticky="w", pady=10)
        
        self.show_bal_cb = ctk.CTkCheckBox(set_frame, text=get_text("balance"), command=self.update_overlay_vis)
        self.show_bal_cb.grid(row=2, column=1, sticky="w")
        if self.overlay_show_balance: self.show_bal_cb.select()
        
        self.show_perc_cb = ctk.CTkCheckBox(set_frame, text=get_text("pnl_percent"), command=self.update_overlay_vis)
        self.show_perc_cb.grid(row=3, column=1, sticky="w")
        if self.overlay_show_pnl_percent: self.show_perc_cb.select()

        self.show_usd_cb = ctk.CTkCheckBox(set_frame, text=get_text("pnl_usd"), command=self.update_overlay_vis)
        self.show_usd_cb.grid(row=4, column=1, sticky="w")
        if self.overlay_show_pnl_usd: self.show_usd_cb.select()

        # Colors
        ctk.CTkLabel(set_frame, text=get_text("overlay_colors")).grid(row=5, column=0, pady=10, sticky="w")
        ctk.CTkButton(set_frame, text=get_text("balance_color"), command=lambda: self.pick_color('bal')).grid(row=6, column=0, padx=5, pady=5)
        ctk.CTkButton(set_frame, text=get_text("positive_position_color"), command=lambda: self.pick_color('pos')).grid(row=6, column=1, padx=5, pady=5)
        ctk.CTkButton(set_frame, text=get_text("negative_position_color"), command=lambda: self.pick_color('neg')).grid(row=6, column=2, padx=5, pady=5)

        # Language
        ctk.CTkLabel(set_frame, text=get_text("select_language")).grid(row=7, column=0, pady=20, sticky="w")
        self.lang_var = ctk.StringVar(value=get_available_languages().get(self.current_language, "Русский"))
        ctk.CTkOptionMenu(set_frame, values=list(get_available_languages().values()), command=self.change_language, variable=self.lang_var).grid(row=7, column=1)

        # Load keys if saved
        if hasattr(self, 'saved_api_key'): self.api_key_entry.insert(0, self.saved_api_key)
        if hasattr(self, 'saved_api_secret'): self.api_secret_entry.insert(0, self.saved_api_secret)

    def create_slider_setting(self, parent, row, text, default, cmd):
        ctk.CTkLabel(parent, text=text).grid(row=row, column=0, sticky="w", pady=5)
        slider = ctk.CTkSlider(parent, from_=8, to=48, number_of_steps=40, command=cmd)
        slider.set(default)
        slider.grid(row=row, column=1, sticky="ew", padx=10)
        lbl = ctk.CTkLabel(parent, text=str(default))
        lbl.grid(row=row, column=2)
        slider.configure(command=lambda v: (cmd(v), lbl.configure(text=str(int(v)))))

    def bind_paste(self, widget):
        # Fix paste shortcut for CustomTkinter
        def on_paste(event):
            try:
                text = self.clipboard_get()
                widget.insert("insert", text)
            except: pass
            return "break"
        widget.bind("<Control-v>", on_paste)

    # ---------------- Logic ----------------

    def toggle_connection(self):
        if self.connection_switch.get():
            self.connect_exchange()
        else:
            self.disconnect_exchange()

    def connect_exchange(self):
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()
        exchange = self.exchange_var.get()

        if not api_key or not api_secret:
            self.connection_switch.deselect()
            return

        def connect_thread():
            try:
                api = None
                if exchange == "Binance":
                    api = BinanceAPI(api_key, api_secret)
                elif exchange == "Bybit":
                    api = BybitAPI(api_key, api_secret)

                if api and api.connect():
                    self.exchanges[exchange] = api
                    self.after(0, self.on_connect_success)
                else:
                    self.after(0, self.on_connect_fail)
            except Exception as e:
                logging.error(f"Connect error: {e}")
                self.after(0, self.on_connect_fail)

        threading.Thread(target=connect_thread, daemon=True).start()

    def on_connect_success(self):
        self.status_icon.configure(text_color="green")
        self.status_text.configure(text=get_text("connected"))
        self.overlay.deiconify()
        self.save_settings()

    def on_connect_fail(self):
        self.status_icon.configure(text_color="red")
        self.status_text.configure(text=get_text("disconnected"))
        self.connection_switch.deselect()

    def disconnect_exchange(self):
        self.exchanges.clear()
        self.status_icon.configure(text_color="red")
        self.status_text.configure(text=get_text("disconnected"))
        self.overlay.withdraw()

    def refresh_overlay_data(self):
        """ Called by DataFetcher thread via after() """
        total = 0.0
        positions = []
        for ex in self.exchanges.values():
            if ex.connected:
                total += ex.balance.get("total", 0)
                positions.extend(ex.positions)
        
        if self.overlay:
            self.overlay.update_data(total, positions)

    def change_exchange(self, choice):
        self.disconnect_exchange()
        self.api_key_entry.delete(0, 'end')
        self.api_secret_entry.delete(0, 'end')

    def try_auto_connect(self):
        if self.saved_api_key and self.saved_api_secret:
            self.connection_switch.select()
            self.connect_exchange()

    # ---------------- Settings & Events ----------------

    def change_bal_size(self, val):
        self.overlay_balance_font_size = int(val)
        self.save_settings()

    def change_pos_size(self, val):
        self.overlay_positions_font_size = int(val)
        self.save_settings()

    def pick_color(self, target):
        col = colorchooser.askcolor()[1]
        if not col: return
        if target == 'bal': self.overlay_balance_color = col
        elif target == 'pos': self.overlay_pos_color_positive = col
        elif target == 'neg': self.overlay_pos_color_negative = col
        self.save_settings()

    def update_overlay_vis(self):
        self.overlay_show_balance = bool(self.show_bal_cb.get())
        self.overlay_show_pnl_percent = bool(self.show_perc_cb.get())
        self.overlay_show_pnl_usd = bool(self.show_usd_cb.get())
        self.save_settings()

    def change_language(self, display_name):
        # Reverse lookup
        code = next((k for k, v in get_available_languages().items() if v == display_name), "ru")
        self.current_language = code
        set_language(code)
        self.save_settings()
        tk.messagebox.showinfo("Info", get_text("language_change_restart"))

    def on_hide_taskbar_change(self):
        self.hide_from_taskbar = self.hide_taskbar_var.get()
        self.save_settings()

    def on_autostart_change(self):
        set_autostart(self.autostart_var.get())
        self.save_settings()

    def copy_wallet(self):
        self.clipboard_clear()
        self.clipboard_append(self.WALLET_ADDRESS)

    def toggle_overlay(self):
        if self.overlay.winfo_viewable():
            self.overlay.withdraw()
        else:
            self.overlay.deiconify()

    def set_overlay_position(self, x, y):
        self.overlay_position = (x, y)
        self.save_settings()

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    self.overlay_balance_font_size = data.get("bal_size", 24)
                    self.overlay_positions_font_size = data.get("pos_size", 14)
                    self.overlay_balance_color = data.get("bal_col", "#FFFFFF")
                    self.overlay_pos_color_positive = data.get("pos_col", "#00C853")
                    self.overlay_pos_color_negative = data.get("neg_col", "#FF3B30")
                    self.auto_connect = data.get("auto_connect", False)
                    self.hide_from_taskbar = data.get("hide_taskbar", True)
                    self.overlay_position = data.get("overlay_pos")
                    self.current_language = data.get("lang", "ru")
                    set_language(self.current_language)
                    
                    self.saved_api_key = data.get("api_key", "")
                    self.saved_api_secret = data.get("api_secret", "")
                    
                    self.overlay_show_balance = data.get("show_bal", True)
                    self.overlay_show_pnl_percent = data.get("show_perc", True)
                    self.overlay_show_pnl_usd = data.get("show_usd", True)
        except Exception as e:
            logging.error(f"Load settings failed: {e}")

    def save_settings(self):
        data = {
            "bal_size": self.overlay_balance_font_size,
            "pos_size": self.overlay_positions_font_size,
            "bal_col": self.overlay_balance_color,
            "pos_col": self.overlay_pos_color_positive,
            "neg_col": self.overlay_pos_color_negative,
            "auto_connect": self.auto_connect_var.get(),
            "hide_taskbar": self.hide_taskbar_var.get(),
            "overlay_pos": self.overlay_position,
            "lang": self.current_language,
            "api_key": self.api_key_entry.get().strip(),
            "api_secret": self.api_secret_entry.get().strip(),
            "show_bal": self.overlay_show_balance,
            "show_perc": self.overlay_show_pnl_percent,
            "show_usd": self.overlay_show_pnl_usd
        }
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Save settings failed: {e}")

    # ---------------- System Tray ----------------

    def setup_system_tray(self):
        image = Image.new('RGB', (64, 64), (73, 109, 137))
        try:
            icon_path = resource_path("favic.ico")
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
        except: pass

        menu = (
            item(get_text('show_app'), self.restore_window),
            item(get_text('exit'), self.quit_app)
        )
        self.tray = pystray.Icon("overlay_trader", image, "Overlay Trader", menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def minimize_to_tray(self):
        self.withdraw()
        if self.hide_from_taskbar:
            # This is a bit of a hack for tkinter to hide from taskbar completely
            self.state('withdrawn')

    def restore_window(self):
        self.deiconify()
        self.state('normal')

    def quit_app(self):
        self.tray.stop()
        self.data_thread.stop()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = OverlayTrader()
    app.mainloop()