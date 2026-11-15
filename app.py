"""Web server and HTML pages for the polish tracker.

Run with:  python3 app.py   then open http://127.0.0.1:8000
All the logic lives in collection.py; this file only handles web requests.
"""

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import collection

HOST, PORT = "127.0.0.1", 8000
DATA_FILE = Path(__file__).with_name("polishes.json")

SORT_CHOICES = {
    "added": ("added", False, "Oldest added first"),
    "added_desc": ("added", True, "Newest added first"),
    "quantity": ("quantity", False, "Lowest stock first"),
    "quantity_desc": ("quantity", True, "Highest stock first"),
}
SEARCH_CHOICES = {"any": "Any field", "brand": "Brand", "color": "Color name",
                  "finish": "Finish"}

STYLE = """
body { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto;
       padding: 0 1rem; color: #222; }
h1 { color: #b0306a; }
section { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
form.inline { display: inline; }
input, select, button { font: inherit; padding: .3rem; margin: .2rem 0; }
input[type=number] { width: 5rem; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: .4rem; border-bottom: 1px solid #eee; }
.out { color: #b00; font-weight: bold; }
.msg { background: #e8f6ea; padding: .6rem; border-radius: 6px; }
.err { background: #fde8e8; padding: .6rem; border-radius: 6px; }
"""


def e(value):
    """Escape text for safe use inside HTML (stops a polish name breaking the page)."""
    return escape(str(value), quote=True)


def page(title, body):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><style>{STYLE}</style></head>
<body><h1>{e(title)}</h1>{body}</body></html>"""


def options(choices, selected):
    return "".join(
        f'<option value="{e(v)}"{" selected" if v == selected else ""}>{e(label)}</option>'
        for v, label in choices)


def quantity_form(polish, label="Update"):
    """A small form that sets a new quantity for one polish (R6)."""
    return f"""<form class="inline" method="post" action="/update">
  <input type="hidden" name="brand" value="{e(polish['brand'])}">
  <input type="hidden" name="color" value="{e(polish['color'])}">
  <input type="number" name="quantity" min="0" value="{e(polish['quantity'])}" required>
  <button>{e(label)}</button></form>"""


def home_page(polishes, params, message="", error="", form=None):
    form = form or {}
    q = params.get("q", "")
    field = params.get("field", "any")
    finish = params.get("finish", "")
    sort = params.get("sort", "added")

    # R3, R4: search, then filter, then sort.
    by, descending, _ = SORT_CHOICES.get(sort, SORT_CHOICES["added"])
    shown = collection.search(polishes, q, field if field in SEARCH_CHOICES else "any")
    shown = collection.filter_by_finish(shown, finish)
    shown = collection.sort_polishes(shown, by, descending)

    notice = ""
    if message:
        notice += f'<p class="msg">{e(message)}</p>'
    if error:
        notice += f'<p class="err">{e(error)}</p>'

    # R1: add form.
    add_form = f"""<section><h2>Add a polish</h2>
<form method="post" action="/add">
  <label>Brand <input name="brand" value="{e(form.get('brand', ''))}" required></label>
  <label>Color name <input name="color" value="{e(form.get('color', ''))}" required></label>
  <label>Finish <input name="finish" list="finishes" value="{e(form.get('finish', ''))}"
         placeholder="creme, glitter..." required></label>
  <label>Bottles <input type="number" name="quantity" min="0"
         value="{e(form.get('quantity', '1'))}" required></label>
  <datalist id="finishes">{''.join(f'<option value="{e(f)}">' for f in collection.finishes(polishes))}</datalist>
  <button>Add</button>
</form></section>"""

    # R3, R4: search / filter / sort controls.
    finish_choices = [("", "All finishes")] + [(f, f) for f in collection.finishes(polishes)]
    controls = f"""<section><h2>Find</h2>
<form method="get" action="/">
  <input name="q" value="{e(q)}" placeholder="Search...">
  <select name="field">{options(SEARCH_CHOICES.items(), field)}</select>
  <select name="finish">{options(finish_choices, finish)}</select>
  <select name="sort">{options(((k, v[2]) for k, v in SORT_CHOICES.items()), sort)}</select>
  <button>Apply</button> <a href="/">Clear</a>
</form></section>"""

    # R2: the collection table.
    if not polishes:
        table = "<p>Your collection is empty. Add your first polish above.</p>"
    elif not shown:
        table = "<p>No polishes match.</p>"
    else:
        rows = "".join(
            f"""<tr><td>{e(p['brand'])}</td><td>{e(p['color'])}</td><td>{e(p['finish'])}</td>
<td{' class="out"' if p['quantity'] == 0 else ''}>{e(p['quantity'])}</td>
<td>{quantity_form(p)}</td></tr>"""
            for p in shown)
        table = f"""<table><thead><tr><th>Brand</th><th>Color name</th><th>Finish</th>
<th>Bottles</th><th>Change quantity</th></tr></thead><tbody>{rows}</tbody></table>"""
    count = f"<p>Showing {len(shown)} of {len(polishes)} polishes.</p>"

    return page("Polish Tracker", notice + add_form + controls +
                f"<section><h2>Collection</h2>{count}{table}</section>")


def duplicate_page(existing):
    """R5 + R6: explain the duplicate, show its quantity, offer a restock."""
    body = f"""<p class="err">{e(existing['brand'])} – {e(existing['color'])}
is already in your collection, so it was not added again.</p>
<p>Finish: {e(existing['finish'])}<br>
Bottles in stock now: <strong>{e(existing['quantity'])}</strong></p>
<p>Restocking? Set the new number of bottles:</p>
{quantity_form(existing, "Save quantity")}
<p><a href="/">Back to the collection</a></p>"""
    return page("Already in your collection", body)


class Handler(BaseHTTPRequestHandler):
    def send_html(self, html, status=200):
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, message):
        # "Post/Redirect/Get": after a change, send the browser back to the home
        # page so refreshing does not resubmit the form.
        self.send_response(303)
        self.send_header("Location", "/?" + urlencode({"msg": message}))
        self.end_headers()

    def read_form(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        return {k: v[0] for k, v in parse_qs(body, keep_blank_values=True).items()}

    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/":
            self.send_html(page("Not found", '<p><a href="/">Home</a></p>'), 404)
            return
        params = {k: v[0] for k, v in parse_qs(url.query).items()}
        polishes = collection.load_collection(DATA_FILE)
        self.send_html(home_page(polishes, params, message=params.get("msg", "")))

    def do_POST(self):
        path = urlparse(self.path).path
        form = self.read_form()
        polishes = collection.load_collection(DATA_FILE)

        if path == "/add":
            try:
                p = collection.add_polish(polishes, form.get("brand", ""),
                                          form.get("color", ""), form.get("finish", ""),
                                          form.get("quantity", ""))
            except collection.DuplicatePolishError as dup:
                self.send_html(duplicate_page(dup.existing))
                return
            except ValueError as err:
                self.send_html(home_page(polishes, {}, error=str(err), form=form), 400)
                return
            collection.save_collection(polishes, DATA_FILE)
            self.redirect(f"Added {p['brand']} {p['color']}.")

        elif path == "/update":
            try:
                p = collection.update_quantity(polishes, form.get("brand", ""),
                                               form.get("color", ""), form.get("quantity", ""))
            except KeyError:
                self.send_html(home_page(polishes, {}, error="That polish was not found."), 404)
                return
            except ValueError as err:
                self.send_html(home_page(polishes, {}, error=str(err)), 400)
                return
            collection.save_collection(polishes, DATA_FILE)
            self.redirect(f"{p['brand']} {p['color']} now has {p['quantity']} bottle(s).")

        else:
            self.send_html(page("Not found", '<p><a href="/">Home</a></p>'), 404)


def main():
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Polish Tracker running at http://{HOST}:{PORT}  (press Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
