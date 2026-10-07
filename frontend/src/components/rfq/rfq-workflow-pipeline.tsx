import React from "react";
import { cn } from "@/lib/utils";
import { Check, Clock, AlertCircle } from "lucide-react";

interface RFQWorkflowPipelineProps {
  status: string;
  className?: string;
}

const ORDERED_STAGES = [
  { key: "DRAFT", label: "Draft" },
  { key: "OPEN", label: "Open" },
  { key: "INVITATIONS_SENT", label: "Invitations Sent" },
  { key: "RESPONSES_RECEIVED", label: "Responses" },
  { key: "UNDER_REVIEW", label: "Under Review" },
  { key: "NEGOTIATION", label: "Negotiation" },
  { key: "AWARDED", label: "Awarded" },
];

export function RFQWorkflowPipeline({
  status,
  className,
}: RFQWorkflowPipelineProps) {
  const isCancelled = status === "CANCELLED";
  const isExpired = status === "EXPIRED";

  const currentIndex = ORDERED_STAGES.findIndex((s) => s.key === status);

  if (isCancelled || isExpired) {
    return (
      <div
        className={cn(
          "flex items-center gap-2 p-3 rounded-xl border border-destructive/20 bg-destructive/5 text-destructive text-sm",
          className
        )}
      >
        <AlertCircle className="size-4 shrink-0" />
        <span className="font-medium">
          This RFQ is {isCancelled ? "Cancelled" : "Expired"}. Workflow is
          concluded and no further quotations may be submitted or awarded.
        </span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "w-full overflow-x-auto py-2",
        className
      )}
    >
      <div className="flex items-center min-w-[700px] justify-between relative">
        {/* Connecting line */}
        <div className="absolute top-1/2 -translate-y-1/2 left-4 right-4 h-0.5 bg-border -z-0" />

        {ORDERED_STAGES.map((stage, idx) => {
          const isCompleted = currentIndex > idx;
          const isCurrent = currentIndex === idx;
          const isUpcoming = currentIndex < idx;

          return (
            <div
              key={stage.key}
              className="flex flex-col items-center relative z-10 bg-background px-2"
            >
              <div
                className={cn(
                  "size-8 rounded-full flex items-center justify-center text-xs font-semibold transition-all border-2",
                  isCompleted &&
                    "bg-emerald-500 border-emerald-500 text-white shadow-sm shadow-emerald-500/20",
                  isCurrent &&
                    "bg-blue-600 border-blue-600 text-white ring-4 ring-blue-500/20 shadow-md shadow-blue-500/30 animate-pulse",
                  isUpcoming &&
                    "bg-muted/80 border-border text-muted-foreground"
                )}
              >
                {isCompleted ? (
                  <Check className="size-4 stroke-[3]" />
                ) : isCurrent ? (
                  <Clock className="size-4" />
                ) : (
                  <span>{idx + 1}</span>
                )}
              </div>
              <span
                className={cn(
                  "text-[11px] font-medium mt-1.5 whitespace-nowrap",
                  isCurrent &&
                    "text-blue-600 dark:text-blue-400 font-semibold",
                  isCompleted && "text-foreground",
                  isUpcoming && "text-muted-foreground"
                )}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
