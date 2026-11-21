# -*- coding: utf-8 -*-
"""
WEXXYY MACRO - макросы для Fortnite (Windows).
Только стандартная библиотека Python 3.8+, ничего устанавливать не нужно.

Запуск:   python W_Macro.py
В .exe:   build.bat  (или pyinstaller --noconsole --onefile --icon assets/wexxyy.ico W_Macro.py)
"""
import base64
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from ctypes import wintypes
from tkinter import colorchooser

APP_NAME = "WEXXYY MACRO"
APP_VER = "V1"

# ───────────────────────── Темы (меняются в разделе «Дизайн») ─────────────────────────
BASES = {
    "ЧЁРНЫЙ": dict(bg="#070809", side="#0b0c0e", panel="#111316", panel2="#181b1f",
                   line="#23272d", text="#f1f3f5", muted="#7b838d"),
    "ГРАФИТ": dict(bg="#101216", side="#14171c", panel="#191d23", panel2="#21262d",
                   line="#2c323b", text="#eef1f4", muted="#8791a0"),
    "ТЁМНО-СИНИЙ": dict(bg="#080b14", side="#0b101c", panel="#0f1524", panel2="#161d31",
                        line="#222b43", text="#e9eefb", muted="#7d89a6"),
}
ACCENTS = [("Красный", "#e5303a"), ("Зелёный", "#3ddc84"), ("Синий", "#4c8dff"),
           ("Фиолетовый", "#9b6bff"), ("Оранжевый", "#ff8a3d"), ("Белый", "#e7ecf1")]
FONTS = ["Segoe UI", "Bahnschrift", "Consolas", "Arial"]

BG = SIDE = PANEL = PANEL2 = LINE = TEXT = MUTED = ACCENT = ON_ACCENT = ""
FONT = "Segoe UI"


def _lum(h):
    try:
        r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
        return 0.299 * r + 0.587 * g + 0.114 * b
    except Exception:
        return 0


def apply_theme(t):
    global BG, SIDE, PANEL, PANEL2, LINE, TEXT, MUTED, ACCENT, ON_ACCENT, FONT
    base = BASES.get(t.get("base"), BASES["ЧЁРНЫЙ"])
    BG, SIDE, PANEL, PANEL2 = base["bg"], base["side"], base["panel"], base["panel2"]
    LINE, TEXT, MUTED = base["line"], base["text"], base["muted"]
    acc = str(t.get("accent", "#e5303a"))
    if not (len(acc) == 7 and acc.startswith("#")):
        acc = "#e5303a"
    ACCENT = acc
    ON_ACCENT = "#0b0d10" if _lum(acc) > 150 else "#ffffff"
    FONT = t.get("font") if t.get("font") in FONTS else "Segoe UI"


def F(size, bold=True):
    return (FONT, size, "bold" if bold else "normal")


# ───────────────────────── Windows API ─────────────────────────
user32 = ctypes.windll.user32
try:
    ctypes.windll.winmm.timeBeginPeriod(1)  # точные задержки ~1 мс
except Exception:
    pass

PUL = ctypes.POINTER(ctypes.c_ulong)


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", PUL)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", PUL)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# vk -> (флаг нажатия, флаг отпускания, mouseData)
MOUSE_BTN = {
    0x01: (0x0002, 0x0004, 0),
    0x02: (0x0008, 0x0010, 0),
    0x04: (0x0020, 0x0040, 0),
    0x05: (0x0080, 0x0100, 1),
    0x06: (0x0080, 0x0100, 2),
}
EXTENDED = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E,
            0xA3, 0xA5, 0x6F, 0x90}


def send_key(vk, down):
    """Нажать/отпустить клавишу или кнопку мыши (сканкоды - работает в играх)."""
    inp = INPUT()
    if vk in MOUSE_BTN:
        d, u, data = MOUSE_BTN[vk]
        inp.type = 0
        inp.u.mi = MOUSEINPUT(0, 0, data, d if down else u, 0, None)
    else:
        scan = user32.MapVirtualKeyW(vk, 0)
        flags = KEYEVENTF_SCANCODE
        if vk in EXTENDED:
            flags |= KEYEVENTF_EXTENDEDKEY
        if not down:
            flags |= KEYEVENTF_KEYUP
        inp.type = 1
        inp.u.ki = KEYBDINPUT(0, scan, flags, 0, None)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def tap(vk, hold=0.008):
    send_key(vk, True)
    time.sleep(hold)
    send_key(vk, False)


def pressed(vk):
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


SPECIAL = {
    1: "MOUSE1", 2: "MOUSE2", 4: "MOUSE3", 5: "XBUTTON1", 6: "XBUTTON2",
    8: "BACKSPACE", 9: "TAB", 13: "ENTER", 16: "SHIFT", 17: "CTRL", 18: "ALT",
    20: "CAPS", 27: "ESC", 32: "SPACE", 33: "PGUP", 34: "PGDN", 35: "END",
    36: "HOME", 37: "LEFT", 38: "UP", 39: "RIGHT", 40: "DOWN", 45: "INS",
    46: "DEL", 0xA0: "LSHIFT", 0xA1: "RSHIFT", 0xA2: "LCTRL", 0xA3: "RCTRL",
    0xA4: "LALT", 0xA5: "RALT",
}


def vk_name(vk):
    if not vk:
        return "НЕ ЗАДАНО"
    if vk in SPECIAL:
        return SPECIAL[vk]
    if 0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A:
        return chr(vk)
    if 0x70 <= vk <= 0x87:
        return "F%d" % (vk - 0x6F)
    if 0x60 <= vk <= 0x69:
        return "NUM%d" % (vk - 0x60)
    return "VK%d" % vk


# ───────────────────────── Конфиг ─────────────────────────
CFG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                       "wexxyy_macro")
CFG_PATH = os.path.join(CFG_DIR, "config.json")

DEFAULT_CFG = {
    "shortcut_done": False,
    "master": True,
    "master_key": 0x77,  # F8 - вкл/выкл все макросы
    "theme": {"accent": "#e5303a", "base": "ЧЁРНЫЙ", "font": "Segoe UI"},
    "macros": {
        "double_edit": {"on": False, "trigger": 0x05, "edit": 0x47, "select": 0x01,
                        "edit_delay": 12, "key_delay": 10, "gap": 25},
        "single_edit": {"on": False, "trigger": 0x06, "edit": 0x47, "select": 0x01,
                        "edit_delay": 12, "key_delay": 10},
        "sit_edit":    {"on": False, "trigger": 0x5A, "edit": 0x47, "select": 0x01,
                        "crouch": 0x43, "edit_delay": 12, "key_delay": 10},
        "pickup":      {"on": False, "trigger": 0x58, "pickup": 0x45, "interval": 20},
    },
}


def load_cfg():
    cfg = json.loads(json.dumps(DEFAULT_CFG))
    try:
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        for k in ("master", "master_key", "shortcut_done"):
            if k in saved:
                cfg[k] = saved[k]
        cfg["theme"].update(saved.get("theme", {}))
        for mid, vals in saved.get("macros", {}).items():
            if mid in cfg["macros"]:
                for k, v in vals.items():
                    if k in cfg["macros"][mid]:
                        cfg["macros"][mid][k] = v
    except Exception:
        pass
    return cfg


def save_cfg(cfg):
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ───────────────────────── Иконка и ярлык ─────────────────────────
ICON_B64 = (
    "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"
)
ICON_PATH = None


def ensure_icon():
    """Сохраняет иконку (большая W на чёрном фоне) рядом с конфигом."""
    global ICON_PATH
    p = os.path.join(CFG_DIR, "wexxyy.ico")
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        with open(p, "wb") as f:
            f.write(base64.b64decode(ICON_B64))
        ICON_PATH = p
    except Exception:
        ICON_PATH = None
    return ICON_PATH


def create_shortcut():
    """Создаёт ярлык «WEXXYY MACRO» с иконкой W на рабочем столе."""
    try:
        if getattr(sys, "frozen", False):
            target, args = sys.executable, ""
            wd = os.path.dirname(sys.executable)
        else:
            py = sys.executable
            pyw = os.path.join(os.path.dirname(py), "pythonw.exe")
            target = pyw if os.path.exists(pyw) else py
            script = os.path.abspath(__file__)
            args, wd = '"%s"' % script, os.path.dirname(script)
        q = lambda x: x.replace("'", "''")
        icon = ICON_PATH or target
        ps = ("$d=[Environment]::GetFolderPath('Desktop');"
              "$s=(New-Object -ComObject WScript.Shell).CreateShortcut("
              "(Join-Path $d 'WEXXYY MACRO.lnk'));"
              "$s.TargetPath='%s';$s.Arguments='%s';$s.WorkingDirectory='%s';"
              "$s.IconLocation='%s';$s.Save()") % (q(target), q(args), q(wd), q(icon))
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           creationflags=0x08000000, timeout=25)
        return r.returncode == 0
    except Exception:
        return False


# ───────────────────────── Движок макросов ─────────────────────────
class Engine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.busy = {}
        self.prev = {}
        self.alive = True
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while self.alive:
            try:
                self.tick()
            except Exception:
                pass
            time.sleep(0.002)

    def tick(self):
        c = self.cfg
        mk = c.get("master_key")
        if mk:
            d = pressed(mk)
            if d and not self.prev.get("_master"):
                c["master"] = not c["master"]
            self.prev["_master"] = d
        for mid, m in c["macros"].items():
            if not (c["master"] and m["on"] and m["trigger"]):
                self.prev[mid] = False
                continue
            d = pressed(m["trigger"])
            was = self.prev.get(mid, False)
            self.prev[mid] = d
            if d and not was and not self.busy.get(mid):
                self.busy[mid] = True
                threading.Thread(target=self.run, args=(mid,), daemon=True).start()

    def run(self, mid):
        try:
            m = self.cfg["macros"][mid]
            if mid == "single_edit":
                self.edit_cycle(m)
            elif mid == "double_edit":
                self.edit_cycle(m)
                time.sleep(m["gap"] / 1000.0)
                self.edit_cycle(m)
            elif mid == "sit_edit":
                send_key(m["crouch"], True)
                time.sleep(m["key_delay"] / 1000.0)
                self.edit_cycle(m)
                send_key(m["crouch"], False)
            elif mid == "pickup":
                while pressed(m["trigger"]) and m["on"] and self.cfg["master"]:
                    tap(m["pickup"], 0.006)
                    time.sleep(m["interval"] / 1000.0)
        finally:
            self.busy[mid] = False

    @staticmethod
    def edit_cycle(m):
        """Зажать Edit -> (EDIT DELAY) -> клик выделения -> (KEY DELAY) -> отпустить Edit."""
        send_key(m["edit"], True)
        time.sleep(m["edit_delay"] / 1000.0)
        tap(m["select"])
        time.sleep(m["key_delay"] / 1000.0)
        send_key(m["edit"], False)


# ───────────────────────── Виджеты ─────────────────────────
class Toggle(tk.Canvas):
    def __init__(self, parent, value=False, command=None, bg=None, w=46, h=24):
        super().__init__(parent, width=w, height=h, bg=bg or BG,
                         highlightthickness=0, cursor="hand2")
        self.w, self.h = w, h
        self.value = bool(value)
        self.command = command
        self.draw()
        self.bind("<Button-1>", self._click)

    def draw(self):
        self.delete("all")
        w, h = self.w, self.h
        r = h / 2
        col = ACCENT if self.value else "#2b313b"
        self.create_oval(0, 0, h, h, fill=col, outline=col)
        self.create_oval(w - h, 0, w, h, fill=col, outline=col)
        self.create_rectangle(r, 0, w - r, h, fill=col, outline=col)
        kx = w - r if self.value else r
        self.create_oval(kx - r + 3, 3, kx + r - 3, h - 3,
                         fill=ON_ACCENT if self.value else "#9aa4b0", outline="")

    def set(self, v):
        v = bool(v)
        if v != self.value:
            self.value = v
            self.draw()

    def _click(self, _e):
        self.value = not self.value
        self.draw()
        if self.command:
            self.command(self.value)


class Slider(tk.Canvas):
    """Тонкий ползунок с кружком акцентного цвета (как в референсе)."""

    def __init__(self, parent, lo, hi, value, command, release=None):
        super().__init__(parent, height=20, bg=BG, highlightthickness=0,
                         cursor="hand2")
        self.lo, self.hi, self.value = lo, hi, value
        self.command, self.release = command, release
        self.bind("<Configure>", lambda _e: self.draw())
        self.bind("<Button-1>", self.drag)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", self.done)

    def draw(self):
        self.delete("all")
        w = max(self.winfo_width(), 40)
        pad, cy = 8, 10
        span = max(1, self.hi - self.lo)
        x = pad + (w - 2 * pad) * (self.value - self.lo) / span
        self.create_line(pad, cy, w - pad, cy, fill=LINE, width=2)
        self.create_line(pad, cy, x, cy, fill=ACCENT, width=2)
        self.create_oval(x - 6, cy - 6, x + 6, cy + 6, fill=ACCENT, outline="")

    def drag(self, e):
        w = max(self.winfo_width(), 40)
        pad = 8
        t = min(1.0, max(0.0, (e.x - pad) / float(max(1, w - 2 * pad))))
        v = int(round(self.lo + t * (self.hi - self.lo)))
        if v != self.value:
            self.value = v
            self.draw()
            self.command(v)

    def done(self, _e):
        if self.release:
            self.release()


class BindButton(tk.Label):
    """Кнопка выбора клавиши: нажми на неё, затем нажми нужную клавишу/кнопку мыши."""

    def __init__(self, parent, get, set_, allow_lr=False):
        super().__init__(parent, text=vk_name(get()), bg=PANEL2, fg=TEXT,
                         font=F(9), width=22, pady=9, cursor="hand2")
        self.get, self.set_, self.allow_lr = get, set_, allow_lr
        self.waiting = False
        self.bind("<Button-1>", self.start)

    def refresh(self):
        if not self.waiting:
            self.config(text=vk_name(self.get()), fg=TEXT)

    def start(self, _e=None):
        if self.waiting:
            return
        self.waiting = True
        self.config(text="НАЖМИ КЛАВИШУ…", fg=ACCENT)
        self.after(250, self.scan)

    def scan(self):
        if not self.waiting:
            return
        try:
            if pressed(0x1B):  # Esc - отмена
                self.waiting = False
                self.refresh()
                return
            for vk in range(1, 255):
                if vk in (0x10, 0x11, 0x12, 0x1B):
                    continue
                if vk in (1, 2) and not self.allow_lr:
                    continue
                if pressed(vk):
                    self.waiting = False
                    self.set_(vk)
                    self.config(text=vk_name(vk), fg=TEXT)
                    return
            self.after(15, self.scan)
        except tk.TclError:
            self.waiting = False


# ───────────────────────── Приложение ─────────────────────────
# (id, пункт меню, заголовок, подзаголовок, [(поле, подпись, можно ЛКМ/ПКМ)], [(поле, подпись, min, max)])
PAGES = [
    ("double_edit", "DOUBLE", "DOUBLE EDIT", "ДВОЙНОЕ РЕДАКТИРОВАНИЕ",
     [("select", "ВЫДЕЛЕНИЕ", True), ("edit", "РЕДАКТИРОВАНИЕ", True),
      ("trigger", "АКТИВАЦИЯ", False)],
     [("edit_delay", "EDIT DELAY (МС)", 0, 100), ("key_delay", "KEY DELAY (МС)", 0, 100),
      ("gap", "ПАУЗА МЕЖДУ ЕДИТАМИ (МС)", 0, 200)]),
    ("single_edit", "SINGLE", "SINGLE EDIT", "ОДИНОЧНОЕ РЕДАКТИРОВАНИЕ",
     [("select", "ВЫДЕЛЕНИЕ", True), ("edit", "РЕДАКТИРОВАНИЕ", True),
      ("trigger", "АКТИВАЦИЯ", False)],
     [("edit_delay", "EDIT DELAY (МС)", 0, 100), ("key_delay", "KEY DELAY (МС)", 0, 100)]),
    ("sit_edit", "SIT", "SIT EDIT", "РЕДАКТИРОВАНИЕ В ПРИСЕДЕ",
     [("select", "ВЫДЕЛЕНИЕ", True), ("edit", "РЕДАКТИРОВАНИЕ", True),
      ("crouch", "ПРИСЕД", False), ("trigger", "АКТИВАЦИЯ", False)],
     [("edit_delay", "EDIT DELAY (МС)", 0, 100), ("key_delay", "KEY DELAY (МС)", 0, 100)]),
    ("pickup", "PICKUP", "ПОДНЯТИЕ ОРУЖИЯ", "БЫСТРЫЙ ПОДБОР ПОКА ЗАЖАТА КЛАВИША",
     [("pickup", "ПОДБОР (USE)", False), ("trigger", "АКТИВАЦИЯ", False)],
     [("interval", "ИНТЕРВАЛ (МС)", 5, 200)]),
]


class App:
    def __init__(self, root, cfg, engine):
        self.root, self.cfg, self.engine = root, cfg, engine
        self.toggles, self.binds = [], []
        self.pages, self.nav = {}, {}
        self.current = None
        root.title(APP_NAME)
        root.geometry("900x500")
        root.minsize(820, 470)
        root.configure(bg=BG)
        self.dark_titlebar()
        self.build_ui()
        self.show("double_edit")
        self.sync()

    def dark_titlebar(self):
        try:
            self.root.update_idletasks()
            hwnd = user32.GetParent(self.root.winfo_id())
            v = ctypes.c_int(1)
            for attr in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))
        except Exception:
            pass

    # ── каркас окна ──
    def build_ui(self):
        r = self.root
        head = tk.Frame(r, bg=BG)
        head.pack(side="top", fill="x", padx=22, pady=(14, 10))
        tk.Label(head, text=APP_NAME, bg=BG, fg=TEXT, font=F(13)).pack(side="left")
        tk.Label(head, text="  " + APP_VER, bg=BG, fg=ACCENT, font=F(13)).pack(side="left")
        tk.Frame(r, bg=LINE, height=1).pack(side="top", fill="x")

        bottom = tk.Frame(r, bg=BG)
        bottom.pack(side="bottom", fill="x")
        tk.Frame(r, bg=LINE, height=1).pack(side="bottom", fill="x")

        body = tk.Frame(r, bg=BG)
        body.pack(side="top", fill="both", expand=True)
        side = tk.Frame(body, bg=SIDE, width=170)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        self.content = tk.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        tk.Frame(side, bg=SIDE, height=14).pack()
        for mid, nav, *_ in PAGES:
            self.add_nav(side, mid, nav, SIDE, True)

        # нижняя панель: настройки / дизайн слева, сохранить и общий ползунок справа
        bl = tk.Frame(bottom, bg=BG)
        bl.pack(side="left", padx=(16, 0), pady=8)
        self.add_nav(bl, "settings", "НАСТРОЙКИ", BG, False)
        self.add_nav(bl, "design", "ДИЗАЙН", BG, False)

        self.master_tg = self.add_toggle(
            bottom, lambda: self.cfg["master"],
            lambda v: self.cfg.__setitem__("master", v))
        self.master_tg.pack(side="right", padx=(10, 22), pady=10)
        tk.Label(bottom, text="ВСЕ МАКРОСЫ", bg=BG, fg=MUTED,
                 font=F(8)).pack(side="right")
        self.save_btn = tk.Label(bottom, text="СОХРАНИТЬ", bg=ACCENT, fg=ON_ACCENT,
                                 font=F(9), padx=26, pady=8, cursor="hand2")
        self.save_btn.pack(side="right", padx=18, pady=10)
        self.save_btn.bind("<Button-1>", self.on_save)

        for mid, _n, title, sub, rows, sliders in PAGES:
            self.build_macro_page(mid, title, sub, rows, sliders)
        self.build_settings()
        self.build_design()

    def add_nav(self, parent, key, text, bgc, side_mode):
        row = tk.Frame(parent, bg=bgc, cursor="hand2")
        if side_mode:
            row.pack(fill="x", pady=1)
        else:
            row.pack(side="left", padx=(0, 14))
        bar = None
        if side_mode:
            bar = tk.Frame(row, bg=bgc, width=3)
            bar.pack(side="left", fill="y")
        lb = tk.Label(row, text=text, bg=bgc, fg=MUTED, font=F(9), anchor="w",
                      padx=16 if side_mode else 4, pady=10 if side_mode else 6)
        lb.pack(side="left", fill="x", expand=True)
        for w in (row, lb) + ((bar,) if bar else ()):
            w.bind("<Button-1>", lambda _e, k=key: self.show(k))
        lb.bind("<Enter>", lambda _e, k=key: lb.config(fg=TEXT) if k != self.current else None)
        lb.bind("<Leave>", lambda _e, k=key: lb.config(fg=MUTED) if k != self.current else None)
        self.nav[key] = (bar, lb, bgc)

    def style_nav(self, key, active):
        bar, lb, bgc = self.nav[key]
        lb.config(fg=TEXT if active else MUTED)
        if bar is not None:
            bar.config(bg=ACCENT if active else bgc)

    def show(self, key):
        if self.current in self.pages:
            self.pages[self.current].pack_forget()
            self.style_nav(self.current, False)
        self.current = key
        self.pages[key].pack(fill="both", expand=True)
        self.style_nav(key, True)

    def on_save(self, _e=None):
        save_cfg(self.cfg)
        self.save_btn.config(text="СОХРАНЕНО ✓")
        self.root.after(1500, lambda: self.save_btn.winfo_exists() and
                        self.save_btn.config(text="СОХРАНИТЬ"))

    # ── строительные блоки страниц ──
    def add_toggle(self, parent, getter, setter):
        def cmd(v):
            setter(v)
            save_cfg(self.cfg)
        t = Toggle(parent, getter(), cmd, bg=parent["bg"])
        self.toggles.append((t, getter))
        return t

    def page_header(self, key, title, subtitle, toggle_mid=None):
        f = tk.Frame(self.content, bg=BG)
        self.pages[key] = f
        head = tk.Frame(f, bg=BG)
        head.pack(fill="x", padx=28, pady=(20, 0))
        left = tk.Frame(head, bg=BG)
        left.pack(side="left")
        tk.Label(left, text=title, bg=BG, fg=TEXT, font=F(18)).pack(anchor="w")
        tk.Label(left, text=subtitle, bg=BG, fg=MUTED, font=F(8)).pack(anchor="w", pady=(2, 0))
        if toggle_mid:
            m = self.cfg["macros"][toggle_mid]
            tg = self.add_toggle(head, lambda: m["on"],
                                 lambda v: m.__setitem__("on", v))
            tg.pack(side="right")
            tk.Label(head, text="ВКЛ", bg=BG, fg=MUTED, font=F(8)).pack(side="right", padx=10)
        tk.Frame(f, bg=LINE, height=1).pack(fill="x", padx=28, pady=(14, 8))
        body = tk.Frame(f, bg=BG)
        body.pack(fill="both", expand=True, padx=28)
        return body

    def key_row(self, parent, label, get, set_, default, allow_lr=False):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=6)
        tk.Label(row, text=label, bg=BG, fg=TEXT, font=F(9), anchor="w").pack(side="left")
        reset = tk.Label(row, text="СБРОС", bg=BG, fg=MUTED, font=F(8),
                         width=7, cursor="hand2")
        reset.pack(side="right")

        def setter(vk):
            set_(vk)
            save_cfg(self.cfg)
        b = BindButton(row, get, setter, allow_lr)
        b.pack(side="right", padx=(0, 10))
        self.binds.append(b)

        def do_reset(_e=None):
            setter(default)
            b.refresh()
        reset.bind("<Button-1>", do_reset)

    def slider_row(self, parent, m, field, label, lo, hi):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=5)
        tk.Label(row, text=label, bg=BG, fg=TEXT, font=F(8), width=28,
                 anchor="w").pack(side="left")
        val = tk.Label(row, text=str(m[field]), bg=BG, fg=ACCENT, font=F(8),
                       width=5, anchor="e")
        val.pack(side="right")

        def on(v):
            m[field] = v
            val.config(text=str(v))
        Slider(row, lo, hi, m[field], on,
               release=lambda: save_cfg(self.cfg)).pack(
            side="left", fill="x", expand=True, padx=8)

    def build_macro_page(self, mid, title, sub, rows, sliders):
        body = self.page_header(mid, title, sub, toggle_mid=mid)
        m = self.cfg["macros"][mid]
        d = DEFAULT_CFG["macros"][mid]
        for field, label, lr in rows:
            self.key_row(body, label,
                         lambda f=field: m[f],
                         lambda v, f=field: m.__setitem__(f, v),
                         d[field], lr)
        tk.Frame(body, bg=BG, height=12).pack()
        for field, label, lo, hi in sliders:
            self.slider_row(body, m, field, label, lo, hi)

    # ── настройки ──
    def build_settings(self):
        body = self.page_header("settings", "НАСТРОЙКИ", "ОБЩИЕ ПАРАМЕТРЫ")
        self.key_row(body, "ВКЛ/ВЫКЛ ВСЕ МАКРОСЫ",
                     lambda: self.cfg["master_key"],
                     lambda v: self.cfg.__setitem__("master_key", v),
                     DEFAULT_CFG["master_key"])
        row = tk.Frame(body, bg=BG)
        row.pack(fill="x", pady=6)
        tk.Label(row, text="ЯРЛЫК НА РАБОЧЕМ СТОЛЕ", bg=BG, fg=TEXT, font=F(9)).pack(side="left")
        self.sc_btn = tk.Label(row, text="СОЗДАТЬ", bg=PANEL2, fg=TEXT, font=F(9),
                               width=22, pady=9, cursor="hand2")
        self.sc_btn.pack(side="right", padx=(0, 10 + 56))
        self.sc_btn.bind("<Button-1>", self.make_shortcut)
        tk.Label(body, text="В Fortnite включи «Edit on Release». Если игра запущена от "
                 "администратора, запускай макрос тоже от администратора.\n\nКонфиг: "
                 + CFG_PATH, bg=BG, fg=MUTED, font=F(8, False), justify="left",
                 wraplength=620).pack(anchor="w", pady=(18, 0))

    def make_shortcut(self, _e=None):
        ok = create_shortcut()
        self.sc_btn.config(text="ГОТОВО ✓" if ok else "ОШИБКА", fg=ACCENT if ok else TEXT)
        self.root.after(2000, lambda: self.sc_btn.winfo_exists() and
                        self.sc_btn.config(text="СОЗДАТЬ", fg=TEXT))

    # ── дизайн ──
    def chip(self, parent, text, active, cmd, font=None):
        lb = tk.Label(parent, text=text, bg=ACCENT if active else PANEL2,
                      fg=ON_ACCENT if active else TEXT, font=font or F(9),
                      padx=14, pady=7, cursor="hand2")
        lb.bind("<Button-1>", lambda _e: cmd())
        return lb

    def section(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg=MUTED, font=F(8)).pack(
            anchor="w", pady=(10, 6))

    def build_design(self):
        body = self.page_header("design", "ДИЗАЙН", "ВНЕШНИЙ ВИД ПРОГРАММЫ")
        t = self.cfg["theme"]

        self.section(body, "ЦВЕТ АКЦЕНТА")
        row = tk.Frame(body, bg=BG)
        row.pack(anchor="w")
        for _name, hexc in ACCENTS:
            c = tk.Canvas(row, width=30, height=30, bg=BG, highlightthickness=0,
                          cursor="hand2")
            c.create_oval(3, 3, 27, 27, fill=hexc, width=2,
                          outline=TEXT if str(t.get("accent")).lower() == hexc else BG)
            c.pack(side="left", padx=(0, 8))
            c.bind("<Button-1>", lambda _e, h=hexc: self.set_theme(accent=h))
        self.chip(row, "СВОЙ ЦВЕТ", False, self.pick_color).pack(side="left", padx=(8, 0))

        self.section(body, "ФОН")
        row = tk.Frame(body, bg=BG)
        row.pack(anchor="w")
        for name in BASES:
            self.chip(row, name, t.get("base") == name,
                      lambda n=name: self.set_theme(base=n)).pack(side="left", padx=(0, 8))

        self.section(body, "ШРИФТ")
        row = tk.Frame(body, bg=BG)
        row.pack(anchor="w")
        for fn in FONTS:
            self.chip(row, fn, t.get("font") == fn,
                      lambda n=fn: self.set_theme(font=n),
                      font=(fn, 9, "bold")).pack(side="left", padx=(0, 8))

        tk.Frame(body, bg=BG, height=14).pack()
        self.chip(body, "СБРОСИТЬ ДИЗАЙН", False,
                  lambda: self.set_theme(**DEFAULT_CFG["theme"])).pack(anchor="w")

    def pick_color(self):
        try:
            _rgb, hx = colorchooser.askcolor(color=ACCENT, parent=self.root,
                                             title="Цвет акцента")
        except Exception:
            return
        if hx:
            self.set_theme(accent=hx.lower())

    def set_theme(self, **kw):
        self.cfg["theme"].update(kw)
        apply_theme(self.cfg["theme"])
        save_cfg(self.cfg)
        self.root.after(20, self.rebuild)

    def rebuild(self):
        cur = self.current or "double_edit"
        for w in self.root.winfo_children():
            w.destroy()
        self.toggles, self.binds = [], []
        self.pages, self.nav = {}, {}
        self.current = None
        self.root.configure(bg=BG)
        self.build_ui()
        self.show(cur)

    # ── синхронизация интерфейса с движком ──
    def sync(self):
        try:
            for t, getter in self.toggles:
                t.set(getter())
            for b in self.binds:
                b.refresh()
        except tk.TclError:
            pass
        self.root.after(150, self.sync)


# ───────────────────────── Загрузочный экран ─────────────────────────
def splash_then(root, start_main):
    sp = tk.Toplevel(root)
    sp.overrideredirect(True)
    sp.configure(bg=BG)
    sp.attributes("-topmost", True)
    w, h = 460, 250
    x = (sp.winfo_screenwidth() - w) // 2
    y = (sp.winfo_screenheight() - h) // 2
    sp.geometry("%dx%d+%d+%d" % (w, h, x, y))

    frame = tk.Frame(sp, bg=BG, highlightbackground=ACCENT, highlightthickness=1)
    frame.pack(fill="both", expand=True)
    tk.Label(frame, text="WEXXYY MACRO", bg=BG, fg=TEXT, font=F(26)).pack(pady=(62, 4))
    status = tk.Label(frame, text="Загрузка…", bg=BG, fg=MUTED, font=F(10, False))
    status.pack()
    bar = tk.Canvas(frame, width=320, height=6, bg=PANEL2, highlightthickness=0)
    bar.pack(pady=22)
    fill = bar.create_rectangle(0, 0, 0, 6, fill=ACCENT, outline="")
    steps = ["Загрузка…", "Подготовка модулей…", "Загрузка профилей…", "Готово"]
    state = {"p": 0}

    def step():
        state["p"] += 1
        p = state["p"]
        bar.coords(fill, 0, 0, 320 * p / 100.0, 6)
        status.config(text=steps[min(3, p * 4 // 101)])
        if p < 100:
            sp.after(22, step)
        else:
            sp.after(250, finish)

    def finish():
        sp.destroy()
        start_main()
    step()


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    cfg = load_cfg()
    apply_theme(cfg["theme"])
    engine = Engine(cfg)
    root = tk.Tk()
    root.withdraw()

    def start_main():
        ico = ensure_icon()
        if ico:
            try:
                root.iconbitmap(ico)
            except Exception:
                pass
        if not cfg.get("shortcut_done"):
            cfg["shortcut_done"] = create_shortcut()  # один раз при первом запуске
            save_cfg(cfg)
        App(root, cfg, engine)
        root.deiconify()

    def on_close():
        save_cfg(cfg)
        engine.alive = False
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)
    splash_then(root, start_main)
    root.mainloop()


if __name__ == "__main__":
    main()
