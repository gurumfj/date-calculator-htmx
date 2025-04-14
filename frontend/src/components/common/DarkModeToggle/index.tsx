import React, { useEffect, useState } from 'react';
import { isFeatureEnabled, FEATURES } from '../../../utils/featureFlags';

/**
 * 深色模式切換組件
 * 
 * 只有在 DARK_MODE 功能開關啟用時才會顯示
 */
const DarkModeToggle: React.FC = () => {
  const [darkMode, setDarkMode] = useState(false);
  const isDarkModeEnabled = isFeatureEnabled(FEATURES.DARK_MODE);

  // 切換深色模式
  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    
    if (newMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  // 初始化時設置深色模式狀態
  useEffect(() => {
    const isDark = localStorage.getItem('darkMode') === 'true';
    setDarkMode(isDark);
    
    if (isDark) {
      document.documentElement.classList.add('dark');
    }
  }, []);

  // 保存設置到本地存儲
  useEffect(() => {
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  // 如果深色模式功能開關未啟用，不顯示此組件
  if (!isDarkModeEnabled) {
    return null;
  }

  return (
    <button
      onClick={toggleDarkMode}
      className="fixed top-4 right-4 bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-white p-2 rounded-full shadow-md z-50"
      aria-label={darkMode ? '切換到亮色模式' : '切換到深色模式'}
    >
      {darkMode ? (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
      ) : (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
          />
        </svg>
      )}
    </button>
  );
};

export default DarkModeToggle;
