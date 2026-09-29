# SHARPER 2025 – Indovina: quale attrezzo pesca cosa?

A small memory/matching game built with [pygame](https://www.pygame.org/) for the SHARPER 2025 European Researchers' Night.
Players match each **fishing gear** (top row) with the **species it catches** (bottom row) – e.g. *nassa*, *tramaglio*, *strascico*, *draga idraulica*… paired with *seppia*, *canocchia*, *sogliola*, *vongole*…

*Gioco di memoria per SHARPER 2025: abbina ogni attrezzo da pesca alla specie che cattura.*

## How it works

- At the start all cards are shown face-up for a few seconds, then flipped.
- Click one gear card and one species card: if they belong together they stay matched.
- Match all pairs as fast as possible; the fastest times go into a local leaderboard (`leaderboard.json`, created automatically).

## Run it

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app_sharper_2025.py
```

The game opens in a resizable window sized to your screen. Close the window to quit.

## Project structure

```
app_sharper_2025.py   # the game
placeholder/          # card images and backgrounds
requirements.txt
```

## License

Code released under the [MIT License](LICENSE).
