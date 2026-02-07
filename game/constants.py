"""Constants for Legend of Atlantis."""

import os
from enum import Enum, auto

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "original_code", "Data")
ASSET_DIR = os.path.join(PROJECT_ROOT, "original_code")

# Tile dimensions (source BMP)
TILE_W = 28
TILE_H = 36

# Scale factor
SCALE = 2

# Display tile dimensions
DISPLAY_TILE_W = TILE_W * SCALE  # 56
DISPLAY_TILE_H = TILE_H * SCALE  # 72

# Viewport size (in tiles)
VIEWPORT_TILES = 5

# Game viewport dimensions
VIEWPORT_W = DISPLAY_TILE_W * VIEWPORT_TILES  # 280
VIEWPORT_H = DISPLAY_TILE_H * VIEWPORT_TILES  # 360

# Right panel width
PANEL_W = 260

# Window dimensions
WINDOW_W = VIEWPORT_W + PANEL_W  # 540
WINDOW_H = VIEWPORT_H  # 360

# Character sprite Y offset when drawing (pixels, in display coords)
SPRITE_Y_OFFSET = 15

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_SILVER = (192, 192, 192)
COLOR_TRANSPARENT = COLOR_WHITE  # White is used as transparency key in BMPs

# UI colors
COLOR_PANEL_BG = (60, 60, 80)
COLOR_PANEL_BORDER = (100, 100, 130)
COLOR_TEXT = (220, 220, 220)
COLOR_TEXT_HIGHLIGHT = (255, 255, 100)
COLOR_BUTTON_BG = (80, 80, 110)
COLOR_BUTTON_HOVER = (100, 100, 140)
COLOR_HP_BAR_BG = COLOR_RED
COLOR_HP_BAR_FG = COLOR_GREEN

# Directions (matching original Delphi: 1=S, 2=N, 3=E, 4=W)
DIR_SOUTH = 1
DIR_NORTH = 2
DIR_EAST = 3
DIR_WEST = 4

# Valarray special values
VAL_BLOCKED = 0
VAL_WALKABLE = 1
VAL_STAIRS = -9
# > 1 means location transition to that location number
# <= -10 means story trigger (story file number)

# Character type names (index matches type ID)
TYPE_NAMES = [
    'ALL',   # 0
    'HERO',  # 1
    'WARR',  # 2
    'VICR',  # 3
    'WIZD',  # 4
    'DRGN',  # 5
    'DWRF',  # 6
    'OGRE',  # 7
    'BRDM',  # 8
    'NINJ',  # 9
    'ANGL',  # 10
    'ELDR',  # 11
    'DETH',  # 12
    'ROBT',  # 13
    '????',  # 14
]

# Item types
ITEM_TYPE_NONE = 0
ITEM_TYPE_WEAPON = 1
ITEM_TYPE_ARMOR = 2
ITEM_TYPE_HEAL_SPELL = 3
ITEM_TYPE_ATTACK_SPELL = 4
ITEM_TYPE_CONSUMABLE = 5
ITEM_TYPE_BATTLE_ITEM = 6
ITEM_TYPE_KEY = -11

# Max party / enemy size
MAX_PARTY = 15
MAX_ENEMIES = 15
MAX_ITEMS_PER_CHAR = 6

# Map array dimensions
MAP_MAX = 100

# Global flags array dimensions
GLOBAL_MAX = 101  # 0..100

# Text display
TEXT_CHAR_WIDTH = 8
TEXT_LINE_HEIGHT = 14
TEXT_BOX_MAX_CHARS = 34

# Game states
class GameState(Enum):
    TITLE = auto()
    CREATE_PARTY = auto()
    PLAYING = auto()
    BATTLE = auto()
    STORY = auto()
    MENU = auto()
    INVENTORY = auto()
    SHOP = auto()
    SAVE = auto()
    LOAD = auto()
    GAME_OVER = auto()

# Random name syllables (from original)
NAME_SYLLABLE_1 = [
    'Th', 'Ro', 'Bh', 'Fe', 'Ni', 'Ko', 'Lo', 'Po', 'Go',
    'Re', 'Le', 'De', 'Da', 'Ca', 'Ce', 'Mo', 'Vo',
]
NAME_SYLLABLE_2 = [
    'eo', 'be', 'he', 'lh', 'sd', 'ro', 'bl', 'gf', 'po',
    'iu', 'gh', 'oo', 'aa', 'na', 'fa', 'bu', 'jo', '',
]
NAME_SYLLABLE_3 = [
    'rn', 'gn', 'hn', 'lm', 'sm', 'tm', 'ia', 'ga', 'ra',
    'lt', 'on', 'ce', 'te', 'wl', 'oo', 'oa', 'pa', 'x', 'n', 'x', '',
]

# Starting location
START_LOCATION = 2
START_MONEY = 35

# Default text speed
DEFAULT_SPEED = 3

# FPS target
FPS = 30
