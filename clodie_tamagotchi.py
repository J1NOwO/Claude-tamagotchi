#!/usr/bin/env python3
"""
Clodie - Claude AI Tamagotchi Pet Game
Python 3.8+ / tkinter only
"""
import tkinter as tk
from tkinter import messagebox
import json
import os
import random
import sys

# ─── Constants ────────────────────────────────────────────────────────────────
SAVE_FILE = "claude_pet_save.json"
TICK_MS   = 10_000      # 10 seconds per tick
SCALE     = 9           # pixel art scale
CANVAS_PX = 16 * SCALE  # 144 px  → but we center in 160×160

# Colours
C_BG       = "#1A1A2E"
C_BG_NIGHT = "#0D0D1A"
C_PANEL    = "#16213E"
C_SKIN     = "#F5C89A"
C_BROWN    = "#C17F3A"
C_HAIR     = "#8B5E3C"
C_EYES     = "#2D2D2D"
C_BLUSH    = "#F0A0A0"
C_BODY     = "#E94560"
C_ORANGE   = "#F5A623"
C_WHITE    = "#FFFFFF"
C_GREY     = "#AAAAAA"

BTN_COLORS = {
    "feed":  "#F5A623",
    "play":  "#4ECDC4",
    "sleep": "#7C5CBF",
    "wash":  "#5CB85C",
    "talk":  "#E94560",
}

TALK_LINES = [
    "냐옹~ 같이 놀자!",
    "오늘도 화이팅!",
    "배고프지 않아? 아 사실 조금...",
    "클로디가 곁에 있을게!",
    "넌 정말 멋져! 진심이야.",
    "심심하면 말 걸어줘 ~",
    "오늘 날씨 어때?",
    "같이 낮잠 잘까?",
    "Claude AI 최고야!",
    "내 이름은 클로디야!",
]

# ─── Pixel Art Data (16×16) ────────────────────────────────────────────────────
# Each row is 16 chars; legend: S=skin F=hair B=brown E=eye K=blush R=body O=orange .=transparent
SPRITES = {
    "HAPPY": [
        "................",
        "....FFFFFF......",
        "...FFFFFFFF.....",
        "..FFFFFFFFFF....",
        "..FSSSSSSSFF....",
        "..FSSSSSSSSF....",
        "..FSESSSESFF....",
        "..FSSKSSKFF.....",  # K=blush
        "..FSSSSSSFF.....",
        "...RRRRRRR......",
        "...RRORRR.......",
        "....RRRRR.......",
        ".....SSS........",
        "....SSSSS.......",
        "...SS...SS......",
        "................",
    ],
    "SAD": [
        "................",
        "....FFFFFF......",
        "...FFFFFFFF.....",
        "..FFFFFFFFFF....",
        "..FSSSSSSSFF....",
        "..FSSSSSSSSF....",
        "..FSESSSESFF....",
        "..FSSKKSSFF.....",
        "..FSVVVVSFF.....",  # V=sad mouth
        "...RRRRRRR......",
        "...RRORRR.......",
        "....RRRRR.......",
        ".....SSS........",
        "....SSSSS.......",
        "...SS...SS......",
        "................",
    ],
    "SLEEP": [
        "................",
        "....FFFFFF......",
        "...FFFFFFFF.....",
        "..FFFFFFFFFF....",
        "..FSSSSSSSFF....",
        "..FSSSSSSSSF....",
        "..FS--SSS--F....",  # -= closed eye
        "..FSSSSSSFF.....",
        "..FSuuuuSFF.....",  # u=sleep mouth
        "...RRRRRRR......",
        "...RRORRR.......",
        "....RRRRR.......",
        ".....SSS........",
        "....SSSSS.......",
        "...SS...SS......",
        "................",
    ],
}

PIXEL_MAP = {
    'S': C_SKIN,
    'F': C_HAIR,
    'B': C_BROWN,
    'E': C_EYES,
    'K': C_BLUSH,
    'R': C_BODY,
    'O': C_ORANGE,
    'W': C_WHITE,
    '-': C_EYES,    # closed eye line
    'u': C_SKIN,    # sleep mouth (same as skin, thin line)
    'V': "#8B0000",  # sad mouth dark
    '.': None,
}

# ─── Game State ───────────────────────────────────────────────────────────────
DEFAULT_STATE = {
    "name":       "클로디",
    "age":        0,
    "level":      1,
    "tick_count": 0,
    "hunger":     80,
    "happiness":  80,
    "energy":     80,
    "cleanliness":80,
    "sleeping":   False,
    "alive":      True,
}

# ─── Main Application ─────────────────────────────────────────────────────────
class ClodieApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Clodie – 클로디 키우기")
        self.root.resizable(False, False)
        self.root.configure(bg=C_BG)

        self.state = dict(DEFAULT_STATE)
        self.load_save()

        self.frame_idx   = 0       # animation frame 0-3
        self.zzz_idx     = 0       # zzz animation
        self.bubble_text = tk.StringVar(value="안녕! 나는 클로디야 ~")
        self.night_mode  = False

        self._build_ui()
        self._tick()
        self._animate()

    # ── UI Construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        W = 360
        self.root.geometry(f"{W}x620")

        # Title
        self.lbl_title = tk.Label(self.root, text="✦ Clodie ✦",
            font=("Courier", 20, "bold"), fg=C_ORANGE, bg=C_BG)
        self.lbl_title.pack(pady=(14, 0))

        # Age / Level
        self.lbl_age = tk.Label(self.root, text="",
            font=("Courier", 10), fg=C_GREY, bg=C_BG)
        self.lbl_age.pack()

        # Canvas (160×160)
        self.canvas_frame = tk.Frame(self.root, bg=C_PANEL,
            highlightbackground=C_ORANGE, highlightthickness=2)
        self.canvas_frame.pack(pady=8)
        self.canvas = tk.Canvas(self.canvas_frame, width=160, height=160,
            bg=C_PANEL, highlightthickness=0)
        self.canvas.pack()

        # Speech bubble
        bubble_frame = tk.Frame(self.root, bg=C_BG)
        bubble_frame.pack(fill="x", padx=30, pady=(0, 6))
        self.lbl_bubble = tk.Label(bubble_frame, textvariable=self.bubble_text,
            font=("Courier", 10), fg=C_WHITE, bg=C_PANEL,
            wraplength=280, relief="solid", bd=1,
            padx=10, pady=6)
        self.lbl_bubble.pack(fill="x")

        # Stat bars
        stats_frame = tk.Frame(self.root, bg=C_BG)
        stats_frame.pack(fill="x", padx=20, pady=4)
        self.bars = {}
        for stat, icon in [("hunger","🍖"), ("happiness","😊"),
                            ("energy","⚡"), ("cleanliness","🚿")]:
            row = tk.Frame(stats_frame, bg=C_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{icon}", font=("Courier",10),
                     fg=C_WHITE, bg=C_BG, width=3).pack(side="left")
            tk.Label(row, text=f"{stat[:3].upper()}", font=("Courier",8),
                     fg=C_GREY, bg=C_BG, width=4).pack(side="left")
            bar_bg = tk.Frame(row, bg="#2A2A4A", height=14, width=200)
            bar_bg.pack(side="left", padx=4)
            bar_bg.pack_propagate(False)
            bar_fg = tk.Frame(bar_bg, bg=C_ORANGE, height=14)
            bar_fg.place(x=0, y=0, relheight=1.0, relwidth=0.8)
            val_lbl = tk.Label(row, text="80", font=("Courier",8),
                               fg=C_GREY, bg=C_BG, width=4)
            val_lbl.pack(side="left")
            self.bars[stat] = (bar_bg, bar_fg, val_lbl)

        # Buttons
        btn_frame = tk.Frame(self.root, bg=C_BG)
        btn_frame.pack(pady=8)
        btn_defs = [
            ("🍖 밥주기",  "feed",  self.action_feed),
            ("🎮 놀아주기","play",  self.action_play),
            ("💤 재우기",  "sleep", self.action_sleep),
            ("🚿 씻기기",  "wash",  self.action_wash),
            ("💬 대화하기","talk",  self.action_talk),
        ]
        self.btn_refs = {}
        for i, (label, key, cmd) in enumerate(btn_defs):
            col = i % 3
            row_idx = i // 3
            btn = tk.Button(btn_frame, text=label, command=cmd,
                bg=BTN_COLORS[key], fg=C_BG if key!="sleep" else C_WHITE,
                font=("Courier", 9, "bold"), relief="flat",
                padx=8, pady=5, cursor="hand2",
                activebackground=BTN_COLORS[key])
            btn.grid(row=row_idx, column=col, padx=5, pady=4, sticky="ew")
            self.btn_refs[key] = btn
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        # Footer
        tk.Label(self.root, text="Claude AI × Clodie Pet v1.0",
            font=("Courier", 8), fg="#444466", bg=C_BG).pack(side="bottom", pady=6)

        self._refresh_ui()

    # ── Drawing ────────────────────────────────────────────────────────────────
    def _draw_sprite(self):
        self.canvas.delete("all")
        s = self.state

        # choose sprite
        if not s["alive"]:
            sprite_key = "DEAD"
        elif s["sleeping"]:
            sprite_key = "SLEEP"
        elif s["happiness"] < 30 or s["hunger"] < 30:
            sprite_key = "SAD"
        else:
            sprite_key = "HAPPY"

        if sprite_key == "DEAD":
            self._draw_tombstone()
            return

        grid = SPRITES[sprite_key]

        # wobble offset: frames 0,1,2,3 → dy: 0,1,0,-1
        wobble = [0, 1, 0, -1]
        dy = wobble[self.frame_idx % 4]

        ox = (160 - 16 * SCALE) // 2
        oy = (160 - 16 * SCALE) // 2 + dy

        for r, row in enumerate(grid):
            for c, ch in enumerate(row):
                color = PIXEL_MAP.get(ch)
                if color is None:
                    continue
                x1 = ox + c * SCALE
                y1 = oy + r * SCALE
                self.canvas.create_rectangle(
                    x1, y1, x1+SCALE, y1+SCALE,
                    fill=color, outline="")

        # zzz animation during sleep
        if s["sleeping"]:
            zzz_texts = ["z", "z Z", "z Z Z"]
            zzz = zzz_texts[self.zzz_idx % 3]
            self.canvas.create_text(130, 18, text=zzz,
                font=("Courier", 10, "bold"), fill=C_ORANGE, anchor="ne")

    def _draw_tombstone(self):
        """Simple tombstone pixel art on death."""
        self.canvas.delete("all")
        self.canvas.create_text(80, 60, text="✝",
            font=("Courier", 40), fill=C_GREY)
        self.canvas.create_text(80, 110, text="R.I.P\n클로디",
            font=("Courier", 11), fill=C_GREY, justify="center")

    # ── Stat Bar Refresh ───────────────────────────────────────────────────────
    def _refresh_ui(self):
        s = self.state

        # age label
        self.lbl_age.config(
            text=f"Lv.{s['level']}  |  나이: {s['age']}일")

        # night mode
        night = s["energy"] <= 30 and not s["sleeping"]
        if night != self.night_mode:
            self.night_mode = night
            bg = C_BG_NIGHT if night else C_BG
            self.root.configure(bg=bg)
            for w in (self.lbl_title, self.lbl_age, self.lbl_bubble):
                try: w.configure(bg=bg)
                except: pass

        # stat bars
        for stat, (bar_bg, bar_fg, val_lbl) in self.bars.items():
            val = max(0, min(100, int(s[stat])))
            ratio = val / 100.0
            bar_fg.place(relwidth=ratio)
            color = "#E94560" if val <= 30 else C_ORANGE
            bar_fg.configure(bg=color)
            val_lbl.configure(text=str(val))

        # sleep button label
        if s["sleeping"]:
            self.btn_refs["sleep"].configure(text="☀️ 깨우기")
        else:
            self.btn_refs["sleep"].configure(text="💤 재우기")

        # disable buttons while sleeping (except sleep/wake)
        for key, btn in self.btn_refs.items():
            if key == "sleep":
                continue
            btn.configure(state="disabled" if s["sleeping"] else "normal")

    # ── Tick (game logic, every 10s) ───────────────────────────────────────────
    def _tick(self):
        if not self.state["alive"]:
            self._refresh_ui()
            self._draw_sprite()
            return

        s = self.state
        if s["sleeping"]:
            s["energy"] = min(100, s["energy"] + 5)
            if s["energy"] >= 100:
                s["sleeping"] = False
                self.bubble_text.set("잘 잤다~ 이제 일어날게!")
        else:
            s["hunger"]     = max(0, s["hunger"]     - 3)
            s["happiness"]  = max(0, s["happiness"]  - 2)
            s["energy"]     = max(0, s["energy"]     - 2)
            s["cleanliness"]= max(0, s["cleanliness"]- 1)

        s["tick_count"] += 1

        # age
        if s["tick_count"] % 10 == 0:
            s["age"] += 1
            # level up every 7 days
            new_level = s["age"] // 7 + 1
            if new_level > s["level"]:
                s["level"] = new_level
                self._show_levelup(new_level)

        # death check
        if s["hunger"] <= 0 or s["energy"] <= 0:
            s["alive"] = False
            self._on_death()

        self._refresh_ui()
        self._draw_sprite()
        self.save_state()
        self.root.after(TICK_MS, self._tick)

    # ── Animation (every 500ms) ────────────────────────────────────────────────
    def _animate(self):
        self.frame_idx += 1
        if self.state["sleeping"]:
            self.zzz_idx += 1
        self._draw_sprite()
        self.root.after(500, self._animate)

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_feed(self):
        s = self.state
        s["hunger"]    = min(100, s["hunger"]    + 25)
        s["happiness"] = min(100, s["happiness"] + 5)
        self.bubble_text.set("냠냠~ 맛있다! 고마워!")
        self._refresh_ui(); self._draw_sprite(); self.save_state()

    def action_play(self):
        result = self._minigame()
        if result is None:
            return  # minigame window opened; handled in callback
        self._apply_play(result)

    def _apply_play(self, success: bool):
        s = self.state
        bonus = 10 if success else 0
        s["happiness"]  = min(100, s["happiness"]  + 25 + bonus)
        s["energy"]     = max(0,   s["energy"]     - 10)
        s["cleanliness"]= max(0,   s["cleanliness"]- 5)
        msg = "야호! 신난다! 최고야!" if success else "으~ 힘들어..."
        self.bubble_text.set(msg)
        self._refresh_ui(); self._draw_sprite(); self.save_state()

    def action_sleep(self):
        s = self.state
        s["sleeping"] = not s["sleeping"]
        if s["sleeping"]:
            self.bubble_text.set("쿨쿨~ 잘 자야지...")
        else:
            self.bubble_text.set("잠 깼어~ 안녕!")
        self._refresh_ui(); self._draw_sprite(); self.save_state()

    def action_wash(self):
        s = self.state
        s["cleanliness"] = min(100, s["cleanliness"] + 30)
        s["happiness"]   = min(100, s["happiness"]   + 5)
        self.bubble_text.set("깨끗~! 상쾌해!")
        self._refresh_ui(); self._draw_sprite(); self.save_state()

    def action_talk(self):
        line = random.choice(TALK_LINES)
        self.state["happiness"] = min(100, self.state["happiness"] + 5)
        self.bubble_text.set(line)
        self._refresh_ui(); self.save_state()

    # ── Minigame (timing click) ────────────────────────────────────────────────
    def _minigame(self):
        """Open a tiny timing minigame window. Returns None (async)."""
        win = tk.Toplevel(self.root)
        win.title("미니게임!")
        win.configure(bg=C_BG)
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="빛나는 순간에 클릭!", font=("Courier", 12, "bold"),
                 fg=C_ORANGE, bg=C_BG).pack(pady=10, padx=20)

        bar_canvas = tk.Canvas(win, width=240, height=30, bg="#2A2A4A",
                               highlightthickness=0)
        bar_canvas.pack(padx=20)

        indicator = bar_canvas.create_rectangle(0, 0, 30, 30,
            fill=C_ORANGE, outline="")
        target = bar_canvas.create_rectangle(100, 0, 140, 30,
            fill="#4ECDC4", outline="")

        pos = [0]
        direction = [1]
        result_holder = [None]
        anim_id = [None]

        def move():
            if result_holder[0] is not None:
                return
            pos[0] += direction[0] * 6
            if pos[0] >= 210:
                direction[0] = -1
            elif pos[0] <= 0:
                direction[0] = 1
            bar_canvas.coords(indicator, pos[0], 0, pos[0]+30, 30)
            anim_id[0] = win.after(40, move)

        def click_check():
            if anim_id[0]:
                win.after_cancel(anim_id[0])
            # check if indicator overlaps target zone 100-140
            success = 100 <= pos[0] <= 120
            result_holder[0] = success
            win.destroy()
            self._apply_play(success)

        tk.Button(win, text="클릭!", command=click_check,
            bg=C_ORANGE, fg=C_BG, font=("Courier", 12, "bold"),
            relief="flat", padx=20, pady=8, cursor="hand2").pack(pady=10)

        move()
        return None  # async

    # ── Level Up popup ─────────────────────────────────────────────────────────
    def _show_levelup(self, level: int):
        win = tk.Toplevel(self.root)
        win.title("레벨 업!")
        win.configure(bg=C_BG)
        win.resizable(False, False)
        win.grab_set()
        tk.Label(win, text=f"🎉 레벨 {level} 달성!",
            font=("Courier", 16, "bold"), fg=C_ORANGE, bg=C_BG).pack(pady=20, padx=30)
        tk.Label(win, text="클로디가 쑥쑥 자랐어요!",
            font=("Courier", 11), fg=C_WHITE, bg=C_BG).pack()
        tk.Button(win, text="고마워!", command=win.destroy,
            bg=C_ORANGE, fg=C_BG, font=("Courier", 11, "bold"),
            relief="flat", padx=16, pady=6, cursor="hand2").pack(pady=16)

    # ── Death ──────────────────────────────────────────────────────────────────
    def _on_death(self):
        self.bubble_text.set("...안녕... 다시 만나요...")
        self._draw_sprite()
        self.root.after(1500, lambda: messagebox.showinfo(
            "클로디가 떠났어요 😢",
            f"클로디는 {self.state['age']}일을 살았습니다.\n"
            "다시 시작하려면 앱을 재실행하세요.",
            parent=self.root
        ))

    # ── Save / Load ────────────────────────────────────────────────────────────
    def save_state(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_save(self):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for k, v in saved.items():
                if k in self.state:
                    self.state[k] = v
        except Exception:
            pass


# ─── Entry Point ───────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = ClodieApp(root)

    def on_close():
        app.save_state()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
