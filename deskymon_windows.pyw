"""
deskymon — Windows native version
Run with Windows Python: pythonw deskymon_windows.pyw
Requires: pip install pillow requests pywin32
"""
import tkinter as tk
from PIL import Image, ImageTk
import requests, os, math, random, sys
import ctypes, ctypes.wintypes

BASE  = os.path.dirname(os.path.abspath(__file__))
SPDIR = os.path.join(BASE, "sprites")
os.makedirs(SPDIR, exist_ok=True)

POKEMON_LIST = [
    "pikachu","eevee","psyduck","gengar",
    "snorlax","bulbasaur","charmander","mewtwo",
]
SPRITE_SCALE = 2
FOLLOW_SPEED = 0.10
RUN_SPEED    = 0.18
FOLLOW_DIST  = 180
RUN_DIST     = 55
SPEECH_CHANCE = 0.003

QUIPS = {
    "pikachu":    ["Pika!", "Pikachu!", "Pika pika~", "*zap*"],
    "eevee":      ["Eevee!", "Vee~", "*curious stare*", "Eeev?"],
    "psyduck":    ["Psy...", "Ow my head", "Psy-yi-yi!", "...?"],
    "gengar":     ["Gengar!", "*cackle*", "Heh heh heh"],
    "snorlax":    ["Zzzz...", "*snore*", "Snorlax!"],
    "bulbasaur":  ["Bulba!", "Saur~", "*sniff*"],
    "charmander": ["Char!", "Charmander!", "*tail flicker*"],
    "mewtwo":     ["...", "*stare*", "Mew."],
}

# ── Win32 helpers for click-through + always-on-top ─────────────────────────
GWL_EXSTYLE      = -20
WS_EX_LAYERED    = 0x00080000
WS_EX_TRANSPARENT= 0x00000020
WS_EX_TOPMOST    = 0x00000008
LWA_COLORKEY     = 0x00000001

user32 = ctypes.windll.user32

def set_transparent_window(hwnd, chroma=(1, 1, 1)):
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
        style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
    r, g, b = chroma
    colorref = r | (g << 8) | (b << 16)
    ctypes.windll.user32.SetLayeredWindowAttributes(
        hwnd, colorref, 0, LWA_COLORKEY)


def fetch_sprite(name):
    path = os.path.join(SPDIR, f"{name}.png")
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        data = requests.get(
            f"https://pokeapi.co/api/v2/pokemon/{name}", timeout=10).json()
        raw = requests.get(
            data["sprites"]["front_default"], timeout=10).content
        open(path, "wb").write(raw)
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    return img.resize((w * SPRITE_SCALE, h * SPRITE_SCALE), Image.NEAREST)


# ── Picker ───────────────────────────────────────────────────────────────────
def run_picker():
    root = tk.Tk()
    root.title("deskymon — pick your buddy")
    root.configure(bg="#f5f5f5")
    root.resizable(False, False)
    root.lift(); root.focus_force()
    root.attributes("-topmost", True)

    tk.Label(root, text="deskymon",
             font=("Helvetica", 16, "bold"), bg="#f5f5f5").pack(pady=(20, 4))
    tk.Label(root, text="Pick your desktop buddy",
             font=("Helvetica", 10), fg="#666", bg="#f5f5f5").pack(pady=(0, 14))

    chosen = tk.StringVar()
    f = tk.Frame(root, bg="#f5f5f5")
    f.pack(padx=24, pady=(0, 20))

    def pick(n):
        chosen.set(n); root.destroy()

    for i, n in enumerate(POKEMON_LIST):
        tk.Button(f, text=n.capitalize(), width=11,
                  command=lambda n=n: pick(n),
                  relief="groove", bg="white",
                  activebackground="#e8f4ff",
                  font=("Helvetica", 10)).grid(
            row=i // 4, column=i % 4, padx=6, pady=5)

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
    return chosen.get()


# ── Main buddy window ────────────────────────────────────────────────────────
class DeskyMon:
    CHROMA = "#010101"   # colour key for transparency

    def __init__(self, name):
        self.name = name
        self.root = tk.Tk()
        r = self.root

        SW = r.winfo_screenwidth()
        SH = r.winfo_screenheight()
        self.SW, self.SH = SW, SH

        # Frameless, always-on-top, chroma-key transparent
        r.overrideredirect(True)
        r.wm_attributes("-topmost", True)
        r.wm_attributes("-transparentcolor", self.CHROMA)
        r.configure(bg=self.CHROMA)

        self.sprite_img = fetch_sprite(name)
        self.sw, self.sh = self.sprite_img.size

        WIN_W = self.sw + 20
        WIN_H = self.sh + 36

        self.canvas = tk.Canvas(r,
            width=WIN_W, height=WIN_H,
            bg=self.CHROMA, highlightthickness=0)
        self.canvas.pack()

        self.x = float(SW // 2)
        self.y = float(SH // 2)
        self.vx = self.vy = 0.0
        self.facing = 1
        self.idle_dir = random.choice([-1, 1])
        self.idle_ticks = 0
        self.speech = f"Hi! I'm {name.capitalize()}!"
        self.speech_t = 80
        self.tick = 0

        self.img_r = ImageTk.PhotoImage(self.sprite_img)
        self.img_l = ImageTk.PhotoImage(
            self.sprite_img.transpose(Image.FLIP_LEFT_RIGHT))

        # Right-click menu
        menu = tk.Menu(r, tearoff=0)
        menu.add_command(label="Switch Pokemon", command=self.open_picker)
        menu.add_separator()
        menu.add_command(label="Quit", command=r.destroy)
        self.canvas.bind("<Button-3>",
            lambda e: menu.tk_popup(e.x_root, e.y_root))
        self.canvas.bind("<Button-1>", lambda e: self._poke())

        r.geometry(f"{WIN_W}x{WIN_H}+{int(self.x)}+{int(self.y)}")
        r.update()

        # Apply Win32 click-through so clicks pass to desktop
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        set_transparent_window(hwnd)

        self._loop()
        r.mainloop()

    def _poke(self):
        self.speech  = random.choice(["Ow!", "Hey~", "Eep!", "!"])
        self.speech_t = 60

    def _poll_cursor(self):
        pt = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def _preferred_zone(self, mx, my):
        """Return the quadrant opposite to where the cursor is — least distracting."""
        cx = self.SW / 2
        cy = self.SH / 2
        # target x: opposite horizontal half, 80px from edge
        tx = self.SW - 120 if mx < cx else 120
        # target y: bottom third of screen — out of the way
        ty = self.SH - 160
        return tx, ty

    def _loop(self):
        self.tick += 1
        mx, my = self._poll_cursor()

        # Distance from Pokémon center to cursor
        cx = self.x + self.sw / 2
        cy = self.y + self.sh / 2
        dx = mx - cx
        dy = my - cy
        dist = math.sqrt(dx*dx + dy*dy) or 1

        if dist < RUN_DIST:
            # Panic — flee directly away from cursor
            self.vx -= (dx/dist) * RUN_SPEED * 12
            self.vy -= (dy/dist) * RUN_SPEED * 12
            self.idle_ticks = 0

        elif dist < FOLLOW_DIST:
            # Follow cursor but lag behind it
            self.vx += (dx/dist) * FOLLOW_SPEED * 6
            self.vy += (dy/dist) * FOLLOW_SPEED * 6
            self.idle_ticks = 0

        else:
            # Idle — drift toward the preferred quiet zone
            tx, ty = self._preferred_zone(mx, my)
            zdx = tx - self.x
            zdy = ty - self.y
            zdist = math.sqrt(zdx*zdx + zdy*zdy) or 1

            self.idle_ticks += 1
            if zdist > 40:
                # Slowly migrate toward quiet zone
                self.vx += (zdx/zdist) * 0.3
                self.vy += (zdy/zdist) * 0.2
            else:
                # In zone — gentle wander
                if self.idle_ticks > 100:
                    self.idle_ticks = 0
                    self.idle_dir = random.choice([-1, 1, 1, 0])
                if self.idle_ticks < 60 and self.idle_dir:
                    self.vx += self.idle_dir * 0.25
                else:
                    self.vx *= 0.88
                self.vy *= 0.88

        self.vx *= 0.82
        self.vy *= 0.82

        # Clamp to screen bounds with padding
        PAD = 20
        self.x = max(PAD, min(self.SW - self.sw - PAD, self.x + self.vx))
        self.y = max(PAD, min(self.SH - self.sh - 60, self.y + self.vy))

        if abs(self.vx) > 0.3:
            self.facing = 1 if self.vx > 0 else -1

        if random.random() < SPEECH_CHANCE:
            self.speech   = random.choice(QUIPS.get(self.name, ["!"]))
            self.speech_t = 90

        self._draw()
        self.root.after(16, self._loop)

    def _draw(self):
        c = self.canvas
        c.delete("all")

        if self.speech_t > 0:
            tw = len(self.speech) * 7 + 12
            bx = 10
            c.create_rectangle(bx, 2, bx+tw, 22,
                fill="white", outline="#bbbbbb")
            c.create_text(bx + tw//2, 12,
                text=self.speech, font=("Helvetica", 9), fill="#222")
            self.speech_t -= 1

        img = self.img_r if self.facing >= 0 else self.img_l
        c.create_image(10, 26, anchor="nw", image=img)

        self.root.geometry(
            f"{self.sw+20}x{self.sh+36}+"
            f"{int(self.x)}+{int(self.y)}")

    def open_picker(self):
        picker = tk.Toplevel(self.root)
        picker.title("Switch Pokemon")
        picker.configure(bg="#f5f5f5")
        picker.resizable(False, False)
        picker.lift(); picker.focus_force()
        tk.Label(picker, text="Who's your buddy?",
                 font=("Helvetica", 13, "bold"),
                 bg="#f5f5f5").pack(pady=(16, 8))
        f = tk.Frame(picker, bg="#f5f5f5")
        f.pack(padx=20, pady=(0, 16))
        def pick(n):
            picker.destroy()
            self.switch(n)
        for i, n in enumerate(POKEMON_LIST):
            tk.Button(f, text=n.capitalize(), width=10,
                command=lambda n=n: pick(n),
                relief="groove", bg="white").grid(
                row=i//4, column=i%4, padx=6, pady=4)

    def switch(self, name):
        self.name      = name
        self.sprite_img = fetch_sprite(name)
        self.sw, self.sh = self.sprite_img.size
        self.img_r = ImageTk.PhotoImage(self.sprite_img)
        self.img_l = ImageTk.PhotoImage(
            self.sprite_img.transpose(Image.FLIP_LEFT_RIGHT))
        self.speech   = f"Hi! I'm {name.capitalize()}!"
        self.speech_t = 100


if __name__ == "__main__":
    name = run_picker()
    if name:
        DeskyMon(name)
