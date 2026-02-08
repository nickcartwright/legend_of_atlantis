"""Main game loop and state management for Legend of Atlantis."""

import pygame
import os
from game.constants import (
    WINDOW_W, WINDOW_H, VIEWPORT_W, VIEWPORT_H, FPS,
    ASSET_DIR, GLOBAL_MAX, START_LOCATION, START_MONEY, DEFAULT_SPEED,
    DIR_SOUTH, DIR_NORTH, DIR_EAST, DIR_WEST,
    COLOR_BLACK,
)
from game.renderer import Renderer
from game.world import World
from game.party import Party
from game.ui import UI
from game.audio import Audio
from game.battle import BattleSystem
from game import data_loader
from game.story import run_story, check_conditional_story
from game import save_load


class Game:
    """Main game class - orchestrates all subsystems."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("The Legend of Atlantis - Nevil Software")
        self.clock = pygame.time.Clock()

        # Viewport position on screen
        self.viewport_rect = pygame.Rect(0, 0, VIEWPORT_W, VIEWPORT_H)

        # Subsystems
        self.renderer = Renderer()
        self.world = World()
        self.party = Party()
        self.ui = UI(self.screen)
        self.audio = Audio()
        self.audio.init()
        self.battle_system = BattleSystem(self)

        # Game data
        self.items_data = {}
        self.char_data = {}
        self.enemy_data = {}
        self.music_data = {}
        self.gaze_data = {}

        # Global flags array [0..100][0..100]
        self.global_flags = [[0] * GLOBAL_MAX for _ in range(GLOBAL_MAX)]

        # Animation state
        self.val1 = 1  # Character animation frame

        # Game state
        self.state = 'title'
        self.speed = DEFAULT_SPEED
        self.pmoving = 0  # Current player moving in battle (1-based)
        self.enemies = []  # Active enemies in battle

        # Track loaded BMP IDs
        self._prev_graph_id = -1
        self._prev_good_id = -1
        self._prev_char_id = -1

    def load_data(self):
        """Load all static game data files."""
        self.items_data = data_loader.load_items()
        self.char_data = data_loader.load_characters()
        self.enemy_data = data_loader.load_enemies()
        self.music_data = data_loader.load_music_ini()
        self.audio.set_music_data(self.music_data)
        self.gaze_data = data_loader.load_gaze_ini()

    def load_location(self, loc_number):
        """Load a location and set up all related state."""
        loc_data = data_loader.load_location(loc_number)
        if not loc_data:
            return

        self.world.loc = loc_number
        self.world.load_from_data(loc_data)

        # Load tilesets
        self.renderer.load_tilesets(
            self.world.graph_bmp_id,
            self.world.good_bmp_id,
            self.world.char_bmp_id,
            ASSET_DIR,
        )

        # Play music
        if self.world.muse > 0:
            self.audio.play_music_by_id(self.world.muse, self.music_data)

        # If battle location, set up battle
        if self.world.battle:
            battle_data = data_loader.load_battle(loc_number, self.party.number)
            if battle_data:
                self.battle_system.start_battle(battle_data, self.enemy_data)
                self.enemies = self.battle_system.enemies
                self.pmoving = self.battle_system.pmoving

    def run(self):
        """Main game loop."""
        self.load_data()

        running = True
        while running:
            if self.state == 'title':
                action = self.ui.draw_title_screen()
                if action == 'new':
                    self.state = 'create_party'
                elif action == 'load':
                    self._do_load()
                    if self.state != 'playing':
                        continue

            elif self.state == 'create_party':
                name, speed = self.ui.draw_create_party(self.speed)
                self.speed = speed
                self.party.create_hero(name)
                self.party.money = START_MONEY
                pygame.display.set_caption(f"The Legend of Atlantis - Nevil Software - {name}")

                # Load starting location
                self.world.loc = START_LOCATION
                self.load_location(START_LOCATION)

                # Run opening story (story 35)
                self.state = 'playing'
                self._run_opening_story()

            elif self.state == 'playing':
                self._game_frame()

            elif self.state == 'game_over':
                self.ui.draw_game_over(
                    self.party.get(1).name if self.party.number > 0 else "Hero"
                )
                self.state = 'title'

            self.clock.tick(FPS)

    def _run_opening_story(self):
        """Run the opening story sequence."""
        if self.world.loc == START_LOCATION:
            run_story(35, self)

        # Draw initial board
        self.renderer.draw_board(self.world)
        self.renderer.draw_character(3, 3, self.world.main_dir, self.val1, self.world)
        self.screen.blit(self.renderer.viewport, self.viewport_rect.topleft)
        self.ui.draw_panel(self.party, self.world, self.items_data)
        pygame.display.flip()

    def _game_frame(self):
        """Process one frame of gameplay."""
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)

        # Draw
        if self.world.battle:
            self.renderer.draw_battle(self.world, self.party, self.enemies)
            # Draw lifebar for current player
            member = self.party.get(self.pmoving)
            if member:
                self.renderer.draw_lifebar(
                    member.life, member.hp, member.name, member.type_name,
                    member.move_left
                )
        else:
            self.renderer.draw_board(self.world)
            self.renderer.draw_character(3, 3, self.world.main_dir, self.val1, self.world)

        self.screen.blit(self.renderer.viewport, self.viewport_rect.topleft)
        self.ui.draw_panel(self.party, self.world, self.items_data)
        pygame.display.flip()

    def _handle_key(self, key):
        """Handle keyboard input."""
        if self.world.battle:
            self._handle_battle_key(key)
        else:
            self._handle_explore_key(key)

        # Common keys
        if key == pygame.K_i:
            self.ui.draw_inventory(self.party, self.items_data, self.renderer)
        elif key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self._do_save()
        elif key == pygame.K_F5:
            self._do_save()
        elif key == pygame.K_F9:
            self._do_load()

    def _handle_explore_key(self, key):
        """Handle keyboard input during exploration."""
        dx, dy, direction = 0, 0, 0

        if key == pygame.K_RIGHT:
            dx, direction = 1, DIR_EAST
        elif key == pygame.K_LEFT:
            dx, direction = -1, DIR_WEST
        elif key == pygame.K_DOWN:
            dy, direction = 1, DIR_SOUTH
        elif key == pygame.K_UP:
            dy, direction = -1, DIR_NORTH
        elif key == pygame.K_l and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
            # Look command
            if self.world.description:
                self.ui.show_note(self.world.description, self.speed)
            return
        elif key == pygame.K_h:
            # Help
            self.ui.show_note(
                "Arrows: Move  I: Inventory  L: Look  S: Save  F9: Load  H: Help  ESC: Quit",
                self.speed
            )
            return
        elif key == pygame.K_ESCAPE:
            pygame.quit()
            raise SystemExit
        else:
            return

        if direction == 0:
            return

        result = self.world.try_move(dx, dy, direction)

        if result['moved']:
            if result['stairs']:
                self.audio.play_stairs_sound()
            else:
                self.audio.play_move_sound()

        if result['story_trigger']:
            stry = result['story_trigger']
            # Check for conditional story
            resolved = check_conditional_story(stry, self.global_flags)
            run_story(resolved, self)

            # Redraw after story
            self.renderer.draw_board(self.world)
            self.renderer.draw_character(3, 3, self.world.main_dir, self.val1, self.world)
            self.screen.blit(self.renderer.viewport, self.viewport_rect.topleft)
            self.ui.draw_panel(self.party, self.world, self.items_data)
            pygame.display.flip()

        elif result['location_change']:
            new_loc = result['location_change']
            self.load_location(new_loc)
            self.renderer.fadein(self.world, self.screen, self.viewport_rect, self.clock)

    def _handle_battle_key(self, key):
        """Handle keyboard input during battle."""
        if key == pygame.K_RIGHT:
            self.battle_system.handle_move(DIR_EAST)
        elif key == pygame.K_LEFT:
            self.battle_system.handle_move(DIR_WEST)
        elif key == pygame.K_DOWN:
            self.battle_system.handle_move(DIR_SOUTH)
        elif key == pygame.K_UP:
            self.battle_system.handle_move(DIR_NORTH)
        elif key == pygame.K_SPACE:
            self.battle_system.handle_stay()

        # Update battle state references
        self.pmoving = self.battle_system.pmoving
        self.enemies = self.battle_system.enemies

    def _do_save(self):
        """Handle save game."""
        filename = self.ui.draw_save_screen(self.speed)
        if filename:
            save_load.save_game(
                filename, self.world, self.party,
                self.global_flags, self.audio.music_filename,
                self.world.battle,
            )
            self.ui.show_note("Game saved!", self.speed)

    def _do_load(self):
        """Handle load game."""
        saves = save_load.list_saves()
        filename = self.ui.draw_load_screen(saves, self.speed)
        if filename:
            data = save_load.load_game(filename)
            if data:
                self._restore_from_save(data)
                self.state = 'playing'

    def _restore_from_save(self, data):
        """Restore all game state from save data."""
        # Load the base location first
        self.load_location(data['loc'])

        # Override position from save
        self.world.main_x = data['main_x']
        self.world.main_y = data['main_y']
        self.world.battle = data['battle']

        # Restore party
        self.party.money = data['money']
        self.party.members = []
        from game.party import Character
        for cdata in data['characters']:
            char = Character()
            char.name = cdata['name']
            char.type = cdata['type']
            for slot in range(1, 7):
                char.items[slot] = cdata['items'][slot]
            char.equipped_a = cdata['equipped_a']
            char.equipped_d = cdata['equipped_d']
            char.attack = cdata['attack']
            char.defence = cdata['defence']
            char.hp = cdata['hp']
            char.life = cdata['hp']
            char.magic = cdata['magic']
            char.magic_left = cdata['magic']
            char.resilience = cdata['resilience']
            char.graph_x = cdata['graph_x']
            char.graph_y = cdata['graph_y']
            char.exp = cdata['exp']
            char.move = cdata['move']
            self.party.add_member(char)

        # Restore global flags
        self.global_flags = data['global_flags']

        # Restore location tile arrays
        self.world.arr_x = data['arr_x']
        self.world.arr_y = data['arr_y']
        self.world.graph_array_x = data['graph_array_x']
        self.world.graph_array_y = data['graph_array_y']
        self.world.char_array_x = data['char_array_x']
        self.world.char_array_y = data['char_array_y']
        self.world.val_array = data['val_array']

        # Restore music
        if data.get('music'):
            self.audio.play_music(data['music'])

        pygame.display.set_caption(
            f"The Legend of Atlantis - Nevil Software - {self.party.get(1).name}"
        )

        # Redraw
        if not self.world.battle:
            self.renderer.draw_board(self.world)
            self.renderer.draw_character(3, 3, self.world.main_dir, self.val1, self.world)
            self.screen.blit(self.renderer.viewport, self.viewport_rect.topleft)
            self.ui.draw_panel(self.party, self.world, self.items_data)
            pygame.display.flip()
