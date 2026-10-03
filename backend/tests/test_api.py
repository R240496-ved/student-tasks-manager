import json
import tempfile
import unittest
from pathlib import Path

from app import create_app


class TaskApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "test_tasks.db"
        self.app = create_app({"TESTING": True, "DATABASE": str(database)})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_sample_task(self):
        response = self.client.post(
            "/tasks",
            json={
                "title": "Study algorithms",
                "description": "Review graph traversal",
                "status": "pending",
                "priority": "high",
                "deadline": "2026-10-10",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def test_list_tasks_starts_empty(self):
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_create_get_update_and_delete_task(self):
        task = self.create_sample_task()
        self.assertEqual(set(task), {"id", "title", "description", "status", "priority", "deadline"})

        response = self.client.get(f"/tasks/{task['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["title"], "Study algorithms")

        response = self.client.put(
            f"/tasks/{task['id']}",
            json={"title": "Finish algorithms", "description": "Practice BFS", "status": "done"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "done")
        self.assertIsNone(response.get_json()["priority"])

        response = self.client.delete(f"/tasks/{task['id']}")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get(f"/tasks/{task['id']}").status_code, 404)

    def test_create_requires_non_empty_title(self):
        response = self.client.post("/tasks", json={"description": "No title"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_invalid_field_type_is_rejected(self):
        response = self.client.post("/tasks", json={"title": "Task", "priority": 2})
        self.assertEqual(response.status_code, 400)

    def test_missing_task_returns_404(self):
        self.assertEqual(self.client.get("/tasks/999").status_code, 404)
        self.assertEqual(self.client.put("/tasks/999", json={"title": "Missing"}).status_code, 404)
        self.assertEqual(self.client.delete("/tasks/999").status_code, 404)

    def test_non_json_body_returns_400(self):
        response = self.client.post("/tasks", data=json.dumps({"title": "Task"}))
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
