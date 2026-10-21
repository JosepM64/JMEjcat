"""Cerca unificada v4.0: notes multi-camp + paginació + tramits limit/offset."""

from core.search import escape_like, like_param


def test_escape_like_literal():
    assert escape_like("a%b_c\\d") == "a\\%b\\_c\\\\d"
    assert like_param("x") == "%x%"


def test_search_notes_multifield(notes_db):
    notes_db.create_note("Titol llum", "peticio fosca", "solucio clara", "")
    notes_db.create_note("Altre", "peticio amb llum dins", "res", "")
    # Cerca a solution també (v4.0 SEARCH_FIELDS inclou request/solution)
    r1 = notes_db.search_notes("llum")
    assert len(r1) >= 2
    r2 = notes_db.search_notes("llum", fields=["title"])
    assert any(n["title"] == "Titol llum" for n in r2)
    # Literal % no ha de petar ni retornar-ho tot per wildcard
    r3 = notes_db.search_notes("%")
    assert isinstance(r3, list)


def test_search_notes_pagination(notes_db):
    for i in range(5):
        notes_db.create_note(f"PAG-{i}", "", "", "")
    p1 = notes_db.search_notes("PAG", limit=2, offset=0)
    p2 = notes_db.search_notes("PAG", limit=2, offset=2)
    assert len(p1) == 2 and len(p2) == 2
    assert {n["title"] for n in p1}.isdisjoint({n["title"] for n in p2})


def test_search_title_vs_body_split(notes_db):
    """Les dues caixes de la UI: títol sol vs cos sol."""
    notes_db.create_note("Titol unic", "cos amb paraula secreta", "", "")
    by_title = notes_db.search_notes("Titol unic", fields=["title"])
    assert len(by_title) == 1
    by_body = notes_db.search_notes("secreta", fields=["request", "solution"])
    assert len(by_body) == 1
    by_title_miss = notes_db.search_notes("secreta", fields=["title"])
    assert len(by_title_miss) == 0


def test_search_tramits_limit_offset(tramit_db):
    for i in range(4):
        tramit_db.create_tramit(f"100{i}", 2025, "01/01/2025", "notes", "blau")
    a = tramit_db.search_tramits(numero="100", limit=2, offset=0)
    b = tramit_db.search_tramits(numero="100", limit=2, offset=2)
    assert len(a) == 2 and len(b) == 2
