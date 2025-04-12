#!/bin/bash

# 檢查腳本 - 方便手動運行檢查

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 顯示選項菜單
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}        前端項目檢查工具            ${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}請選擇要運行的檢查:${NC}"
echo -e "  ${GREEN}1)${NC} 快速檢查 (僅類型檢查)"
echo -e "  ${GREEN}2)${NC} 完整檢查 (lint + 類型檢查 + 構建)"
echo -e "  ${GREEN}3)${NC} 運行所有檢查並修復可自動修復的問題"
echo -e "  ${GREEN}0)${NC} 退出"
echo -e "${BLUE}========================================${NC}"
echo -n "請輸入選項 [0-3]: "
read -r option

case $option in
  1)
    echo -e "${YELLOW}執行快速檢查...${NC}"
    bun run quick-check
    ;;
  2)
    echo -e "${YELLOW}執行完整檢查...${NC}"
    bun run full-check
    ;;
  3)
    echo -e "${YELLOW}執行自動修復...${NC}"
    bun run lint --fix
    echo -e "${YELLOW}執行類型檢查...${NC}"
    bun run typecheck
    echo -e "${YELLOW}嘗試構建...${NC}"
    bun run build
    ;;
  0)
    echo -e "${BLUE}退出檢查工具${NC}"
    exit 0
    ;;
  *)
    echo -e "${RED}無效選項!${NC}"
    exit 1
    ;;
esac

# 檢查結果
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ 檢查成功!${NC}"
else
  echo -e "${RED}❌ 檢查失敗! 請修復問題後再試.${NC}"
fi
