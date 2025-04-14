/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  // 其他環境變量...
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
