"""Server-side storage for the app: who is signed in, and each user's history.

Everything lives in RIZZML_HOME (default ui/.rizzml, git-ignored), so it survives restarts:
    history.db   uploads, analyses and downloaded files, per user (SQLite)
    uploads/     the raw files of every upload, so History can reopen an analysis
    files/       a copy of every file a user downloaded, so History can hand it out again
    secret       key that signs the login cookie

    python ui/store.py   # self-check in a temporary folder
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path

HOME = Path(os.environ.get("RIZZML_HOME", Path(__file__).parent / ".rizzml"))

# ponytail: one shared demo account and no real authentication, as asked for the prototype.
# Swap for SOCAR's directory (LDAP / SSO) before anyone relies on it.
USERS = {"rizzman@socar.az": "guessme"}


def uploads() -> Path:
    return HOME / "uploads"


# ------------------------------------------------------------------------------------ sign-in
def check(email: str, password: str) -> str | None:
    """The normalised email if the pair is a known account, else None."""
    email = (email or "").strip().lower()
    return email if email in USERS and hmac.compare_digest(USERS[email], password or "") else None


def _secret() -> bytes:
    f = HOME / "secret"
    if not f.exists():
        HOME.mkdir(parents=True, exist_ok=True)
        f.write_bytes(os.urandom(32))
    return f.read_bytes()


def token(user: str) -> str:
    """Cookie value that remembers the user in this browser; signed, so it cannot be edited into another user."""
    name = base64.urlsafe_b64encode(user.encode()).decode().rstrip("=")
    return f"{name}.{hmac.new(_secret(), user.encode(), 'sha256').hexdigest()[:32]}"


def user_from(cookie: str | None) -> str | None:
    try:
        name, _ = (cookie or "").split(".")
        user = base64.urlsafe_b64decode(name + "=" * (-len(name) % 4)).decode()
    except ValueError:
        return None
    return user if user in USERS and hmac.compare_digest(token(user), cookie) else None


# ------------------------------------------------------------------------------------ history
def _db() -> sqlite3.Connection:
    HOME.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(HOME / "history.db")
    c.execute("create table if not exists events (id integer primary key, user text not null, ts real not null,"
              " kind text not null, title text not null, data_key text, path text, size integer)")
    return c


def log(user: str, kind: str, title: str, data_key: str | None = None, path: Path | None = None,
        size: int | None = None) -> None:
    """kind: upload | analysis | file."""
    with closing(_db()) as c, c:
        c.execute("insert into events (user, ts, kind, title, data_key, path, size) values (?, ?, ?, ?, ?, ?, ?)",
                  (user, time.time(), kind, title, data_key, str(path) if path else None, size))


def keep(user: str, name: str, data: bytes | str, title: str) -> None:
    """Store a copy of a file the user downloaded and log it."""
    data = data.encode() if isinstance(data, str) else data
    folder = HOME / "files" / hashlib.sha1(user.encode()).hexdigest()[:12]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{time.strftime('%Y%m%d-%H%M%S')}_{re.sub(r'[^\w.-]', '_', name)}"
    path.write_bytes(data)
    log(user, "file", title, path=path, size=len(data))


def events(user: str, limit: int = 100) -> list[dict]:
    """This user's history, newest first."""
    with closing(_db()) as c:
        c.row_factory = sqlite3.Row
        return [dict(e) for e in c.execute("select * from events where user = ? order by ts desc, id desc limit ?",
                                           (user, limit))]


if __name__ == "__main__":
    import tempfile
    HOME = Path(tempfile.mkdtemp())
    a, b = "rizzman@socar.az", "someone@socar.az"
    assert check(" RizzMan@socar.az ", "guessme") == a and check(a, "nope") is None and check(b, "guessme") is None
    assert user_from(token(a)) == a and user_from(token(a)[:-1] + "0") is None and user_from("junk") is None
    log(a, "upload", "high_freq_data.csv", data_key="abc", size=10)
    keep(a, "rates.csv", "x,y\n1,2\n", "Daily rates (CSV)")
    log(b, "analysis", "someone else's", data_key="sample")
    mine = events(a)
    assert [e["kind"] for e in mine] == ["file", "upload"] and Path(mine[0]["path"]).read_text() == "x,y\n1,2\n"
    assert [e["title"] for e in events(b)] == ["someone else's"]
    print("OK: sign-in, signed cookie, per-user history and stored files")
