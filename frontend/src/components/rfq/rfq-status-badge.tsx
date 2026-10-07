import React from "react";
import { cn } from "@/lib/utils";

interface RFQStatusBadgeProps {
  status: string;
  className?: string;
}

const STATUS_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; border: string; dot: string }
> = {
  DRAFT: {
    label: "Draft",
    bg: "bg-neutral-100 dark:bg-neutral-800",
    text: "text-neutral-700 dark:text-neutral-300",
    border: "border-neutral-200 dark:border-neutral-700",
    dot: "bg-neutral-400",
  },
  OPEN: {
    label: "Open",
    bg: "bg-blue-50 dark:bg-blue-950/60",
    text: "text-blue-700 dark:text-blue-300",
    border: "border-blue-200 dark:border-blue-800",
    dot: "bg-blue-500",
  },
  INVITATIONS_SENT: {
    label: "Invitations Sent",
    bg: "bg-indigo-50 dark:bg-indigo-950/60",
    text: "text-indigo-700 dark:text-indigo-300",
    border: "border-indigo-200 dark:border-indigo-800",
    dot: "bg-indigo-500",
  },
  RESPONSES_RECEIVED: {
    label: "Responses Received",
    bg: "bg-amber-50 dark:bg-amber-950/60",
    text: "text-amber-700 dark:text-amber-300",
    border: "border-amber-200 dark:border-amber-800",
    dot: "bg-amber-500",
  },
  UNDER_REVIEW: {
    label: "Under Review",
    bg: "bg-purple-50 dark:bg-purple-950/60",
    text: "text-purple-700 dark:text-purple-300",
    border: "border-purple-200 dark:border-purple-800",
    dot: "bg-purple-500",
  },
  NEGOTIATION: {
    label: "In Negotiation",
    bg: "bg-cyan-50 dark:bg-cyan-950/60",
    text: "text-cyan-700 dark:text-cyan-300",
    border: "border-cyan-200 dark:border-cyan-800",
    dot: "bg-cyan-500",
  },
  AWARDED: {
    label: "Awarded",
    bg: "bg-emerald-50 dark:bg-emerald-950/60",
    text: "text-emerald-700 dark:text-emerald-300",
    border: "border-emerald-200 dark:border-emerald-800",
    dot: "bg-emerald-500",
  },
  CANCELLED: {
    label: "Cancelled",
    bg: "bg-rose-50 dark:bg-rose-950/60",
    text: "text-rose-700 dark:text-rose-300",
    border: "border-rose-200 dark:border-rose-800",
    dot: "bg-rose-500",
  },
  EXPIRED: {
    label: "Expired",
    bg: "bg-neutral-100 dark:bg-neutral-800",
    text: "text-neutral-500 dark:text-neutral-400",
    border: "border-neutral-200 dark:border-neutral-700",
    dot: "bg-neutral-400",
  },
};

export function RFQStatusBadge({ status, className }: RFQStatusBadgeProps) {
  const cfg = STATUS_CONFIG[status] || {
    label: status,
    bg: "bg-neutral-100",
    text: "text-neutral-700",
    border: "border-neutral-200",
    dot: "bg-neutral-400",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",
        cfg.bg,
        cfg.text,
        cfg.border,
        className
      )}
    >
      <span className={cn("size-1.5 rounded-full", cfg.dot)} />
      {cfg.label}
    </span>
  );
}
