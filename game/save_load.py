"""Save and load game state for Legend of Atlantis."""

import os
from game.constants import GLOBAL_MAX, MAX_ITEMS_PER_CHAR, ASSET_DIR


SAVE_DIR = os.path.join(ASSET_DIR, "Save")


def ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def save_game(filename, world, party, global_flags, music_filename, battle):
    """
    Save the game state to .sav and .loc files.

    Format matches original Delphi save format:
    .sav: loc battle mainX mainY money / music / number / character data / global array
    .loc: arrX arrY / tile data
    """
    ensure_save_dir()
    sav_path = os.path.join(SAVE_DIR, f"{filename}.sav")
    loc_path = os.path.join(SAVE_DIR, f"{filename}.loc")

    # Write .sav file
    with open(sav_path, 'w') as f:
        # Line 1: loc battle mainX mainY money
        battle_val = 5 if battle else 0
        f.write(f"{world.loc} {battle_val} {world.main_x} {world.main_y} {party.money}\n")

        # Line 2: music filename
        f.write(f"{music_filename}\n")

        # Line 3: number of party members
        f.write(f"{party.number}\n")

        # Character data
        for i in range(party.number):
            char = party.members[i]
            f.write(f"{char.name}\n")
            line = f"{char.type} "
            for slot in range(1, MAX_ITEMS_PER_CHAR + 1):
                line += f"{char.items[slot]} "
            line += f"{char.equipped_a} {char.equipped_d} "
            line += f"{char.attack} {char.defence} {char.hp} {char.magic} "
            line += f"{char.resilience} {char.graph_x} {char.graph_y} "
            line += f"{char.exp} {char.move}"
            f.write(line + "\n")

        # Global flags array
        for c in range(GLOBAL_MAX):
            line = ' '.join(str(global_flags[c][d]) for d in range(GLOBAL_MAX))
            f.write(line + "\n")

    # Write .loc file
    with open(loc_path, 'w') as f:
        f.write(f"{world.arr_x} {world.arr_y}\n")
        for a in range(1, world.arr_x + 1):
            parts = []
            for b in range(1, world.arr_y + 1):
                parts.append(f"{world.graph_array_x[a][b]} {world.graph_array_y[a][b]} "
                           f"{world.char_array_x[a][b]} {world.char_array_y[a][b]} "
                           f"{world.val_array[a][b]}")
            f.write(' '.join(parts) + "\n")


def load_game(filename):
    """
    Load a saved game. Returns dict with all game state, or None if file not found.
    """
    sav_path = os.path.join(SAVE_DIR, f"{filename}.sav")
    loc_path = os.path.join(SAVE_DIR, f"{filename}.loc")

    if not os.path.exists(sav_path) or not os.path.exists(loc_path):
        return None

    result = {}

    # Read .sav file
    with open(sav_path, 'r') as f:
        # Line 1: loc battle mainX mainY money
        parts = f.readline().split()
        result['loc'] = int(parts[0])
        result['battle'] = int(parts[1]) == 5
        result['main_x'] = int(parts[2])
        result['main_y'] = int(parts[3])
        result['money'] = int(parts[4])

        # Line 2: music filename
        result['music'] = f.readline().strip()

        # Line 3: party size
        result['number'] = int(f.readline().strip())

        # Character data
        result['characters'] = []
        for _ in range(result['number']):
            char_data = {}
            char_data['name'] = f.readline().strip()
            parts = f.readline().split()
            idx = 0
            char_data['type'] = int(parts[idx]); idx += 1
            char_data['items'] = [0]  # 0-index placeholder
            for _ in range(MAX_ITEMS_PER_CHAR):
                char_data['items'].append(int(parts[idx])); idx += 1
            char_data['equipped_a'] = int(parts[idx]); idx += 1
            char_data['equipped_d'] = int(parts[idx]); idx += 1
            char_data['attack'] = int(parts[idx]); idx += 1
            char_data['defence'] = int(parts[idx]); idx += 1
            char_data['hp'] = int(parts[idx]); idx += 1
            char_data['magic'] = int(parts[idx]); idx += 1
            char_data['resilience'] = int(parts[idx]); idx += 1
            char_data['graph_x'] = int(parts[idx]); idx += 1
            char_data['graph_y'] = int(parts[idx]); idx += 1
            char_data['exp'] = int(parts[idx]); idx += 1
            char_data['move'] = int(parts[idx]); idx += 1
            result['characters'].append(char_data)

        # Global flags
        result['global_flags'] = [[0] * GLOBAL_MAX for _ in range(GLOBAL_MAX)]
        for c in range(GLOBAL_MAX):
            line = f.readline()
            if line:
                parts = line.split()
                for d in range(min(GLOBAL_MAX, len(parts))):
                    try:
                        result['global_flags'][c][d] = int(parts[d])
                    except (ValueError, IndexError):
                        pass

    # Read .loc file
    with open(loc_path, 'r') as f:
        parts = f.readline().split()
        result['arr_x'] = int(parts[0])
        result['arr_y'] = int(parts[1])

        from game.constants import MAP_MAX
        result['graph_array_x'] = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
        result['graph_array_y'] = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
        result['char_array_x'] = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
        result['char_array_y'] = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
        result['val_array'] = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]

        for a in range(1, result['arr_x'] + 1):
            line = f.readline()
            if not line:
                break
            tokens = line.split()
            idx = 0
            for b in range(1, result['arr_y'] + 1):
                if idx + 4 < len(tokens):
                    try:
                        result['graph_array_x'][a][b] = int(tokens[idx]); idx += 1
                        result['graph_array_y'][a][b] = int(tokens[idx]); idx += 1
                        result['char_array_x'][a][b] = int(tokens[idx]); idx += 1
                        result['char_array_y'][a][b] = int(tokens[idx]); idx += 1
                        result['val_array'][a][b] = int(tokens[idx]); idx += 1
                    except (ValueError, IndexError):
                        idx += 5

    return result


def list_saves():
    """List available save files."""
    ensure_save_dir()
    saves = []
    for f in os.listdir(SAVE_DIR):
        if f.endswith('.sav'):
            saves.append(f[:-4])
    return sorted(saves)
