import tkinter as tk
from PIL import Image, ImageTk
import requests, os, math, random
import config

SPRITE_DIR = os.path.join(os.path.dirname(__file__), "sprites")
os.makedirs(SPRITE_DIR, exist_ok=True)


def fetch_sprite(name):
    path = os.path.join(SPRITE_DIR, f"{name}.png")
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}", timeout=10).json()
        img_data = requests.get(data["sprites"]["front_default"], timeout=10).content
        open(path, "wb").write(img_data)
        print(f"Saved {name}.png")
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    return img.resize((w * config.SPRITE_SCALE, h * config.SPRITE_SCALE), Image.NEAREST)


class DeskyMon:
    def __init__(self, root, name):
        self.root = root
        self.name = name

        self.screen_w = root.winfo_screenwidth()
        self.screen_h = root.winfo_screenheight()

        # Simple visible window — no transparency tricks
        root.title("")
        root.wm_attributes("-topmost", True)
        root.configure(bg="#2b2b2b")
        root.resizable(False, False)

        self.sprite = fetch_sprite(name)
        self.sw, self.sh = self.sprite.size

        self.canvas = tk.Canvas(root,
            width=self.sw, height=self.sh + 40,
            bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack()

        # Position: start center screen
        self.x = float(self.screen_w // 2 - self.sw // 2)
        self.y = float(self.screen_h // 2 - self.sh // 2)
        self.vx = self.vy = 0.0
        self.facing = 1
        self.tick = 0
        self.idle_dir = random.choice([-1, 1])
        self.idle_ticks = 0
        self.speech = ""
        self.speech_t = 0

        # Cursor polling via tkinter — no pynput
        self.mx = self.screen_w // 2
        self.my = self.screen_h // 2
        self._poll_cursor()

        self.img_r = ImageTk.PhotoImage(self.sprite)
        self.img_l = ImageTk.PhotoImage(
            self.sprite.transpose(Image.FLIP_LEFT_RIGHT))

        # Right-click menu
        menu = tk.Menu(root, tearoff=0)
        menu.add_command(label="Switch Pokémon", command=self.open_picker)
        menu.add_separator()
        menu.add_command(label="Quit", command=root.destroy)
        self.canvas.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
        self.canvas.bind("<Button-1>", lambda e: self._poke())

        root.geometry(f"{self.sw}x{self.sh+40}+{int(self.x)}+{int(self.y)}")
        self._loop()

    def _poll_cursor(self):
        try:
            self.mx, self.my = self.root.winfo_pointerxy()
        except Exception:
            pass
        self.root.after(50, self._poll_cursor)

    def _poke(self):
        self.speech = random.choice(["!", "Ow!", "Hey~", "*surprised*", "Eep!"])
        self.speech_t = 60

    def _update(self):
        # Window center position for distance calc
        wx = self.x + self.sw // 2
        wy = self.y + self.sh // 2
        dx = self.mx - wx
        dy = self.my - wy
        dist = math.sqrt(dx*dx + dy*dy) or 1

        if dist < config.RUN_DISTANCE:
            self.vx -= (dx/dist) * config.RUN_SPEED * 10
            self.vy -= (dy/dist) * config.RUN_SPEED * 10
        elif dist < config.FOLLOW_DISTANCE:
            self.vx += (dx/dist) * config.FOLLOW_SPEED * 8
            self.vy += (dy/dist) * config.FOLLOW_SPEED * 8
        else:
            self.idle_ticks += 1
            if self.idle_ticks > 80:
                self.idle_ticks = 0
                self.idle_dir = random.choice([-1, 1, 1, 0])
            if self.idle_ticks < 50 and self.idle_dir:
                self.vx += self.idle_dir * 0.4
            else:
                self.vx *= 0.85
            self.vy *= 0.85

        self.vx *= 0.80
        self.vy *= 0.80
        self.x = max(0, min(self.screen_w - self.sw, self.x + self.vx))
        self.y = max(0, min(self.screen_h - self.sh - 60, self.y + self.vy))

        if abs(self.vx) > 0.5:
            self.facing = 1 if self.vx > 0 else -1

        if random.random() < config.SPEECH_CHANCE:
            quips = {
                "pikachu":    ["Pika!", "Pikachu!", "Pika pika~", "*zap*"],
                "eevee":      ["Eevee!", "Vee~", "*curious stare*"],
                "psyduck":    ["Psy...", "Ow my head", "Psy-yi-yi!"],
                "gengar":     ["Gengar!", "*cackle*", "Heh heh"],
                "snorlax":    ["Zzzz...", "*snore*"],
                "bulbasaur":  ["Bulba!", "Saur~"],
                "charmander": ["Char!", "*tail flicker*"],
                "mewtwo":     ["...", "*stare*"],
            }
            self.speech = random.choice(quips.get(self.name, ["!"]))
            self.speech_t = 90

    def _draw(self):
        self.canvas.delete("all")

        # Speech bubble
        if self.speech_t > 0:
            tw = len(self.speech) * 7 + 16
            bx = self.sw // 2 - tw // 2
            self.canvas.create_rectangle(bx, 2, bx+tw, 22,
                fill="white", outline="#aaaaaa", width=1)
            self.canvas.create_text(bx + tw//2, 12,
                text=self.speech, font=("Helvetica", 9), fill="#222222")
            self.speech_t -= 1

        # Sprite
        img = self.img_r if self.facing >= 0 else self.img_l
        self.canvas.create_image(0, 24, anchor="nw", image=img)

        # Move window
        self.root.geometry(
            f"{self.sw}x{self.sh+40}+{int(self.x)}+{int(self.y)}")

    def _loop(self):
        self.tick += 1
        self._update()
        self._draw()
        self.root.after(16, self._loop)

    def open_picker(self):
        picker = tk.Toplevel(self.root)
        picker.title("Switch Pokémon")
        picker.configure(bg="#f5f5f5")
        picker.resizable(False, False)
        picker.lift()
        picker.focus_force()
        tk.Label(picker, text="Who's your buddy?",
                 font=("Helvetica", 13, "bold"), bg="#f5f5f5").pack(pady=(16,8))
        f = tk.Frame(picker, bg="#f5f5f5")
        f.pack(padx=20, pady=(0,16))
        def pick(n):
            picker.destroy()
            self.switch(n)
        for i, n in enumerate(config.POKEMON_LIST):
            tk.Button(f, text=n.capitalize(), width=10,
                command=lambda n=n: pick(n),
                relief="groove", bg="white").grid(
                row=i//4, column=i%4, padx=6, pady=4)

    def switch(self, name):
        self.name = name
        self.sprite = fetch_sprite(name)
        self.sw, self.sh = self.sprite.size
        self.img_r = ImageTk.PhotoImage(self.sprite)
        self.img_l = ImageTk.PhotoImage(
            self.sprite.transpose(Image.FLIP_LEFT_RIGHT))
        self.speech = f"Hi! I'm {name.capitalize()}!"
        self.speech_t = 100


def main():
    root = tk.Tk()
    root.withdraw()

    picker = tk.Toplevel(root)
    picker.title("deskymon — pick your buddy")
    picker.configure(bg="#f5f5f5")
    picker.resizable(False, False)
    picker.lift()
    picker.focus_force()
    picker.attributes("-topmost", True)
    picker.protocol("WM_DELETE_WINDOW", root.destroy)

    tk.Label(picker, text="deskymon",
             font=("Helvetica", 16, "bold"), bg="#f5f5f5").pack(pady=(20,4))
    tk.Label(picker, text="Pick your desktop buddy",
             font=("Helvetica", 10), fg="#666666", bg="#f5f5f5").pack(pady=(0,14))

    chosen = tk.StringVar()
    f = tk.Frame(picker, bg="#f5f5f5")
    f.pack(padx=24, pady=(0,20))

    def pick(n):
        chosen.set(n)
        picker.destroy()

    for i, n in enumerate(config.POKEMON_LIST):
        tk.Button(f, text=n.capitalize(), width=11,
            command=lambda n=n: pick(n),
            relief="groove", bg="white", activebackground="#e8f4ff",
            font=("Helvetica", 10)).grid(row=i//4, column=i%4, padx=6, pady=5)

    root.wait_window(picker)

    if not chosen.get():
        root.destroy()
        return

    print(f"Starting {chosen.get()}...")
    root.deiconify()
    DeskyMon(root, chosen.get())
    root.mainloop()


if __name__ == "__main__":
    main()
