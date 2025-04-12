import { Dispatch, SetStateAction } from 'react';
import { SupabaseHookState } from './types';

/**
 * 更新 hook 狀態
 * @param state 當前狀態
 * @param setData 更新數據的函數
 * @param setError 更新錯誤的函數
 * @param setLoading 更新加載狀態的函數
 * @param loading 是否加載中
 * @param error 錯誤信息
 * @param data 新數據
 */
export const updateHookState = <T>(
  state: SupabaseHookState<T>,
  setData: Dispatch<SetStateAction<T[] | null>>,
  setError: Dispatch<SetStateAction<Error | null>>,
  setLoading: Dispatch<SetStateAction<boolean>>,
  loading?: boolean,
  error?: Error | null,
  data?: T[] | null
): void => {
  if (!state.isMounted.current) return;

  if (loading !== undefined) {
    setLoading(loading);
  }

  if (error !== undefined) {
    setError(error);
  }

  if (data !== undefined) {
    setData(data);
  }
};

/**
 * 本地更新新增操作後的狀態
 * @param state 當前狀態
 * @param setData 更新數據的函數
 * @param newItem 新增的項目
 */
export const updateStateAfterInsert = <T>(
  state: SupabaseHookState<T>,
  setData: Dispatch<SetStateAction<T[] | null>>,
  newItem: T
): void => {
  if (!state.isMounted.current) return;

  setData(prev => {
    const newData = prev ? [...prev, newItem] : [newItem];
    return newData;
  });
};

/**
 * 本地更新修改操作後的狀態
 * @param state 當前狀態
 * @param setData 更新數據的函數
 * @param id 修改的項目ID
 * @param updatedItem 修改後的項目
 * @param idField 主鍵欄位名
 */
export const updateStateAfterUpdate = <T>(
  state: SupabaseHookState<T>,
  setData: Dispatch<SetStateAction<T[] | null>>,
  id: string,
  updatedItem: T,
  idField: string
): void => {
  if (!state.isMounted.current) return;

  setData(prev => {
    if (!prev) return prev;
    return prev.map(item => 
      item[idField as keyof T] === id ? {...item, ...updatedItem} as T : item
    );
  });
};

/**
 * 本地更新刪除操作後的狀態
 * @param state 當前狀態
 * @param setData 更新數據的函數
 * @param id 刪除的項目ID
 * @param idField 主鍵欄位名
 */
export const updateStateAfterRemove = <T>(
  state: SupabaseHookState<T>,
  setData: Dispatch<SetStateAction<T[] | null>>,
  id: string,
  idField: string
): void => {
  if (!state.isMounted.current) return;

  setData(prev => {
    if (!prev) return prev;
    return prev.filter(item => item[idField as keyof T] !== id);
  });
};
