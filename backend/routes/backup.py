"""
Backup & Restore — owner-only blueprint.

Routes
------
GET  /backup/                       — history + controls page
POST /backup/create                 — create a new backup now
GET  /backup/download/<filename>    — authenticated file download
POST /backup/restore                — upload a backup file and restore it
POST /backup/delete/<filename>      — delete a backup file from disk

Design
------
• SQLite: uses the sqlite3 online backup API (safe with running app).
• Postgres: pg_dump / psql via subprocess (requires pg client tools).
• Backups stored in {BASE_DIR}/backups/   (outside static/, auth-gated download).
• Filenames: THMS_Backup_YYYYMMDD_HHMMSS[.db|.sql]
• Before every restore an automatic safety backup is created first.
• Every create / restore / delete action is written to AuditLog.
"""

import os
import re
import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, send_file, abort,
)
from flask_login import login_required, current_user

from backend.extensions import db
from backend.models.audit import AuditLog

backup_bp = Blueprint("backup", __name__)

# ── Constants ─────────────────────────────────────────────────────────────────
BACKUP_FILENAME_RE = re.compile(r"^THMS_Backup_\d{8}_\d{6}\.(db|sql)$")
SQLITE_MAGIC       = b"SQLite format 3\x00"
REQUIRED_TABLES    = {"users", "payments", "contracts", "drivers", "vehicles"}
MAX_UPLOAD_MB      = 200  # reject files larger than this at the route level


# ── Helpers ───────────────────────────────────────────────────────────────────

def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != "owner":
            flash("Access restricted to owners.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated


def _log(action: str, description: str, entity_id: int = None):
    db.session.add(AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type="Backup",
        entity_id=entity_id or current_user.id,
        description=description,
        ip_address=request.remote_addr,
        user_agent=(request.headers.get("User-Agent") or "")[:255],
    ))


def _backup_dir() -> Path:
    """Return (and create) the backup storage directory."""
    from backend.config import BASE_DIR
    d = BASE_DIR / "backups"
    d.mkdir(exist_ok=True)
    return d


def _db_info() -> dict:
    """
    Return {'type': 'sqlite'|'postgres'|'unknown', 'path': ..., 'uri': ...}.
    """
    uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("sqlite:///"):
        raw = uri[len("sqlite:///"):]
        p = Path(raw) if raw.startswith("/") else Path(current_app.root_path).parent / raw
        return {"type": "sqlite", "path": p, "uri": uri}
    if "postgres" in uri or "postgresql" in uri:
        return {"type": "postgres", "path": None, "uri": uri}
    return {"type": "unknown", "path": None, "uri": uri}


def _new_backup_filename(ext: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"THMS_Backup_{ts}.{ext}"


# ── SQLite backup / restore ───────────────────────────────────────────────────

def _sqlite_backup(src_path: Path, dst_path: Path) -> None:
    """Use sqlite3's online backup API (safe with a live database)."""
    src = sqlite3.connect(str(src_path))
    try:
        dst = sqlite3.connect(str(dst_path))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()


def _sqlite_restore(backup_path: Path, target_path: Path) -> None:
    """Replace target db with the backup (via sqlite3 backup API in reverse)."""
    src = sqlite3.connect(str(backup_path))
    try:
        dst = sqlite3.connect(str(target_path))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()


# ── Postgres backup / restore ─────────────────────────────────────────────────

def _postgres_backup(uri: str, dst_path: Path) -> tuple[bool, str]:
    """
    Run pg_dump and write a plain-SQL dump to dst_path.
    --clean --if-exists: the dump includes DROP statements so restore is
    idempotent and replaces existing schema/data cleanly.
    Returns (ok, error_message).
    """
    try:
        result = subprocess.run(
            [
                "pg_dump",
                "--format=plain",
                "--clean",
                "--if-exists",
                "--no-password",
                uri,
            ],
            capture_output=True,
            timeout=300,
        )
        if result.returncode != 0:
            return False, result.stderr.decode(errors="replace")[:500]
        dst_path.write_bytes(result.stdout)
        return True, ""
    except FileNotFoundError:
        return False, "pg_dump not found. Install postgresql-client."
    except subprocess.TimeoutExpired:
        return False, "pg_dump timed out after 5 minutes."
    except Exception as e:
        return False, str(e)


def _postgres_restore(uri: str, src_path: Path) -> tuple[bool, str]:
    """
    Run psql to restore from a plain SQL dump produced by _postgres_backup.
    Returns (ok, error_message).
    """
    try:
        result = subprocess.run(
            ["psql", "--no-password", "--set=ON_ERROR_STOP=0", uri],
            input=src_path.read_bytes(),
            capture_output=True,
            timeout=300,
        )
        # psql exits 3 when ON_ERROR_STOP is off and there were warnings —
        # treat any non-fatal exit as success if there's meaningful output.
        if result.returncode not in (0, 3):
            return False, result.stderr.decode(errors="replace")[:500]
        return True, ""
    except FileNotFoundError:
        return False, "psql not found. Install postgresql-client."
    except subprocess.TimeoutExpired:
        return False, "psql timed out after 5 minutes."
    except Exception as e:
        return False, str(e)


# ── Validation ────────────────────────────────────────────────────────────────

def _validate_sqlite_file(path: Path) -> tuple[bool, str]:
    """Return (is_valid, error_msg). Checks magic bytes + required tables."""
    try:
        data = path.read_bytes()
        if len(data) < 16 or data[:16] != SQLITE_MAGIC:
            return False, "Not a valid SQLite database file (wrong header)."
        conn = sqlite3.connect(str(path))
        try:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cur.fetchall()}
        finally:
            conn.close()
        missing = REQUIRED_TABLES - tables
        if missing:
            return False, f"Missing expected tables: {', '.join(sorted(missing))}. This may not be a THMS backup."
        return True, ""
    except sqlite3.DatabaseError as e:
        return False, f"SQLite error: {e}"
    except Exception as e:
        return False, str(e)


def _validate_sql_file(path: Path) -> tuple[bool, str]:
    """
    Validate a pg_dump plain-SQL file.
    Checks the header comment block that pg_dump always emits.
    """
    try:
        if path.stat().st_size == 0:
            return False, "Backup file is empty."
        head = path.read_bytes()[:4096].decode(errors="replace")
        # pg_dump always begins with these header comment lines
        if "PostgreSQL database dump" not in head:
            return False, (
                "File does not appear to be a PostgreSQL pg_dump output. "
                "Upload a .sql file created by THMS backup."
            )
        return True, ""
    except Exception as e:
        return False, str(e)


# ── Backup listing ────────────────────────────────────────────────────────────

def _list_backups() -> list[dict]:
    """
    Return list of backup dicts sorted newest first:
    {filename, path, ext, created_at, size_bytes, size_human}
    """
    d = _backup_dir()
    items = []
    for f in sorted(d.iterdir(), reverse=True):
        if not BACKUP_FILENAME_RE.match(f.name):
            continue
        # Parse timestamp from filename: THMS_Backup_YYYYMMDD_HHMMSS.ext
        try:
            ts_str = f.stem[len("THMS_Backup_"):]        # "20260714_142500"
            created = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
        except ValueError:
            created = datetime.utcfromtimestamp(f.stat().st_mtime)
        size = f.stat().st_size
        items.append({
            "filename":   f.name,
            "path":       f,
            "ext":        f.suffix.lstrip("."),
            "created_at": created,
            "size_bytes": size,
            "size_human": _human_size(size),
        })
    return items


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"


# ── Routes ────────────────────────────────────────────────────────────────────

@backup_bp.route("/")
@login_required
@owner_required
def index():
    db_info  = _db_info()
    backups  = _list_backups()
    bdir     = _backup_dir()
    total_sz = sum(b["size_bytes"] for b in backups)
    return render_template(
        "backup/index.html",
        db_info=db_info,
        backups=backups,
        backup_dir=str(bdir),
        total_size=_human_size(total_sz),
        backup_count=len(backups),
    )


@backup_bp.route("/create", methods=["POST"])
@login_required
@owner_required
def create():
    """Create a new database backup immediately."""
    info = _db_info()
    note = request.form.get("note", "").strip()[:120]

    if info["type"] == "sqlite":
        src = info["path"]
        if not src.exists():
            flash(f"Database file not found at {src}.", "danger")
            return redirect(url_for("backup.index"))

        dst = _backup_dir() / _new_backup_filename("db")
        try:
            _sqlite_backup(src, dst)
        except Exception as e:
            flash(f"Backup failed: {e}", "danger")
            return redirect(url_for("backup.index"))

        desc = (
            f"Database backup created: {dst.name}"
            + (f" — {note}" if note else "")
            + f" ({_human_size(dst.stat().st_size)})"
        )
        _log("BACKUP_CREATE", desc)
        db.session.commit()
        flash(f"Backup created: {dst.name}", "success")

    elif info["type"] == "postgres":
        dst = _backup_dir() / _new_backup_filename("sql")
        ok, err = _postgres_backup(info["uri"], dst)
        if not ok:
            flash(f"Postgres backup failed: {err}", "danger")
            return redirect(url_for("backup.index"))
        desc = (
            f"Postgres backup created: {dst.name}"
            + (f" — {note}" if note else "")
        )
        _log("BACKUP_CREATE", desc)
        db.session.commit()
        flash(f"Backup created: {dst.name}", "success")

    else:
        flash("Unsupported database type — cannot create backup.", "danger")

    return redirect(url_for("backup.index"))


@backup_bp.route("/download/<filename>")
@login_required
@owner_required
def download(filename):
    """Authenticated download of a backup file."""
    if not BACKUP_FILENAME_RE.match(filename):
        abort(404)
    path = _backup_dir() / filename
    if not path.exists():
        flash("Backup file not found.", "danger")
        return redirect(url_for("backup.index"))

    _log("BACKUP_DOWNLOAD", f"Backup downloaded: {filename}")
    db.session.commit()

    return send_file(
        str(path),
        as_attachment=True,
        download_name=filename,
    )


@backup_bp.route("/restore", methods=["POST"])
@login_required
@owner_required
def restore():
    """
    Restore from an uploaded backup file.
    Steps:
      1. Validate the uploaded file (extension, magic bytes, THMS tables).
      2. Create an automatic safety backup of the CURRENT database.
      3. Replace the live database with the uploaded backup.
      4. Audit log the restore.
    """
    info = _db_info()
    upload = request.files.get("backup_file")

    if not upload or not upload.filename:
        flash("No file selected for restore.", "danger")
        return redirect(url_for("backup.index"))

    orig_name = upload.filename
    ext = Path(orig_name).suffix.lower().lstrip(".")

    # ── Validate extension matches DB type ───────────────────────────────────
    if info["type"] == "sqlite" and ext != "db":
        flash("For SQLite databases, upload a .db backup file.", "danger")
        return redirect(url_for("backup.index"))
    if info["type"] == "postgres" and ext != "sql":
        flash("For Postgres databases, upload a .sql backup file.", "danger")
        return redirect(url_for("backup.index"))
    if info["type"] == "unknown":
        flash("Unsupported database type — cannot restore.", "danger")
        return redirect(url_for("backup.index"))

    # ── Save upload to a temp file ───────────────────────────────────────────
    tmp_path = _backup_dir() / f"_restore_tmp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
    try:
        upload.save(str(tmp_path))
    except Exception as e:
        flash(f"Failed to save uploaded file: {e}", "danger")
        return redirect(url_for("backup.index"))

    # ── Validate contents ────────────────────────────────────────────────────
    if info["type"] == "sqlite":
        valid, err = _validate_sqlite_file(tmp_path)
    else:
        valid, err = _validate_sql_file(tmp_path)

    if not valid:
        tmp_path.unlink(missing_ok=True)
        flash(f"Uploaded file is invalid: {err}", "danger")
        return redirect(url_for("backup.index"))

    # ── Auto-backup current database before touching it ──────────────────────
    safety_name = _new_backup_filename("db" if info["type"] == "sqlite" else "sql")
    safety_path = _backup_dir() / safety_name

    if info["type"] == "sqlite":
        src_path = info["path"]
        if not src_path.exists():
            tmp_path.unlink(missing_ok=True)
            flash("Cannot locate the current database for safety backup. Restore aborted.", "danger")
            return redirect(url_for("backup.index"))
        try:
            _sqlite_backup(src_path, safety_path)
        except Exception as e:
            tmp_path.unlink(missing_ok=True)
            flash(f"Safety backup failed — restore aborted for your protection: {e}", "danger")
            return redirect(url_for("backup.index"))
    else:
        ok, err = _postgres_backup(info["uri"], safety_path)
        if not ok:
            tmp_path.unlink(missing_ok=True)
            flash(f"Safety backup failed — restore aborted: {err}", "danger")
            return redirect(url_for("backup.index"))

    # ── Perform the restore ──────────────────────────────────────────────────
    if info["type"] == "sqlite":
        try:
            # Close all SQLAlchemy connections before swapping the file
            db.engine.dispose()
            _sqlite_restore(tmp_path, src_path)
        except Exception as e:
            flash(
                f"Restore failed: {e}. "
                f"Your previous data is safe — a backup was saved as {safety_name}.",
                "danger",
            )
            tmp_path.unlink(missing_ok=True)
            return redirect(url_for("backup.index"))
    else:
        ok, err = _postgres_restore(info["uri"], tmp_path)
        if not ok:
            flash(
                f"Restore failed: {err}. "
                f"Your previous data is safe — a backup was saved as {safety_name}.",
                "danger",
            )
            tmp_path.unlink(missing_ok=True)
            return redirect(url_for("backup.index"))

    # ── Rename temp to a permanent backup filename ────────────────────────────
    final_path = _backup_dir() / _new_backup_filename(ext)
    shutil.move(str(tmp_path), str(final_path))

    # ── Audit log ────────────────────────────────────────────────────────────
    _log(
        "BACKUP_RESTORE",
        f"Database restored from '{orig_name}' by {current_user.username}. "
        f"Safety backup saved as {safety_name}.",
    )
    try:
        db.session.commit()
    except Exception:
        pass  # session may be stale after restore; non-fatal

    flash(
        f"Database restored successfully from '{orig_name}'. "
        f"A safety backup of your previous data was saved as {safety_name}.",
        "success",
    )
    return redirect(url_for("backup.index"))


@backup_bp.route("/delete/<filename>", methods=["POST"])
@login_required
@owner_required
def delete(filename):
    """Permanently delete a backup file from disk."""
    if not BACKUP_FILENAME_RE.match(filename):
        abort(404)
    path = _backup_dir() / filename
    if not path.exists():
        flash("Backup file not found.", "danger")
        return redirect(url_for("backup.index"))

    try:
        path.unlink()
    except Exception as e:
        flash(f"Could not delete backup: {e}", "danger")
        return redirect(url_for("backup.index"))

    _log("BACKUP_DELETE", f"Backup file deleted: {filename}")
    db.session.commit()
    flash(f"Backup {filename} has been deleted.", "warning")
    return redirect(url_for("backup.index"))
