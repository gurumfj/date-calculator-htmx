import React, { Suspense } from "react";

const HomePage: React.FC = () => {
  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">儀表盤</h2>
      <Suspense fallback={<div className="text-center p-4">載入中...</div>}>
        {/* <Dashboard /> */}
      </Suspense>
    </div>
  );
};

export default HomePage;
