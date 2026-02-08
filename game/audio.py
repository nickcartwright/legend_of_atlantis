"""Audio management for Legend of Atlantis - MIDI music and WAV sound effects."""

import os
import pygame
from game.constants import SOUND_DIR

MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'music')


class Audio:
    """Handles music playback and sound effects."""

    def __init__(self):
        self.music_playing = False
        self.current_music = ''
        self._sound_move = None
        self._sound_stairs = None
        self._initialized = False
        self._key_lookup = {}  # maps key (lowercase) -> actual filename from music.ini

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
            w1_path = os.path.join(SOUND_DIR, "w1.WAV")
            if not os.path.exists(w1_path):
                w1_path = os.path.join(SOUND_DIR, "w1.wav")
            w2_path = os.path.join(SOUND_DIR, "w2.wav")
            if not os.path.exists(w2_path):
                w2_path = os.path.join(SOUND_DIR, "w2.WAV")

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

    def set_music_data(self, music_data):
        """Store the key lookup from music.ini so all references resolve through it."""
        self._key_lookup = music_data.get('_key_lookup', {})

    def play_music(self, filename):
        """
        Play a music file. Resolves through music.ini key lookup first,
        so swapping tracks only requires changing music.ini.
        """
        if not self._initialized:
            return

        # Resolve through music.ini: if filename matches a Key, use the configured Name
        basename = os.path.basename(filename)
        resolved = self._key_lookup.get(basename.lower(), basename)
        path = os.path.join(MUSIC_DIR, resolved)

        if not os.path.exists(path):
            # Try case-insensitive match in midi dir
            try:
                for f in os.listdir(MUSIC_DIR):
                    if f.lower() == resolved.lower():
                        path = os.path.join(MUSIC_DIR, f)
                        break
            except OSError:
                pass

        if not os.path.exists(path):
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
