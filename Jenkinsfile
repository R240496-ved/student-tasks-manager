pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    environment {
        COMPOSE_PROJECT_NAME = 'student-task-manager'
        BACKEND_IMAGE = 'student-task-manager-backend'
        FRONTEND_IMAGE = 'student-task-manager-frontend'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                // Use the Jenkins home volume so the Python container can access
                // the workspace without relying on a host-only bind-mount path.
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --volume jenkins_home:/var/jenkins_home \
                        --workdir "$WORKSPACE" \
                        python:3.12-slim \
                        sh -c "python -m venv .venv && .venv/bin/python -m pip install --no-cache-dir -r backend/requirements.txt"
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    docker run --rm \
                        --user "$(id -u):$(id -g)" \
                        --volume jenkins_home:/var/jenkins_home \
                        --workdir "$WORKSPACE/backend" \
                        python:3.12-slim \
                        "$WORKSPACE/.venv/bin/python" -m unittest discover -s tests -v
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker compose -f docker-compose.yml -p "$COMPOSE_PROJECT_NAME" build backend frontend
                    docker image tag "$BACKEND_IMAGE:latest" "$BACKEND_IMAGE:build-$BUILD_NUMBER"
                    docker image tag "$FRONTEND_IMAGE:latest" "$FRONTEND_IMAGE:build-$BUILD_NUMBER"
                '''
            }
        }

        stage('Docker Deployment') {
            steps {
                sh '''
                    docker compose -f docker-compose.yml -p "$COMPOSE_PROJECT_NAME" up -d --no-build
                '''
            }
        }
    }
}
