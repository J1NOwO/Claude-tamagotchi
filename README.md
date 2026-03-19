# Clodie 🤖 - Claude AI Tamagotchi

A pixel-art pet raising game built with Python + tkinter.

## Features
- 16×16 pixel-art character with 3 states: HAPPY / SAD / SLEEP
- 4 stats: Hunger, Happiness, Energy, Cleanliness (decay every 10 s)
- 5 action buttons: Feed · Play · Sleep · Wash · Chat
- Mini-game: timing click when playing
- Level-up every 7 in-game days with popup
- Night mode when energy ≤ 30
- Auto-save to `claude_pet_save.json`
- Game over + gravestone screen on death

## Run
```bash
python3 clodie_game.py
```

## Build standalone .exe
```bash
pip install pyinstaller
pyinstaller --onefile --windowed clodie_game.py
```

## Tech Stack
- Python 3.8+
- tkinter (stdlib only, no external packages)
- Canvas.create_rectangle() for pixel rendering (SCALE=9)
