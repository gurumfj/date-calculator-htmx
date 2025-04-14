import { ROUTE_TITLES } from "./constants";

// 獲取當前路由標題的邏輯
export const getCurrentRouteTitle = (pathname: string): string => {
  // 精確匹配
  if (ROUTE_TITLES[pathname]) {
    return ROUTE_TITLES[pathname];
  }
  
  // 前綴匹配
  const matchingPrefix = Object.keys(ROUTE_TITLES).find(key => 
    pathname.startsWith(key)
  );
  
  return matchingPrefix ? ROUTE_TITLES[matchingPrefix] : 
    pathname.slice(1).charAt(0).toUpperCase() + 
    pathname.slice(2);
};

// 判斷哪個選項是活躍的
export const isActive = (currentPath: string, itemPath: string): boolean => {
  return (
    currentPath === itemPath ||
    (itemPath !== "/" && currentPath.startsWith(itemPath))
  );
};
