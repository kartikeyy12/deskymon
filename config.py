# deskymon config — tweak these to change behavior

POKEMON_LIST = [
    "pikachu",
    "eevee",
    "psyduck",
    "gengar",
    "snorlax",
    "bulbasaur",
    "charmander",
    "mewtwo",
]

# Sprite display size (pixels) — keep it a multiple of the source (32 or 64)
SPRITE_SCALE = 3        # 3x = ~96px on screen

# Speed settings
FOLLOW_SPEED = 0.10     # how fast it chases your cursor (0.0–1.0)
WANDER_SPEED = 1.2      # pixels per frame when idle-wandering
RUN_SPEED    = 0.18     # how fast it flees when you're too close

# Distance thresholds (pixels from cursor)
FOLLOW_DISTANCE = 220   # enter follow mode inside this radius
RUN_DISTANCE    = 70    # panic and run inside this radius

# Animation
FPS          = 12       # frame rate of the walk cycle
IDLE_FRAMES  = 2        # frames before switching idle direction

# Speech bubble chance per idle tick (0.0–1.0)
SPEECH_CHANCE = 0.003
