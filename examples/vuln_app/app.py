import os
import pickle
import sqlite3
import subprocess
import hashlib
import yaml


def get_user_by_name(conn: sqlite3.Connection, username: str):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return conn.execute(query).fetchall()


def deserialize_profile(blob: bytes):
    return pickle.loads(blob)


def run_user_command(user_cmd: str):
    return subprocess.run(user_cmd, shell=True, capture_output=True, text=True)


def weak_password_hash(password: str):
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def load_config(raw: str):
    return yaml.load(raw)


def read_file(base_dir: str, filename: str):
    path = os.path.join(base_dir, filename)
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()
