"""UI system for Legend of Atlantis - HUD, menus, text display, shop, inventory."""

import os
import pygame
from game.constants import (
    VIEWPORT_W, VIEWPORT_H, PANEL_W, WINDOW_W, WINDOW_H,
    COLOR_BLACK, COLOR_WHITE, COLOR_TEXT, COLOR_TEXT_HIGHLIGHT,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_BUTTON_BG, COLOR_BUTTON_HOVER,
    COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_SILVER,
    TYPE_NAMES, DISPLAY_TILE_W, DISPLAY_TILE_H,
    TEXT_CHAR_WIDTH, TEXT_LINE_HEIGHT, TEXT_BOX_MAX_CHARS,
    NAME_SYLLABLE_1, NAME_SYLLABLE_2, NAME_SYLLABLE_3,
    ASSET_DIR,
)
import random


class UI:
    """Manages all UI rendering and interaction."""

    def __init__(self, screen):
        self.screen = screen
        self.font_small = None
        self.font_medium = None
        self.font_large = None
        self.font_note = None
        self._init_fonts()

        # Note display state
        self.note_text = ''
        self.note_visible = False

        # Portrait display state
        self.portrait_surface = None

        # Speed control
        self.speed = 3

        # Text command mode
        self.text_mode = False
        self.command_log = []
        self.command_input = ''

        # Inventory state
        self.inv_visible = False
        self.inv_selected_member = 0  # 1-based index

        # Shop state
        self.shop_visible = False
        self.shop_items = []  # List of item IDs
        self.shop_selected = -1

    def _init_fonts(self):
        try:
            self.font_small = pygame.font.SysFont('arial', 11)
            self.font_medium = pygame.font.SysFont('arial', 13)
            self.font_large = pygame.font.SysFont('arial', 16, bold=True)
            self.font_note = pygame.font.SysFont('courier', 13)
        except Exception:
            self.font_small = pygame.font.Font(None, 14)
            self.font_medium = pygame.font.Font(None, 16)
            self.font_large = pygame.font.Font(None, 20)
            self.font_note = pygame.font.Font(None, 16)

    def draw_panel(self, party, world, items_data):
        """Draw the right-side status panel."""
        panel_x = VIEWPORT_W
        panel_rect = pygame.Rect(panel_x, 0, PANEL_W, WINDOW_H)
        self.screen.fill(COLOR_PANEL_BG, panel_rect)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, panel_rect, 1)

        y = 5

        # Title
        title = self.font_large.render("Legend of Atlantis", True, COLOR_TEXT_HIGHLIGHT)
        self.screen.blit(title, (panel_x + 10, y))
        y += 22

        # Location info
        if world.description:
            desc = self.font_small.render(world.description[:30], True, COLOR_TEXT)
            self.screen.blit(desc, (panel_x + 10, y))
        y += 16

        # Money
        money_text = self.font_medium.render(f"Money: {party.money} R", True, COLOR_YELLOW)
        self.screen.blit(money_text, (panel_x + 10, y))
        y += 18

        # Separator
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER,
                        (panel_x + 5, y), (panel_x + PANEL_W - 5, y))
        y += 5

        # Party members
        for i, member in enumerate(party.members):
            if y > WINDOW_H - 20:
                break
            color = COLOR_TEXT if member.alive else COLOR_RED
            name_text = self.font_small.render(
                f"{member.name} {member.type_name} HP:{member.life}/{member.hp}",
                True, color
            )
            self.screen.blit(name_text, (panel_x + 10, y))
            y += 14

        y += 5
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER,
                        (panel_x + 5, y), (panel_x + PANEL_W - 5, y))
        y += 5

        # Portrait
        if self.portrait_surface:
            self.screen.blit(self.portrait_surface, (panel_x + 10, y))
            y += DISPLAY_TILE_H + 5

        # Controls help
        y = WINDOW_H - 70
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER,
                        (panel_x + 5, y), (panel_x + PANEL_W - 5, y))
        y += 3
        controls = [
            "Arrows: Move  I: Inventory",
            "S: Save  L: Load  H: Help",
            "Space: Stay (battle)",
        ]
        for line in controls:
            text = self.font_small.render(line, True, (150, 150, 170))
            self.screen.blit(text, (panel_x + 10, y))
            y += 13

    def show_note(self, text, speed, party_name=''):
        """
        Display a note with typewriter effect.
        Blocks until the text is fully displayed.
        Handles 'ZZ' replacement with player name.
        """
        # Replace ZZ with player name
        if party_name and 'ZZ' in text:
            text = text.replace('ZZ', party_name)

        # Draw text box at bottom of viewport area
        box_rect = pygame.Rect(0, VIEWPORT_H - 60, VIEWPORT_W, 60)
        self.screen.fill((20, 20, 40), box_rect)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, box_rect, 1)

        # Typewriter display with word wrapping
        col = 0
        row = 0
        for i, ch in enumerate(text):
            if ch == ' ':
                # Word wrap: look ahead to next space
                next_space = text.find(' ', i + 1)
                if next_space == -1:
                    next_space = len(text)
                if col + (next_space - i) >= TEXT_BOX_MAX_CHARS:
                    row += 1
                    col = 0

            char_surface = self.font_note.render(ch, True, COLOR_TEXT)
            self.screen.blit(char_surface, (4 + col * 8, VIEWPORT_H - 56 + row * 14))
            col += 1
            if col >= TEXT_BOX_MAX_CHARS:
                row += 1
                col = 0

            pygame.display.flip()

            # Delay per character
            delay = 30 + speed * 5
            pygame.time.delay(delay)

            # Allow events during display
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        # Skip rest of text
                        remaining = text[i+1:]
                        for j, ch2 in enumerate(remaining):
                            if ch2 == ' ':
                                next_space2 = remaining.find(' ', j + 1)
                                if next_space2 == -1:
                                    next_space2 = len(remaining)
                                if col + (next_space2 - j) >= TEXT_BOX_MAX_CHARS:
                                    row += 1
                                    col = 0
                            char_surface2 = self.font_note.render(ch2, True, COLOR_TEXT)
                            self.screen.blit(char_surface2,
                                           (4 + col * 8, VIEWPORT_H - 56 + row * 14))
                            col += 1
                            if col >= TEXT_BOX_MAX_CHARS:
                                row += 1
                                col = 0
                        pygame.display.flip()
                        pygame.time.delay(200)
                        return

        # Pause after text display
        pause = 500 + speed * 500
        pygame.time.delay(pause)

    def show_note_long(self, text, speed, party_name=''):
        """Show note with longer pause (att=5 in original)."""
        self.show_note(text, speed, party_name)
        pygame.time.delay(1000)

    def ask_question(self, text, speed, party_name=''):
        """Show a yes/no question. Returns True for Yes, False for No."""
        self.show_note(text, speed, party_name)

        # Draw Yes/No buttons
        yes_rect = pygame.Rect(40, VIEWPORT_H - 25, 80, 20)
        no_rect = pygame.Rect(160, VIEWPORT_H - 25, 80, 20)
        pygame.draw.rect(self.screen, COLOR_BUTTON_BG, yes_rect)
        pygame.draw.rect(self.screen, COLOR_BUTTON_BG, no_rect)
        pygame.draw.rect(self.screen, COLOR_WHITE, yes_rect, 1)
        pygame.draw.rect(self.screen, COLOR_WHITE, no_rect, 1)

        yes_text = self.font_medium.render("Yes (Y)", True, COLOR_TEXT)
        no_text = self.font_medium.render("No (N)", True, COLOR_TEXT)
        self.screen.blit(yes_text, (yes_rect.x + 10, yes_rect.y + 2))
        self.screen.blit(no_text, (no_rect.x + 15, no_rect.y + 2))
        pygame.display.flip()

        # Wait for input
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        return True
                    if event.key == pygame.K_n:
                        return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if yes_rect.collidepoint(event.pos):
                        return True
                    if no_rect.collidepoint(event.pos):
                        return False
            pygame.time.delay(16)

    def draw_inventory(self, party, items_data, renderer):
        """Draw the inventory/equipment screen. Returns when closed."""
        selected_member = 1
        running = True

        while running:
            # Draw background
            self.screen.fill(COLOR_PANEL_BG)

            # Title
            title = self.font_large.render("Inventory", True, COLOR_TEXT_HIGHLIGHT)
            self.screen.blit(title, (WINDOW_W // 2 - 40, 5))

            # Money
            money = self.font_medium.render(f"= {party.money} R", True, COLOR_YELLOW)
            self.screen.blit(money, (WINDOW_W - 120, 5))

            # Member list (left side)
            y = 30
            for i, member in enumerate(party.members):
                color = COLOR_TEXT_HIGHLIGHT if (i + 1) == selected_member else COLOR_TEXT
                if not member.alive:
                    color = COLOR_RED
                text = self.font_medium.render(
                    f"{i+1}. {member.name} {member.type_name}", True, color
                )
                self.screen.blit(text, (10, y))
                y += 18

            # Selected member details (right side)
            if 1 <= selected_member <= party.number:
                member = party.get(selected_member)
                dx = 200
                dy = 30

                # Portrait
                if renderer.good_bmp:
                    portrait = renderer.view_picture(1, member.graph_x, member.graph_y)
                    self.screen.blit(portrait, (dx, dy))
                    dx_info = dx + 70
                else:
                    dx_info = dx

                # Stats
                stats = [
                    f"{member.name}  {member.type_name}",
                    f"HP={member.hp}  Magic={member.magic}",
                    f"Attack={member.attack}  Defence={member.defence}",
                    f"Resiliance={member.resilience}",
                    f"Experience={member.exp}  Move={member.move}",
                ]

                # Effective attack/defence with equipment
                eff_atk = member.attack
                eff_def = member.defence
                if member.equipped_a > 0:
                    item_id = member.get_item(member.equipped_a)
                    if item_id in items_data:
                        eff_atk += items_data[item_id]['value']
                if member.equipped_d > 0:
                    item_id = member.get_item(member.equipped_d)
                    if item_id in items_data:
                        eff_def += items_data[item_id]['value']

                stats[2] = f"Attack={eff_atk}  Defence={eff_def}"

                sy = dy
                for s in stats:
                    text = self.font_small.render(s, True, COLOR_TEXT)
                    self.screen.blit(text, (dx_info, sy))
                    sy += 14

                # HP / Magic bars
                sy += 5
                # HP bar
                pygame.draw.rect(self.screen, COLOR_RED, (dx_info, sy, member.hp * 2, 8))
                pygame.draw.rect(self.screen, COLOR_GREEN, (dx_info, sy, min(member.life, member.hp) * 2, 8))
                sy += 12
                # Magic bar
                if member.magic > 0:
                    pygame.draw.rect(self.screen, (0, 0, 200), (dx_info, sy, member.magic * 2, 8))
                    pygame.draw.rect(self.screen, (100, 100, 255), (dx_info, sy, min(member.magic_left, member.magic) * 2, 8))
                sy += 15

                # Items
                item_y = sy
                for slot in range(1, 7):
                    item_id = member.get_item(slot)
                    if item_id > 0 and item_id in items_data:
                        item = items_data[item_id]
                        prefix = ""
                        if member.equipped_a == slot:
                            prefix = "[ATK] "
                        elif member.equipped_d == slot:
                            prefix = "[DEF] "
                        text = self.font_small.render(
                            f"{slot}. {prefix}{item['name']} ({item['description'][:20]})",
                            True, COLOR_TEXT
                        )
                    else:
                        text = self.font_small.render(f"{slot}. ---", True, (100, 100, 100))
                    self.screen.blit(text, (dx, item_y))
                    item_y += 16

                # Equipment help
                item_y += 10
                help_text = self.font_small.render(
                    "E+slot: Equip  D+slot: Drop  G+slot: Give",
                    True, (150, 150, 170)
                )
                self.screen.blit(help_text, (dx, item_y))

            # Footer
            footer = self.font_small.render("Press ESC/I to close inventory", True, (150, 150, 170))
            self.screen.blit(footer, (10, WINDOW_H - 18))

            pygame.display.flip()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_i):
                        running = False
                    elif event.key == pygame.K_UP:
                        selected_member = max(1, selected_member - 1)
                    elif event.key == pygame.K_DOWN:
                        selected_member = min(party.number, selected_member + 1)
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        num = event.key - pygame.K_0
                        if 1 <= num <= party.number:
                            selected_member = num
                    elif event.key == pygame.K_e:
                        # Equip: wait for slot number
                        self._handle_equip(party, selected_member, items_data)
                    elif event.key == pygame.K_d:
                        # Drop: wait for slot number
                        self._handle_drop(party, selected_member, items_data)

            pygame.time.delay(16)

    def _handle_equip(self, party, member_idx, items_data):
        """Handle equip action - wait for slot key."""
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if pygame.K_1 <= event.key <= pygame.K_6:
                        slot = event.key - pygame.K_0
                        member = party.get(member_idx)
                        if member:
                            item_id = member.get_item(slot)
                            if item_id > 0 and item_id in items_data:
                                item = items_data[item_id]
                                itype = item['type']
                                fortype = item['fortype']
                                if itype == 1 and (fortype == member.type or fortype == 0):
                                    member.equipped_a = slot
                                elif itype == 2:
                                    member.equipped_d = slot
                    waiting = False
            pygame.time.delay(16)

    def _handle_drop(self, party, member_idx, items_data):
        """Handle drop action - wait for slot key."""
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if pygame.K_1 <= event.key <= pygame.K_6:
                        slot = event.key - pygame.K_0
                        member = party.get(member_idx)
                        if member:
                            member.remove_item(slot)
                    waiting = False
            pygame.time.delay(16)

    def draw_shop(self, party, items_data, shop_item_ids, speed):
        """
        Display the shop interface.
        shop_item_ids: list of item IDs available for purchase.
        """
        self.show_note("Welcome to my shop stranger. I have lots of good items.", speed)

        selected = 0
        running = True

        while running:
            self.screen.fill(COLOR_PANEL_BG)

            title = self.font_large.render("Shop", True, COLOR_TEXT_HIGHLIGHT)
            self.screen.blit(title, (WINDOW_W // 2 - 20, 5))

            money = self.font_medium.render(f"Money = {party.money} R", True, COLOR_YELLOW)
            self.screen.blit(money, (WINDOW_W - 140, 5))

            # Item list
            y = 35
            for i, item_id in enumerate(shop_item_ids):
                if item_id in items_data:
                    item = items_data[item_id]
                    color = COLOR_TEXT_HIGHLIGHT if i == selected else COLOR_TEXT
                    type_name = TYPE_NAMES[item['fortype']] if 0 <= item['fortype'] < len(TYPE_NAMES) else '???'
                    text = self.font_small.render(
                        f"{item['name']} - {item['price']} R - For {type_name} - Power {item['value']}",
                        True, color
                    )
                    self.screen.blit(text, (20, y))
                    y += 16

            # Footer
            footer = self.font_small.render(
                "ENTER: Buy  ESC: Leave  Up/Down: Select", True, (150, 150, 170)
            )
            self.screen.blit(footer, (10, WINDOW_H - 18))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.show_note("Stop again soon, I may have some more items", speed)
                        running = False
                    elif event.key == pygame.K_UP:
                        selected = max(0, selected - 1)
                    elif event.key == pygame.K_DOWN:
                        selected = min(len(shop_item_ids) - 1, selected + 1)
                    elif event.key == pygame.K_RETURN:
                        if 0 <= selected < len(shop_item_ids):
                            item_id = shop_item_ids[selected]
                            if item_id in items_data:
                                price = items_data[item_id]['price']
                                if party.money >= price:
                                    # Find a party member with free slot
                                    buyer = self._select_buyer(party, items_data, item_id, speed)
                                    if buyer > 0:
                                        member = party.get(buyer)
                                        slot = member.find_free_slot()
                                        if slot > 0:
                                            member.set_item(slot, item_id)
                                            party.money -= price
                                            self.show_note(
                                                f"You purchased {items_data[item_id]['name']} for {member.name}",
                                                speed
                                            )
                                else:
                                    self.show_note("You can't afford that!", speed)

            pygame.time.delay(16)

    def _select_buyer(self, party, items_data, item_id, speed):
        """Select which party member gets the purchased item. Returns 1-based index or 0."""
        selected = 0
        running = True

        while running:
            self.screen.fill(COLOR_PANEL_BG)

            title = self.font_medium.render(
                f"Who shall have the {items_data.get(item_id, {}).get('name', '?')}",
                True, COLOR_TEXT
            )
            self.screen.blit(title, (20, 10))

            y = 40
            for i, member in enumerate(party.members):
                has_space = member.find_free_slot() > 0
                color = COLOR_TEXT_HIGHLIGHT if i == selected else COLOR_TEXT
                if not has_space:
                    color = (100, 100, 100)
                text = self.font_small.render(
                    f"{i+1}. {member.name} {member.type_name}", True, color
                )
                self.screen.blit(text, (30, y))
                y += 18

            footer = self.font_small.render("ENTER: Select  ESC: Cancel", True, (150, 150, 170))
            self.screen.blit(footer, (10, WINDOW_H - 18))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 0
                    elif event.key == pygame.K_UP:
                        selected = max(0, selected - 1)
                    elif event.key == pygame.K_DOWN:
                        selected = min(party.number - 1, selected + 1)
                    elif event.key == pygame.K_RETURN:
                        member = party.get(selected + 1)
                        if member and member.find_free_slot() > 0:
                            return selected + 1

            pygame.time.delay(16)

        return 0

    def draw_title_screen(self):
        """Draw the title screen. Returns when player is ready."""
        # Try to load title BMP
        import os
        title_path = os.path.join(ASSET_DIR, "title2.bmp")
        title_img = None
        if os.path.exists(title_path):
            try:
                title_img = pygame.image.load(title_path).convert()
            except pygame.error:
                pass

        running = True
        while running:
            self.screen.fill(COLOR_BLACK)

            if title_img:
                # Scale to fit window
                scaled = pygame.transform.scale(title_img, (WINDOW_W, WINDOW_H))
                self.screen.blit(scaled, (0, 0))
            else:
                # Fallback title
                title = self.font_large.render("The Legend of Atlantis", True, COLOR_TEXT_HIGHLIGHT)
                self.screen.blit(title, (WINDOW_W // 2 - 100, 80))

                subtitle = self.font_medium.render("Nevil Software", True, COLOR_TEXT)
                self.screen.blit(subtitle, (WINDOW_W // 2 - 50, 120))

            prompt = self.font_medium.render("Press ENTER to start, L to load", True, COLOR_TEXT)
            self.screen.blit(prompt, (WINDOW_W // 2 - 110, WINDOW_H - 40))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return 'new'
                    if event.key == pygame.K_l:
                        return 'load'
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        raise SystemExit

            pygame.time.delay(16)

    def draw_create_party(self, speed_val=3):
        """Draw the party creation screen. Returns (name, speed)."""
        name = self._generate_name()
        speed = speed_val

        running = True
        while running:
            self.screen.fill(COLOR_PANEL_BG)

            title = self.font_large.render("Create Your Hero", True, COLOR_TEXT_HIGHLIGHT)
            self.screen.blit(title, (WINDOW_W // 2 - 70, 30))

            # Name input
            name_label = self.font_medium.render("Name:", True, COLOR_TEXT)
            self.screen.blit(name_label, (100, 100))

            name_box = pygame.Rect(170, 96, 200, 24)
            pygame.draw.rect(self.screen, COLOR_BLACK, name_box)
            pygame.draw.rect(self.screen, COLOR_WHITE, name_box, 1)
            name_text = self.font_medium.render(name, True, COLOR_TEXT)
            self.screen.blit(name_text, (175, 100))

            # Random name button
            rand_text = self.font_small.render("R: Random Name", True, COLOR_TEXT)
            self.screen.blit(rand_text, (380, 100))

            # Speed
            speed_label = self.font_medium.render(f"Text Speed: {speed}", True, COLOR_TEXT)
            self.screen.blit(speed_label, (100, 150))
            speed_help = self.font_small.render("+/-: Adjust speed", True, (150, 150, 170))
            self.screen.blit(speed_help, (280, 152))

            # Type info
            info = self.font_medium.render("Type: HERO", True, COLOR_TEXT)
            self.screen.blit(info, (100, 200))

            stats = self.font_small.render("HP:30 ATK:7 DEF:2 MAG:0 RES:10 MOV:2", True, COLOR_TEXT)
            self.screen.blit(stats, (100, 225))

            equipment = self.font_small.render("Equipment: Short Sword, Wooden Shield", True, COLOR_TEXT)
            self.screen.blit(equipment, (100, 245))

            # Start
            start_text = self.font_medium.render("Press ENTER to begin your adventure!", True, COLOR_TEXT_HIGHLIGHT)
            self.screen.blit(start_text, (WINDOW_W // 2 - 130, WINDOW_H - 50))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return (name if name else "Hero", speed)
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif event.key == pygame.K_r:
                        name = self._generate_name()
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        speed = min(10, speed + 1)
                    elif event.key == pygame.K_MINUS:
                        speed = max(0, speed - 1)
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        raise SystemExit
                    elif event.unicode and event.unicode.isprintable() and len(name) < 12:
                        name += event.unicode

            pygame.time.delay(16)

        return (name, speed)

    def _generate_name(self):
        """Generate a random name using the original syllable tables."""
        s1 = random.choice(NAME_SYLLABLE_1)
        s2 = random.choice(NAME_SYLLABLE_2)
        s3 = random.choice(NAME_SYLLABLE_3)
        return s1 + s2 + s3

    def draw_game_over(self, player_name):
        """Draw the game over screen."""
        running = True
        while running:
            self.screen.fill(COLOR_BLACK)
            text1 = self.font_large.render(f"{player_name} is exhausted...", True, COLOR_RED)
            text2 = self.font_medium.render("GAME OVER", True, COLOR_RED)
            text3 = self.font_small.render("Press any key to return to title", True, COLOR_TEXT)
            self.screen.blit(text1, (WINDOW_W // 2 - 100, WINDOW_H // 2 - 40))
            self.screen.blit(text2, (WINDOW_W // 2 - 50, WINDOW_H // 2))
            self.screen.blit(text3, (WINDOW_W // 2 - 100, WINDOW_H // 2 + 40))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    return

            pygame.time.delay(16)

    def draw_party_scene(self, text1, text2, text3, screen):
        """Draw the party/credits scene (command 29)."""
        import os
        screen.fill(COLOR_BLACK)

        # Try to load part.bmp
        part_path = os.path.join(ASSET_DIR, "part.bmp")
        if os.path.exists(part_path):
            try:
                part_img = pygame.image.load(part_path).convert()
                scaled = pygame.transform.scale(part_img, (WINDOW_W, WINDOW_H))
                screen.blit(scaled, (0, 0))
            except pygame.error:
                pass

        # Draw text overlay
        y = WINDOW_H // 3
        for txt in [text1, text2, text3]:
            if txt:
                rendered = self.font_large.render(txt, True, COLOR_TEXT_HIGHLIGHT)
                screen.blit(rendered, (WINDOW_W // 2 - rendered.get_width() // 2, y))
                y += 40

        pygame.display.flip()

    def draw_save_screen(self, speed):
        """Draw save game dialog. Returns filename or None."""
        name = ''
        running = True

        while running:
            self.screen.fill(COLOR_PANEL_BG)

            title = self.font_large.render("Save Game", True, COLOR_TEXT_HIGHLIGHT)
            self.screen.blit(title, (WINDOW_W // 2 - 40, 30))

            label = self.font_medium.render("Save name:", True, COLOR_TEXT)
            self.screen.blit(label, (100, 100))

            name_box = pygame.Rect(200, 96, 200, 24)
            pygame.draw.rect(self.screen, COLOR_BLACK, name_box)
            pygame.draw.rect(self.screen, COLOR_WHITE, name_box, 1)
            name_text = self.font_medium.render(name, True, COLOR_TEXT)
            self.screen.blit(name_text, (205, 100))

            help_text = self.font_small.render("ENTER: Save  ESC: Cancel", True, (150, 150, 170))
            self.screen.blit(help_text, (100, WINDOW_H - 30))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and name:
                        return name
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif event.unicode and event.unicode.isprintable() and len(name) < 20:
                        name += event.unicode

            pygame.time.delay(16)

        return None

    def draw_load_screen(self, saves, speed):
        """Draw load game dialog. Returns filename or None."""
        if not saves:
            self.show_note("No save files found!", speed)
            return None

        selected = 0
        running = True

        while running:
            self.screen.fill(COLOR_PANEL_BG)

            title = self.font_large.render("Load Game", True, COLOR_TEXT_HIGHLIGHT)
            self.screen.blit(title, (WINDOW_W // 2 - 40, 30))

            y = 70
            for i, save_name in enumerate(saves):
                color = COLOR_TEXT_HIGHLIGHT if i == selected else COLOR_TEXT
                text = self.font_medium.render(f"{i+1}. {save_name}", True, color)
                self.screen.blit(text, (100, y))
                y += 22

            help_text = self.font_small.render("ENTER: Load  ESC: Cancel", True, (150, 150, 170))
            self.screen.blit(help_text, (100, WINDOW_H - 30))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and saves:
                        return saves[selected]
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_UP:
                        selected = max(0, selected - 1)
                    elif event.key == pygame.K_DOWN:
                        selected = min(len(saves) - 1, selected + 1)

            pygame.time.delay(16)

        return None
