"""Story script interpreter for Legend of Atlantis - all 29 command types."""

import pygame
from game.constants import GLOBAL_MAX
from game.data_loader import open_story_file


def check_conditional_story(story_number, global_flags):
    """
    Check if a story file starts with -1 (conditional branch).
    If so, returns the resolved story number based on Global[b][c].
    Otherwise returns the original story number.
    """
    reader = open_story_file(story_number)
    if not reader:
        return story_number

    first_val = reader.read_int()
    if first_val == -1:
        b = reader.read_int()
        c = reader.read_int()
        branches = []
        for _ in range(5):  # d, e, f, g, h
            branches.append(reader.read_int())
        reader.close()

        flag_val = global_flags[b][c] if 0 <= b < GLOBAL_MAX and 0 <= c < GLOBAL_MAX else 0
        if 0 <= flag_val < len(branches):
            return branches[flag_val]
        return branches[0] if branches else story_number

    reader.close()
    return story_number


def run_story(story_number, game):
    """
    Execute a story script.

    game: the Game object with access to world, party, renderer, ui, audio, etc.
    """
    reader = open_story_file(story_number)
    if not reader:
        return

    # Read the first value - could be -1 (conditional) or command count
    first_val = reader.read_int()

    if first_val == -1:
        # Conditional - resolve and re-open
        b = reader.read_int()
        c = reader.read_int()
        branches = []
        for _ in range(5):
            branches.append(reader.read_int())
        reader.close()

        flag_val = game.global_flags[b][c] if 0 <= b < GLOBAL_MAX and 0 <= c < GLOBAL_MAX else 0
        resolved = branches[flag_val] if 0 <= flag_val < len(branches) else branches[0]

        reader = open_story_file(resolved)
        if not reader:
            return
        first_val = reader.read_int()

    num_commands = first_val
    skipping = False

    for _ in range(num_commands):
        cmd = reader.read_int()
        if skipping:
            _skip_command(cmd, reader)
            continue
        _execute_command(cmd, reader, game)

        # Process pygame events to keep the window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                reader.close()
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                skipping = True

    reader.close()

    # Re-draw after story
    if game.world.battle:
        game.renderer.draw_battle(game.world, game.party, game.enemies)
        game.renderer.draw_lifebar(
            game.party.get(game.pmoving).life if game.pmoving > 0 else 0,
            game.party.get(game.pmoving).hp if game.pmoving > 0 else 0,
            game.party.get(game.pmoving).name if game.pmoving > 0 else '',
            game.party.get(game.pmoving).type_name if game.pmoving > 0 else '',
            game.party.get(game.pmoving).move_left if game.pmoving > 0 else 0,
        )


def _execute_command(cmd, reader, game):
    """Execute a single story command."""
    world = game.world
    renderer = game.renderer
    ui = game.ui
    party = game.party
    audio = game.audio
    screen = game.screen
    clock = game.clock
    speed = game.speed
    viewport_rect = game.viewport_rect

    if cmd == 1:
        # Display text
        reader.readln()
        text = reader.read_string()
        player_name = party.get(1).name if party.number > 0 else ''

        # Draw current state first
        renderer.draw_board(world)
        renderer.draw_character(3, 3, world.main_dir, game.val1, world)
        screen.blit(renderer.viewport, viewport_rect.topleft)
        ui.draw_panel(party, world, game.items_data)

        ui.show_note(text, speed, player_name)

    elif cmd == 2:
        # Change board position
        world.main_x = reader.read_int()
        world.main_y = reader.read_int()

    elif cmd == 3:
        # Draw character at position
        x = reader.read_int()
        y = reader.read_int()
        renderer.draw_character(x, y, world.main_dir, game.val1, world)
        screen.blit(renderer.viewport, viewport_rect.topleft)
        pygame.display.flip()

    elif cmd == 4:
        # Draw the board
        renderer.draw_board(world)
        screen.blit(renderer.viewport, viewport_rect.topleft)
        pygame.display.flip()

    elif cmd == 5:
        # Load array (reload current location)
        game.load_location(world.loc)

    elif cmd == 6:
        # View picture: type x y
        t = reader.read_int()
        x = reader.read_int()
        y = reader.read_int()
        portrait = renderer.view_picture(t, x, y, game.val1)
        ui.portrait_surface = portrait

        # Also draw the portrait on the panel
        screen.blit(renderer.viewport, viewport_rect.topleft)
        ui.draw_panel(party, world, game.items_data)
        pygame.display.flip()

    elif cmd == 7:
        # Display WMF (not supported, skip)
        reader.readln()
        reader.read_string()

    elif cmd == 8:
        # Change graphic position of square
        x = reader.read_int()
        y = reader.read_int()
        world.graph_array_x[x][y] = reader.read_int()
        world.graph_array_y[x][y] = reader.read_int()

    elif cmd == 9:
        # Change character position on square
        x = reader.read_int()
        y = reader.read_int()
        world.char_array_x[x][y] = reader.read_int()
        world.char_array_y[x][y] = reader.read_int()

    elif cmd == 10:
        # Change tile value
        x = reader.read_int()
        y = reader.read_int()
        world.val_array[x][y] = reader.read_int()

    elif cmd == 11:
        # Wipe screen
        color_type = reader.read_int()
        renderer.wipe(color_type)
        screen.blit(renderer.viewport, viewport_rect.topleft)
        pygame.display.flip()

    elif cmd == 12:
        # Delay
        ms = reader.read_int()
        _delay_with_events(ms)

    elif cmd == 13:
        # Change location
        new_loc = reader.read_int()
        world.loc = new_loc

    elif cmd == 14:
        # Change direction
        world.main_dir = reader.read_int()

    elif cmd == 15:
        # Load MIDI/music
        reader.readln()
        music_name = reader.read_string().strip()
        if music_name:
            audio.play_music(music_name)

    elif cmd == 16:
        # Draw a man at position
        sprite_x = reader.read_int()
        sprite_y = reader.read_int()
        pos_x = reader.read_int()
        pos_y = reader.read_int()
        renderer.draw_man(sprite_x, sprite_y, pos_x, pos_y, 0)
        screen.blit(renderer.viewport, viewport_rect.topleft)
        pygame.display.flip()

    elif cmd == 17:
        # Hide panel5 (inventory panel) - in our version, just clear portrait
        ui.portrait_surface = None

    elif cmd == 18:
        # Panel13 visible = false (no-op in our version)
        pass

    elif cmd == 19:
        # Fade out
        renderer.fadeout(world, screen, viewport_rect, clock)

    elif cmd == 20:
        # Fade in
        renderer.fadein(world, screen, viewport_rect, clock)

    elif cmd == 21:
        # Fade out 2
        renderer.fadeout2(world, screen, viewport_rect, clock)

    elif cmd == 22:
        # Add character to party
        char_id = reader.read_int()
        if char_id in game.char_data:
            party.add_from_data(game.char_data[char_id])

    elif cmd == 24:
        # Set global variable
        x = reader.read_int()
        y = reader.read_int()
        v = reader.read_int()
        if 0 <= x < GLOBAL_MAX and 0 <= y < GLOBAL_MAX:
            game.global_flags[x][y] = v

    elif cmd == 25:
        # Pick up item
        item_id = reader.read_int()
        player_name = party.get(1).name if party.number > 0 else ''

        if item_id in game.items_data:
            item_name = game.items_data[item_id]['name']
            _draw_and_note(game, f"You get the {item_name}")

            # Find first party member with free slot (search backward like original)
            m, k = party.find_free_slot_any()
            if m > 0:
                member = party.get(m)
                _draw_and_note(game, f"{member.name} Picks up the {item_name}")
                member.set_item(k, item_id)
            else:
                _draw_and_note(game, "But none of your players have any free space")

    elif cmd == 26:
        # Drop/give item
        item_id = reader.read_int()
        if item_id in game.items_data:
            item_name = game.items_data[item_id]['name']
            _draw_and_note(game, f"You look for the {item_name}")

            m, k = party.find_item_holder(item_id)
            if m > 0:
                member = party.get(m)
                _draw_and_note(game, f"{member.name} Uses the {item_name}")
                member.set_item(k, 0)
            else:
                _draw_and_note(game, f"Knowone has the {item_name}")

    elif cmd == 27:
        # Shop
        num_items = reader.read_int()
        shop_items = []
        for _ in range(num_items):
            shop_items.append(reader.read_int())
        ui.draw_shop(party, game.items_data, shop_items, speed)

    elif cmd == 28:
        # Find money
        amount = reader.read_int()
        party.money += amount
        _draw_and_note(game, f"You find {amount} Rubions")

    elif cmd == 29:
        # Party scene / credits
        reader.readln()
        text1 = reader.read_string()
        reader.readln()
        text2 = reader.read_string()
        reader.readln()
        text3 = reader.read_string()

        # Play part.mid if available
        old_music = audio.music_filename
        audio.play_music("part.mid")

        ui.draw_party_scene(text1, text2, text3, screen)
        _delay_with_events(10000)

        # Restore music
        if old_music:
            audio.play_music(old_music)

        # Hide party scene by redrawing
        renderer.draw_board(world)
        screen.blit(renderer.viewport, viewport_rect.topleft)
        pygame.display.flip()


def _skip_command(cmd, reader):
    """Read and discard a command's parameters to keep the reader aligned."""
    if cmd == 1:
        reader.readln(); reader.read_string()
    elif cmd == 2:
        reader.read_int(); reader.read_int()
    elif cmd == 3:
        reader.read_int(); reader.read_int()
    elif cmd in (4, 5, 17, 18, 19, 20, 21):
        pass  # No parameters
    elif cmd == 6:
        reader.read_int(); reader.read_int(); reader.read_int()
    elif cmd == 7:
        reader.readln(); reader.read_string()
    elif cmd == 8:
        reader.read_int(); reader.read_int(); reader.read_int(); reader.read_int()
    elif cmd == 9:
        reader.read_int(); reader.read_int(); reader.read_int(); reader.read_int()
    elif cmd == 10:
        reader.read_int(); reader.read_int(); reader.read_int()
    elif cmd == 11:
        reader.read_int()
    elif cmd == 12:
        reader.read_int()
    elif cmd == 13:
        reader.read_int()
    elif cmd == 14:
        reader.read_int()
    elif cmd == 15:
        reader.readln(); reader.read_string()
    elif cmd == 16:
        reader.read_int(); reader.read_int(); reader.read_int(); reader.read_int()
    elif cmd == 22:
        reader.read_int()
    elif cmd == 24:
        reader.read_int(); reader.read_int(); reader.read_int()
    elif cmd == 25:
        reader.read_int()
    elif cmd == 26:
        reader.read_int()
    elif cmd == 27:
        n = reader.read_int()
        for _ in range(n):
            reader.read_int()
    elif cmd == 28:
        reader.read_int()
    elif cmd == 29:
        reader.readln(); reader.read_string()
        reader.readln(); reader.read_string()
        reader.readln(); reader.read_string()


def _delay_with_events(ms):
    """Delay while processing pygame events to keep the window responsive."""
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < ms:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        pygame.time.delay(16)


def _draw_and_note(game, text):
    """Helper to draw viewport state and show a note."""
    game.renderer.draw_board(game.world)
    game.renderer.draw_character(3, 3, game.world.main_dir, game.val1, game.world)
    game.screen.blit(game.renderer.viewport, game.viewport_rect.topleft)
    game.ui.draw_panel(game.party, game.world, game.items_data)
    player_name = game.party.get(1).name if game.party.number > 0 else ''
    game.ui.show_note(text, game.speed, player_name)
