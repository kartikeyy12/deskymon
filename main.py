import os, sys, math, random
import requests
import pygame
import config

BASE  = os.path.dirname(os.path.abspath(__file__))
SPDIR = os.path.join(BASE, "sprites")
os.makedirs(SPDIR, exist_ok=True)

CHROMAKEY = (1, 1, 1)   # near-black used as transparent colour

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


def fetch_sprite(name):
    path = os.path.join(SPDIR, f"{name}.png")
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        data = requests.get(
            f"https://pokeapi.co/api/v2/pokemon/{name}", timeout=10).json()
        raw = requests.get(
            data["sprites"]["front_default"], timeout=10).content
        open(path, "wb").write(raw)
        print(f"  saved {name}.png")
    return path


def load_surface(name):
    path = fetch_sprite(name)
    img  = pygame.image.load(path).convert_alpha()
    w, h = img.get_size()
    return pygame.transform.scale(
        img, (w * config.SPRITE_SCALE, h * config.SPRITE_SCALE))


def run_picker():
    import tkinter as tk
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
        chosen.set(n)
        root.destroy()

    for i, n in enumerate(config.POKEMON_LIST):
        tk.Button(f, text=n.capitalize(), width=11,
                  command=lambda n=n: pick(n),
                  relief="groove", bg="white",
                  activebackground="#e8f4ff",
                  font=("Helvetica", 10)).grid(
            row=i // 4, column=i % 4, padx=6, pady=5)

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
    return chosen.get()


def main():
    name = run_picker()
    if not name:
        sys.exit(0)

    print(f"Starting {name}...")

    os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"
    os.environ["PYGAME_DETECT_AVX2"] = "1"

    pygame.init()
    info = pygame.display.Info()
    SW, SH = info.current_w, info.current_h

    screen = pygame.display.set_mode((SW, SH), pygame.NOFRAME)
    pygame.display.set_caption("deskymon")

    # overlay has per-pixel alpha — we blit it onto the chroma-keyed screen
    overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)

    sprite_r = load_surface(name)
    sprite_l = pygame.transform.flip(sprite_r, True, False)
    sw, sh   = sprite_r.get_size()

    font = pygame.font.SysFont("helvetica", 14)

    x  = float(SW // 2 - sw // 2)
    y  = float(SH // 2 - sh // 2)
    vx = vy = 0.0
    facing     = 1
    idle_dir   = random.choice([-1, 1])
    idle_ticks = 0
    speech     = f"Hi! I'm {name.capitalize()}!"
    speech_t   = 80
    tick       = 0
    clock      = pygame.time.Clock()

    running = True
    while running:
        clock.tick(60)
        tick += 1

        mx, my = pygame.mouse.get_pos()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                sx, sy = int(x), int(y)
                if ev.button == 1 and sx < mx < sx+sw and sy < my < sy+sh:
                    speech   = random.choice(["Ow!", "Hey~", "Eep!", "!"])
                    speech_t = 60
                if ev.button == 3:
                    running = False

        # physics
        cx = x + sw / 2
        cy = y + sh / 2
        dx = mx - cx
        dy = my - cy
        dist = math.sqrt(dx*dx + dy*dy) or 1

        if dist < config.RUN_DISTANCE:
            vx -= (dx/dist) * config.RUN_SPEED * 10
            vy -= (dy/dist) * config.RUN_SPEED * 10
        elif dist < config.FOLLOW_DISTANCE:
            vx += (dx/dist) * config.FOLLOW_SPEED * 8
            vy += (dy/dist) * config.FOLLOW_SPEED * 8
        else:
            idle_ticks += 1
            if idle_ticks > 80:
                idle_ticks = 0
                idle_dir = random.choice([-1, 1, 1, 0])
            if idle_ticks < 50 and idle_dir:
                vx += idle_dir * 0.4
            else:
                vx *= 0.85
            vy *= 0.85

        vx *= 0.80
        vy *= 0.80
        x = max(0, min(SW - sw, x + vx))
        y = max(0, min(SH - sh - 40, y + vy))
        if abs(vx) > 0.5:
            facing = 1 if vx > 0 else -1

        if random.random() < config.SPEECH_CHANCE:
            speech   = random.choice(QUIPS.get(name, ["!"]))
            speech_t = 90

        # draw — chroma key background + alpha overlay
        screen.fill(CHROMAKEY)
        overlay.fill((0, 0, 0, 0))

        spr = sprite_r if facing >= 0 else sprite_l
        overlay.blit(spr, (int(x), int(y)))

        if speech_t > 0:
            txt    = font.render(speech, True, (30, 30, 30))
            tw, th = txt.get_size()
            pad    = 6
            bx     = int(x + sw/2 - tw/2 - pad)
            by     = int(y - th - pad*2 - 4)
            bubble = pygame.Surface((tw+pad*2, th+pad*2), pygame.SRCALPHA)
            bubble.fill((255, 255, 255, 220))
            overlay.blit(bubble, (bx, by))
            overlay.blit(txt, (bx+pad, by+pad))
            speech_t -= 1

        screen.blit(overlay, (0, 0))
        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()
