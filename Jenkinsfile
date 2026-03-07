pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = 'tiktok-discord-notifier'
        // กำหนดให้ดึงค่าจาก Jenkins Credentials (Secret text)
        DISCORD_WEBHOOK_URL = credentials('discord-webhook-url')
        TIKTOK_USERNAME = credentials('tiktok-username')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build & Deploy') {
            steps {
                script {
                    // Try the modern docker compose plugin first, fallback to older standalone docker-compose
                    sh 'docker compose down'
                    sh 'docker compose up -d --build'
                }
            }
        }
        
        stage('Cleanup') {
            steps {
                script {
                    // Remove dangling images
                    sh 'docker image prune -f'
                }
            }
        }
    }
    
    post {
        success {
            echo 'Deployment successful. Bot is now running.'
        }
        failure {
            echo 'Deployment failed. Check Jenkins logs for details.'
        }
    }
}
