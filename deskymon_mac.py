"""
deskymon — macOS version
Run: python3 deskymon_mac.py
Requires: pip3 install pillow requests
"""
import tkinter as tk
from PIL import Image, ImageTk
import requests, os, math, random, sys

BASE  = os.path.dirname(os.path.abspath(__file__))
SPDIR = os.path.join(BASE, "sprites")
os.makedirs(SPDIR, exist_ok=True)

POKEMON_LIST  = ["pikachu","eevee","psyduck","gengar","snorlax","bulbasaur","charmander","mewtwo"]
SPRITE_SCALE  = 2
FOLLOW_SPEED  = 0.06
RUN_SPEED     = 0.14
FOLLOW_DIST   = 160
RUN_DIST      = 50
DEADZONE      = 30
SPEECH_CHANCE = 0.003
CHROMA        = "#00fe00"   # green chroma key — keyed out by transparentcolor

QUIPS = {
    "pikachu":    ["Pika!", "Pika pika!", "Pikachu!", "Pikaa~"],
    "eevee":      ["Eevee!", "Vui!", "Eevee vui!", "Vuiii~"],
    "psyduck":    ["Psy?", "Psyduck!", "Psy psy!", "Psyyy..."],
    "gengar":     ["Gengar!", "Geng!", "Gengarrr~"],
    "snorlax":    ["Snorlax!", "Snor...", "Snoooor~"],
    "bulbasaur":  ["Bulba!", "Bulbasaur!", "Saur!"],
    "charmander": ["Char!", "Charmander!", "Charrr~"],
    "mewtwo":     ["Mew.", "Mewtwo!", "Mewww~"],
}
REACTIONS = {
    "pikachu":    ["Pika pi!", "Pikachuuu!"],
    "eevee":      ["Vui vui!", "Eevee!"],
    "psyduck":    ["PSY!", "Psyduck!"],
    "gengar":     ["GENGAR!", "Gengarrr!"],
    "snorlax":    ["SNORLAX!", "LAX!"],
    "bulbasaur":  ["BULBA!", "Bulbasaur!"],
    "charmander": ["CHAR!", "Charrr!!"],
    "mewtwo":     ["MEW.", "Mewtwo!!"],
}


def fetch_sprite(name):
    path = os.path.join(SPDIR, f"{name}.png")
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}", timeout=10).json()
        raw  = requests.get(data["sprites"]["front_default"], timeout=10).content
        open(path, "wb").write(raw)
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    return img.resize((w * SPRITE_SCALE, h * SPRITE_SCALE), Image.NEAREST)


def composite(sprite_img):
    """Composite onto a unique bg color that will be keyed out by the window."""
    # Use a very specific purple that won't appear in any Pokemon sprite
    KEY = (254, 0, 254, 255)
    bg = Image.new("RGBA", sprite_img.size, KEY)
    bg.paste(sprite_img, mask=sprite_img.split()[3])
    return bg.convert("RGB")


def run_picker():
    root = tk.Tk()
    root.title("deskymon")
    root.configure(bg="#f5f5f5")
    root.resizable(False, False)
    root.lift()
    root.focus_force()
    root.attributes("-topmost", True)

    tk.Label(root, text="deskymon", font=("Helvetica", 16, "bold"), bg="#f5f5f5").pack(pady=(20,4))
    tk.Label(root, text="Pick your desktop buddy", font=("Helvetica",10), fg="#666", bg="#f5f5f5").pack(pady=(0,14))

    chosen = tk.StringVar()
    f = tk.Frame(root, bg="#f5f5f5")
    f.pack(padx=24, pady=(0,20))

    def pick(n):
        chosen.set(n); root.destroy()

    for i, n in enumerate(POKEMON_LIST):
        tk.Button(f, text=n.capitalize(), width=11, command=lambda n=n: pick(n),
                  relief="groove", bg="white", activebackground="#e8f4ff",
                  font=("Helvetica", 10)).grid(row=i//4, column=i%4, padx=6, pady=5)

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
    return chosen.get()


class DeskyMon:
    def __init__(self, name):
        self.name = name
        self.root = r = tk.Tk()

        self.SW = r.winfo_screenwidth()
        self.SH = r.winfo_screenheight()

        BGCOL = "#fe00fe"  # magic purple — keyed transparent
        r.wm_attributes("-topmost", True)
        r.wm_attributes("-transparent", True)
        r.configure(bg=BGCOL)
        # Tell the Mac compositor to key out this exact color
        r.update()
        r.tk.call("wm", "attributes", r._w, "-transparentcolor", BGCOL)
        r.resizable(False, False)

        # Hide title bar — works on macOS without overrideredirect
        try:
            r.tk.call("::tk::unsupported::MacWindowStyle", "style", r._w, "plain", "none")
        except Exception:
            pass

        self.sprite_img = fetch_sprite(name)
        self.sw, self.sh = self.sprite_img.size
        self.WIN_W = self.sw + 20
        self.WIN_H = self.sh + 36

        # Single label — composite sprite onto chroma bg, window keys it out
        self.lbl = tk.Label(r, bd=0, highlightthickness=0, bg="#fe00fe")
        self.lbl.pack(pady=(26, 0), padx=10, anchor="w")

        # Speech bubble
        self.bubble = tk.Label(r, font=("Helvetica", 9), fg="#222",
                               bg="white", relief="solid", bd=1, padx=4, pady=2)

        self.x  = float(self.SW - self.sw - 80)
        self.y  = float(self.SH - self.sh - 80)
        self.vx = self.vy = 0.0
        self.facing     = 1
        self._side      = "right"
        self.idle_dir   = random.choice([-1, 1])
        self.idle_ticks = 0
        self.speech     = f"Hi! I'm {name.capitalize()}!"
        self.speech_t   = 80
        self.tick       = 0
        self.mx = self.SW // 2
        self.my = self.SH // 2

        self._load_images()

        menu = tk.Menu(r, tearoff=0)
        menu.add_command(label="Switch Pokémon", command=self.open_picker)
        menu.add_separator()
        menu.add_command(label="Quit", command=r.destroy)
        self.lbl.bind("<Button-2>",         lambda e: menu.tk_popup(e.x_root, e.y_root))
        self.lbl.bind("<Control-Button-1>", lambda e: menu.tk_popup(e.x_root, e.y_root))
        self.lbl.bind("<Button-1>",         lambda e: self._poke())

        r.wm_geometry(f"{self.WIN_W}x{self.WIN_H}+{int(self.x)}+{int(self.y)}")
        self._poll_cursor()
        self._loop()
        r.mainloop()

    def _load_images(self):
        img_r = composite(self.sprite_img)
        img_l = composite(self.sprite_img.transpose(Image.FLIP_LEFT_RIGHT))
        self.img_r = ImageTk.PhotoImage(img_r)
        self.img_l = ImageTk.PhotoImage(img_l)
        self.lbl.img_r = self.img_r
        self.lbl.img_l = self.img_l

    def _poll_cursor(self):
        try:
            self.mx, self.my = self.root.winfo_pointerxy()
        except Exception:
            pass
        self.root.after(50, self._poll_cursor)

    def _poke(self):
        self.speech   = random.choice(REACTIONS.get(self.name, ["!"]))
        self.speech_t = 60

    def _preferred_zone(self):
        if self.mx < self.SW * 0.4:
            self._side = "right"
        elif self.mx > self.SW * 0.6:
            self._side = "left"
        tx = self.SW - 100 if self._side == "right" else 100
        ty = self.SH - self.sh - 80
        return tx, ty

    def _loop(self):
        self.tick += 1
        cx = self.x + self.sw / 2
        cy = self.y + self.sh / 2
        dx = self.mx - cx
        dy = self.my - cy
        dist = math.sqrt(dx*dx + dy*dy) or 1

        if dist < RUN_DIST:
            self.vx -= (dx/dist) * RUN_SPEED * 10
            self.vy -= (dy/dist) * RUN_SPEED * 10
            self.idle_ticks = 0
        elif DEADZONE < dist < FOLLOW_DIST:
            self.vx += (dx/dist) * FOLLOW_SPEED * 5
            self.vy += (dy/dist) * FOLLOW_SPEED * 5
            self.idle_ticks = 0
        else:
            tx, ty = self._preferred_zone()
            zdx = tx - self.x
            zdy = ty - self.y
            zdist = math.sqrt(zdx*zdx + zdy*zdy) or 1
            self.idle_ticks += 1
            if zdist > 25:
                self.vx += (zdx/zdist) * 0.55
                self.vy += (zdy/zdist) * 0.45
            else:
                if self.idle_ticks > 120:
                    self.idle_ticks = 0
                    self.idle_dir = random.choice([-1, 0, 0, 1])
                if self.idle_ticks < 50 and self.idle_dir:
                    self.vx += self.idle_dir * 0.15
                else:
                    self.vx *= 0.80
                self.vy *= 0.80

        friction = 0.75 if dist > FOLLOW_DIST else 0.84
        self.vx *= friction
        self.vy *= friction
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > 6.0:
            self.vx = (self.vx/speed) * 6.0
            self.vy = (self.vy/speed) * 6.0

        self.x = max(20, min(self.SW - self.sw - 20, self.x + self.vx))
        self.y = max(20, min(self.SH - self.sh - 60, self.y + self.vy))
        if abs(self.vx) > 0.6:
            self.facing = 1 if self.vx > 0 else -1

        if random.random() < SPEECH_CHANCE:
            self.speech   = random.choice(QUIPS.get(self.name, ["!"]))
            self.speech_t = 90

        self._draw()
        self.root.after(16, self._loop)

    def _draw(self):
        img = self.img_r if self.facing >= 0 else self.img_l
        self.lbl.configure(image=img)

        if self.speech_t > 0:
            self.bubble.configure(text=self.speech)
            self.bubble.place(x=10, y=4)
            self.speech_t -= 1
        else:
            self.bubble.place_forget()

        self.root.wm_geometry(
            f"{self.WIN_W}x{self.WIN_H}+{int(self.x)}+{int(self.y)}")

    def open_picker(self):
        picker = tk.Toplevel(self.root)
        picker.title("Switch Pokémon")
        picker.configure(bg="#f5f5f5")
        picker.resizable(False, False)
        picker.lift(); picker.focus_force()
        tk.Label(picker, text="Who's your buddy?",
                 font=("Helvetica", 13, "bold"), bg="#f5f5f5").pack(pady=(16,8))
        f = tk.Frame(picker, bg="#f5f5f5")
        f.pack(padx=20, pady=(0,16))
        def pick(n):
            picker.destroy(); self.switch(n)
        for i, n in enumerate(POKEMON_LIST):
            tk.Button(f, text=n.capitalize(), width=10,
                command=lambda n=n: pick(n),
                relief="groove", bg="white").grid(row=i//4, column=i%4, padx=6, pady=4)

    def switch(self, name):
        self.name       = name
        self.sprite_img = fetch_sprite(name)
        self.sw, self.sh = self.sprite_img.size
        self._load_images()
        self.speech   = f"Hi! I'm {name.capitalize()}!"
        self.speech_t = 100


if __name__ == "__main__":
    name = run_picker()
    if name:
        DeskyMon(name)
