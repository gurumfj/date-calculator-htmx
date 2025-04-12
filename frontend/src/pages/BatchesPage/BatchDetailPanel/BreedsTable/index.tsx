import React from "react";
import { BatchAggregate } from "@app-types";
import { BreedsRecordsTable } from "./BreedsRecordsTable";
import { BreedSummaryCard } from "../../components/BatchSummaryCards";

export interface BatchDetailProps {
  batch: BatchAggregate;
  isLoading?: boolean;
  error?: Error | null;
}

export const BatchDetail: React.FC<BatchDetailProps> = ({
  batch,
  isLoading = false,
  error = null,
}) => {
  return (
    <div className="space-y-6">
      <BreedSummaryCard batch={batch} />
      <BreedsRecordsTable batch={batch} isLoading={isLoading} error={error} />
    </div>
  );
};

export default BatchDetail;
