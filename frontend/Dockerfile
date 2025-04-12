# 依賴項安裝階段
FROM oven/bun:1 AS deps

WORKDIR /app

# 只複製 package.json 和 lockfile
COPY package.json bun.lockb* ./

# 安裝依賴，但不執行 postinstall 腳本
RUN sed -i 's/"postinstall": "node hooks\/setup.js"/"postinstall": ""/' package.json && \
    bun install --no-optional && \
    bun add -d @rollup/rollup-linux-arm64-gnu

# 構建階段
FROM oven/bun:1 AS builder

WORKDIR /app

# 從依賴項階段複製 node_modules
COPY --from=deps /app/node_modules ./node_modules

# 複製源代碼，但不包括 hooks 目錄
COPY . .
RUN rm -rf hooks

# 設置生產環境變量
# ENV NODE_ENV=production
# ENV VITE_API_URL=/api

# 構建應用
RUN bun run build

# 生產運行階段
FROM nginx:alpine AS production

# 複製 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 從構建階段複製構建結果
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露 80 端口
EXPOSE 80

# 啟動 nginx
CMD ["nginx", "-g", "daemon off;"]
