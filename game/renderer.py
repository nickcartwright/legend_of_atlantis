"""Rendering for Legend of Atlantis - tile rendering, viewport, sprite drawing, fade effects."""

import pygame
from game.constants import (
    TILE_W, TILE_H, SCALE, DISPLAY_TILE_W, DISPLAY_TILE_H,
    VIEWPORT_TILES, VIEWPORT_W, VIEWPORT_H,
    SPRITE_Y_OFFSET, COLOR_BLACK, COLOR_WHITE, COLOR_YELLOW,
    COLOR_RED, COLOR_GREEN, COLOR_TRANSPARENT,
)


class Renderer:
    """Handles all game rendering to the viewport surface."""

    def __init__(self):
        self.viewport = pygame.Surface((VIEWPORT_W, VIEWPORT_H))
        self.graph_bmp = None
        self.good_bmp = None
        self.char_bmp = None
        # Cache loaded BMP IDs to avoid reloading
        self._loaded_graph_id = -1
        self._loaded_good_id = -1
        self._loaded_char_id = -1

    def load_tilesets(self, graph_id, good_id, char_id, asset_dir):
        """Load tileset BMPs by ID if not already loaded."""
        import os
        if graph_id != self._loaded_graph_id:
            path = os.path.join(asset_dir, f"G{graph_id}.bmp")
            if not os.path.exists(path):
                path = os.path.join(asset_dir, f"g{graph_id}.bmp")
            if os.path.exists(path):
                self.graph_bmp = pygame.image.load(path).convert()
                self.graph_bmp.set_colorkey(COLOR_TRANSPARENT)
                self._loaded_graph_id = graph_id

        if good_id != self._loaded_good_id:
            path = os.path.join(asset_dir, f"G{good_id}.bmp")
            if not os.path.exists(path):
                path = os.path.join(asset_dir, f"g{good_id}.bmp")
            if os.path.exists(path):
                self.good_bmp = pygame.image.load(path).convert()
                self.good_bmp.set_colorkey(COLOR_TRANSPARENT)
                self._loaded_good_id = good_id

        if char_id != self._loaded_char_id:
            path = os.path.join(asset_dir, f"G{char_id}.bmp")
            if not os.path.exists(path):
                path = os.path.join(asset_dir, f"g{char_id}.bmp")
            if os.path.exists(path):
                self.char_bmp = pygame.image.load(path).convert()
                self.char_bmp.set_colorkey(COLOR_TRANSPARENT)
                self._loaded_char_id = char_id

    def draw_board(self, world):
        """
        Draw the 5x5 tile viewport.
        Matches original Drawbrd: for A=1..5, B=1..5, tile at [A-3+MainX][B-3+MainY].
        """
        self.viewport.fill(COLOR_BLACK)
        if not self.graph_bmp:
            return

        main_x = world.main_x
        main_y = world.main_y
        arr_x = world.arr_x
        arr_y = world.arr_y

        for a in range(1, VIEWPORT_TILES + 1):
            for b in range(1, VIEWPORT_TILES + 1):
                tx = a - 3 + main_x
                ty = b - 3 + main_y

                # Bounds check (matching original: A-4+MainX < ArrX and B-4+MainY < ArrY
                # and A-3+MainX > 0 and B-3+MainY > 0)
                if tx < 1 or ty < 1 or tx > arr_x or ty > arr_y:
                    continue

                gx = world.graph_array_x[tx][ty]
                gy = world.graph_array_y[tx][ty]

                # Source rect from tileset
                src_rect = pygame.Rect(gx * TILE_W, gy * TILE_H, TILE_W, TILE_H)
                # Dest rect on viewport
                dst_rect = pygame.Rect(
                    (a - 1) * DISPLAY_TILE_W,
                    (b - 1) * DISPLAY_TILE_H,
                    DISPLAY_TILE_W,
                    DISPLAY_TILE_H,
                )

                # Scale tile from source to destination
                try:
                    tile_surf = self.graph_bmp.subsurface(src_rect)
                    scaled = pygame.transform.scale(tile_surf, (DISPLAY_TILE_W, DISPLAY_TILE_H))
                    self.viewport.blit(scaled, dst_rect.topleft)
                except (ValueError, pygame.error):
                    pass

                # Draw NPC characters from char_array
                cx = world.char_array_x[tx][ty]
                cy = world.char_array_y[tx][ty]
                if cx > 0 and self.char_bmp:
                    self._draw_sprite(self.char_bmp, cy, cx, a, b)

    def draw_character(self, x, y, main_dir, val1, world):
        """
        Draw the main player character at grid position (x, y) on the viewport.
        x, y are viewport grid positions (1-5), typically (3, 3) for center.
        main_dir = direction (1=S, 2=N, 3=E, 4=W) -> column in good_bmp
        val1 = animation frame row in good_bmp
        """
        if not self.good_bmp:
            return
        self._draw_sprite(self.good_bmp, main_dir, val1, x, y)

    def _draw_sprite(self, source_bmp, sprite_col, sprite_row, grid_x, grid_y):
        """
        Draw a sprite from source_bmp at viewport grid position.
        sprite_col, sprite_row are 1-based tile coordinates in the BMP.
        grid_x, grid_y are 1-based viewport grid positions.

        Matches original pixel-by-pixel transparent drawing with 2x scale
        and -15 pixel Y offset (SPRITE_Y_OFFSET).
        """
        src_x = (sprite_col - 1) * TILE_W
        src_y = (sprite_row - 1) * TILE_H

        try:
            sprite_surf = source_bmp.subsurface(
                pygame.Rect(src_x, src_y, TILE_W, TILE_H)
            )
        except (ValueError, pygame.error):
            return

        # Scale 2x and preserve transparency
        scaled = pygame.transform.scale(sprite_surf, (DISPLAY_TILE_W, DISPLAY_TILE_H))
        scaled.set_colorkey(COLOR_TRANSPARENT)

        # Position on viewport with Y offset
        dest_x = (grid_x - 1) * DISPLAY_TILE_W
        dest_y = (grid_y - 1) * DISPLAY_TILE_H - SPRITE_Y_OFFSET

        self.viewport.blit(scaled, (dest_x, dest_y))

    def draw_man(self, sprite_x, sprite_y, pos_x, pos_y, source_type, world=None):
        """
        Draw a character/NPC at viewport position.
        sprite_x, sprite_y: sprite coordinates (1-based) in the BMP.
        pos_x, pos_y: viewport grid position (1-based).
        source_type: 0 = char_bmp, 5 = good_bmp (matching original t parameter).
        """
        if source_type == 0:
            bmp = self.char_bmp
        elif source_type == 5:
            bmp = self.good_bmp
        else:
            bmp = self.char_bmp

        if not bmp:
            return

        self._draw_sprite(bmp, sprite_x, sprite_y, pos_x, pos_y)

    def draw_battle(self, world, party, enemies):
        """Draw the battle screen with all combatants."""
        # First clear enemy positions in char_array, then set living enemies
        for enemy in enemies:
            world.char_array_x[enemy.bat_x][enemy.bat_y] = 0
            world.char_array_y[enemy.bat_x][enemy.bat_y] = 0

        for enemy in enemies:
            if enemy.alive:
                world.char_array_x[enemy.bat_x][enemy.bat_y] = enemy.graph_x
                world.char_array_y[enemy.bat_x][enemy.bat_y] = enemy.graph_y

        # Draw the base board
        self.draw_board(world)

        # Draw player characters on top
        main_x = world.main_x
        main_y = world.main_y

        for i, member in enumerate(party.members):
            if not member.alive:
                continue
            vx = member.bat_x - main_x + 3
            vy = member.bat_y - main_y + 3
            if 1 <= vx <= 5 and 1 <= vy <= 5:
                self.draw_man(member.graph_x, member.graph_y, vx, vy, 5)

    def draw_lifebar(self, current_hp, max_hp, name, type_name, moves_left, is_enemy=False):
        """Draw the HP bar at the top of the viewport."""
        bar_area = pygame.Rect(0, 0, VIEWPORT_W, 24)
        self.viewport.fill(COLOR_BLACK, bar_area)

        # Red background (max HP)
        max_bar_w = min(max_hp * 2, VIEWPORT_W - 4)
        pygame.draw.rect(self.viewport, COLOR_RED, (2, 2, max_bar_w, 11))

        # Green foreground (current HP)
        cur_bar_w = min(max(current_hp, 0) * 2, max_bar_w)
        pygame.draw.rect(self.viewport, COLOR_GREEN, (2, 2, cur_bar_w, 11))

        # Border
        text_color = COLOR_RED if is_enemy else COLOR_WHITE
        pygame.draw.rect(self.viewport, COLOR_WHITE, (0, 0, VIEWPORT_W, 24), 1)
        pygame.draw.rect(self.viewport, COLOR_WHITE, (2, 2, max_bar_w, 11), 1)

        # Text
        font = pygame.font.SysFont('arial', 12)
        hp_text = font.render(f"{current_hp}/{max_hp}", True, text_color)
        self.viewport.blit(hp_text, (max_bar_w + 5, 0))

        info_text = font.render(f"{name} {type_name} - Moves = {moves_left}", True, text_color)
        self.viewport.blit(info_text, (2, 13))

    def wipe(self, color_type):
        """Wipe the viewport with a color. 1=white, 2=black, 3=yellow."""
        if color_type == 1:
            self.viewport.fill(COLOR_WHITE)
        elif color_type == 2:
            self.viewport.fill(COLOR_BLACK)
        elif color_type == 3:
            self.viewport.fill(COLOR_YELLOW)

    def view_picture(self, source_type, x, y, val1=1):
        """
        Get a 56x72 portrait surface.
        source_type: 0=char_bmp, 1=good_bmp (uses val1 for row), 2=graph_bmp
        x, y: 1-based tile coords in the source BMP.
        """
        if source_type == 1 and self.good_bmp:
            src_rect = pygame.Rect(0, (val1 - 1) * TILE_H, TILE_W, TILE_H)
            bmp = self.good_bmp
        elif source_type == 0 and self.char_bmp:
            src_rect = pygame.Rect((x - 1) * TILE_W, (y - 1) * TILE_H, TILE_W, TILE_H)
            bmp = self.char_bmp
        elif source_type == 2 and self.graph_bmp:
            src_rect = pygame.Rect((x - 1) * TILE_W, (y - 1) * TILE_H, TILE_W, TILE_H)
            bmp = self.graph_bmp
        else:
            surf = pygame.Surface((DISPLAY_TILE_W, DISPLAY_TILE_H))
            surf.fill(COLOR_BLACK)
            return surf

        try:
            tile = bmp.subsurface(src_rect)
            return pygame.transform.scale(tile, (DISPLAY_TILE_W, DISPLAY_TILE_H))
        except (ValueError, pygame.error):
            surf = pygame.Surface((DISPLAY_TILE_W, DISPLAY_TILE_H))
            surf.fill(COLOR_BLACK)
            return surf

    def fadeout(self, world, screen, screen_rect, clock):
        """Fade out effect - shrinks tiles inward with black bars."""
        if not self.graph_bmp:
            return
        main_x = world.main_x
        main_y = world.main_y
        arr_x = world.arr_x
        arr_y = world.arr_y

        for c in range(1, 20):
            self.viewport.fill(COLOR_BLACK)
            for a in range(1, VIEWPORT_TILES + 1):
                for b in range(1, VIEWPORT_TILES + 1):
                    tx = a - 3 + main_x
                    ty = b - 3 + main_y
                    if tx < 1 or ty < 1 or tx > arr_x or ty > arr_y:
                        continue
                    gx = world.graph_array_x[tx][ty]
                    gy = world.graph_array_y[tx][ty]
                    src_rect = pygame.Rect(gx * TILE_W, gy * TILE_H, TILE_W, TILE_H)
                    # Shrinking destination rect
                    dx = (a - 1) * DISPLAY_TILE_W + c
                    dy = (b - 1) * DISPLAY_TILE_H + (c - 1) * 2
                    dw = DISPLAY_TILE_W - (c - 1) * 2 - c
                    dh = DISPLAY_TILE_H - (c - 1) * 2 - (c - 1) * 2
                    if dw > 0 and dh > 0:
                        try:
                            tile = self.graph_bmp.subsurface(src_rect)
                            scaled = pygame.transform.scale(tile, (dw, dh))
                            self.viewport.blit(scaled, (dx, dy))
                        except (ValueError, pygame.error):
                            pass
            screen.blit(self.viewport, screen_rect.topleft)
            pygame.display.flip()
            pygame.time.delay(50)
        self.wipe(2)

    def fadein(self, world, screen, screen_rect, clock):
        """Fade in effect - tiles expand outward from center."""
        if not self.graph_bmp:
            return
        main_x = world.main_x
        main_y = world.main_y
        arr_x = world.arr_x
        arr_y = world.arr_y

        for c in range(1, 20):
            d = 20 - c
            self.viewport.fill(COLOR_BLACK)
            for a in range(1, VIEWPORT_TILES + 1):
                for b in range(1, VIEWPORT_TILES + 1):
                    tx = a - 3 + main_x
                    ty = b - 3 + main_y
                    if tx < 1 or ty < 1 or tx > arr_x or ty > arr_y:
                        continue
                    gx = world.graph_array_x[tx][ty]
                    gy = world.graph_array_y[tx][ty]
                    src_rect = pygame.Rect(gx * TILE_W, gy * TILE_H, TILE_W, TILE_H)
                    dx = (a - 1) * DISPLAY_TILE_W + d - 2
                    dy = (b - 1) * DISPLAY_TILE_H + (d - 1) * 2 - 2
                    dw = DISPLAY_TILE_W - (d - 1) * 2 - d + 3
                    dh = DISPLAY_TILE_H - (d - 1) * 2 - (d - 1) * 2 + 3
                    if dw > 0 and dh > 0:
                        try:
                            tile = self.graph_bmp.subsurface(src_rect)
                            scaled = pygame.transform.scale(tile, (dw, dh))
                            self.viewport.blit(scaled, (dx, dy))
                        except (ValueError, pygame.error):
                            pass
            screen.blit(self.viewport, screen_rect.topleft)
            pygame.display.flip()
            pygame.time.delay(50)

    def fadeout2(self, world, screen, screen_rect, clock):
        """Fade out 2 - zoom effect expanding outward."""
        if not self.graph_bmp:
            return
        main_x = world.main_x
        main_y = world.main_y
        arr_x = world.arr_x
        arr_y = world.arr_y

        for c in range(1, 57):
            self.wipe(2)
            for a in range(1, VIEWPORT_TILES + 1):
                for b in range(1, VIEWPORT_TILES + 1):
                    tx = a - 3 + main_x
                    ty = b - 3 + main_y
                    if tx < 1 or ty < 1 or tx > arr_x or ty > arr_y:
                        continue
                    gx = world.graph_array_x[tx][ty]
                    gy = world.graph_array_y[tx][ty]
                    src_rect = pygame.Rect(gx * TILE_W, gy * TILE_H, TILE_W, TILE_H)
                    dx = (a - 1) * DISPLAY_TILE_W + (c - 1) * 5
                    dy = (b - 1) * DISPLAY_TILE_H + (c - 1) * 5
                    dw = DISPLAY_TILE_W + c * 5 - (c - 1) * 5
                    dh = DISPLAY_TILE_H + c * 5 - (c - 1) * 5
                    if dw > 0 and dh > 0:
                        try:
                            tile = self.graph_bmp.subsurface(src_rect)
                            scaled = pygame.transform.scale(tile, (dw, dh))
                            self.viewport.blit(scaled, (dx, dy))
                        except (ValueError, pygame.error):
                            pass
            screen.blit(self.viewport, screen_rect.topleft)
            pygame.display.flip()
            pygame.time.delay(30)
        self.wipe(2)
