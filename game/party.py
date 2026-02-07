"""Party and character management for Legend of Atlantis."""

import random
from game.constants import MAX_PARTY, MAX_ITEMS_PER_CHAR, TYPE_NAMES


class Character:
    """A party member or enemy character."""

    def __init__(self):
        self.name = ''
        self.type = 0
        self.items = [0] * (MAX_ITEMS_PER_CHAR + 1)  # 1-indexed: items[1..6]
        self.equipped_a = 0  # Attack equipment slot (1-6, 0=none)
        self.equipped_d = 0  # Defense equipment slot (1-6, 0=none)
        self.attack = 0
        self.defence = 0
        self.hp = 0      # Max HP
        self.life = 0    # Current HP
        self.magic = 0   # Max magic
        self.magic_left = 0  # Current magic
        self.resilience = 0
        self.graph_x = 0
        self.graph_y = 0
        self.exp = 0
        self.move = 0    # Movement points per turn
        self.move_left = 0  # Movement points remaining this turn
        self.bat_x = 0   # Battle position X
        self.bat_y = 0   # Battle position Y

    @property
    def type_name(self):
        if 0 <= self.type < len(TYPE_NAMES):
            return TYPE_NAMES[self.type]
        return '????'

    @property
    def alive(self):
        return self.life > 0

    def get_item(self, slot):
        """Get item ID in slot (1-6)."""
        if 1 <= slot <= MAX_ITEMS_PER_CHAR:
            return self.items[slot]
        return 0

    def set_item(self, slot, item_id):
        """Set item in slot (1-6)."""
        if 1 <= slot <= MAX_ITEMS_PER_CHAR:
            self.items[slot] = item_id

    def find_free_slot(self):
        """Find the first free inventory slot (1-6), or 0 if none."""
        for i in range(1, MAX_ITEMS_PER_CHAR + 1):
            if self.items[i] == 0:
                return i
        return 0

    def find_item_slot(self, item_id):
        """Find the slot containing item_id (1-6), or 0 if not found."""
        for i in range(1, MAX_ITEMS_PER_CHAR + 1):
            if self.items[i] == item_id:
                return i
        return 0

    def remove_item(self, slot):
        """Remove item from slot, clearing equipment if needed."""
        if 1 <= slot <= MAX_ITEMS_PER_CHAR:
            self.items[slot] = 0
            if self.equipped_a == slot:
                self.equipped_a = 0
            if self.equipped_d == slot:
                self.equipped_d = 0


class Enemy:
    """An enemy in battle."""

    def __init__(self):
        self.name = ''
        self.type = 0
        self.equipped_a = 0
        self.equipped_d = 0
        self.hp = 0
        self.life = 0
        self.attack = 0
        self.defence = 0
        self.magic = 0
        self.resilience = 0
        self.graph_x = 0
        self.graph_y = 0
        self.move = 0
        self.move_left = 0
        self.bat_x = 0
        self.bat_y = 0
        self.tactics = 0
        self.ref_id = 0

    @property
    def type_name(self):
        if 0 <= self.type < len(TYPE_NAMES):
            return TYPE_NAMES[self.type]
        return '????'

    @property
    def alive(self):
        return self.life > 0


class Party:
    """Manages the player's party."""

    def __init__(self):
        self.members = []  # List of Character objects (index 0 = party member 1)
        self.money = 0

    @property
    def number(self):
        return len(self.members)

    def get(self, index):
        """Get party member by 1-based index."""
        if 1 <= index <= len(self.members):
            return self.members[index - 1]
        return None

    def add_member(self, char):
        """Add a Character to the party."""
        if len(self.members) < MAX_PARTY:
            self.members.append(char)

    def create_hero(self, name):
        """Create the starting hero character."""
        hero = Character()
        hero.name = name
        hero.type = 1  # HERO
        hero.items[1] = 1   # SHORT SWORD
        hero.items[2] = 5   # WOODEN SHIELD
        hero.equipped_a = 1  # Weapon in slot 1
        hero.equipped_d = 2  # Shield in slot 2
        hero.hp = 30
        hero.life = 30
        hero.attack = 7
        hero.defence = 2
        hero.magic = 0
        hero.magic_left = 0
        hero.resilience = 10
        hero.graph_x = 1
        hero.graph_y = 1
        hero.exp = 0
        hero.move = 2
        self.members = [hero]

    def add_from_data(self, char_data):
        """Add a character from character data dict (from data_loader.load_characters)."""
        char = Character()
        char.name = char_data['name']
        char.type = char_data['type']
        char.items[1] = char_data['item1']
        char.items[2] = char_data['item2']
        char.items[3] = char_data['item3']
        char.items[4] = char_data.get('item4', 0)
        char.items[5] = char_data.get('item5', 0)
        char.items[6] = char_data.get('item6', 0)
        char.equipped_a = char_data['equipped_a']
        char.equipped_d = char_data['equipped_d']
        char.hp = char_data['hp']
        char.life = char_data['hp']
        char.attack = char_data['attack']
        char.defence = char_data['defence']
        char.magic = char_data['magic']
        char.magic_left = char_data['magic']
        char.resilience = char_data['resilience']
        char.graph_x = char_data['graph_x']
        char.graph_y = char_data['graph_y']
        char.exp = char_data['exp']
        char.move = char_data['move']
        self.add_member(char)

    def find_item_holder(self, item_id):
        """Find which party member holds an item. Returns (member_index_1based, slot) or (0, 0)."""
        for i, member in enumerate(self.members):
            for slot in range(1, MAX_ITEMS_PER_CHAR + 1):
                if member.items[slot] == item_id:
                    return (i + 1, slot)
        return (0, 0)

    def find_free_slot_any(self):
        """
        Find first party member with a free slot.
        Returns (member_index_1based, slot) or (0, 0).
        Searches from last member backward to first (matching original).
        """
        best_member = 0
        best_slot = 0
        for i in range(len(self.members) - 1, -1, -1):
            for slot in range(MAX_ITEMS_PER_CHAR, 0, -1):
                if self.members[i].items[slot] == 0:
                    best_member = i + 1
                    best_slot = slot
        return (best_member, best_slot)

    def do_level_up(self, member_index):
        """
        Perform level-up for a character who reached 100 XP.
        Returns list of description strings.
        """
        char = self.get(member_index)
        if not char or char.exp < 100:
            return []

        messages = [f"{char.name} has reached 100 experience points !"]
        char.exp = 0  # Reset XP after level up

        att = random.randint(0, 3)
        if att == 1:
            bonus = random.randint(0, 2)
            char.attack += bonus
            messages.append(f"{char.name}`s attack increases by {bonus}")
        elif att == 2:
            bonus = random.randint(0, 2)
            char.defence += bonus
            messages.append(f"{char.name}`s defence increases by {bonus}")
        elif att == 3:
            bonus = random.randint(0, 2)
            char.resilience += bonus
            messages.append(f"{char.name}`s resiliance increases by {bonus}")

        # Secondary bonus (same att value check as original)
        if att == 1:
            bonus = random.randint(0, 5)
            if bonus == 5:
                char.move += 1
                messages.append(f"{char.name}`s movement increases by 1")
        elif att == 2:
            bonus = random.randint(0, 2)
            char.hp += bonus
            messages.append(f"{char.name}`s HP increases by {bonus}")
        elif att == 3:
            bonus = random.randint(0, 2)
            char.magic += bonus
            messages.append(f"{char.name}`s magic increases by {bonus}")

        return messages
