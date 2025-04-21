#!/bin/bash
# merge-frontend-subtree.sh
# 用於從前端倉庫更新後端倉庫中的frontend子目錄
# 作者: Pierre Wu
# 日期: 2025-04-22

set -e  # 任何命令失敗時立即停止腳本執行

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 前端倉庫URL
FRONTEND_REPO="https://github.com/gurumfj/cleansales-frontend.git"
FRONTEND_BRANCH="main"
SUBTREE_PREFIX="frontend"

# 顯示腳本說明
echo -e "${BLUE}=== CleanSales 前端 Subtree 合併工具 ===${NC}"
echo -e "此腳本將從前端倉庫更新後端倉庫中的${SUBTREE_PREFIX}子目錄"
echo -e "前端倉庫: ${FRONTEND_REPO}"
echo -e "分支: ${FRONTEND_BRANCH}\n"

# 檢查當前目錄是否為後端倉庫根目錄
if [ ! -d ".git" ]; then
  echo -e "${RED}錯誤: 請在後端倉庫根目錄執行此腳本${NC}"
  exit 1
fi

# 確認用戶是否想要繼續
echo -e "${YELLOW}警告: 在執行操作前，建議先確保當前的工作目錄是乾淨的，且所有本地更改已提交。${NC}"
read -p "是否繼續? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo -e "${RED}操作取消${NC}"
  exit 0
fi

# 步驟1: 檢查並創建備份分支
echo -e "\n${BLUE}步驟 1: 創建備份分支${NC}"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
BACKUP_BRANCH="backup-before-subtree-merge-$(date +%Y%m%d-%H%M%S)"

echo -e "當前分支: ${CURRENT_BRANCH}"
echo -e "創建備份分支: ${BACKUP_BRANCH}"

git branch $BACKUP_BRANCH
echo -e "${GREEN}✓ 已創建備份分支${NC}"

# 步驟2: 檢查frontend子目錄是否已是subtree
echo -e "\n${BLUE}步驟 2: 檢查frontend子目錄${NC}"
if [ ! -d "$SUBTREE_PREFIX" ]; then
  echo -e "${YELLOW}警告: $SUBTREE_PREFIX 目錄不存在，將執行初始添加操作${NC}"
  echo -e "將執行: git subtree add --prefix=$SUBTREE_PREFIX $FRONTEND_REPO $FRONTEND_BRANCH --squash"
  read -p "是否繼續? (y/n): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}操作取消${NC}"
    exit 0
  fi

  git subtree add --prefix=$SUBTREE_PREFIX $FRONTEND_REPO $FRONTEND_BRANCH --squash
  echo -e "${GREEN}✓ 成功添加subtree${NC}"
else
  echo -e "${GREEN}✓ $SUBTREE_PREFIX 目錄已存在${NC}"
fi

# 步驟3: 從前端倉庫拉取最新更改
echo -e "\n${BLUE}步驟 3: 從前端倉庫拉取最新更改${NC}"
echo -e "將執行: git subtree pull --prefix=$SUBTREE_PREFIX $FRONTEND_REPO $FRONTEND_BRANCH --squash"

# 讓用戶確認拉取操作
read -p "是否繼續? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo -e "${RED}操作取消${NC}"
  exit 0
fi

# 使用--no-verify跳過pre-push檢查
git subtree pull --prefix=$SUBTREE_PREFIX $FRONTEND_REPO $FRONTEND_BRANCH --squash --no-verify
PULL_RESULT=$?

if [ $PULL_RESULT -eq 0 ]; then
  echo -e "${GREEN}✓ 成功從前端倉庫拉取最新更改${NC}"
else
  echo -e "${RED}× 拉取失敗，請檢查日誌以獲取更多信息${NC}"
  echo -e "${YELLOW}提示: 如果出現衝突，您需要手動解決衝突後提交更改${NC}"
  exit 1
fi

# 步驟4: 顯示倉庫狀態
echo -e "\n${BLUE}步驟 4: 顯示當前倉庫狀態${NC}"
git status

# 結束說明
echo -e "\n${GREEN}=== 操作完成 ===${NC}"
echo -e "備份分支 ${BACKUP_BRANCH} 已創建，以備需要時使用"
echo -e "前端目錄 ${SUBTREE_PREFIX} 已使用subtree更新"
echo -e "\n${YELLOW}注意:${NC}"
echo -e "1. 如需將變更推送到遠端，請執行: git push"
echo -e "2. 如發現問題需要回退，請執行: git checkout ${BACKUP_BRANCH}"
echo -e "   然後執行: git branch -D ${CURRENT_BRANCH} && git checkout -b ${CURRENT_BRANCH}"
echo -e "3. 運行 'git log' 查看最新的合併提交與變更歷史"
