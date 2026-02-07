"""Audio management for Legend of Atlantis - MIDI music and WAV sound effects."""

import os
import pygame
from game.constants import ASSET_DIR


class Audio:
    """Handles music playback and sound effects."""

    def __init__(self):
        self.music_playing = False
        self.current_music = ''
        self._sound_move = None
        self._sound_stairs = None
        self._initialized = False

    def init(self):
        """Initialize the audio system."""
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._initialized = True
        except pygame.error:
            print("Warning: Could not initialize audio system")
            self._initialized = False

        # Try to load sound effects
        if self._initialized:
            w1_path = os.path.join(ASSET_DIR, "w1.WAV")
            if not os.path.exists(w1_path):
                w1_path = os.path.join(ASSET_DIR, "w1.wav")
            w2_path = os.path.join(ASSET_DIR, "w2.wav")
            if not os.path.exists(w2_path):
                w2_path = os.path.join(ASSET_DIR, "w2.WAV")

            try:
                if os.path.exists(w1_path):
                    self._sound_move = pygame.mixer.Sound(w1_path)
                    self._sound_move.set_volume(0.3)
            except pygame.error:
                pass

            try:
                if os.path.exists(w2_path):
                    self._sound_stairs = pygame.mixer.Sound(w2_path)
                    self._sound_stairs.set_volume(0.3)
            except pygame.error:
                pass

    def play_music(self, filename):
        """
        Play a music file. Supports MIDI (.mid) and OGG (.ogg).
        filename can be just the name (e.g., 'movement2.mid') or a full path.
        """
        if not self._initialized:
            return

        # Build the full path
        if os.path.isabs(filename):
            path = filename
        else:
            path = os.path.join(ASSET_DIR, filename)

        if not os.path.exists(path):
            # Try .ogg version in game/assets/music/ directory
            ogg_name = os.path.splitext(os.path.basename(filename))[0] + '.ogg'
            ogg_path = os.path.join(os.path.dirname(ASSET_DIR), 'game', 'assets', 'music', ogg_name)
            if os.path.exists(ogg_path):
                path = ogg_path
            else:
                return

        try:
            if self.current_music == path and self.music_playing:
                return
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)  # Loop indefinitely
            self.music_playing = True
            self.current_music = path
        except pygame.error:
            pass

    def play_music_by_id(self, music_id, music_data):
        """Play music by ID using the music.ini data."""
        if music_id > 0 and music_id in music_data:
            self.play_music(music_data[music_id]['name'])

    def stop_music(self):
        """Stop music playback."""
        if not self._initialized:
            return
        try:
            pygame.mixer.music.stop()
            self.music_playing = False
        except pygame.error:
            pass

    def rewind_music(self):
        """Rewind and replay the current music."""
        if not self._initialized:
            return
        try:
            pygame.mixer.music.rewind()
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def play_move_sound(self):
        """Play the movement sound effect."""
        if self._sound_move:
            try:
                self._sound_move.play()
            except pygame.error:
                pass

    def play_stairs_sound(self):
        """Play the stairs/water sound effect."""
        if self._sound_stairs:
            try:
                self._sound_stairs.play()
            except pygame.error:
                pass

    @property
    def music_filename(self):
        return self.current_music
