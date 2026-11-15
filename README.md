# Polish Tracker

A small web app for keeping track of my nail polish collection, so I don't buy
colors I already have. It runs in my browser from my own computer and uses only
the Python standard library, with no packages to install.

It lets me:

- add a polish with its brand, color name, finish, and number of bottles
- see the whole collection in one table
- search by brand, color name, or finish
- sort by oldest/newest added or by quantity, and filter by finish
- avoid duplicates: adding a brand + color that already exists is refused, and
  the app shows its current quantity with a form to restock it

The collection is saved to `polishes.json` in this folder (not tracked by git).
See [spec.md](spec.md) for the full design.

## Run it

```bash
python3 app.py
```

Then open <http://127.0.0.1:8000> in a browser. Press `Ctrl+C` in the terminal to stop.

## Run the tests

```bash
python3 -m pytest
```

## Files

- `collection.py`: all the logic (adding, duplicates, search, sort, filter, save/load)
- `app.py`: the web server and HTML pages
- `tests/test_collection.py`: pytest tests, each named after the requirement (R1–R6) it checks
