"""Battle system for Legend of Atlantis."""

import random
import os
from collections import deque
import pygame
from game.constants import (
    TYPE_NAMES, DIR_SOUTH, DIR_NORTH, DIR_EAST, DIR_WEST,
)
from game.party import Enemy


ATTACK_DESCRIPTIONS = {
    1: 'Misses!',
    2: 'Strikes with a small attack',
    3: 'Strikes',
    4: 'Strikes with a MASSIVE ATTACK!',
}


class BattleSystem:
    """Manages turn-based battle encounters."""

    def __init__(self, game):
        self.game = game
        self.enemies = []   # List of Enemy objects
        self.enemy_count = 0
        self.win_story = 0
        self.pmoving = 0    # Current player index (1-based)
        self.attack_dir = 0  # Direction of last attempted attack

    def start_battle(self, battle_data, enemy_definitions):
        """Initialize a battle from battle data."""
        party = self.game.party
        world = self.game.world

        # Set player starting positions and restore HP/MP
        for i, (x, y) in enumerate(battle_data['player_positions']):
            if i < party.number:
                member = party.get(i + 1)
                member.bat_x = x
                member.bat_y = y
                member.life = member.hp
                member.move_left = member.move
                member.magic_left = member.magic

        # Load enemies
        self.enemies = []
        self.enemy_count = battle_data['enemy_count']
        for edata in battle_data['enemies']:
            enemy = Enemy()
            ref_id = edata['ref_id']
            enemy.ref_id = ref_id
            enemy.bat_x = edata['bat_x']
            enemy.bat_y = edata['bat_y']
            enemy.tactics = edata['tactics']

            if ref_id in enemy_definitions:
                edef = enemy_definitions[ref_id]
                enemy.name = edef['name']
                enemy.type = edef['type']
                enemy.equipped_a = edef['equipped_a']
                enemy.equipped_d = edef['equipped_d']
                enemy.hp = edef['hp']
                enemy.life = edef['hp']
                enemy.attack = edef['attack']
                enemy.defence = edef['defence']
                enemy.magic = edef['magic']
                enemy.resilience = edef['resilience']
                enemy.graph_x = edef['graph_x']
                enemy.graph_y = edef['graph_y']
                enemy.move = edef['move']
                enemy.move_left = edef['move']

            self.enemies.append(enemy)

        self.win_story = battle_data['win_story']

        # Start first player's turn
        self.pmoving = 0
        self._set_pmove()

        # Recommend saving
        self._note("It is reccomended you save the game now incase you die! "
                   "as you cannot save the game during a battle.", att=5)

    def _note(self, text, att=1):
        """Show a note during battle."""
        self.game.renderer.draw_board(self.game.world)
        self.game.renderer.draw_battle(self.game.world, self.game.party, self.enemies)
        self.game.screen.blit(self.game.renderer.viewport, self.game.viewport_rect.topleft)
        self.game.ui.draw_panel(self.game.party, self.game.world, self.game.items_data)
        player_name = self.game.party.get(1).name if self.game.party.number > 0 else ''
        if att == 5:
            self.game.ui.show_note_long(text, self.game.speed, player_name)
        else:
            self.game.ui.show_note(text, self.game.speed, player_name)

    def _redraw(self):
        """Redraw the battle screen."""
        reachable, active_pos = self.get_reachable_tiles()
        self.game.renderer.draw_battle(
            self.game.world, self.game.party, self.enemies, reachable, active_pos
        )
        self._draw_current_lifebar()
        self.game.screen.blit(self.game.renderer.viewport, self.game.viewport_rect.topleft)
        self.game.ui.draw_panel(self.game.party, self.game.world, self.game.items_data)
        pygame.display.flip()

    def _draw_current_lifebar(self):
        """Draw lifebar for current moving player."""
        if 1 <= self.pmoving <= self.game.party.number:
            member = self.game.party.get(self.pmoving)
            self.game.renderer.draw_lifebar(
                member.life, member.hp, member.name, member.type_name,
                member.move_left, is_enemy=False
            )

    def _draw_enemy_lifebar(self, enemy_idx):
        """Draw lifebar for an enemy."""
        if 0 <= enemy_idx < len(self.enemies):
            enemy = self.enemies[enemy_idx]
            self.game.renderer.draw_lifebar(
                enemy.life, enemy.hp, enemy.name, enemy.type_name,
                enemy.move_left, is_enemy=True
            )

    def _set_pmove(self):
        """Advance to next player with movement points, or trigger enemy turn."""
        party = self.game.party
        world = self.game.world

        member = party.get(self.pmoving) if self.pmoving > 0 else None
        if member and member.move_left <= 0:
            # Reset move for current, advance
            member.move_left = member.move
            if self.pmoving < party.number:
                self.pmoving += 1
            else:
                # All players done - enemy turn
                self._enemy_turn()
                self.pmoving = 1
                first = party.get(1)
                if first:
                    first.move_left = first.move

            # Skip dead players
            attempts = 0
            while self.pmoving <= party.number and attempts < party.number + 1:
                pm = party.get(self.pmoving)
                if pm and pm.alive:
                    break
                if self.pmoving < party.number:
                    self.pmoving += 1
                else:
                    self._enemy_turn()
                    self.pmoving = 1
                attempts += 1

        if self.pmoving == 0:
            self.pmoving = 1

        # Center on current player
        member = party.get(self.pmoving)
        if member and self.game.world.battle:
            world.main_x = member.bat_x
            world.main_y = member.bat_y

    def get_reachable_tiles(self):
        """BFS flood-fill from active player's position up to move_left steps.

        Returns (reachable_set, (active_x, active_y)) where reachable_set is a
        set of (x, y) tuples the player can move to or attack.
        Returns (set(), None) if no active player.
        """
        party = self.game.party
        world = self.game.world

        member = party.get(self.pmoving)
        if not member or not member.alive:
            return set(), None

        start = (member.bat_x, member.bat_y)
        active_pos = start
        move_left = member.move_left

        if move_left <= 0:
            return set(), active_pos

        # Collect friendly positions (excluding current player)
        friendly_positions = set()
        for i in range(1, party.number + 1):
            if i == self.pmoving:
                continue
            other = party.get(i)
            if other and other.alive:
                friendly_positions.add((other.bat_x, other.bat_y))

        # Collect enemy positions (attackable, so included in reachable)
        enemy_positions = set()
        for enemy in self.enemies:
            if enemy.alive:
                enemy_positions.add((enemy.bat_x, enemy.bat_y))

        reachable = set()
        # BFS: (x, y, steps_remaining)
        visited = {start: move_left}
        queue = deque([(start[0], start[1], move_left)])

        while queue:
            x, y, steps = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                val = world.get_val(nx, ny)
                if val == 0:
                    continue  # blocked tile

                pos = (nx, ny)

                # Friendly units block movement
                if pos in friendly_positions:
                    continue

                # Enemy tiles are reachable (attackable) but don't propagate through
                if pos in enemy_positions:
                    if pos not in reachable:
                        reachable.add(pos)
                    continue

                # Normal walkable tile with no NPC
                char_at = world.get_char(nx, ny)
                if char_at != 0:
                    continue  # NPC blocks

                new_steps = steps - 1
                if pos in visited and visited[pos] >= new_steps:
                    continue  # already visited with equal or more steps

                visited[pos] = new_steps
                reachable.add(pos)
                if new_steps > 0:
                    queue.append((nx, ny, new_steps))

        return reachable, active_pos

    def handle_move(self, direction):
        """Handle player movement in battle. Returns True if action was taken."""
        party = self.game.party
        world = self.game.world

        self.attack_dir = direction

        member = party.get(self.pmoving)
        if not member or member.move_left <= 0:
            return False

        # Calculate target position
        dx, dy = 0, 0
        if direction == DIR_EAST:
            dx = 1
        elif direction == DIR_WEST:
            dx = -1
        elif direction == DIR_SOUTH:
            dy = 1
        elif direction == DIR_NORTH:
            dy = -1

        target_x = member.bat_x + dx
        target_y = member.bat_y + dy

        # Check for friendly units at target
        friendly_at_target = False
        for i in range(1, party.number + 1):
            other = party.get(i)
            if other and other.alive and i != self.pmoving:
                if other.bat_x == target_x and other.bat_y == target_y:
                    friendly_at_target = True
                    break

        # Check for enemy at target
        enemy_at_target = None
        for enemy in self.enemies:
            if enemy.alive and enemy.bat_x == target_x and enemy.bat_y == target_y:
                enemy_at_target = enemy
                break

        # If enemy, show attack prompt
        if enemy_at_target:
            return self._player_attack_enemy(enemy_at_target)

        # If friendly, could heal
        if friendly_at_target:
            # Show heal/use option - for now just skip
            return False

        # Try to move
        val = world.get_val(target_x, target_y)
        char_at = world.get_char(target_x, target_y)

        if val == 1 and char_at == 0 and not friendly_at_target:
            member.bat_x = target_x
            member.bat_y = target_y
            member.move_left -= 1

            if member.move_left <= 0:
                self._redraw()
                pygame.time.delay(1000)

            world.main_x = member.bat_x
            world.main_y = member.bat_y
            self._set_pmove()
            self._redraw()
            return True

        return False

    def handle_stay(self):
        """Player chooses to stay (skip turn)."""
        member = self.game.party.get(self.pmoving)
        if member:
            member.move_left = 0
        self._set_pmove()
        self._redraw()

    def _player_attack_enemy(self, enemy):
        """Execute player attack on an enemy."""
        party = self.game.party
        member = party.get(self.pmoving)
        items_data = self.game.items_data

        # Play attack music
        old_music = self.game.audio.music_filename
        self.game.audio.play_music("attack.mid")

        self._note(f"{member.name} {member.type_name} Attacks "
                  f"{enemy.name} {enemy.type_name}", att=5)

        # Calculate attack
        pygame.time.delay(500)
        att = random.randint(0, 49)
        if att < 5:
            dec = 1
        elif att < 15:
            dec = 2
        elif att < 45:
            dec = 3
        else:
            dec = 4

        self._note(f"{member.name} {ATTACK_DESCRIPTIONS[dec]}.......", att=5)

        size = member.attack
        size = size - 2 + random.randint(0, 2)

        if dec == 3:
            # Add weapon bonus
            if member.equipped_a > 0:
                weapon_item = member.get_item(member.equipped_a)
                if weapon_item in items_data:
                    size += items_data[weapon_item]['value']
        elif dec == 4:
            size *= 2
        elif dec == 2:
            size -= 3

        size -= enemy.defence
        if size <= 0:
            size = 1
        if dec == 1:
            size = 0

        self._note(f".......With an attack of {size} HP", att=5)

        pygame.time.delay(1000)
        enemy.life -= size

        # Show enemy lifebar
        enemy_idx = self.enemies.index(enemy)
        self._draw_enemy_lifebar(enemy_idx)
        self.game.screen.blit(self.game.renderer.viewport, self.game.viewport_rect.topleft)
        pygame.display.flip()
        pygame.time.delay(2000)

        self._draw_current_lifebar()
        self.game.screen.blit(self.game.renderer.viewport, self.game.viewport_rect.topleft)
        pygame.display.flip()
        pygame.time.delay(1000)

        # XP gain
        xp_gain = random.randint(0, size * 2 + dec * 5)
        if xp_gain > 50:
            xp_gain = 49
        if member.exp + xp_gain > 100:
            xp_gain = 100 - self.pmoving  # Matches original bug
        self._note(f"{member.name} gains {xp_gain} experience points!", att=5)
        member.exp += xp_gain

        # Level up check
        if member.exp >= 100:
            messages = party.do_level_up(self.pmoving)
            for msg in messages:
                self._note(msg, att=5)

        # End player's attack turn
        member.move_left = 0

        # Restore music
        if old_music:
            self.game.audio.play_music(old_music)

        self._set_pmove()
        self._redraw()

        # Check win/loss
        self._check_battle_end()
        return True

    def _enemy_turn(self):
        """Execute all enemy movements and attacks."""
        world = self.game.world
        party = self.game.party

        if not world.battle:
            return

        for eidx, enemy in enumerate(self.enemies):
            if not enemy.alive:
                continue

            enemy.move_left = enemy.move

            # Center viewport on this enemy
            world.main_x = enemy.bat_x
            world.main_y = enemy.bat_y
            self.game.renderer.draw_battle(world, party, self.enemies)
            self._draw_enemy_lifebar(eidx)
            self.game.screen.blit(self.game.renderer.viewport, self.game.viewport_rect.topleft)
            self.game.ui.draw_panel(party, world, self.game.items_data)
            pygame.display.flip()
            pygame.time.delay(1000)

            for _ in range(enemy.move):
                if not world.battle:
                    return
                if not enemy.alive:
                    break

                move_dir = self._enemy_ai(enemy)
                attacked = False

                if move_dir > 0:
                    # Clear old position
                    world.char_array_x[enemy.bat_x][enemy.bat_y] = 0
                    world.char_array_y[enemy.bat_x][enemy.bat_y] = 0

                    old_x, old_y = enemy.bat_x, enemy.bat_y
                    if move_dir == 1:
                        enemy.bat_y += 1
                    elif move_dir == 2:
                        enemy.bat_y -= 1
                    elif move_dir == 3:
                        enemy.bat_x += 1
                    elif move_dir == 4:
                        enemy.bat_x -= 1

                    # Check if enemy landed on a player -> attack
                    for pi in range(1, party.number + 1):
                        pm = party.get(pi)
                        if pm and pm.alive:
                            if pm.bat_x == enemy.bat_x and pm.bat_y == enemy.bat_y:
                                attacked = self._enemy_attack_player(enemy, eidx, pm, pi, move_dir)
                                break

                    if attacked:
                        break

                # Update viewport
                world.main_x = enemy.bat_x
                world.main_y = enemy.bat_y
                self.game.renderer.draw_battle(world, party, self.enemies)
                self._draw_enemy_lifebar(eidx)
                self.game.screen.blit(self.game.renderer.viewport, self.game.viewport_rect.topleft)
                self.game.ui.draw_panel(party, world, self.game.items_data)
                pygame.display.flip()
                pygame.time.delay(1000)

                # Process events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        raise SystemExit

            if not world.battle:
                return

    def _enemy_ai(self, enemy):
        """
        Determine enemy movement direction using AI tactics.
        Returns direction (1=down, 2=up, 3=right, 4=left, 0=stay).
        """
        world = self.game.world
        party = self.game.party

        # Check which directions are passable
        can_up = (world.get_val(enemy.bat_x, enemy.bat_y - 1) != 0 and
                  world.get_char(enemy.bat_x, enemy.bat_y - 1) == 0)
        can_down = (world.get_val(enemy.bat_x, enemy.bat_y + 1) != 0 and
                    world.get_char(enemy.bat_x, enemy.bat_y + 1) == 0)
        can_left = (world.get_val(enemy.bat_x - 1, enemy.bat_y) != 0 and
                    world.get_char(enemy.bat_x - 1, enemy.bat_y) == 0)
        can_right = (world.get_val(enemy.bat_x + 1, enemy.bat_y) != 0 and
                     world.get_char(enemy.bat_x + 1, enemy.bat_y) == 0)

        # Check if completely stuck
        stuck = True
        if world.get_val(enemy.bat_x + 1, enemy.bat_y) == 1:
            stuck = False
        if world.get_val(enemy.bat_x - 1, enemy.bat_y) == 1:
            stuck = False
        if world.get_val(enemy.bat_x, enemy.bat_y + 1) == 1:
            stuck = False
        if world.get_val(enemy.bat_x, enemy.bat_y - 1) == 1:
            stuck = False

        if stuck:
            return 0

        endd = 0

        if enemy.tactics in (2, 3):
            # Find nearest player and move toward them
            best_dist = 999
            target = None

            for pi in range(1, party.number + 1):
                pm = party.get(pi)
                if pm and pm.alive:
                    dist = abs(pm.bat_x - enemy.bat_x) + abs(pm.bat_y - enemy.bat_y)
                    if dist < best_dist:
                        best_dist = dist
                        target = pm

            if target:
                # Check for adjacent player (can attack)
                if target.bat_x == enemy.bat_x and target.bat_y == enemy.bat_y - 1:
                    endd = 2  # Move up to attack
                elif target.bat_x == enemy.bat_x and target.bat_y == enemy.bat_y + 1:
                    endd = 1  # Move down to attack
                elif target.bat_y == enemy.bat_y and target.bat_x == enemy.bat_x + 1:
                    endd = 3  # Move right to attack
                elif target.bat_y == enemy.bat_y and target.bat_x == enemy.bat_x - 1:
                    endd = 4  # Move left to attack
                else:
                    # Move toward target
                    dx = target.bat_x - enemy.bat_x
                    dy = target.bat_y - enemy.bat_y

                    if abs(dx) > abs(dy):
                        if dx > 0 and can_right:
                            endd = 3
                        elif dx < 0 and can_left:
                            endd = 4
                        elif dy > 0 and can_down:
                            endd = 1
                        elif dy < 0 and can_up:
                            endd = 2
                    else:
                        if dy > 0 and can_down:
                            endd = 1
                        elif dy < 0 and can_up:
                            endd = 2
                        elif dx > 0 and can_right:
                            endd = 3
                        elif dx < 0 and can_left:
                            endd = 4

        return endd

    def _enemy_attack_player(self, enemy, eidx, player, player_idx, move_dir):
        """Execute enemy attack on a player. Returns True if attack happened."""
        items_data = self.game.items_data

        # Revert enemy position (they bounce back after attacking)
        if move_dir == 1:
            enemy.bat_y -= 1
        elif move_dir == 2:
            enemy.bat_y += 1
        elif move_dir == 3:
            enemy.bat_x -= 1
        elif move_dir == 4:
            enemy.bat_x += 1

        # Play attack music
        old_music = self.game.audio.music_filename
        self.game.audio.play_music("attack.mid")

        self._note(f"{enemy.name} {enemy.type_name} Attacks "
                  f"{player.name} {player.type_name}", att=5)

        pygame.time.delay(500)

        # Calculate attack
        att = random.randint(0, 49)
        if att < 5:
            dec = 1
        elif att < 15:
            dec = 2
        elif att < 45:
            dec = 3
        else:
            dec = 4

        self._note(f"{enemy.name} {ATTACK_DESCRIPTIONS[dec]}.......", att=5)

        size = enemy.attack
        size = size - 2 + random.randint(0, 2)

        if dec == 3:
            if enemy.equipped_a > 0 and enemy.equipped_a in items_data:
                size += items_data[enemy.equipped_a]['value']
        elif dec == 4:
            size *= 2
        elif dec == 2:
            size -= 3

        size -= player.defence
        if size <= 0:
            size = 1
        if dec == 1:
            size = 0

        self._note(f".......With an attack of {size} HP", att=5)

        player.life -= size
        pygame.time.delay(1000)

        # Show player lifebar
        self.pmoving = player_idx
        self._redraw()
        pygame.time.delay(2000)

        self._draw_enemy_lifebar(eidx)
        self.game.screen.blit(self.game.renderer.viewport, self.game.viewport_rect.topleft)
        pygame.display.flip()
        pygame.time.delay(1000)

        # Restore music
        if old_music:
            self.game.audio.play_music(old_music)

        self._check_battle_end()
        return True

    def handle_cast(self, item_id, on_enemy, target_idx):
        """Handle spell casting or item use in battle."""
        party = self.game.party
        member = party.get(self.pmoving)
        items_data = self.game.items_data

        if item_id not in items_data:
            return

        item = items_data[item_id]
        magic_cost = item.get('magic', 0)

        if member.magic_left < magic_cost:
            self._note("You don`t have enough magic to cast the spell", att=5)
            return

        member.magic_left -= magic_cost

        # Play attack music
        old_music = self.game.audio.music_filename
        self.game.audio.play_music("attack.mid")

        if on_enemy:
            target = self.enemies[target_idx]
            self._note(f"{member.name} casts {item['name']} on {target.name}", att=5)
        else:
            target = party.get(target_idx)
            self._note(f"{member.name} casts {item['name']} on {target.name}", att=5)

        # Calculate effect
        chance = random.randint(0, 9)
        if chance == 1:
            self._note("But the spell has no effect...", att=5)
        else:
            amount = item['value'] - 2 + random.randint(0, 3)
            if on_enemy:
                self._note(f"{target.name} is damaged by {amount} hit points!", att=5)
                target.life -= amount
            else:
                self._note(f"{target.name} is healed by {amount} hit points!", att=5)
                target.life = min(target.life + amount, target.hp)

            pygame.time.delay(1000)

            # XP gain
            xp = random.randint(0, 10 + amount * 2)
            if xp > 50:
                xp = 49
            if member.exp + xp > 100:
                xp = 100 - self.pmoving
            self._note(f"{member.name} gains {xp} experience points!", att=5)
            member.exp += xp

            if member.exp >= 100:
                messages = party.do_level_up(self.pmoving)
                for msg in messages:
                    self._note(msg, att=5)

        member.move_left = 0

        if old_music:
            self.game.audio.play_music(old_music)

        self._set_pmove()
        self._redraw()
        self._check_battle_end()

    def _check_battle_end(self):
        """Check if battle is over (win or lose)."""
        # Win: all enemies dead
        all_dead = all(not e.alive for e in self.enemies)
        if all_dead:
            self._game_win()
            return

        # Lose: player 1 dead
        hero = self.game.party.get(1)
        if hero and not hero.alive:
            self._game_lose()
            return

    def _game_win(self):
        """Handle battle victory."""
        self.game.world.battle = False
        # Run win story
        from game.story import run_story
        run_story(self.win_story, self.game)

    def _game_lose(self):
        """Handle battle defeat."""
        hero = self.game.party.get(1)
        self._note(f"{hero.name} is exhausted...", att=5)
        self.game.world.battle = False
        self.game.ui.draw_game_over(hero.name)
        self.game.state = 'game_over'
