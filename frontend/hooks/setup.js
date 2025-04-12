#!/usr/bin/env node

/**
 * Git hooks 自動設置腳本
 * 該腳本會在 npm/bun install 後自動執行
 * 它會將專案中的 hooks 目錄中的檔案連結到 .git/hooks 目錄
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

// 獲取當前文件的目錄名
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 獲取專案根目錄
const projectRoot = path.resolve(__dirname, '..');
const hooksDir = path.resolve(projectRoot, 'hooks');
const gitHooksDir = path.resolve(projectRoot, '.git', 'hooks');

// 確保 .git/hooks 目錄存在
if (!fs.existsSync(gitHooksDir)) {
  console.error('找不到 .git/hooks 目錄，請確認這是一個 Git 倉庫');
  // 使用不同的方式退出
  console.error('退出安裝過程');
  throw new Error('Git hooks 安裝失敗');
}

// 設置 hooks
const hookFiles = [
  'pre-commit',
  'pre-push',
  'post-merge'
];

for (const hookFile of hookFiles) {
  const hookSource = path.resolve(hooksDir, hookFile);
  const hookTarget = path.resolve(gitHooksDir, hookFile);
  
  if (fs.existsSync(hookSource)) {
    // 如果目標已存在，先刪除
    if (fs.existsSync(hookTarget)) {
      fs.unlinkSync(hookTarget);
    }
    
    // 為 hook 腳本設置可執行權限
    execSync(`chmod +x ${hookSource}`);
    
    // 創建軟連結
    fs.symlinkSync(hookSource, hookTarget);
    console.log(`已設置 ${hookFile} hook`);
  } else {
    console.warn(`警告: 找不到源文件 ${hookSource}`);
  }
}

console.log('Git hooks 設置完成!');
