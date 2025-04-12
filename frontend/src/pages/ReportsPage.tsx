import React, { Suspense } from "react";

const ReportsPage: React.FC = () => {
  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">銷售報表</h2>
      <Suspense
        fallback={<div className="text-center p-4">載入中...</div>}
      ></Suspense>
    </div>
  );
};

export default ReportsPage;
