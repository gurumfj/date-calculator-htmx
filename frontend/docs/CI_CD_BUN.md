# Bun CI/CD 配置指南

本文檔提供了在不同 CI/CD 環境中使用 Bun 的配置指南。

## 目錄

1. [GitHub Actions](#github-actions)
2. [Docker 配置](#docker-配置)
3. [GitLab CI/CD](#gitlab-cicd)
4. [Jenkins](#jenkins)
5. [CircleCI](#circleci)

## GitHub Actions

我們已經在 `.github/workflows/bun-ci.yml` 中提供了 GitHub Actions 的配置。此配置會在每次推送到 main/master 分支或創建 Pull Request 時運行。

主要步驟包括：
- 設置 Bun 環境
- 安裝依賴
- 運行 Lint 檢查
- 運行 TypeScript 類型檢查
- 構建應用

## Docker 配置

我們已經更新了 `Dockerfile` 和 `docker-compose.dev.yaml` 以使用 Bun 替代 Node.js。

### 開發環境

在開發環境中，我們使用 `docker-compose.dev.yaml`：

```bash
docker-compose -f docker-compose.dev.yaml up
```

### 生產環境

在生產環境中，我們使用 `docker-compose.yaml`：

```bash
docker-compose up -d
```

## GitLab CI/CD

如果你使用 GitLab CI/CD，可以創建一個 `.gitlab-ci.yml` 文件：

```yaml
image: oven/bun:1

stages:
  - test
  - build
  - deploy

variables:
  BUN_INSTALL_CACHE: .bun-cache

cache:
  paths:
    - $BUN_INSTALL_CACHE

before_script:
  - cd frontend
  - bun install --cache=$BUN_INSTALL_CACHE

lint:
  stage: test
  script:
    - bun run lint

typecheck:
  stage: test
  script:
    - bunx --bun tsc --noEmit

build:
  stage: build
  script:
    - bun run build
  artifacts:
    paths:
      - frontend/dist/
```

## Jenkins

在 Jenkins 中，你可以使用 Docker 或直接安裝 Bun：

```groovy
pipeline {
    agent {
        docker {
            image 'oven/bun:1'
        }
    }
    stages {
        stage('Install') {
            steps {
                dir('frontend') {
                    sh 'bun install'
                }
            }
        }
        stage('Lint') {
            steps {
                dir('frontend') {
                    sh 'bun run lint'
                }
            }
        }
        stage('Build') {
            steps {
                dir('frontend') {
                    sh 'bun run build'
                }
            }
        }
    }
}
```

## CircleCI

對於 CircleCI，你可以創建一個 `.circleci/config.yml` 文件：

```yaml
version: 2.1

jobs:
  build:
    docker:
      - image: oven/bun:1
    steps:
      - checkout
      - restore_cache:
          keys:
            - bun-deps-{{ checksum "frontend/package.json" }}
      - run:
          name: Install Dependencies
          command: cd frontend && bun install
      - save_cache:
          paths:
            - frontend/node_modules
          key: bun-deps-{{ checksum "frontend/package.json" }}
      - run:
          name: Lint
          command: cd frontend && bun run lint
      - run:
          name: Build
          command: cd frontend && bun run build
      - persist_to_workspace:
          root: frontend
          paths:
            - dist

workflows:
  version: 2
  build-and-deploy:
    jobs:
      - build
```

## 性能比較

使用 Bun 替代 Node.js 可以帶來以下優勢：

1. **更快的安裝速度**：Bun 的包管理器比 npm 快 30-50 倍
2. **更快的構建速度**：Bun 的構建工具比 Webpack 快 4-5 倍
3. **更低的資源消耗**：Bun 的記憶體使用量比 Node.js 低 30-40%

這些優勢在 CI/CD 環境中尤為明顯，可以顯著減少構建時間和資源消耗。
