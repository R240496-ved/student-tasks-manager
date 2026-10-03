"""Simple Flask API for managing student tasks."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, jsonify, request


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "tasks.db"))
TASK_FIELDS = ("title", "description", "status", "priority", "deadline")


def connect_db(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def database_connection(database_path):
    connection = connect_db(database_path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(database_path):
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    with database_connection(database_path) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT,
                priority TEXT,
                deadline TEXT
            )"""
        )


def task_to_dict(row):
    return {"id": row["id"], **{field: row[field] for field in TASK_FIELDS}}


def validate_task_payload(payload):
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."
    if not isinstance(payload.get("title"), str) or not payload["title"].strip():
        return None, "Field 'title' is required and must be a non-empty string."

    task = {field: payload.get(field) for field in TASK_FIELDS}
    task["title"] = task["title"].strip()
    for field in TASK_FIELDS[1:]:
        if task[field] is not None and not isinstance(task[field], str):
            return None, f"Field '{field}' must be a string or null."
    return task, None


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["DATABASE"] = str(DEFAULT_DATABASE)
    if test_config:
        app.config.update(test_config)

    initialize_database(app.config["DATABASE"])

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": getattr(error, "description", "Bad request.")}), 400

    @app.get("/tasks")
    def list_tasks():
        with database_connection(app.config["DATABASE"]) as connection:
            rows = connection.execute("SELECT * FROM tasks ORDER BY id").fetchall()
        return jsonify([task_to_dict(row) for row in rows])

    @app.get("/tasks/<int:task_id>")
    def get_task(task_id):
        with database_connection(app.config["DATABASE"]) as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return jsonify({"error": "Task not found."}), 404
        return jsonify(task_to_dict(row))

    @app.post("/tasks")
    def create_task():
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json."}), 400
        task, error = validate_task_payload(request.get_json(silent=True))
        if error:
            return jsonify({"error": error}), 400
        with database_connection(app.config["DATABASE"]) as connection:
            cursor = connection.execute(
                """INSERT INTO tasks (title, description, status, priority, deadline)
                   VALUES (?, ?, ?, ?, ?)""",
                tuple(task[field] for field in TASK_FIELDS),
            )
            task_id = cursor.lastrowid
        task["id"] = task_id
        return jsonify(task), 201

    @app.put("/tasks/<int:task_id>")
    def update_task(task_id):
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json."}), 400
        task, error = validate_task_payload(request.get_json(silent=True))
        if error:
            return jsonify({"error": error}), 400
        with database_connection(app.config["DATABASE"]) as connection:
            cursor = connection.execute(
                """UPDATE tasks SET title = ?, description = ?, status = ?, priority = ?, deadline = ?
                   WHERE id = ?""",
                tuple(task[field] for field in TASK_FIELDS) + (task_id,),
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "Task not found."}), 404
        task["id"] = task_id
        return jsonify(task)

    @app.delete("/tasks/<int:task_id>")
    def delete_task(task_id):
        with database_connection(app.config["DATABASE"]) as connection:
            cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            if cursor.rowcount == 0:
                return jsonify({"error": "Task not found."}), 404
        return "", 204

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
