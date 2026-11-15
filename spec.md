# Polish Tracker: Specification

A small web app, run on my own computer, for keeping track of my nail polish
collection so I do not buy duplicates. It uses only the Python standard library.
It runs at <http://127.0.0.1:8000> and stores the collection in a local JSON
file, `polishes.json`, in the project folder.

## Structure

| File | Role |
|------|------|
| `collection.py` | All logic: the polish records, adding, duplicate checking, quantity updates, searching, sorting, filtering, saving, and loading. No web server or HTML code. |
| `app.py` | The web server (`http.server`) and the HTML pages. It calls `collection.py` for everything else. |
| `tests/` | pytest tests for `collection.py`. Each test names the requirement it checks. |
| `polishes.json` | The saved collection. It is created on first save and ignored by git. |

## Data model

The collection is a list of polishes. Each polish is a dictionary:

```json
{"brand": "OPI", "color": "Big Apple Red", "finish": "creme", "quantity": 2, "added": 1}
```

- `brand`, `color`, `finish`: text. Leading and trailing spaces are removed. None of them may be empty.
- `quantity`: a whole number, 0 or more (bottles in stock).
- `added`: a counter that goes up by one with every new polish (1, 2, 3, …). It
  records the order polishes were added, so "oldest to newest" never depends on the
  clock.

Invalid input (an empty field, a negative or non-numeric quantity) raises
`ValueError`. The web page shows that message instead of saving.

## Requirements

### R1: Add a polish with brand, color name, finish, and quantity

- `add_polish(collection, brand, color, finish, quantity)` checks the input,
  builds the record with the next `added` number, appends it, and returns it.
- The home page has an "Add a polish" form with those four fields. When it is
  submitted, the app adds the polish, saves the file, and goes back to the home page.

### R2: Display the whole collection at once

- The home page shows every polish in one table: brand, color, finish, and
  quantity. If the collection is empty, it says so.

### R3: Search by brand, color name, or finish

- `search(collection, query, field)` returns the polishes whose `field`
  (`"brand"`, `"color"`, `"finish"`, or `"any"` for all three) contains the
  query. Matching ignores upper/lower case, so "opi" finds "OPI". An empty query
  returns everything.
- The home page has a search box and a "search in" drop-down.

### R4: Sort by date added or by quantity, and filter by finish

- `sort_polishes(collection, by, descending=False)` sorts by `"added"` (oldest
  to newest by default) or by `"quantity"` (lowest stock first by default).
  `descending=True` reverses the order. It returns a new list and leaves the
  original order alone.
- `filter_by_finish(collection, finish)` keeps only polishes with that finish,
  ignoring case. An empty finish keeps everything.
- `finishes(collection)` lists the distinct finishes, for the drop-down.
- The home page has "sort by" and "finish" drop-downs. Search, filter, and sort
  can be combined (for example, all OPI cremes, lowest stock first).

### R5: Refuse a duplicate brand + color name

- Two polishes are duplicates only when **both** the brand and the color name
  match, ignoring case and surrounding spaces. The same color name from a
  different brand is allowed.
- `find_polish(collection, brand, color)` returns the matching polish or `None`.
- `add_polish` raises `DuplicatePolishError` when a match exists, and the
  collection is not changed. The error carries the existing polish.

### R6: When a duplicate is attempted, show its quantity and allow updating it

- When the add form hits a duplicate, the app shows a page saying the polish
  is already in the collection, with its current quantity, and a form to set a
  new quantity (for restocking).
- `update_quantity(collection, brand, color, quantity)` checks the quantity, sets
  it on the matching polish, and returns it. It raises `KeyError` if there is no
  such polish.
- Each row in the main table also has a small form to change its quantity.

## Saving and loading

- `save_collection(collection, path)` writes the list as JSON. It writes to a
  temporary file first and then swaps it into place, so a crash halfway through
  cannot leave a half-written file.
- `load_collection(path)` reads it back. A missing file means an empty
  collection.
- The app saves after every change, so nothing is lost when the server stops.

## Out of scope

Deleting polishes, editing brand/color/finish, multiple users, and access from
other computers. The server listens only on `127.0.0.1`.
