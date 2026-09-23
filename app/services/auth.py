import base64
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from pathlib import Path

from fastapi import HTTPException

DATABASE_PATH = Path(__file__).resolve().parents[2] / "portfolio.db"
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, avatar_url TEXT, theme TEXT NOT NULL DEFAULT 'system', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
    if "avatar_url" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    if "theme" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN theme TEXT NOT NULL DEFAULT 'system'")
    return connection


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    salt_encoded, digest_encoded = stored_hash.split("$", 1)
    salt = base64.urlsafe_b64decode(salt_encoded.encode())
    expected = base64.urlsafe_b64decode(digest_encoded.encode())
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return hmac.compare_digest(actual, expected)


def _token_for_user(user_id: int) -> str:
    payload = f"{user_id}:{int(time.time()) + TOKEN_TTL_SECONDS}"
    secret = os.getenv("AUTH_SECRET", "change-this-development-secret").encode()
    signature = hmac.new(secret, payload.encode(), hashlib.sha256).digest()
    return f"{base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"


def _user_response(user: sqlite3.Row) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "avatar_url": user["avatar_url"],
        "theme": user["theme"] or "system",
    }


def register_user(name: str, email: str, password: str) -> dict:
    connection = _connection()
    try:
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name.strip(), email.strip().lower(), _hash_password(password)),
        )
        connection.commit()
        user = connection.execute(
            "SELECT id, name, email, avatar_url, theme FROM users WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Email is already registered.") from error
    finally:
        connection.close()
    return {"user": _user_response(user), "token": _token_for_user(user["id"])}


def login_user(email: str, password: str) -> dict:
    connection = _connection()
    try:
        user = connection.execute(
            "SELECT id, name, email, password_hash, avatar_url, theme FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    finally:
        connection.close()

    if not user or not _verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {"user": _user_response(user), "token": _token_for_user(user["id"])}


def user_from_token(token: str) -> dict:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        payload = base64.urlsafe_b64decode(encoded_payload + "===").decode()
        user_id_text, expiry_text = payload.split(":", 1)
        signature = base64.urlsafe_b64decode(encoded_signature + "===")
        secret = os.getenv("AUTH_SECRET", "change-this-development-secret").encode()
        expected = hmac.new(secret, payload.encode(), hashlib.sha256).digest()
        if int(expiry_text) < time.time() or not hmac.compare_digest(signature, expected):
            raise ValueError
        user_id = int(user_id_text)
    except (ValueError, TypeError, IndexError, UnicodeDecodeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    connection = _connection()
    try:
        user = connection.execute(
            "SELECT id, name, email, avatar_url, theme FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        connection.close()
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists.")
    return _user_response(user)


def update_user_profile(user_id: int, name: str | None, avatar_url: str | None, theme: str | None) -> dict:
    connection = _connection()
    try:
        current = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="User not found.")
        updated_name = name.strip() if name is not None else current["name"]
        if len(updated_name) < 2:
            raise HTTPException(status_code=400, detail="Name must be at least 2 characters.")
        connection.execute(
            "UPDATE users SET name = ?, avatar_url = ?, theme = ? WHERE id = ?",
            (updated_name, avatar_url if avatar_url is not None else current["avatar_url"], theme or current["theme"], user_id),
        )
        connection.commit()
        updated = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        connection.close()
    return _user_response(updated)


def change_user_password(user_id: int, current_password: str, new_password: str) -> None:
    connection = _connection()
    try:
        user = connection.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or not _verify_password(current_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (_hash_password(new_password), user_id),
        )
        connection.commit()
    finally:
        connection.close()