import React from "react";
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from "@headlessui/react";
import FeedRecordTable from "./FeedsTable";
import { BatchAggregate } from "@app-types";
import {
  determineBatchState,
  getBatchStateDisplay,
} from "@utils/batchCalculations";
import BatchDetail from "./BreedsTable";
import SalesRawTable from "./SalesTable";
import TodoistPage from "./todoist";
import { CheckCircleIcon } from "@heroicons/react/24/outline";

const BatchDetailPanel: React.FC<{ batch: BatchAggregate }> = ({ batch }) => {
  // 使用計算工具函數確定批次狀態
  const batchState = determineBatchState(batch);

  // 獲取狀態的顯示樣式
  const stateDisplay = getBatchStateDisplay(batchState);

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="border-b border-gray-200 p-4 bg-white">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-[#1C1C1E]">
            {batch.batchName} 詳細資訊
          </h2>
          <div className="flex items-center">
            <span
              className={`px-2 py-1 rounded-md text-xs font-medium
              ${stateDisplay.bgClass} ${stateDisplay.textClass} mr-2`}
            >
              {stateDisplay.label}
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <TabGroup>
          <TabList className="flex space-x-2 rounded-xl bg-[#F2F2F7] p-1 mb-4 sticky top-0 z-10">
            <Tab
              className={({ selected }) =>
                `flex-1 rounded-lg py-2 text-sm font-medium leading-5 transition-all
                  ${
                    selected
                      ? "bg-white text-[#007AFF] shadow"
                      : "text-[#8E8E93] hover:bg-white/[0.12] hover:text-[#8E8E93]"
                  }`
              }
            >
              {"批次資訊"}
            </Tab>
            {batch.sales && batch.sales.length > 0 && (
              <Tab
                className={({ selected }) =>
                  `flex-1 rounded-lg py-2 text-sm font-medium leading-5 transition-all
                    ${
                      selected
                        ? "bg-white text-[#007AFF] shadow"
                        : "text-[#8E8E93] hover:bg-white/[0.12] hover:text-[#8E8E93]"
                    }`
                }
              >
                {"銷售"}
              </Tab>
            )}
            {batch.feeds && batch.feeds.length > 0 && (
              <Tab
                className={({ selected }) =>
                  `flex-1 rounded-lg py-2 text-sm font-medium leading-5 transition-all
                    ${
                      selected
                        ? "bg-white text-[#007AFF] shadow"
                        : "text-[#8E8E93] hover:bg-white/[0.12] hover:text-[#8E8E93]"
                    }`
                }
              >
                {"飼料"}
              </Tab>
            )}
            <Tab
              className={({ selected }) =>
                `flex-1 rounded-lg py-2 text-sm font-medium leading-5 transition-all flex items-center justify-center
                  ${
                    selected
                      ? "bg-white text-[#007AFF] shadow"
                      : "text-[#8E8E93] hover:bg-white/[0.12] hover:text-[#8E8E93]"
                  }`
              }
            >
              <CheckCircleIcon className="w-4 h-4 mr-1" />
              {"待辦事項"}
            </Tab>
          </TabList>

          <TabPanels>
            <TabPanel className="focus:outline-none">
              <BatchDetail batch={batch} />
            </TabPanel>
            {batch.sales && batch.sales.length > 0 && (
              <TabPanel className="focus:outline-none">
                <SalesRawTable batch={batch} />
              </TabPanel>
            )}

            {/* ��料 */}
            {batch.feeds && batch.feeds.length > 0 && (
              <TabPanel className="focus:outline-none">
                <FeedRecordTable batch={batch} />
              </TabPanel>
            )}

            {/* 待辦事項 */}
            <TabPanel className="focus:outline-none">
              <TodoistPage batch={batch} />
            </TabPanel>
          </TabPanels>
        </TabGroup>
      </div>
    </div>
  );
};

export default BatchDetailPanel;
