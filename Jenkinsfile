pipeline {
    agent any

    // ==================== 环境变量 ====================
    environment {
        APP_NAME       = 'deep-search-pro'
        APP_PORT       = '8000'
        HOST_PORT      = '8000'
        IMAGE_TAG      = "${APP_NAME}:${BUILD_NUMBER}"
        IMAGE_LATEST   = "${APP_NAME}:latest"
        CONTAINER_NAME = 'python-agent-app'
        HEALTH_URL     = "http://localhost:${HOST_PORT}/health"
    }

    options {
        timestamps()                    // 显示时间戳
        timeout(time: 15, unit: 'MINUTES')  // 超时保护
        disableConcurrentBuilds()       // 禁止并发构建
        buildDiscarder(logRotator(numToKeepStr: '10'))  // 保留最近10次构建
    }

    stages {
        // ==================== 阶段1: 拉取代码 ====================
        stage('Checkout') {
            steps {
                echo "📥 拉取代码..."
                checkout scm
                echo "✅ 代码拉取完成，分支: ${env.BRANCH_NAME ?: 'main'}"
            }
        }

        // ==================== 阶段2: 依赖安装验证（项目暂无单元测试） ====================
        stage('Test') {
            steps {
                echo "🧪 验证依赖可正常安装..."
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
                    python -c "import fastapi, langchain, qdrant_client; print('核心依赖导入正常')"
                '''
            }
            post {
                always {
                    sh 'rm -rf .venv'
                }
            }
        }

        // ==================== 阶段3: 构建 Docker 镜像 ====================
        stage('Build Image') {
            steps {
                echo "🔨 构建 Docker 镜像: ${IMAGE_TAG}"
                sh """
                    docker build -t ${IMAGE_TAG} .
                    docker tag ${IMAGE_TAG} ${IMAGE_LATEST}
                """
                echo "✅ 镜像构建完成"
            }
        }

        // ==================== 阶段4: 部署 ====================
        stage('Deploy') {
            steps {
                echo "🚀 开始部署..."
                // 从 Jenkins 凭据中取出 .env 文件（需在 Jenkins 中创建 File 类型凭据，ID 为 app-env-file，
                // 内容为完整的 .env：MYSQL_*、QDRANT_*、OPENAI_API_KEY、TAVILY_API_KEY 等）
                withCredentials([file(credentialsId: 'app-env-file', variable: 'ENV_FILE')]) {
                    sh """
                        # 停止并删除旧容器（如果存在）
                        if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}\$"; then
                            echo "停止旧容器 ${CONTAINER_NAME}..."
                            docker stop ${CONTAINER_NAME} || true
                            docker rm ${CONTAINER_NAME} || true
                        fi
        
                        # 启动新容器
                        # --add-host 使容器内可通过 host.docker.internal 访问宿主机上的 MySQL/Qdrant
                        docker run -d \\
                            --name ${CONTAINER_NAME} \\
                            --restart=unless-stopped \\
                            -p ${HOST_PORT}:${APP_PORT} \\
                            --add-host=host.docker.internal:host-gateway \\
                            --env-file "\$ENV_FILE" \\
                            ${IMAGE_TAG}
        
                        echo "✅ 容器已启动"
                    """
                }
            }
        }

        // ==================== 阶段5: 健康检查 ====================
        stage('Health Check') {
            steps {
                echo "🏥 执行健康检查..."
                sh """
                    echo "等待服务启动..."
                    sleep 5

                    MAX_RETRIES=10
                    RETRY_COUNT=0
                    while [ \$RETRY_COUNT -lt \$MAX_RETRIES ]; do
                        HTTP_CODE=\$(curl -s -o /dev/null -w '%{http_code}' ${HEALTH_URL} || echo "000")
                        if [ "\$HTTP_CODE" = "200" ]; then
                            echo "✅ 健康检查通过！服务正常运行"
                            exit 0
                        fi
                        RETRY_COUNT=\$((RETRY_COUNT + 1))
                        echo "等待中... (\$RETRY_COUNT/\$MAX_RETRIES)"
                        sleep 3
                    done

                    echo "❌ 健康检查失败！"
                    docker logs ${CONTAINER_NAME} --tail 50
                    exit 1
                """
            }
        }

        // ==================== 阶段6: 清理旧镜像 ====================
        stage('Cleanup') {
            steps {
                echo "🧹 清理旧镜像..."
                sh """
                    # 删除悬空镜像
                    docker image prune -f

                    # 只保留最近5个版本的镜像
                    docker images ${APP_NAME} --format '{{.Tag}} {{.ID}}' | \
                        grep -v latest | \
                        sort -rn | \
                        awk 'NR>5 {print \$2}' | \
                        xargs -r docker rmi -f 2>/dev/null || true
                """
                echo "✅ 清理完成"
            }
        }
    }

    // ==================== 构建后操作 ====================
    post {
        success {
            echo """
            ╔══════════════════════════════════════╗
            ║  🎉 部署成功！                        ║
            ║  镜像: ${IMAGE_TAG}
            ║  地址: http://localhost:${HOST_PORT}
            ║  健康: ${HEALTH_URL}
            ╚══════════════════════════════════════╝
            """
        }
        failure {
            echo "❌ 构建失败！请检查日志。"
            sh """
                if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
                    echo "=== 容器日志 ==="
                    docker logs ${CONTAINER_NAME} --tail 30
                fi
            """
        }
        always {
            // 清理工作空间
            cleanWs(deleteDirs: true, notFailBuild: true)
        }
    }
}
