# deskymon 🐾

A tiny pixel-art Pokémon that lives on your desktop, follows your cursor, and reacts when you get too close.

Inspired by the on-screen cat trend — but make it Pokémon.

![deskymon demo](assets/demo.gif)

## Pokémon available

Pikachu · Eevee · Psyduck · Gengar · Snorlax · Bulbasaur · Charmander · Mewtwo

(sprites auto-downloaded from PokéAPI on first run — no manual download needed)

## Requirements

- Python 3.8+
- A Linux desktop with X11 or Wayland (WSL2 with WSLg works)
- Windows native also supported via the `--windows` flag

## Install

```bash
git clone https://github.com/kartikeyy12/deskymon.git
cd deskymon
pip install pillow pynput requests
```

## Run

```bash
python3 main.py
```

Pick your Pokémon from the selector that appears, then minimize it — your buddy will roam your desktop.

**Right-click the buddy** to open the menu (switch Pokémon / quit).

## How it works

- Sprites fetched from [PokéAPI](https://pokeapi.co) and cached locally in `sprites/`
- Transparent always-on-top window tracks your cursor position
- Three states: idle wander → follow → run away when you get too close
- Runs entirely offline after first sprite download

## License

MIT — do whatever you want with it.
