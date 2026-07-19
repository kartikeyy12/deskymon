# deskymon 🐾
 
A tiny pixel-art Pokémon that lives on your desktop — follows your cursor, runs away when you get too close, and quietly hangs out in the corner while you work.
 
Sprites are auto-downloaded from PokéAPI on first run. No manual setup needed.
 
---

## Download

**Windows** → [deskymon.exe](https://github.com/kartikeyy12/deskymon/releases/latest/download/deskymon.exe) — no Python needed, just double-click.

**Mac** → see installation instructions below.

---

## Pokémon available
 
Pikachu · Eevee · Psyduck · Gengar · Snorlax · Bulbasaur · Charmander · Mewtwo
 
You can add any Pokémon by editing `config.py` — over 1000 supported.
 
---
 
## Installation
 
### Windows
 
**1. Install Python**
Download from [python.org/downloads](https://python.org/downloads) — check **"Add Python to PATH"** during install.
 
**2. Install dependencies**
 
Open Command Prompt and run:
```
pip install pillow requests pywin32
```
 
**3. Download deskymon**
 
Click the green **Code** button → **Download ZIP** → extract anywhere.
 
**4. Run it**
 
Double-click `START_WINDOWS.bat` inside the folder.
 
---
 
### macOS
 
**1. Install Python**
```bash
brew install python
```
Or download from [python.org/downloads](https://python.org/downloads).
 
**2. Install dependencies**
```bash
pip3 install pillow requests
```
 
**3. Clone or download**
```bash
git clone https://github.com/kartikeyy12/deskymon.git
cd deskymon
```
 
**4. Run it**
```bash
python3 deskymon_mac.py
```
 
---
 
### Linux
 
**1. Install dependencies**
```bash
sudo apt install python3-tk python3-pip
pip3 install pillow requests
```
 
**2. Clone**
```bash
git clone https://github.com/kartikeyy12/deskymon.git
cd deskymon
```
 
**3. Run**
```bash
python3 deskymon_linux.py
```
 
---
 
## Usage
 
| Action | Result |
|---|---|
| Move cursor near it | Pokémon follows you |
| Get too close | It runs away |
| Left-click | It reacts |
| Right-click | Switch Pokémon / Quit |
 
The buddy parks itself in the bottom corner opposite your cursor — out of the way while you work.
 
---
 
## Add any Pokémon
 
Open `config.py` and add any name from [pokeapi.co](https://pokeapi.co):
 
```python
POKEMON_LIST = [
    "pikachu",
    "eevee",
    "umbreon",
    "lucario",
    "squirtle",
    # any pokémon name works
]
```
 
Sprites download automatically on first pick.
 
---
 
## Tweak the behavior
 
All settings are in `config.py`:
 
```python
SPRITE_SCALE  = 2      # size: 2 = small, 3 = large
FOLLOW_SPEED  = 0.06   # how fast it chases you
RUN_SPEED     = 0.14   # how fast it flees
FOLLOW_DIST   = 160    # how close before it starts following (pixels)
RUN_DIST      = 50     # how close before it panics
SPEECH_CHANCE = 0.003  # how often it says something
```
 
---
 
## How it works
 
- Sprites fetched from [PokéAPI](https://pokeapi.co) and cached locally in `sprites/`
- Transparent always-on-top window via platform-native APIs
- Three behavior states: **idle** → **follow** → **run away**
- Smart corner placement — drifts to whichever side your cursor isn't on
---
 
## License
 
MIT — do whatever you want with it.
 
---
 
*Built by [@kartikeyy12](https://github.com/kartikeyy12)*
