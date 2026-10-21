"""Integració export MD (+ smoke PDF sense thread)."""

from pathlib import Path


def _sample_notes():
    return [
        {
            "id": 1,
            "title": "Nota export",
            "request": "<p>Petició <b>negreta</b></p>",
            "solution": "<p>Solució</p>",
            "examples": "",
            "created_at": "2025-01-01T10:00:00",
            "updated_at": "2025-01-02T10:00:00",
        },
        {
            "id": 2,
            "title": "Segona",
            "request": "plain",
            "solution": "plain2",
            "examples": "ex",
            "created_at": "2025-01-01T10:00:00",
            "updated_at": "2025-01-02T10:00:00",
        },
    ]


def test_md_export_all_in_one(tmp_path: Path):
    from md_exporter import export_notes_to_md

    out = tmp_path / "notes.md"
    res = export_notes_to_md(_sample_notes(), out, all_in_one=True)
    text = Path(res).read_text(encoding="utf-8")
    assert "Nota export" in text and "Segona" in text
    assert out.stat().st_size > 0


def test_md_export_separate(tmp_path: Path):
    from md_exporter import export_notes_to_md

    outdir = tmp_path / "mds"
    export_notes_to_md(_sample_notes(), outdir, all_in_one=False)
    files = list(outdir.glob("*.md"))
    assert len(files) == 2
