# Student Task Manager

This is a Student Task Manager CRUD project with a Flask and SQLite backend and a plain HTML, CSS, and JavaScript frontend.

## Run with Docker Compose

From the repository root, build and start both services:

```sh
docker compose up --build
```

Open the frontend at <http://localhost:8000>. The frontend container proxies task API requests to the backend service over the Compose network. The backend API is also available at <http://localhost:5000>, and SQLite data is stored in the `task_data` named volume.

Stop the services with `docker compose down`. The named data volume remains available across container restarts.

## Project tools

The project uses Docker Compose for local deployment. Jenkins, Terraform, Ansible, and AWS EC2 are planned for later phases, with AWS Lambda and DynamoDB considered for a later iteration.
