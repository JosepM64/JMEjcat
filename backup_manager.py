"""
Backup manager for JMEJCat
Provides backup, restore, and verification functions for databases and images.
"""

import shutil
import logging
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import DB_FILENAME, DB_FILENAME_TRAMITACIO, BACKUP_COUNT
from utils import get_data_path, get_backups_path

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backup operations for databases and images."""

    @staticmethod
    def backup_database(backup_type: str = "all") -> bool:
        """
        Creates a backup of the database and/or images.

        Args:
            backup_type: "all" (everything), "notes" (only databases), "images" (only images)

        Returns:
            bool: True if backup was successful, False otherwise.
        """
        data_path = get_data_path()
        backups_path = get_backups_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        success = True

        # Backup of databases
        if backup_type in ["all", "notes"]:
            databases = [DB_FILENAME, DB_FILENAME_TRAMITACIO]

            for db_name in databases:
                db_path = data_path / db_name

                if not db_path.exists():
                    logger.warning(f"Database not found for backup: {db_path}")
                    continue

                try:
                    backup_name = f"backup_notes_{db_name}.backup_{timestamp}"
                    backup_path = backups_path / backup_name
                    # sqlite3 backup API instead of file copy: produces a
                    # consistent snapshot even with a live WAL, which a plain
                    # shutil.copy2 can miss or tear.
                    src_conn = sqlite3.connect(str(db_path))
                    dst_conn = sqlite3.connect(str(backup_path))
                    try:
                        with dst_conn:
                            src_conn.backup(dst_conn)
                    finally:
                        dst_conn.close()
                        src_conn.close()
                    logger.info(f"Database backup created: {backup_path}")
                except Exception as e:
                    logger.error(f"Error creating backup of {db_name}: {e}")
                    success = False

        # Backup of images
        if backup_type in ["all", "images"]:
            images_path = data_path / "images"

            if images_path.exists() and any(images_path.iterdir()):
                try:
                    backup_name = f"backup_images_{timestamp}.zip"
                    backup_path = backups_path / backup_name

                    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                        for img_file in images_path.rglob("*"):
                            if img_file.is_file():
                                arcname = img_file.relative_to(images_path)
                                zf.write(img_file, arcname)

                    logger.info(f"Images backup created: {backup_path}")
                except Exception as e:
                    logger.error(f"Error creating images backup: {e}")
                    success = False

        return success

    @staticmethod
    def restore_backup(backup_filename: str) -> bool:
        """
        Restores a backup (databases or images).

        Args:
            backup_filename: Name of the backup file.

        Returns:
            bool: True if restoration was successful, False otherwise.
        """
        backups_path = get_backups_path()
        data_path = get_data_path()
        backup_path = backups_path / backup_filename

        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_path}")
            return False

        try:
            # Determine backup type
            if backup_filename.startswith("backup_images_"):
                # Restore images
                images_path = data_path / "images"
                images_path.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(backup_path, "r") as zf:
                    zf.extractall(images_path)

                logger.info(f"Images backup restored from: {backup_path}")

            elif backup_filename.startswith("backup_notes_"):
                # Restore databases - determine which database
                db_match = backup_filename.replace("backup_notes_", "").split(
                    ".backup_"
                )[0]

                if db_match == DB_FILENAME:
                    db_to_restore = DB_FILENAME
                elif db_match == DB_FILENAME_TRAMITACIO:
                    db_to_restore = DB_FILENAME_TRAMITACIO
                else:
                    logger.error(f"Unrecognized notes backup: {backup_filename}")
                    return False

                db_path = data_path / db_to_restore
                shutil.copy2(backup_path, db_path)
                logger.info(f"Notes backup restored from: {backup_path}")

            elif backup_filename.startswith("jmejcat.db.backup_"):
                # Old format: jmejcat.db.backup_TIMESTAMP
                db_path = data_path / DB_FILENAME
                shutil.copy2(backup_path, db_path)
                logger.info(f"Notes backup (old format) restored from: {backup_path}")

            elif backup_filename.startswith("tramitacio.db.backup_"):
                # Old format: tramitacio.db.backup_TIMESTAMP
                db_path = data_path / DB_FILENAME_TRAMITACIO
                shutil.copy2(backup_path, db_path)
                logger.info(
                    f"Tramitacio backup (old format) restored from: {backup_path}"
                )

            else:
                logger.error(f"Unrecognized backup type: {backup_filename}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False

    @staticmethod
    def get_backup_list(db_name: Optional[str] = None) -> list:
        """
        Gets the list of available backups.

        Args:
            db_name: Specific database name (optional).
                     If None, lists all databases.

        Returns:
            list: List of backups sorted by date (most recent first).
        """
        backups_path = get_backups_path()

        try:
            all_backups = []

            # Search for notes backups (new format: backup_notes_jmejcat.db.backup_TIMESTAMP)
            notes_backups = list(backups_path.glob("backup_notes_*.backup_*"))
            for bf in notes_backups:
                try:
                    # Extract timestamp from name: backup_notes_jmejcat.db.backup_20260320_120000
                    parts = bf.name.replace("backup_notes_", "").split(".backup_")
                    if len(parts) == 2:
                        db_part = parts[0]
                        timestamp = parts[1]

                        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                        readable_date = dt.strftime("%Y-%m-%d %H:%M:%S")

                        size_kb = bf.stat().st_size / 1024

                        if db_part == "jmejcat.db":
                            db_type = "Notes"
                        elif db_part == "tramitacio.db":
                            db_type = "Tramitació"
                        else:
                            db_type = db_part

                        all_backups.append(
                            {
                                "filename": bf.name,
                                "path": bf,
                                "date": readable_date,
                                "size_kb": f"{size_kb:.1f} KB",
                                "timestamp": timestamp,
                                "db_type": db_type,
                                "backup_type": "notes",
                            }
                        )
                except Exception as e:
                    logger.warning(f"Error processing backup {bf.name}: {e}")

            # Search for notes backups (old format: jmejcat.db.backup_TIMESTAMP)
            old_notes_backups = list(backups_path.glob("jmejcat.db.backup_*"))
            for bf in old_notes_backups:
                try:
                    # Extract timestamp: jmejcat.db.backup_20260320_144439
                    parts = bf.name.replace("jmejcat.db.backup_", "").split(".backup_")
                    if len(parts) >= 1:
                        timestamp = parts[-1]
                        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                        readable_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                        size_kb = bf.stat().st_size / 1024

                        all_backups.append(
                            {
                                "filename": bf.name,
                                "path": bf,
                                "date": readable_date,
                                "size_kb": f"{size_kb:.1f} KB",
                                "timestamp": timestamp,
                                "db_type": "Notes",
                                "backup_type": "notes",
                            }
                        )
                except Exception as e:
                    logger.warning(f"Error processing backup {bf.name}: {e}")

            # Search for tramitacio backups (old format: tramitacio.db.backup_TIMESTAMP)
            old_tramit_backups = list(backups_path.glob("tramitacio.db.backup_*"))
            for bf in old_tramit_backups:
                try:
                    timestamp = bf.name.replace("tramitacio.db.backup_", "")
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    readable_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                    size_kb = bf.stat().st_size / 1024

                    all_backups.append(
                        {
                            "filename": bf.name,
                            "path": bf,
                            "date": readable_date,
                            "size_kb": f"{size_kb:.1f} KB",
                            "timestamp": timestamp,
                            "db_type": "Tramitació",
                            "backup_type": "notes",
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error processing backup {bf.name}: {e}")

            # Search for images backups (format: backup_images_TIMESTAMP.zip)
            images_backups = list(backups_path.glob("backup_images_*.zip"))
            for bf in images_backups:
                try:
                    # Extract timestamp: backup_images_20260320_120000.zip
                    parts = bf.name.replace("backup_images_", "").replace(".zip", "")
                    timestamp = parts

                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    readable_date = dt.strftime("%Y-%m-%d %H:%M:%S")

                    size_kb = bf.stat().st_size / 1024

                    all_backups.append(
                        {
                            "filename": bf.name,
                            "path": bf,
                            "date": readable_date,
                            "size_kb": f"{size_kb:.1f} KB",
                            "timestamp": timestamp,
                            "db_type": "Imatges",
                            "backup_type": "images",
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error processing backup {bf.name}: {e}")

            # Sort by timestamp (most recent first)
            all_backups.sort(key=lambda x: x["timestamp"], reverse=True)

            return all_backups

        except Exception as e:
            logger.error(f"Error getting backup list: {e}")
            return []

    @staticmethod
    def verify_backup_file(backup_path: Path) -> Dict[str, Any]:
        """Verifies the integrity of a backup file."""
        result = {"valid": False, "error": None, "size_kb": 0.0, "type": None}
        if not backup_path.exists():
            result["error"] = "File does not exist"
            return result
        result["size_kb"] = backup_path.stat().st_size / 1024
        filename = backup_path.name
        if filename.startswith("backup_images_") and filename.endswith(".zip"):
            result["type"] = "Imatges"
            try:
                with zipfile.ZipFile(backup_path, "r") as zf:
                    _ = zf.namelist()
                result["valid"] = True
            except zipfile.BadZipFile as e:
                result["error"] = f"Corrupt ZIP: {e}"
            except Exception as e:
                result["error"] = f"Error reading ZIP: {e}"
            return result
        if (
            filename.startswith("backup_notes_")
            or filename.startswith("jmejcat.db.backup_")
            or filename.startswith("tramitacio.db.backup_")
        ):
            if "tramitacio" in filename:
                result["type"] = "Tramitació"
            else:
                result["type"] = "Notes"
            try:
                conn = sqlite3.connect(str(backup_path))
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                _ = cur.fetchone()
                conn.close()
                result["valid"] = True
            except sqlite3.DatabaseError as e:
                result["error"] = f"Corrupt database: {e}"
            except Exception as e:
                result["error"] = f"Error opening DB: {e}"
            return result
        result["error"] = "Unrecognized backup type"
        return result

    @staticmethod
    def verify_backups_in_folder(folder_path: Path) -> List[Dict[str, Any]]:
        """Verifies all backups in a folder."""
        if not folder_path.exists() or not folder_path.is_dir():
            logger.error(f"Invalid folder: {folder_path}")
            return []
        try:
            backups = []
            for file_path in folder_path.iterdir():
                if not file_path.is_file():
                    continue
                fname = file_path.name
                if fname.startswith("backup_images_") and fname.endswith(".zip"):
                    btype = "images"
                    db_type = "Imatges"
                    ts_part = fname.replace("backup_images_", "").replace(".zip", "")
                    timestamp = ts_part
                elif fname.startswith("backup_notes_"):
                    btype = "notes"
                    parts = fname.replace("backup_notes_", "").split(".backup_")
                    if len(parts) < 2:
                        continue
                    db_part = parts[0]
                    timestamp = parts[1]
                    if db_part == "jmejcat.db":
                        db_type = "Notes"
                    elif db_part == "tramitacio.db":
                        db_type = "Tramitació"
                    else:
                        db_type = db_part
                elif fname.startswith("jmejcat.db.backup_"):
                    btype = "notes"
                    db_type = "Notes"
                    timestamp = fname.replace("jmejcat.db.backup_", "")
                elif fname.startswith("tramitacio.db.backup_"):
                    btype = "notes"
                    db_type = "Tramitació"
                    timestamp = fname.replace("tramitacio.db.backup_", "")
                else:
                    continue
                try:
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    readable_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    mtime = file_path.stat().st_mtime
                    dt = datetime.fromtimestamp(mtime)
                    readable_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                backup_info = {
                    "filename": fname,
                    "path": file_path,
                    "date": readable_date,
                    "size_kb": f"{file_path.stat().st_size / 1024:.1f} KB",
                    "timestamp": dt.strftime("%Y%m%d_%H%M%S"),
                    "db_type": db_type,
                    "backup_type": "notes" if btype == "notes" else "images",
                }
                backups.append(backup_info)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            for bk in backups:
                vf = BackupManager.verify_backup_file(bk["path"])
                bk["valid"] = vf["valid"]
                bk["error"] = vf.get("error")
            return backups
        except Exception as e:
            logger.error(f"Error verifying backups in {folder_path}: {e}")
            return []

    @staticmethod
    def cleanup_old_backups(
        backup_type: str = "all", dry_run: bool = False
    ) -> tuple[int, list[str]]:
        """
        Deletes old backups, keeping only the BACKUP_COUNT most recent of each type.

        Args:
            backup_type: "all" (all), "notes" (notes and tramitacio), "images" (images)
            dry_run: If True, doesn't actually delete, just shows what would be deleted.

        Returns:
            tuple: (number of backups deleted, list of deleted filenames)
        """

        backups = BackupManager.get_backup_list()

        # Filter by type if needed
        if backup_type != "all":
            backups = [b for b in backups if b["backup_type"] == backup_type]

        # Group by database type (Notes, Tramitació, Imatges)
        backups_by_db_type = {}
        for backup in backups:
            dbtype = backup["db_type"]
            backups_by_db_type.setdefault(dbtype, []).append(backup)

        deleted_count = 0
        deleted_files = []

        for dbtype, dbtype_backups in backups_by_db_type.items():
            # Sort by timestamp descending (most recent first)
            dbtype_backups.sort(key=lambda x: x["timestamp"], reverse=True)

            # Keep only BACKUP_COUNT most recent of each type
            to_delete = dbtype_backups[BACKUP_COUNT:]

            for backup in to_delete:
                try:
                    if not dry_run:
                        backup["path"].unlink()  # Delete file
                    deleted_count += 1
                    deleted_files.append(backup["filename"])
                    if dry_run:
                        logger.info(
                            f"[DRY RUN] Old backup that would be deleted ({dbtype}): {backup['filename']}"
                        )
                    else:
                        logger.info(
                            f"Old backup deleted ({dbtype}): {backup['filename']}"
                        )
                except Exception as e:
                    logger.error(f"Error deleting backup {backup['filename']}: {e}")

        return deleted_count, deleted_files
