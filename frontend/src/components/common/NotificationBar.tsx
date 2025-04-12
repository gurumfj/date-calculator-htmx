import React, { useEffect, useState } from "react";
import { useNotification } from "../../contexts/NotificationContext";

interface NotificationBarProps {
  message?: string;
}

const NotificationBar: React.FC<NotificationBarProps> = () => {
  const { notification } = useNotification();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (notification) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [notification]);

  if (!notification) return null;

  return (
    <div className="fixed left-0 z-50 flex justify-center w-full pointer-events-none">
      <div
        className={`
          max-w-md
          bg-[#E8F5E9]
          rounded-b-lg shadow-sm border border-[#C8E6C9]
          py-2 px-4
          text-center
          text-sm
          transition-all duration-300
          ${visible ? "translate-y-0 opacity-100" : "-translate-y-full opacity-0"}
        `}
      >
        <span className="text-[#2E7D32]">{notification}</span>
      </div>
    </div>
  );
};

export default NotificationBar;
