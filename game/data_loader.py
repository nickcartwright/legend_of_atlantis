"""Data loading for Legend of Atlantis - INI files, location maps, battle maps, story scripts."""

import configparser
import os
import pygame
from game.constants import (
    DATA_DIR, ASSET_DIR, TILE_W, TILE_H, COLOR_TRANSPARENT, MAP_MAX,
)


def _ini_path(filename):
    return os.path.join(DATA_DIR, filename)


def _asset_path(filename):
    return os.path.join(ASSET_DIR, filename)


def load_ini(filename):
    """Load an INI file from the Data directory, returning a configparser object."""
    path = _ini_path(filename)
    config = configparser.ConfigParser()
    config.read(path, encoding='utf-8')
    return config


def load_items():
    """Load items.itm -> dict of {item_id: {name, type, fortype, description, value, range, price, magic}}."""
    config = load_ini("items.itm")
    items = {}
    for section in config.sections():
        item_id = int(section)
        items[item_id] = {
            'name': config.get(section, 'NAME', fallback=''),
            'type': config.getint(section, 'TYPE', fallback=0),
            'fortype': config.getint(section, 'FORTYPE', fallback=0),
            'description': config.get(section, 'DESCRIPTION', fallback=''),
            'value': _parse_int_safe(config.get(section, 'VALUE', fallback='0')),
            'range': _parse_int_safe(config.get(section, 'RANGE', fallback='0')),
            'price': config.getint(section, 'PRICE', fallback=0),
            'magic': config.getint(section, 'MAGIC', fallback=0),
        }
    return items


def _parse_int_safe(val):
    """Parse an integer, returning 0 for non-numeric values like '?'."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def load_characters():
    """Load characters.txt -> dict of {char_id: char_data}."""
    config = load_ini("characters.txt")
    chars = {}
    for section in config.sections():
        char_id = int(section)
        chars[char_id] = {
            'name': config.get(section, 'Name', fallback=''),
            'type': config.getint(section, 'Type', fallback=0),
            'item1': config.getint(section, 'Item1', fallback=0),
            'item2': config.getint(section, 'Item2', fallback=0),
            'item3': config.getint(section, 'Item3', fallback=0),
            'item4': config.getint(section, 'Item4', fallback=0),
            'item5': config.getint(section, 'Item5', fallback=0),
            'item6': config.getint(section, 'Item6', fallback=0),
            'equipped_a': config.getint(section, 'EquippedA', fallback=0),
            'equipped_d': config.getint(section, 'EquippedD', fallback=0),
            'hp': config.getint(section, 'HP', fallback=0),
            'attack': config.getint(section, 'Attack', fallback=0),
            'defence': config.getint(section, 'Defence', fallback=0),
            'magic': config.getint(section, 'Magic', fallback=0),
            'resilience': config.getint(section, 'Resillance', fallback=0),
            'graph_x': config.getint(section, 'GraphX', fallback=0),
            'graph_y': config.getint(section, 'GraphY', fallback=0),
            'exp': config.getint(section, 'Exp', fallback=0),
            'move': config.getint(section, 'Move', fallback=0),
        }
    return chars


def load_enemies():
    """Load Enemy.ini -> dict of {enemy_id: enemy_data}."""
    config = load_ini("Enemy.ini")
    enemies = {}
    for section in config.sections():
        enemy_id = int(section)
        enemies[enemy_id] = {
            'name': config.get(section, 'Name', fallback=''),
            'type': config.getint(section, 'Type', fallback=0),
            'equipped_a': config.getint(section, 'EquippedA', fallback=0),
            'equipped_d': config.getint(section, 'EquippedD', fallback=0),
            'hp': config.getint(section, 'HP', fallback=0),
            'attack': config.getint(section, 'Attack', fallback=0),
            'defence': config.getint(section, 'Defence', fallback=0),
            'magic': config.getint(section, 'Magic', fallback=0),
            'resilience': config.getint(section, 'Resillance', fallback=0),
            'graph_x': config.getint(section, 'graphX', fallback=0),
            'graph_y': config.getint(section, 'graphY', fallback=0),
            'move': config.getint(section, 'Move', fallback=0),
        }
    return enemies


def load_music_ini():
    """
    Load music.ini -> dict of {music_id: {name, key, credit}}.
    Also builds a key_lookup: {key_lower: name} for resolving filenames.
    """
    config = load_ini("music.ini")
    music = {}
    key_lookup = {}
    for section in config.sections():
        music_id = int(section)
        name = config.get(section, 'Name', fallback='')
        key = config.get(section, 'Key', fallback=name)
        music[music_id] = {
            'name': name,
            'key': key,
            'credit': config.get(section, 'L1', fallback=''),
        }
        key_lookup[key.lower()] = name
    music['_key_lookup'] = key_lookup
    return music


def load_gaze_ini():
    """Load gaze.ini -> dict of {gaze_id: description_string}."""
    config = load_ini("gaze.ini")
    gaze = {}
    if config.has_section('gaze'):
        for key, val in config.items('gaze'):
            try:
                gaze[int(key)] = val
            except ValueError:
                pass
    return gaze


def load_tileset(filename):
    """Load a BMP tileset from the asset directory, with white as transparent."""
    path = _asset_path(filename)
    if not os.path.exists(path):
        return None
    surface = pygame.image.load(path).convert()
    surface.set_colorkey(COLOR_TRANSPARENT)
    return surface


def load_location(loc_number):
    """
    Load a .loc file and return location data dict.

    .loc format (space-separated integers):
    Line 1 header: battle_flag N O P muse arrX arrY mainX mainY mainDir
    Then arrX * arrY tiles, each = 5 ints: graphX graphY charX charY val
    Then a trailing description string.

    Returns dict with:
        battle_flag, graph_bmp_id, good_bmp_id, char_bmp_id,
        muse, arr_x, arr_y, main_x, main_y, main_dir,
        graph_array_x, graph_array_y, char_array_x, char_array_y, val_array,
        description
    """
    path = os.path.join(DATA_DIR, f"Loc{loc_number}.loc")
    if not os.path.exists(path):
        # Try lowercase
        path = os.path.join(DATA_DIR, f"loc{loc_number}.loc")
    if not os.path.exists(path):
        return None

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Split into tokens and trailing text
    lines = content.split('\n')
    all_text = ' '.join(lines)

    # Parse all integers from the file
    tokens = all_text.split()

    # Parse header
    idx = 0
    battle_flag = int(tokens[idx]); idx += 1
    graph_bmp_id = int(tokens[idx]); idx += 1
    good_bmp_id = int(tokens[idx]); idx += 1
    char_bmp_id = int(tokens[idx]); idx += 1
    muse = int(tokens[idx]); idx += 1
    arr_x = int(tokens[idx]); idx += 1
    arr_y = int(tokens[idx]); idx += 1
    main_x = int(tokens[idx]); idx += 1
    main_y = int(tokens[idx]); idx += 1
    main_dir = int(tokens[idx]); idx += 1

    # Initialize arrays (1-indexed, using [0] unused)
    graph_array_x = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
    graph_array_y = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
    char_array_x = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
    char_array_y = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
    val_array = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]

    # Parse tile data
    for a in range(1, arr_x + 1):
        for b in range(1, arr_y + 1):
            if idx + 4 < len(tokens):
                try:
                    graph_array_x[a][b] = int(tokens[idx]); idx += 1
                    graph_array_y[a][b] = int(tokens[idx]); idx += 1
                    char_array_x[a][b] = int(tokens[idx]); idx += 1
                    char_array_y[a][b] = int(tokens[idx]); idx += 1
                    val_array[a][b] = int(tokens[idx]); idx += 1
                except (ValueError, IndexError):
                    idx += 5
            else:
                break

    # Remaining tokens form the description
    description = ''
    # The description is on the last line of the file after tile data
    # In the original, after reading all tile data, readln then read gets the description
    # We look for text after the numeric data
    remaining_tokens = tokens[idx:]
    # Try to find non-numeric trailing text
    desc_parts = []
    for t in remaining_tokens:
        try:
            int(t)
        except ValueError:
            desc_parts.append(t)
    if desc_parts:
        description = ' '.join(desc_parts)
    else:
        # Check the last line of the file
        for line in reversed(lines):
            stripped = line.strip()
            if stripped and not stripped.replace(' ', '').replace('-', '').lstrip('-').isdigit():
                # Has non-numeric content
                try:
                    # Try to parse as all ints
                    [int(x) for x in stripped.split()]
                except ValueError:
                    description = stripped
                    break

    return {
        'battle_flag': battle_flag,
        'graph_bmp_id': graph_bmp_id,
        'good_bmp_id': good_bmp_id,
        'char_bmp_id': char_bmp_id,
        'muse': muse,
        'arr_x': arr_x,
        'arr_y': arr_y,
        'main_x': main_x,
        'main_y': main_y,
        'main_dir': main_dir,
        'graph_array_x': graph_array_x,
        'graph_array_y': graph_array_y,
        'char_array_x': char_array_x,
        'char_array_y': char_array_y,
        'val_array': val_array,
        'description': description,
    }


def load_battle(loc_number, party_size):
    """
    Load a Battle*.loc file using line-based reading matching the original Delphi.

    Format (original Delphi reads):
    Line 1: read pairs of (x, y) for each party member, then readln
    Line 2+: read enemy_count, then for each enemy read (batX batY refID tactics)
    Last value: win story number

    Returns dict with:
        player_positions: [(x, y), ...]
        enemy_count: int
        enemies: [{bat_x, bat_y, ref_id, tactics}, ...]
        win_story: int
    """
    path = os.path.join(DATA_DIR, f"Battle{loc_number}.loc")
    if not os.path.exists(path):
        return None

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Line 1: player starting positions (read party_size pairs, then skip rest of line)
    line1_tokens = [int(t) for t in lines[0].split() if t.strip()]
    player_positions = []
    for i in range(party_size):
        if i * 2 + 1 < len(line1_tokens):
            player_positions.append((line1_tokens[i * 2], line1_tokens[i * 2 + 1]))

    # Remaining lines: flatten into tokens
    remaining_tokens = []
    for line in lines[1:]:
        remaining_tokens.extend(int(t) for t in line.split() if t.strip())

    idx = 0

    # Read enemy count
    enemy_count = remaining_tokens[idx]; idx += 1

    # Read enemy data
    enemies = []
    for _ in range(enemy_count):
        bat_x = remaining_tokens[idx]; idx += 1
        bat_y = remaining_tokens[idx]; idx += 1
        ref_id = remaining_tokens[idx]; idx += 1
        tactics = remaining_tokens[idx]; idx += 1
        enemies.append({
            'bat_x': bat_x,
            'bat_y': bat_y,
            'ref_id': ref_id,
            'tactics': tactics,
        })

    # Read win story number
    win_story = remaining_tokens[idx] if idx < len(remaining_tokens) else 0

    return {
        'player_positions': player_positions,
        'enemy_count': enemy_count,
        'enemies': enemies,
        'win_story': win_story,
    }


def open_story_file(story_number):
    """
    Open a story .txt file and return a token reader.

    Story files can be negative numbers (e.g., -10.txt).
    Returns a StoryReader object or None if file doesn't exist.
    """
    path = os.path.join(DATA_DIR, f"{story_number}.txt")
    if not os.path.exists(path):
        return None
    return StoryReader(path)


class StoryReader:
    """
    Reads story script files token by token, matching the original Delphi
    read() / readln() behavior on text files.

    In Delphi:
    - read(f, intvar) reads the next integer (skipping whitespace)
    - readln(f) advances to the next line
    - read(f, strvar) reads the rest of the current line
    """

    def __init__(self, path):
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            self.lines = f.readlines()
        self.line_idx = 0
        self.col_idx = 0

    def read_int(self):
        """Read the next integer from the stream (skips whitespace, can cross lines)."""
        while self.line_idx < len(self.lines):
            line = self.lines[self.line_idx]
            # Skip whitespace from current position
            while self.col_idx < len(line) and line[self.col_idx] in ' \t\r\n':
                if line[self.col_idx] == '\n':
                    # Don't cross newline boundary for read() - in Delphi read() on
                    # text files DOES cross line boundaries for numeric reads
                    self.line_idx += 1
                    self.col_idx = 0
                    if self.line_idx >= len(self.lines):
                        return 0
                    line = self.lines[self.line_idx]
                    continue
                self.col_idx += 1

            # Try to read an integer
            start = self.col_idx
            if self.col_idx < len(line) and (line[self.col_idx] == '-' or line[self.col_idx].isdigit()):
                self.col_idx += 1
                while self.col_idx < len(line) and line[self.col_idx].isdigit():
                    self.col_idx += 1
                try:
                    return int(line[start:self.col_idx])
                except ValueError:
                    return 0
            else:
                # No number found on this line, move to next
                self.line_idx += 1
                self.col_idx = 0
        return 0

    def readln(self):
        """Advance to the start of the next line."""
        self.line_idx += 1
        self.col_idx = 0

    def read_string(self):
        """Read the rest of the current line as a string (like Delphi read(f, strvar))."""
        if self.line_idx >= len(self.lines):
            return ''
        line = self.lines[self.line_idx]
        result = line[self.col_idx:].rstrip('\r\n')
        self.col_idx = len(line)
        return result

    def close(self):
        """No-op for compatibility."""
        pass

    @property
    def eof(self):
        return self.line_idx >= len(self.lines)
