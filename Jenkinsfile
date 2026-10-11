
pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    parameters {
        string(
            name: 'EC2_HOST',
            defaultValue: '13.126.17.162',
            description: 'Public IPv4 address of the AWS EC2 instance'
        )
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

        stage('Deploy to EC2') {
            steps {
                withCredentials([sshUserPrivateKey(
                    credentialsId: 'ec2-deploy-key',
                    keyFileVariable: 'EC2_KEY',
                    usernameVariable: 'EC2_USER'
                )]) {
                    sh '''
                        set -eu

                        ssh -i "$EC2_KEY" \
                            -o StrictHostKeyChecking=accept-new \
                            -o ConnectTimeout=15 \
                            "$EC2_USER@$EC2_HOST" \
                            'cd ~/student-tasks-manager && git pull --ff-only origin main && docker compose up -d --build && docker compose ps'
                    '''
                    //trying to set continuoues CI/CD
                }
            }
        }
    }
}
