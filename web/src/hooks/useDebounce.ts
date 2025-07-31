import { useState, useEffect, useCallback, useRef } from 'react';

// 防抖值Hook
export function useDebounceValue<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// 防抖函数Hook
export function useDebounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  return useCallback(
    ((...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        func(...args);
      }, delay);
    }) as T,
    [func, delay]
  );
}

// 防抖搜索Hook
export function useDebounceSearch(initialValue: string = '', delay: number = 300) {
  const [searchTerm, setSearchTerm] = useState(initialValue);
  const debouncedSearchTerm = useDebounceValue(searchTerm, delay);

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  }, []);

  const clearSearch = useCallback(() => {
    setSearchTerm('');
  }, []);

  return {
    searchTerm,
    debouncedSearchTerm,
    handleSearchChange,
    clearSearch,
    setSearchTerm
  };
}