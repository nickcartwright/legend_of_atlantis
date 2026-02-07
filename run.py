#!/usr/bin/env python3
"""Launch script for The Legend of Atlantis."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.main import Game


def main():
    game = Game()
    try:
        game.run()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
