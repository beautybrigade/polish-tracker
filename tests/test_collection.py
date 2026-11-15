"""Tests for collection.py. Each test name starts with the requirement it checks."""

import json

import pytest

import collection as c


@pytest.fixture
def sample():
    """A small collection built through add_polish, in a known order."""
    col = []
    c.add_polish(col, "OPI", "Big Apple Red", "creme", 3)
    c.add_polish(col, "Essie", "Ballet Slippers", "sheer", 1)
    c.add_polish(col, "Zoya", "Storm", "glitter", 5)
    c.add_polish(col, "Essie", "Bordeaux", "creme", 0)
    return col


def colors(polishes):
    return [p["color"] for p in polishes]


# --- R1: add a polish with its details ---------------------------------------

def test_R1_add_polish_stores_all_details():
    col = []
    polish = c.add_polish(col, "OPI", "Big Apple Red", "creme", 2)
    assert polish == {
        "brand": "OPI", "color": "Big Apple Red", "finish": "creme",
        "quantity": 2, "added": 1,
    }
    assert col == [polish]


def test_R1_add_polish_strips_spaces_and_converts_quantity_text():
    col = []
    polish = c.add_polish(col, "  OPI ", " Big Apple Red ", " creme ", " 4 ")
    assert (polish["brand"], polish["color"], polish["finish"]) == (
        "OPI", "Big Apple Red", "creme")
    assert polish["quantity"] == 4


def test_R1_added_counter_increases_with_each_polish(sample):
    assert [p["added"] for p in sample] == [1, 2, 3, 4]


@pytest.mark.parametrize("brand, color, finish", [
    ("", "Red", "creme"),
    ("OPI", "   ", "creme"),
    ("OPI", "Red", ""),
])
def test_R1_add_polish_rejects_empty_fields(brand, color, finish):
    col = []
    with pytest.raises(ValueError):
        c.add_polish(col, brand, color, finish, 1)
    assert col == []


@pytest.mark.parametrize("quantity", [-1, "two", "", "1.5"])
def test_R1_add_polish_rejects_bad_quantity(quantity):
    col = []
    with pytest.raises(ValueError):
        c.add_polish(col, "OPI", "Red", "creme", quantity)
    assert col == []


def test_R1_zero_quantity_is_allowed():
    col = []
    assert c.add_polish(col, "OPI", "Red", "creme", 0)["quantity"] == 0


# --- R2: display the whole collection ----------------------------------------

def test_R2_default_view_contains_every_polish(sample):
    # The home page shows sort_polishes(filter(search(...))) with no criteria.
    view = c.sort_polishes(c.filter_by_finish(c.search(sample, ""), ""))
    assert colors(view) == ["Big Apple Red", "Ballet Slippers", "Storm", "Bordeaux"]


def test_R2_whole_collection_survives_save_and_load(sample, tmp_path):
    path = tmp_path / "polishes.json"
    c.save_collection(sample, path)
    assert c.load_collection(path) == sample


def test_R2_load_missing_file_gives_empty_collection(tmp_path):
    assert c.load_collection(tmp_path / "nope.json") == []


def test_R2_save_writes_valid_json_and_leaves_no_temp_files(sample, tmp_path):
    path = tmp_path / "polishes.json"
    c.save_collection(sample, path)
    c.save_collection(sample[:1], path)  # overwrite works
    assert json.loads(path.read_text()) == sample[:1]
    assert [f.name for f in tmp_path.iterdir()] == ["polishes.json"]


# --- R3: search by brand, color name, or finish -------------------------------

def test_R3_search_by_brand_ignores_case(sample):
    assert colors(c.search(sample, "essie", "brand")) == ["Ballet Slippers", "Bordeaux"]


def test_R3_search_by_color_matches_part_of_name(sample):
    assert colors(c.search(sample, "slip", "color")) == ["Ballet Slippers"]


def test_R3_search_by_finish(sample):
    assert colors(c.search(sample, "GLITTER", "finish")) == ["Storm"]


def test_R3_search_only_looks_in_chosen_field(sample):
    # "creme" is a finish, not a brand or color.
    assert c.search(sample, "creme", "brand") == []
    assert c.search(sample, "creme", "color") == []


def test_R3_search_any_field_checks_all_three(sample):
    # "o" is in OPI and Zoya (brands) and Bordeaux (color), but not in Essie/Ballet Slippers/sheer.
    assert colors(c.search(sample, "o")) == ["Big Apple Red", "Storm", "Bordeaux"]
    assert colors(c.search(sample, "sheer", "any")) == ["Ballet Slippers"]


def test_R3_empty_search_returns_everything(sample):
    assert c.search(sample, "  ") == sample


def test_R3_search_unknown_field_is_an_error(sample):
    with pytest.raises(ValueError):
        c.search(sample, "x", "price")


# --- R4: sort by added or quantity, filter by finish --------------------------

def test_R4_sort_by_added_oldest_first_then_newest_first(sample):
    shuffled = [sample[2], sample[0], sample[3], sample[1]]
    assert colors(c.sort_polishes(shuffled, "added")) == [
        "Big Apple Red", "Ballet Slippers", "Storm", "Bordeaux"]
    assert colors(c.sort_polishes(shuffled, "added", descending=True)) == [
        "Bordeaux", "Storm", "Ballet Slippers", "Big Apple Red"]


def test_R4_sort_by_quantity_lowest_first_then_highest_first(sample):
    assert colors(c.sort_polishes(sample, "quantity")) == [
        "Bordeaux", "Ballet Slippers", "Big Apple Red", "Storm"]
    assert colors(c.sort_polishes(sample, "quantity", descending=True)) == [
        "Storm", "Big Apple Red", "Ballet Slippers", "Bordeaux"]


def test_R4_quantity_ties_keep_order_added():
    col = []
    c.add_polish(col, "A", "One", "creme", 2)
    c.add_polish(col, "B", "Two", "creme", 2)
    assert colors(c.sort_polishes(list(reversed(col)), "quantity")) == ["One", "Two"]


def test_R4_sort_does_not_change_the_original(sample):
    before = list(sample)
    c.sort_polishes(sample, "quantity")
    assert sample == before


def test_R4_sort_unknown_key_is_an_error(sample):
    with pytest.raises(ValueError):
        c.sort_polishes(sample, "brand")


def test_R4_filter_by_finish_ignores_case(sample):
    assert colors(c.filter_by_finish(sample, "CREME")) == ["Big Apple Red", "Bordeaux"]


def test_R4_filter_by_finish_is_exact_not_partial(sample):
    assert c.filter_by_finish(sample, "crem") == []


def test_R4_empty_filter_keeps_everything(sample):
    assert c.filter_by_finish(sample, "") == sample


def test_R4_finishes_lists_each_finish_once_sorted(sample):
    c.add_polish(sample, "OPI", "Malaga Wine", "Creme", 1)
    assert c.finishes(sample) == ["creme", "glitter", "sheer"]


def test_R4_search_filter_and_sort_combine(sample):
    view = c.sort_polishes(
        c.filter_by_finish(c.search(sample, "essie", "brand"), "creme"), "quantity")
    assert colors(view) == ["Bordeaux"]


# --- R5: refuse duplicate brand + color --------------------------------------

def test_R5_duplicate_brand_and_color_is_refused(sample):
    before = [dict(p) for p in sample]
    with pytest.raises(c.DuplicatePolishError):
        c.add_polish(sample, "OPI", "Big Apple Red", "shimmer", 9)
    assert sample == before


def test_R5_duplicate_check_ignores_case_and_spaces(sample):
    with pytest.raises(c.DuplicatePolishError):
        c.add_polish(sample, " opi ", "big apple RED", "creme", 1)
    assert len(sample) == 4


def test_R5_same_color_name_different_brand_is_allowed(sample):
    c.add_polish(sample, "Essie", "Big Apple Red", "creme", 1)
    assert len(sample) == 5


def test_R5_same_brand_different_color_is_allowed(sample):
    c.add_polish(sample, "OPI", "Malaga Wine", "creme", 1)
    assert len(sample) == 5


def test_R5_find_polish_needs_both_brand_and_color(sample):
    assert c.find_polish(sample, "opi", "BIG APPLE RED") is sample[0]
    assert c.find_polish(sample, "OPI", "Storm") is None
    assert c.find_polish(sample, "Zoya", "Big Apple Red") is None


# --- R6: see and update quantity of an existing polish ------------------------

def test_R6_duplicate_error_carries_existing_polish_and_quantity(sample):
    with pytest.raises(c.DuplicatePolishError) as info:
        c.add_polish(sample, "essie", "bordeaux", "creme", 2)
    assert info.value.existing is sample[3]
    assert info.value.existing["quantity"] == 0


def test_R6_update_quantity_restocks_the_polish(sample):
    updated = c.update_quantity(sample, "essie", "BORDEAUX", 6)
    assert updated is sample[3]
    assert sample[3]["quantity"] == 6
    # Nothing else changed.
    assert [p["quantity"] for p in sample] == [3, 1, 5, 6]


def test_R6_update_quantity_accepts_text_from_a_form(sample):
    c.update_quantity(sample, "Zoya", "Storm", "7")
    assert sample[2]["quantity"] == 7


def test_R6_update_quantity_of_missing_polish_is_an_error(sample):
    with pytest.raises(KeyError):
        c.update_quantity(sample, "OPI", "Storm", 2)


@pytest.mark.parametrize("quantity", [-3, "lots"])
def test_R6_update_quantity_rejects_bad_quantity(sample, quantity):
    with pytest.raises(ValueError):
        c.update_quantity(sample, "Zoya", "Storm", quantity)
    assert sample[2]["quantity"] == 5


def test_R6_updated_quantity_is_saved(sample, tmp_path):
    path = tmp_path / "polishes.json"
    c.update_quantity(sample, "Zoya", "Storm", 0)
    c.save_collection(sample, path)
    assert c.find_polish(c.load_collection(path), "Zoya", "Storm")["quantity"] == 0
