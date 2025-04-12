import React, { useRef, useState, useEffect } from 'react';

interface PullToRefreshProps {
  onRefresh: () => Promise<void>;
  children: React.ReactNode;
  pullDownThreshold?: number;
  maxPullDownDistance?: number;
  refreshIndicatorHeight?: number;
  backgroundColor?: string;
  pullingContent?: React.ReactNode;
  refreshingContent?: React.ReactNode;
  spinnerColor?: string;
}

const PullToRefresh: React.FC<PullToRefreshProps> = ({
  onRefresh,
  children,
  pullDownThreshold = 80,
  maxPullDownDistance = 120,
  refreshIndicatorHeight = 60,
  backgroundColor = 'white',
  pullingContent,
  refreshingContent,
  spinnerColor = '#0088FE',
}) => {
  const [isPulling, setIsPulling] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const startY = useRef<number | null>(null);
  const currentY = useRef<number | null>(null);

  // 預設的下拉指示器內容 - 下拉中
  const defaultPullingContent = (
    <div className="flex items-center justify-center h-full text-gray-500">
      <svg
        className={`animate-spin h-5 w-5 mr-2 ${pullDistance > pullDownThreshold ? 'opacity-100' : 'opacity-50'}`}
        fill="none"
        viewBox="0 0 24 24"
        style={{ transform: `rotate(${Math.min(pullDistance / pullDownThreshold * 360, 360)}deg)` }}
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        ></circle>
        <path
          className="opacity-75"
          fill={spinnerColor}
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
      <span>{pullDistance > pullDownThreshold ? '鬆開重新整理' : '下拉重新整理'}</span>
    </div>
  );

  // 預設的下拉指示器內容 - 重新整理中
  const defaultRefreshingContent = (
    <div className="flex items-center justify-center h-full text-gray-500">
      <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill={spinnerColor} d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span>重新整理中...</span>
    </div>
  );

  // 處理觸摸事件
  const handleTouchStart = (e: React.TouchEvent) => {
    // 只有在頂部才允許下拉刷新
    if (containerRef.current && containerRef.current.scrollTop === 0) {
      startY.current = e.touches[0].clientY;
      setIsPulling(true);
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (isPulling && startY.current !== null && !isRefreshing) {
      currentY.current = e.touches[0].clientY;
      const distance = Math.max(0, currentY.current - startY.current);

      // 應用阻尼效果，使下拉感覺更自然
      const dampedDistance = Math.min(
        distance * 0.4, // 阻尼系數
        maxPullDownDistance
      );

      setPullDistance(dampedDistance);
    }
  };

  const handleTouchEnd = async () => {
    if (isPulling && !isRefreshing) {
      if (pullDistance > pullDownThreshold) {
        // 觸發刷新
        setIsRefreshing(true);

        try {
          await onRefresh();
        } catch (error) {
          console.error('刷新失敗:', error);
        } finally {
          // 延遲重置，使動畫更流暢
          setTimeout(() => {
            setIsRefreshing(false);
            setPullDistance(0);
            setIsPulling(false);
          }, 300);
        }
      } else {
        // 未達到閾值，重置
        setPullDistance(0);
        setIsPulling(false);
      }
    }

    startY.current = null;
    currentY.current = null;
  };

  useEffect(() => {
    // 當isRefreshing狀態變化時，如果是開始刷新，設置pullDistance為指示器高度
    if (isRefreshing) {
      setPullDistance(refreshIndicatorHeight);
    }
  }, [isRefreshing, refreshIndicatorHeight]);

  return (
    <div
      ref={containerRef}
      className="overflow-auto h-full"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      style={{ WebkitOverflowScrolling: 'touch' }}
    >
      {/* 下拉指示器容器 */}
      <div
        className="flex items-center justify-center transition-transform"
        style={{
          height: `${refreshIndicatorHeight}px`,
          marginTop: `-${refreshIndicatorHeight}px`,
          transform: `translateY(${pullDistance}px)`,
          backgroundColor: backgroundColor,
          pointerEvents: 'none',
          zIndex: 10,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {isRefreshing
          ? refreshingContent || defaultRefreshingContent
          : pullingContent || defaultPullingContent}
      </div>

      {/* 實際內容，隨下拉指示器一起移動 */}
      <div
        style={{
          transform: `translateY(${pullDistance}px)`,
          transition: isRefreshing ? 'none' : 'transform 0.2s ease',
        }}
      >
        {children}
      </div>
    </div>
  );
};

export default PullToRefresh;
