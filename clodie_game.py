"""
Clodie - Claude AI Tamagotchi Pet Game
Python 3.8+ / tkinter only
"""
import tkinter as tk
from tkinter import messagebox
import json, os, random, time

SAVE_FILE = "claude_pet_save.json"

# ── Palette ──────────────────────────────────────────────────────────────────
C_BG       = "#1A1A2E"
C_PANEL    = "#16213E"
C_ORANGE   = "#F5A623"
C_BROWN    = "#C17F3A"
C_SKIN     = "#F5C89A"
C_EYE      = "#2D2D2D"
C_CHEEK    = "#F0A0A0"
C_BODY     = "#E94560"
C_HAIR     = "#8B5E3C"
C_WHITE    = "#FFFFFF"
C_NIGHT_BG = "#0A0A1A"
C_BAR_OK   = "#4ECDC4"
C_BAR_WARN = "#E94560"

BTN_COLORS = {
    "feed":  ("#F5A623","#1A1A2E"),
    "play":  ("#4ECDC4","#1A1A2E"),
    "sleep": ("#7C5CBF","#FFFFFF"),
    "wash":  ("#5CB85C","#FFFFFF"),
    "chat":  ("#E94560","#FFFFFF"),
}

SCALE = 9
GRID  = 16
CANVAS_PX = SCALE * GRID   # 144

# ── Pixel Art Sprites (16×16) ─────────────────────────────────────────────────
# Each row = 16 chars: . = transparent, colours defined below
# Key: S=skin, B=brown, H=hair, E=eye, K=cheek, R=body, O=orange, W=white

def _parse(rows, mapping):
    """Convert list-of-strings sprite to list of (col,row,color)."""
    result = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch in mapping and mapping[ch]:
                result.append((c, r, mapping[ch]))
    return result

_M = {'.':None,'S':C_SKIN,'B':C_BROWN,'H':C_HAIR,'E':C_EYE,
      'K':C_CHEEK,'R':C_BODY,'O':C_ORANGE,'W':C_WHITE,'P':'#F08030'}

SPRITE_HAPPY = _parse([
    "....HHHHHH......",
    "...HHHHHHHH.....",
    "..HHSSSSSSHHH...",
    "..HSSSSSSSSSH...",
    ".HSSSSSSSSSSBH..",
    ".HSSESSSSESSH...",
    ".HSSESSSSESSH...",
    ".HSSSSKSSSSSH...",
    ".HSSS.K.SSSSH...",
    ".HSSS.K.SSSSH...",
    ".HSSSSSSSSSS H..",
    "..HRRRRRRRRRH...",
    "..HRRORRORRH....",
    "...RRRRRRRRR....",
    "....RRRRRRRR....",
    "....BBBB.BBB....",
], _M)

SPRITE_SAD = _parse([
    "....HHHHHH......",
    "...HHHHHHHH.....",
    "..HHSSSSSSHHH...",
    "..HSSSSSSSSSH...",
    ".HSSSSSSSSSSBH..",
    ".HSSEESSSEES H..",
    ".HSSEESSSEES H..",
    ".HSSSSSSSSSS H..",
    ".HSSSK.KSSSSH...",
    ".HSSS...SSSSH...",
    ".HSSSSSSSSSS H..",
    "..HRRRRRRRRRH...",
    "..HRRORRORRH....",
    "...RRRRRRRRR....",
    "....RRRRRRRR....",
    "....BBBB.BBB....",
], _M)

SPRITE_SLEEP = _parse([
    "....HHHHHH......",
    "...HHHHHHHH.....",
    "..HHSSSSSSHHH...",
    "..HSSSSSSSSSH...",
    ".HSSSSSSSSSSBH..",
    ".HSSE.SSSE. SH..",
    ".HSSE.SSSE. SH..",
    ".HSSSSSSSSSSH...",
    ".HSSSSSSSSSS H..",
    ".HSSSSSSSSSS H..",
    ".HSSSSSSSSSS H..",
    "..HRRRRRRRRRH...",
    "..HRRORRORRH....",
    "...RRRRRRRRR....",
    "....RRRRRRRR....",
    "....BBBB.BBB....",
], _M)

SPRITE_DEAD = _parse([
    "....HHHHHH......",
    "...HHHHHHHH.....",
    "..HHSSSSSSHHH...",
    "..HSSSSSSSSSH...",
    ".HSSSSSSSSSSBH..",
    ".HSSE.SSSE. SH..",
    ".HSSE.SSSE. SH..",
    ".HSSSSSSSSSSSH..",
    ".HSSSSSSSSSS H..",
    "..BBBBBBBBBBB...",
    "...BWBWBWBWB....",
    "....BBBBBBB.....",
    ".....BWWWWB.....",
    "......BBBBB.....",
    "..E.........E...",
    "...EEEEEEEE.....",
], _M)

# ── Chat messages ─────────────────────────────────────────────────────────────
CHAT_MSGS = [
    "I ♥ Claude!", "Beep boop~", "Feed me more!",
    "Let's be friends!", "I'm so happy!",
    "Orange is the best color!", "Clodie loves you!",
    "Processing cuteness...", "Error: Too adorable.",
    "*happy noises*", "Am I a good pet?",
    "I learned something today!", "Stay curious!",
]

# ── Main Application ──────────────────────────────────────────────────────────
class ClodieApp(tk.Tk):
    TICK_MS   = 10_000   # 10 s per game tick
    ANIM_MS   = 300      # sprite shake frame
    ZZZ_MS    = 800      # zzz cycle

    def __init__(self):
        super().__init__()
        self.title("Clodie 🤖")
        self.resizable(False, False)
        self.configure(bg=C_BG)

        # ── State ──────────────────────────────────────────────────────────
        self.hunger     = tk.IntVar(value=80)
        self.happiness  = tk.IntVar(value=80)
        self.energy     = tk.IntVar(value=80)
        self.cleanliness= tk.IntVar(value=80)
        self.age        = tk.IntVar(value=0)
        self.level      = tk.IntVar(value=1)
        self.tick_count = 0
        self.sleeping   = False
        self.dead       = False
        self.bubble_text= tk.StringVar(value="Hi! I'm Clodie!")
        self.anim_frame = 0
        self.zzz_state  = 0
        self.night_mode = False

        self._load()
        self._build_ui()
        self._schedule_tick()
        self._animate()
        self._zzz_loop()

    # ── Save / Load ────────────────────────────────────────────────────────
    def _save(self):
        data = {
            "hunger":      self.hunger.get(),
            "happiness":   self.happiness.get(),
            "energy":      self.energy.get(),
            "cleanliness": self.cleanliness.get(),
            "age":         self.age.get(),
            "level":       self.level.get(),
            "tick_count":  self.tick_count,
            "sleeping":    self.sleeping,
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)

    def _load(self):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE) as f:
                d = json.load(f)
            self.hunger.set(d.get("hunger",80))
            self.happiness.set(d.get("happiness",80))
            self.energy.set(d.get("energy",80))
            self.cleanliness.set(d.get("cleanliness",80))
            self.age.set(d.get("age",0))
            self.level.set(d.get("level",1))
            self.tick_count = d.get("tick_count",0)
            self.sleeping   = d.get("sleeping",False)
        except Exception:
            pass

    # ── UI Construction ────────────────────────────────────────────────────
    def _build_ui(self):
        W = 360
        self.geometry(f"{W}x640")

        # Title bar
        tk.Label(self, text="✦ CLODIE ✦", font=("Courier",22,"bold"),
                 bg=C_BG, fg=C_ORANGE).pack(pady=(14,2))

        # Age / Level
        self.age_label = tk.Label(self, textvariable=self.age,
                                  font=("Courier",11), bg=C_BG, fg=C_BROWN)
        self._update_age_label()
        self.age_label.pack()

        # Canvas
        self.canvas = tk.Canvas(self, width=CANVAS_PX+32, height=CANVAS_PX+32,
                                bg=C_BG, highlightthickness=0)
        self.canvas.pack(pady=8)

        # Speech bubble
        bubble_frame = tk.Frame(self, bg=C_BG)
        bubble_frame.pack(fill="x", padx=20)
        tk.Label(bubble_frame, textvariable=self.bubble_text,
                 font=("Courier",11), bg="#16213E", fg=C_WHITE,
                 relief="flat", bd=0, padx=10, pady=6,
                 wraplength=310).pack(fill="x")

        # Stat bars
        bar_frame = tk.Frame(self, bg=C_BG)
        bar_frame.pack(fill="x", padx=20, pady=6)
        self.bar_refs = {}
        stats = [
            ("🍖 Hunger",    self.hunger),
            ("😊 Happy",     self.happiness),
            ("⚡ Energy",    self.energy),
            ("🚿 Clean",     self.cleanliness),
        ]
        for label, var in stats:
            row = tk.Frame(bar_frame, bg=C_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, width=12, anchor="w",
                     font=("Courier",9), bg=C_BG, fg=C_WHITE).pack(side="left")
            bg_bar = tk.Canvas(row, width=160, height=12,
                               bg="#2D2D4E", highlightthickness=0)
            bg_bar.pack(side="left", padx=4)
            fill = bg_bar.create_rectangle(0,0,0,12, fill=C_BAR_OK, outline="")
            self.bar_refs[label] = (bg_bar, fill, var)

        self._refresh_bars()

        # Buttons
        btn_frame = tk.Frame(self, bg=C_BG)
        btn_frame.pack(pady=8)
        buttons = [
            ("🍖 Feed",  "feed",  self._feed),
            ("🎮 Play",  "play",  self._play),
            ("💤 Sleep", "sleep", self._toggle_sleep),
            ("🚿 Wash",  "wash",  self._wash),
            ("💬 Chat",  "chat",  self._chat),
        ]
        for i, (text, key, cmd) in enumerate(buttons):
            bg, fg = BTN_COLORS[key]
            b = tk.Button(btn_frame, text=text, command=cmd,
                          bg=bg, fg=fg, font=("Courier",10,"bold"),
                          relief="flat", padx=8, pady=6, cursor="hand2",
                          activebackground=bg, activeforeground=fg)
            b.grid(row=i//3, column=i%3, padx=4, pady=4)

        # Footer
        tk.Label(self, text="Claude AI Pet  •  Auto-saves every 10s",
                 font=("Courier",8), bg=C_BG, fg="#555577").pack(pady=(4,8))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Sprite / Canvas Drawing ───────────────────────────────────────────
    def _draw(self):
        c = self.canvas
        c.delete("all")

        # Background
        night = self.energy.get() <= 30 and not self.dead
        bg = C_NIGHT_BG if night else C_BG
        c.configure(bg=bg)

        if self.dead:
            sprite = SPRITE_DEAD
        elif self.sleeping:
            sprite = SPRITE_SLEEP
        elif self.happiness.get() < 30:
            sprite = SPRITE_SAD
        else:
            sprite = SPRITE_HAPPY

        # Shake offset
        ox = [0, 1, 0, -1][self.anim_frame % 4]
        oy = [0, 0, 1,  0][self.anim_frame % 4]

        off_x = 16 + ox
        off_y = 16 + oy
        for (col, row, color) in sprite:
            x1 = off_x + col * SCALE
            y1 = off_y + row * SCALE
            c.create_rectangle(x1, y1, x1+SCALE-1, y1+SCALE-1,
                                fill=color, outline="")

        # ZZZ
        if self.sleeping and not self.dead:
            zs = ["z", "z Z", "z Z Z"][self.zzz_state % 3]
            c.create_text(off_x + CANVAS_PX + 2, off_y + 4,
                          text=zs, anchor="nw",
                          font=("Courier",14,"bold"),
                          fill=C_ORANGE)

    # ── Animation loops ───────────────────────────────────────────────────
    def _animate(self):
        if not self.dead:
            self.anim_frame = (self.anim_frame + 1) % 4
        self._draw()
        self.after(self.ANIM_MS, self._animate)

    def _zzz_loop(self):
        self.zzz_state = (self.zzz_state + 1) % 3
        self.after(self.ZZZ_MS, self._zzz_loop)

    # ── Stat Bars ─────────────────────────────────────────────────────────
    def _refresh_bars(self):
        for label, (bg_bar, fill, var) in self.bar_refs.items():
            v = max(0, min(100, var.get()))
            w = int(160 * v / 100)
            color = C_BAR_WARN if v <= 30 else C_BAR_OK
            bg_bar.coords(fill, 0, 0, w, 12)
            bg_bar.itemconfig(fill, fill=color)

    def _update_age_label(self):
        age = self.age.get()
        lv  = self.level.get()
        self.age_label.config(
            text=f"Age {age} days  •  Lv {lv}",
            font=("Courier",11), bg=C_BG, fg=C_BROWN
        )

    # ── Game Tick ────────────────────────────────────────────────────────
    def _schedule_tick(self):
        self.after(self.TICK_MS, self._tick)

    def _tick(self):
        if self.dead:
            return
        self.tick_count += 1

        if self.sleeping:
            self._add(self.energy, +5)
            # auto-wake
            if self.energy.get() >= 100:
                self.sleeping = False
                self.bubble_text.set("*yawns* Good morning!")
        else:
            self._add(self.hunger,      -3)
            self._add(self.happiness,   -2)
            self._add(self.energy,      -2)
            self._add(self.cleanliness, -2)

        # Age
        if self.tick_count % 10 == 0:
            self.age.set(self.age.get() + 1)
            self._update_age_label()

        # Level up every 7 days (70 ticks)
        if self.tick_count % 70 == 0 and self.tick_count > 0:
            self.level.set(self.level.get() + 1)
            self._update_age_label()
            self._level_up_popup()

        # Game over check
        if self.hunger.get() <= 0 or self.energy.get() <= 0:
            self._game_over()
            return

        self._refresh_bars()
        self._save()
        self._schedule_tick()

    def _add(self, var, delta):
        var.set(max(0, min(100, var.get() + delta)))

    # ── Buttons ───────────────────────────────────────────────────────────
    def _feed(self):
        if self.dead: return
        self._add(self.hunger, +25)
        self._add(self.happiness, +5)
        self.bubble_text.set("Yum yum! Thanks!")
        self._refresh_bars()

    def _play(self):
        if self.dead: return
        if self.sleeping:
            self.bubble_text.set("Zzz... let me sleep!")
            return
        result = self._minigame()
        if result:
            self._add(self.happiness, +30)
            self.bubble_text.set("Woohoo! I won!")
        else:
            self._add(self.happiness, +10)
            self.bubble_text.set("That was fun anyway~")
        self._add(self.energy,      -10)
        self._add(self.cleanliness, -5)
        self._refresh_bars()

    def _toggle_sleep(self):
        if self.dead: return
        self.sleeping = not self.sleeping
        if self.sleeping:
            self.bubble_text.set("Good night... zzz")
        else:
            self.bubble_text.set("I'm awake! Morning!")
        self._refresh_bars()

    def _wash(self):
        if self.dead: return
        self._add(self.cleanliness, +30)
        self._add(self.happiness, +5)
        self.bubble_text.set("Squeaky clean! ✨")
        self._refresh_bars()

    def _chat(self):
        if self.dead: return
        msg = random.choice(CHAT_MSGS)
        self._add(self.happiness, +5)
        self.bubble_text.set(msg)
        self._refresh_bars()

    # ── Mini-game ──────────────────────────────────────────────────────────
    def _minigame(self):
        """Simple timing mini-game: press button in the highlighted window."""
        win = tk.Toplevel(self)
        win.title("Mini Game!")
        win.configure(bg=C_BG)
        win.resizable(False,False)
        win.geometry("280x200")
        win.grab_set()

        tk.Label(win, text="⚡ Timing Game ⚡",
                 font=("Courier",14,"bold"), bg=C_BG, fg=C_ORANGE).pack(pady=10)
        tk.Label(win, text="Press HIT when bar turns green!",
                 font=("Courier",9), bg=C_BG, fg=C_WHITE).pack()

        bar_canvas = tk.Canvas(win, width=220, height=24,
                               bg="#2D2D4E", highlightthickness=0)
        bar_canvas.pack(pady=8)
        cursor = bar_canvas.create_rectangle(0,0,24,24, fill=C_ORANGE, outline="")

        result = [False]
        win_start = random.randint(80, 140)
        win_end   = win_start + 30
        pos = [0]
        direction = [1]
        running = [True]

        def move():
            if not running[0]: return
            pos[0] += direction[0] * 4
            if pos[0] >= 220 or pos[0] <= 0:
                direction[0] *= -1
            in_win = win_start <= pos[0] <= win_end
            color = "#00FF88" if in_win else C_ORANGE
            bar_canvas.coords(cursor, pos[0], 0, pos[0]+24, 24)
            bar_canvas.itemconfig(cursor, fill=color)
            if running[0]:
                win.after(30, move)

        def hit():
            running[0] = False
            result[0] = win_start <= pos[0] <= win_end
            win.destroy()

        tk.Button(win, text="HIT!", command=hit,
                  bg="#00FF88", fg=C_BG,
                  font=("Courier",14,"bold"),
                  relief="flat", padx=20, pady=8).pack(pady=6)

        move()
        self.wait_window(win)
        return result[0]

    # ── Level Up ──────────────────────────────────────────────────────────
    def _level_up_popup(self):
        lv = self.level.get()
        win = tk.Toplevel(self)
        win.title("Level Up!")
        win.configure(bg=C_BG)
        win.geometry("260x160")
        win.grab_set()
        tk.Label(win, text="🎉 LEVEL UP! 🎉",
                 font=("Courier",16,"bold"), bg=C_BG, fg=C_ORANGE).pack(pady=20)
        tk.Label(win, text=f"Clodie is now Level {lv}!",
                 font=("Courier",12), bg=C_BG, fg=C_WHITE).pack()
        tk.Button(win, text="Yay!", command=win.destroy,
                  bg=C_ORANGE, fg=C_BG,
                  font=("Courier",12,"bold"),
                  relief="flat", padx=16, pady=6).pack(pady=20)

    # ── Game Over ─────────────────────────────────────────────────────────
    def _game_over(self):
        self.dead = True
        self.bubble_text.set("...goodbye... 💔")
        self._draw()

        # Delete save so next run starts fresh
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)

        win = tk.Toplevel(self)
        win.title("Game Over")
        win.configure(bg=C_BG)
        win.geometry("280x220")
        win.grab_set()

        tk.Label(win, text="✝  CLODIE HAS GONE  ✝",
                 font=("Courier",13,"bold"), bg=C_BG, fg="#888888").pack(pady=16)
        tk.Label(win, text=f"Age: {self.age.get()} days\nLevel: {self.level.get()}",
                 font=("Courier",11), bg=C_BG, fg=C_WHITE).pack()
        tk.Label(win, text="Here lies Clodie\nA beloved AI pet",
                 font=("Courier",10,"italic"), bg=C_BG, fg="#666688").pack(pady=8)

        def restart():
            win.destroy()
            self._restart()

        tk.Button(win, text="New Game", command=restart,
                  bg=C_ORANGE, fg=C_BG,
                  font=("Courier",12,"bold"),
                  relief="flat", padx=14, pady=6).pack(pady=10)

    def _restart(self):
        self.hunger.set(80); self.happiness.set(80)
        self.energy.set(80); self.cleanliness.set(80)
        self.age.set(0);     self.level.set(1)
        self.tick_count = 0; self.sleeping = False; self.dead = False
        self.anim_frame = 0
        self.bubble_text.set("Hi! I'm Clodie!")
        self._update_age_label()
        self._refresh_bars()
        self._schedule_tick()

    def _on_close(self):
        self._save()
        self.destroy()

# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ClodieApp()
    app.mainloop()
