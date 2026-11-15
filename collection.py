"""Logic for the polish tracker: no web server or HTML lives here.

A collection is a list of polishes. Each polish is a dict:
    {"brand": str, "color": str, "finish": str, "quantity": int, "added": int}
"added" is a counter (1, 2, 3, ...) recording the order polishes were added.
"""

import json
import os
import tempfile

SEARCH_FIELDS = ("brand", "color", "finish")
SORT_KEYS = ("added", "quantity")


class DuplicatePolishError(Exception):
    """Raised when adding a polish whose brand and color already exist (R5)."""

    def __init__(self, existing):
        super().__init__(
            f"{existing['brand']} {existing['color']} is already in the collection"
        )
        self.existing = existing


def _clean_text(value, field):
    """Strip surrounding spaces; refuse empty text."""
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} must not be empty")
    return text


def _clean_quantity(value):
    """Turn value into a whole number of bottles, 0 or more."""
    try:
        quantity = int(str(value).strip())
    except ValueError:
        raise ValueError("quantity must be a whole number") from None
    if quantity < 0:
        raise ValueError("quantity must not be negative")
    return quantity


def _key(text):
    """Comparison key that ignores case and surrounding spaces."""
    return str(text).strip().casefold()


# --- R5: duplicate checking ---------------------------------------------------

def find_polish(collection, brand, color):
    """Return the polish matching BOTH brand and color (ignoring case), or None."""
    for polish in collection:
        if _key(polish["brand"]) == _key(brand) and _key(polish["color"]) == _key(color):
            return polish
    return None


# --- R1: adding ---------------------------------------------------------------

def add_polish(collection, brand, color, finish, quantity):
    """Add a new polish and return it.

    Raises ValueError for bad input and DuplicatePolishError if the
    brand + color combination already exists (the collection is unchanged).
    """
    brand = _clean_text(brand, "brand")
    color = _clean_text(color, "color name")
    finish = _clean_text(finish, "finish")
    quantity = _clean_quantity(quantity)

    existing = find_polish(collection, brand, color)
    if existing is not None:
        raise DuplicatePolishError(existing)

    next_added = max((p["added"] for p in collection), default=0) + 1
    polish = {
        "brand": brand,
        "color": color,
        "finish": finish,
        "quantity": quantity,
        "added": next_added,
    }
    collection.append(polish)
    return polish


# --- R6: updating quantity ----------------------------------------------------

def update_quantity(collection, brand, color, quantity):
    """Set a new quantity on an existing polish and return it.

    Raises KeyError if no such polish, ValueError for a bad quantity.
    """
    quantity = _clean_quantity(quantity)
    polish = find_polish(collection, brand, color)
    if polish is None:
        raise KeyError(f"no polish {brand!r} {color!r} in the collection")
    polish["quantity"] = quantity
    return polish


# --- R3: searching ------------------------------------------------------------

def search(collection, query, field="any"):
    """Return polishes whose field contains query, ignoring case.

    field is "brand", "color", "finish", or "any" (all three).
    An empty query returns every polish.
    """
    if field == "any":
        fields = SEARCH_FIELDS
    elif field in SEARCH_FIELDS:
        fields = (field,)
    else:
        raise ValueError(f"cannot search by {field!r}")

    needle = _key(query)
    return [p for p in collection if any(needle in _key(p[f]) for f in fields)]


# --- R4: sorting and filtering -------------------------------------------------

def sort_polishes(collection, by="added", descending=False):
    """Return a new list sorted by "added" (oldest first) or "quantity" (lowest first).

    descending=True reverses the order. The original list is not changed.
    """
    if by not in SORT_KEYS:
        raise ValueError(f"cannot sort by {by!r}")
    # Ties on quantity fall back to the order added, so results are predictable.
    return sorted(collection, key=lambda p: (p[by], p["added"]), reverse=descending)


def filter_by_finish(collection, finish):
    """Return only polishes with this finish (ignoring case). Empty keeps all."""
    if not str(finish).strip():
        return list(collection)
    return [p for p in collection if _key(p["finish"]) == _key(finish)]


def finishes(collection):
    """Distinct finishes in the collection, sorted, for a drop-down menu."""
    seen = {}
    for polish in collection:
        seen.setdefault(_key(polish["finish"]), polish["finish"])
    return [seen[k] for k in sorted(seen)]


# --- Saving and loading ---------------------------------------------------------

def load_collection(path):
    """Read the collection from a JSON file. A missing file means empty."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_collection(collection, path):
    """Write the collection as JSON, safely.

    Writes to a temporary file in the same folder, then swaps it into place,
    so a crash mid-write never leaves a half-written data file.
    """
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=folder, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(collection, f, indent=2)
        os.replace(tmp_path, path)
    except BaseException:
        os.remove(tmp_path)
        raise
