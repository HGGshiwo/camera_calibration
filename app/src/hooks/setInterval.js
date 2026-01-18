
import { useRef, useEffect, useCallback } from "react";

export default function useInterval(callback, delay) {
  const savedCallback = useRef();
  const timeoutRef = useRef();
  
  // 保存最新的回调
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);
  
  // 设置递归的 setTimeout
  useEffect(() => {
    function tick() {
      savedCallback.current();
      // 重新设置下一次
      timeoutRef.current = setTimeout(tick, delay);
    }
    
    if (delay !== null) {
      timeoutRef.current = setTimeout(tick, delay);
      return () => clearTimeout(timeoutRef.current);
    }
  }, [delay]);
  
  // 提供清除函数
  const clear = useCallback(() => {
    clearTimeout(timeoutRef.current);
  }, []);
  
  return clear;
}