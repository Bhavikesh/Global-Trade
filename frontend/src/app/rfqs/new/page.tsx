"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useOrganization } from "@/lib/organization-context";
import {
  RFQCreate,
  RFQItemCreate,
  RFQ,
  fetchWithAuth,
} from "@/lib/api";
import {
  FileSpreadsheet,
  Plus,
  Trash2,
  ArrowLeft,
  Building2,
  AlertCircle,
  Loader2,
  Package,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const INCOTERMS = [
  "FOB",
  "CIF",
  "CFR",
  "EXW",
  "FCA",
  "CPT",
  "CIP",
  "DAP",
  "DPU",
  "DDP",
];

const CURRENCIES = ["USD", "EUR", "GBP", "CNY", "INR", "JPY", "SGD", "AED"];

const COMMON_COUNTRIES = [
  { code: "US", name: "United States (US)" },
  { code: "IN", name: "India (IN)" },
  { code: "DE", name: "Germany (DE)" },
  { code: "GB", name: "United Kingdom (GB)" },
  { code: "SG", name: "Singapore (SG)" },
  { code: "AE", name: "United Arab Emirates (AE)" },
  { code: "CN", name: "China (CN)" },
  { code: "JP", name: "Japan (JP)" },
  { code: "AU", name: "Australia (AU)" },
  { code: "CA", name: "Canada (CA)" },
  { code: "NL", name: "Netherlands (NL)" },
  { code: "VN", name: "Vietnam (VN)" },
  { code: "BR", name: "Brazil (BR)" },
];

const COMMON_UNITS = [
  "PCS",
  "KG",
  "MT",
  "LITERS",
  "CBM",
  "METERS",
  "BOXES",
  "PALLETS",
  "CONTAINERS",
];

export default function CreateRFQPage() {
  const router = useRouter();
  const { activeOrg, isLoading: orgLoading } = useOrganization();

  // RFQ Core Fields
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [destinationCountry, setDestinationCountry] = useState("US");
  const [destinationPort, setDestinationPort] = useState("");
  const [deliveryDate, setDeliveryDate] = useState("");
  const [preferredIncoterm, setPreferredIncoterm] = useState("FOB");
  const [paymentTerms, setPaymentTerms] = useState("Net 30");
  const [currency, setCurrency] = useState("USD");
  const [notes, setNotes] = useState("");

  // Items
  const [items, setItems] = useState<RFQItemCreate[]>([
    {
      item_index: 1,
      product_name_snapshot: "",
      description: "",
      quantity: "100.00",
      unit: "PCS",
      target_unit_price: "",
      specifications: "",
      quality_requirements: "",
      packaging_requirements: "",
    },
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addItem() {
    setItems((prev) => [
      ...prev,
      {
        item_index: prev.length + 1,
        product_name_snapshot: "",
        description: "",
        quantity: "100.00",
        unit: "PCS",
        target_unit_price: "",
        specifications: "",
        quality_requirements: "",
        packaging_requirements: "",
      },
    ]);
  }

  function removeItem(idx: number) {
    if (items.length <= 1) return;
    setItems((prev) =>
      prev
        .filter((_, i) => i !== idx)
        .map((itm, i) => ({ ...itm, item_index: i + 1 }))
    );
  }

  function updateItem(idx: number, field: keyof RFQItemCreate, value: string) {
    setItems((prev) => {
      const copy = [...prev];
      copy[idx] = { ...copy[idx], [field]: value };
      return copy;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!activeOrg) return;

    setError(null);

    // Client-side validations
    if (!title.trim()) {
      setError("RFQ Title is required.");
      return;
    }

    if (items.length === 0) {
      setError("At least one RFQ item is required.");
      return;
    }

    for (let i = 0; i < items.length; i++) {
      const itm = items[i];
      if (!itm.product_name_snapshot.trim()) {
        setError(`Item #${i + 1} requires a Product Name.`);
        return;
      }
      const qtyNum = Number(itm.quantity);
      if (isNaN(qtyNum) || qtyNum <= 0) {
        setError(`Item #${i + 1} quantity must be a positive number.`);
        return;
      }
      if (itm.target_unit_price) {
        const priceNum = Number(itm.target_unit_price);
        if (isNaN(priceNum) || priceNum < 0) {
          setError(`Item #${i + 1} target price cannot be negative.`);
          return;
        }
      }
    }

    setIsSubmitting(true);
    try {
      const payload: RFQCreate = {
        title: title.trim(),
        description: description.trim() || null,
        destination_country: destinationCountry.toUpperCase(),
        destination_port: destinationPort.trim() || null,
        required_delivery_date: deliveryDate || null,
        preferred_incoterm: preferredIncoterm,
        preferred_payment_terms: paymentTerms.trim() || null,
        currency,
        notes: notes.trim() || null,
        items: items.map((itm, idx) => ({
          item_index: idx + 1,
          product_name_snapshot: itm.product_name_snapshot.trim(),
          description: itm.description?.trim() || null,
          quantity: itm.quantity,
          unit: itm.unit || "PCS",
          target_unit_price: itm.target_unit_price?.trim() || null,
          specifications: itm.specifications?.trim() || null,
          quality_requirements: itm.quality_requirements?.trim() || null,
          packaging_requirements: itm.packaging_requirements?.trim() || null,
        })),
      };

      const created = await fetchWithAuth<RFQ>(
        `/v1/organizations/${activeOrg.id}/rfqs/`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );

      router.push(`/rfqs/${created.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setIsSubmitting(false);
    }
  }

  if (orgLoading) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-16 text-center">
        <Loader2 className="size-8 text-blue-600 animate-spin mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">Loading workspace...</p>
      </div>
    );
  }

  if (!activeOrg) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-16 text-center">
        <div className="max-w-md mx-auto p-8 rounded-2xl border border-border bg-card">
          <Building2 className="size-12 text-muted-foreground mx-auto mb-3 opacity-50" />
          <h2 className="text-lg font-bold">Active Organization Required</h2>
          <p className="text-xs text-muted-foreground mt-1 mb-5">
            Select or register an active buyer organization to initiate RFQs.
          </p>
          <Link href="/organizations">
            <Button size="sm">Go to Organizations</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-5xl px-4 sm:px-8 py-8 space-y-6">
      {/* Top back bar */}
      <div className="flex items-center gap-3">
        <Link
          href="/rfqs"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          Back to RFQs Dashboard
        </Link>
      </div>

      <div className="flex flex-col gap-1 pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-500/10 px-2 py-0.5 rounded">
            New Procurement RFQ
          </span>
          <span className="text-xs text-muted-foreground font-mono">
            Org: {activeOrg.display_name || activeOrg.legal_name}
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
          Create Request For Quotation
        </h1>
        <p className="text-sm text-muted-foreground">
          Define commercial specifications, required items, delivery terms, and target pricing.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/10 text-destructive text-sm flex items-start gap-3">
          <AlertCircle className="size-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Validation Error</p>
            <p className="text-xs mt-0.5 opacity-90">{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Section 1: Commercial Details */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-5">
          <h2 className="text-base font-bold text-foreground border-b border-border pb-3 flex items-center gap-2">
            <FileSpreadsheet className="size-4 text-blue-500" />
            1. Core Commercial Parameters
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="text-xs font-medium text-foreground block mb-1">
                RFQ Title *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Sourcing 200 MT Raw Grade-A Cotton Bales"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            <div className="md:col-span-2">
              <label className="text-xs font-medium text-foreground block mb-1">
                Description &amp; Commercial Scope
              </label>
              <textarea
                rows={2}
                placeholder="Detailed procurement brief, quality standards, or delivery conditions..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-xl border border-border bg-background p-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-foreground block mb-1">
                Destination Country *
              </label>
              <select
                value={destinationCountry}
                onChange={(e) => setDestinationCountry(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                {COMMON_COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code} className="bg-popover text-foreground">
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-foreground block mb-1">
                Destination Port (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Port of Rotterdam / Hamburg / Mumbai"
                value={destinationPort}
                onChange={(e) => setDestinationPort(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-foreground block mb-1">
                Preferred Incoterm
              </label>
              <select
                value={preferredIncoterm}
                onChange={(e) => setPreferredIncoterm(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20 font-semibold"
              >
                {INCOTERMS.map((inc) => (
                  <option key={inc} value={inc} className="bg-popover text-foreground">
                    {inc}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-foreground block mb-1">
                Trading Currency *
              </label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20 font-mono font-bold"
              >
                {CURRENCIES.map((cur) => (
                  <option key={cur} value={cur} className="bg-popover text-foreground">
                    {cur}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-foreground block mb-1">
                Required Delivery Date
              </label>
              <input
                type="date"
                value={deliveryDate}
                onChange={(e) => setDeliveryDate(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-foreground block mb-1">
                Preferred Payment Terms
              </label>
              <input
                type="text"
                placeholder="e.g. Net 30, T/T 30/70, Irrevocable L/C"
                value={paymentTerms}
                onChange={(e) => setPaymentTerms(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            <div className="md:col-span-2">
              <label className="text-xs font-medium text-foreground block mb-1">
                Additional Commercial Notes &amp; Instructions
              </label>
              <textarea
                rows={2}
                placeholder="Special buyer instructions, customs remarks, inspection terms..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full rounded-xl border border-border bg-background px-3.5 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Line Items Builder */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div>
              <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                <Package className="size-4 text-emerald-500" />
                2. RFQ Line Items
              </h2>
              <p className="text-xs text-muted-foreground">
                Specify product snapshots, quantities, packaging, and target unit prices.
              </p>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addItem}
              className="text-xs"
            >
              <Plus className="size-3.5 mr-1" />
              Add Item
            </Button>
          </div>

          <div className="space-y-4">
            {items.map((item, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-border bg-muted/20 space-y-4 relative group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                    <span className="size-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-mono">
                      {idx + 1}
                    </span>
                    Line Item #{idx + 1}
                  </span>
                  {items.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeItem(idx)}
                      className="text-muted-foreground hover:text-destructive p-1 rounded transition-colors"
                      aria-label="Remove item"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="sm:col-span-2">
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Product Name Snapshot *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Electric AC Induction Motor 10HP"
                      value={item.product_name_snapshot}
                      onChange={(e) =>
                        updateItem(idx, "product_name_snapshot", e.target.value)
                      }
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Target Unit Price ({currency})
                    </label>
                    <input
                      type="number"
                      step="0.0001"
                      min="0"
                      placeholder="e.g. 250.0000"
                      value={item.target_unit_price || ""}
                      onChange={(e) =>
                        updateItem(idx, "target_unit_price", e.target.value)
                      }
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Quantity *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      required
                      value={item.quantity}
                      onChange={(e) => updateItem(idx, "quantity", e.target.value)}
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground font-mono focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Unit of Measure *
                    </label>
                    <select
                      value={item.unit}
                      onChange={(e) => updateItem(idx, "unit", e.target.value)}
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    >
                      {COMMON_UNITS.map((u) => (
                        <option key={u} value={u} className="bg-popover text-foreground">
                          {u}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Specifications (Summary)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. 3-Phase, 400V, 50Hz, IP55"
                      value={item.specifications || ""}
                      onChange={(e) =>
                        updateItem(idx, "specifications", e.target.value)
                      }
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Quality &amp; Compliance Standards
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. ISO 9001 certified, CE marked"
                      value={item.quality_requirements || ""}
                      onChange={(e) =>
                        updateItem(idx, "quality_requirements", e.target.value)
                      }
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-foreground block mb-1">
                      Packaging &amp; Pallet Requirements
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Seaworthy wooden crates, ISPM 15 fumigated"
                      value={item.packaging_requirements || ""}
                      onChange={(e) =>
                        updateItem(idx, "packaging_requirements", e.target.value)
                      }
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addItem}
            className="w-full border-dashed"
          >
            <Plus className="size-3.5 mr-1" />
            Add Another Line Item
          </Button>
        </div>

        {/* Action Toolbar */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-border">
          <Link href="/rfqs">
            <Button type="button" variant="outline" disabled={isSubmitting}>
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm px-6"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="size-4 animate-spin mr-2" />
                Drafting RFQ...
              </>
            ) : (
              <>
                <FileSpreadsheet className="size-4 mr-2" />
                Save &amp; Create Draft RFQ
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
