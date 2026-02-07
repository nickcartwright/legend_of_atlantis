# The Legend of Atlantis

*A tile-based RPG originally written in Delphi Pascal, circa 2000. Resurrected in Python.*

---

## About the Game

The Legend of Atlantis is a top-down, tile-based RPG set on the mythical floating continent of Atlantis. You play as a young hero, awakened by a distant noise and thrust into an ancient conflict between gods, priests, and daemonic forces.

The story opens with a sweeping cinematic: Atlantis was once peaceful, ruled by an order of priest-magicians called the Elite, who discovered a sealed power beneath the continent and grew corrupt feeding on it. The gods locked the power away, and generations forgot it existed, until a dark army arrived to break the seal. War consumed Atlantis. In the midst of it, the King received a vision of a boy who would save the world. A messenger named KORAL was sent to find that boy. That boy is you.

From the home town of Knashmore, you journey through underground passages, the magic city of Atlantis itself, the throne room of its castle, and into the realm of the Red Priest. Along the way you recruit companions -- RUNEL the warrior, ANRIKO the vicar healer, DANTO the wizard -- fight turn-based battles on tactical grids, collect swords and staves and herbs, and piece together a story told through over 160 scripted story sequences.

## What Makes This Special

This game was written by a kid. You can tell, and that's what makes it wonderful.

The spelling is charmingly inconsistent -- "alcamists", "monstors", "Suddleny", "forgotton", "Transcendedt", "wodden". The item descriptions are earnest and direct: *"A small sword for a HERO"*, *"A wodden staff for a VICR"*. A character class is literally called "BRDM" (bard-man?). When you can't use a quest item, the game tells you *"Knowone has the item"*. The music credits include *"Found on the Internet...."* and the composer signs off as *"Nick 8) - Nevil Software"*.

But underneath the rough edges is a remarkably ambitious piece of work. The developer built:

- A **custom scripting engine** with 29 command types that handles dialogue, cutscenes, camera movement, screen fades, tile modification, inventory management, shops, branching story paths, and party management -- all driven by numbered text files
- A **conditional story branching system** using a 101x101 global flags array, where story files can check flag values and jump to entirely different scripts
- A **turn-based tactical battle system** with movement points, attack quality rolls, magic casting, consumable items, enemy AI with multiple tactics, XP and leveling
- **17 explorable locations** ranging from small 5x5 rooms to a sprawling 50x32 city, with 2 battle arenas
- An **equipment and class system** with 14 character types (HERO, WARR, VICR, WIZD, DRGN, DWRF, OGRE, BRDM, NINJ, ANGL, ELDR, DETH, ROBT, and ????)
- **Save/load support**, multiple party members, a shop economy, fade transitions, portrait displays, MIDI music, and a scrolling cinematic opening

All in a single 4,038-line Delphi Pascal file called `title.pas`.

That's not a toy project. That's a kid who loved RPGs and taught themselves to build one from scratch, inventing their own scripting language, their own data formats, their own tile engine. The `help.txt` file in the data directory is the developer's own notes to themselves about how their scripting commands work, complete with *"Experement..."* next to the wipe command they weren't sure about. It's a snapshot of someone learning by doing, building something they cared about, and having fun doing it.

## This Rewrite

The original game was built with Borland Delphi and only runs on vintage Windows systems. This Python/Pygame rewrite makes it playable on modern machines while keeping every original asset untouched -- the same BMP spritesheets, MIDI music files, story scripts, location maps, and data files from ~25 years ago.

### Running

```bash
pip install pygame
python run.py
```

### Controls

| Key | Action |
|-----|--------|
| Arrow keys | Move / Battle movement |
| Space | End turn (battle) |
| I | Inventory |
| L | Look around |
| H | Help |
| F5 | Save |
| F9 | Load |
| ESC | Quit |

### Architecture

```
game/
  main.py          # Game loop and state management
  constants.py     # Tile sizes, colors, directions, type tables
  data_loader.py   # INI, location, battle, and story file parsers
  renderer.py      # Tile viewport, sprites, fades, battle screen
  world.py         # Location state, movement, collision
  battle.py        # Turn-based combat, enemy AI, damage calc
  story.py         # 29-command script interpreter
  party.py         # Characters, stats, inventory, leveling
  ui.py            # Panels, menus, shops, text display
  save_load.py     # Game state serialization
  audio.py         # MIDI music and sound effects
```

All original game data lives in `original_code/Data/` and `original_code/` exactly as it was.

---

*Originally developed by Nevil Software. Python rewrite by Claude Code.*
