"""Integració backup restore (v4.0)."""

from pathlib import Path


def _patch_bm_paths(monkeypatch, tmp_path: Path):
    """Redirigeix utils + backup_manager + database al tmp del test.

    conftest només parcheja utils.*; els mòduls amb from-import ja tenen
    la referència antiga, cal parchejar-los també.
    """
    import backup_manager as bm
    import database as dbmod
    import utils

    data = tmp_path / "data"
    backups = tmp_path / "backups"
    data.mkdir(parents=True, exist_ok=True)
    backups.mkdir(parents=True, exist_ok=True)
    for mod in (utils, bm, dbmod):
        if hasattr(mod, "get_data_path"):
            monkeypatch.setattr(mod, "get_data_path", lambda _d=data: _d)
        if hasattr(mod, "get_backups_path"):
            monkeypatch.setattr(mod, "get_backups_path", lambda _b=backups: _b)
    return data, backups


def test_backup_restore_roundtrip(tmp_path, monkeypatch):
    data, _ = _patch_bm_paths(monkeypatch, tmp_path)
    from backup_manager import BackupManager
    from database import Database

    db = Database()
    nid = db.create_note("Nota backup", "pet", "sol", "ex")
    db.close()
    assert BackupManager.backup_database("notes") is True
    backups = BackupManager.get_backup_list("jmejcat.db")
    assert backups, "cal haver-hi backup de notes"
    (data / "jmejcat.db").unlink()
    assert BackupManager.restore_backup(backups[0]["filename"]) is True
    db2 = Database()
    try:
        note = db2.get_note(nid)
        assert note is not None and note["title"] == "Nota backup"
    finally:
        db2.close()


def test_restore_corrupt_fails(tmp_path, monkeypatch):
    _, backups = _patch_bm_paths(monkeypatch, tmp_path)
    from backup_manager import BackupManager

    corrupt = backups / "backup_notes_jmejcat.db.backup_20000101_000000"
    corrupt.write_bytes(b"aixo no es una sqlite valida")
    assert BackupManager.restore_backup(corrupt.name) is False
    assert BackupManager.verify_backup_file(corrupt)["valid"] is False
    assert BackupManager.verify_backup_file(backups / "noexisteix.db")["valid"] is False


def test_cleanup_keeps_count(tmp_path, monkeypatch):
    _, backups = _patch_bm_paths(monkeypatch, tmp_path)
    import backup_manager as bm
    from backup_manager import BackupManager

    monkeypatch.setattr(bm, "BACKUP_COUNT", 2)
    for i in range(1, 6):
        (backups / f"backup_notes_jmejcat.db.backup_2020010{i}_000000").write_bytes(
            b"notadb"
        )
    deleted, _ = BackupManager.cleanup_old_backups("notes")
    assert deleted == 3
    assert len(BackupManager.get_backup_list("jmejcat.db")) == 2
