"""World/location management for Legend of Atlantis."""

from game.constants import MAP_MAX, VAL_BLOCKED, VAL_WALKABLE, VAL_STAIRS


class World:
    """Manages current location state - tile arrays, position, and dimensions."""

    def __init__(self):
        self.main_x = 0
        self.main_y = 0
        self.main_dir = 1  # 1=S, 2=N, 3=E, 4=W
        self.arr_x = 0
        self.arr_y = 0
        self.loc = 0  # Current location number

        # Tile arrays (1-indexed)
        self.graph_array_x = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
        self.graph_array_y = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
        self.char_array_x = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
        self.char_array_y = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]
        self.val_array = [[0] * (MAP_MAX + 1) for _ in range(MAP_MAX + 1)]

        # BMP IDs for current location
        self.graph_bmp_id = 0
        self.good_bmp_id = 0
        self.char_bmp_id = 0
        self.muse = 0  # Music ID

        # Battle flag
        self.battle = False
        self.loc_type = 0  # 0=normal, 1=battle

        # Location description
        self.description = ''

    def load_from_data(self, loc_data):
        """Load world state from a location data dict (from data_loader.load_location)."""
        self.loc_type = loc_data['battle_flag']
        self.battle = loc_data['battle_flag'] == 1
        self.graph_bmp_id = loc_data['graph_bmp_id']
        self.good_bmp_id = loc_data['good_bmp_id']
        self.char_bmp_id = loc_data['char_bmp_id']
        self.muse = loc_data['muse']
        self.arr_x = loc_data['arr_x']
        self.arr_y = loc_data['arr_y']
        self.main_x = loc_data['main_x']
        self.main_y = loc_data['main_y']
        self.main_dir = loc_data['main_dir']
        self.description = loc_data.get('description', '')

        # Copy arrays
        self.graph_array_x = loc_data['graph_array_x']
        self.graph_array_y = loc_data['graph_array_y']
        self.char_array_x = loc_data['char_array_x']
        self.char_array_y = loc_data['char_array_y']
        self.val_array = loc_data['val_array']

    def get_val(self, x, y):
        """Get the value at map position (x, y). Returns 0 (blocked) if out of bounds."""
        if 1 <= x <= self.arr_x and 1 <= y <= self.arr_y:
            return self.val_array[x][y]
        return VAL_BLOCKED

    def get_char(self, x, y):
        """Get character array X value at position. 0 = no character."""
        if 1 <= x <= self.arr_x and 1 <= y <= self.arr_y:
            return self.char_array_x[x][y]
        return 0

    def can_walk(self, x, y):
        """Check if position (x, y) is walkable."""
        return self.get_val(x, y) == VAL_WALKABLE

    def try_move(self, dx, dy, direction):
        """
        Try to move the player in a direction.
        Returns a result dict with what happened:
            'moved': True if player moved
            'location_change': loc number if transitioning (>1)
            'story_trigger': story number if story triggered (<=-10)
            'stairs': True if hit stairs (-9)
        """
        self.main_dir = direction
        new_x = self.main_x + dx
        new_y = self.main_y + dy

        val = self.get_val(new_x, new_y)

        result = {
            'moved': False,
            'location_change': 0,
            'story_trigger': 0,
            'stairs': False,
        }

        if val == VAL_WALKABLE:
            self.main_x = new_x
            self.main_y = new_y
            result['moved'] = True
        elif val == VAL_STAIRS:
            # Stairs: jump 2 tiles in Y direction
            if dy != 0:
                self.main_y += dy * 2
            else:
                self.main_y -= 2
            result['stairs'] = True
            result['moved'] = True
        elif val <= -10:
            result['story_trigger'] = val
        elif val > 1:
            result['location_change'] = val
        # val == 0: blocked, do nothing

        return result
