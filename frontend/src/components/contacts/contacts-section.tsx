"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Users,
  Plus,
  Mail,
  Phone,
  Briefcase,
  Star,
  Edit2,
  Trash2,
  AlertCircle,
  X,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  CRMContact,
  CRMContactCreateInput,
  CRMContactUpdateInput,
  fetchBuyerContacts,
  createBuyerContact,
  fetchSupplierContacts,
  createSupplierContact,
  updateContact,
  deleteContact,
} from "@/lib/api";

interface ContactsSectionProps {
  orgId: string;
  parentType: "buyer" | "supplier";
  parentId: string;
  canEdit?: boolean;
}

export function ContactsSection({
  orgId,
  parentType,
  parentId,
  canEdit = true,
}: ContactsSectionProps) {
  const [contacts, setContacts] = useState<CRMContact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingContact, setEditingContact] = useState<CRMContact | null>(null);
  const [deletingContact, setDeletingContact] = useState<CRMContact | null>(null);

  // Form field states
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [designation, setDesignation] = useState("");
  const [notes, setNotes] = useState("");
  const [isPrimary, setIsPrimary] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch contacts
  const refreshContacts = useCallback(async () => {
    if (!orgId || !parentId) return;
    setIsLoading(true);
    try {
      const data =
        parentType === "buyer"
          ? await fetchBuyerContacts(orgId, parentId)
          : await fetchSupplierContacts(orgId, parentId);
      setContacts(data);
      setError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to load CRM contacts.");
    } finally {
      setIsLoading(false);
    }
  }, [orgId, parentId, parentType]);

  useEffect(() => {
    let active = true;
    if (!orgId || !parentId) return;

    async function fetchInitial() {
      try {
        const data =
          parentType === "buyer"
            ? await fetchBuyerContacts(orgId, parentId)
            : await fetchSupplierContacts(orgId, parentId);
        if (!active) return;
        setContacts(data);
        setError(null);
      } catch (err: unknown) {
        if (!active) return;
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg || "Failed to load CRM contacts.");
      } finally {
        if (active) setIsLoading(false);
      }
    }

    fetchInitial();
    return () => {
      active = false;
    };
  }, [orgId, parentId, parentType]);

  // Open Add Modal
  const openAddModal = () => {
    setName("");
    setEmail("");
    setPhone("");
    setDesignation("");
    setNotes("");
    setIsPrimary(contacts.length === 0); // Default to primary if first contact
    setFormError(null);
    setShowAddModal(true);
  };

  // Open Edit Modal
  const openEditModal = (contact: CRMContact) => {
    setEditingContact(contact);
    setName(contact.name || "");
    setEmail(contact.email || "");
    setPhone(contact.phone || "");
    setDesignation(contact.designation || "");
    setNotes(contact.notes || "");
    setIsPrimary(contact.is_primary);
    setFormError(null);
  };

  // Close Modals
  const closeModal = () => {
    setShowAddModal(false);
    setEditingContact(null);
    setFormError(null);
  };

  // Validate form
  const validateForm = (): boolean => {
    const trimmedName = name.trim();
    if (!trimmedName) {
      setFormError("Contact name is required.");
      return false;
    }
    if (email.trim()) {
      const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
      if (!emailRegex.test(email.trim())) {
        setFormError("Please enter a valid email address.");
        return false;
      }
    }
    return true;
  };

  // Submit Add Contact
  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);
    setFormError(null);
    try {
      const payload: CRMContactCreateInput = {
        name: name.trim(),
        email: email.trim() || null,
        phone: phone.trim() || null,
        designation: designation.trim() || null,
        notes: notes.trim() || null,
        is_primary: isPrimary,
      };

      if (parentType === "buyer") {
        await createBuyerContact(orgId, parentId, payload);
      } else {
        await createSupplierContact(orgId, parentId, payload);
      }

      closeModal();
      await refreshContacts();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFormError(msg || "Failed to create contact.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Edit Contact
  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingContact) return;
    if (!validateForm()) return;

    setIsSubmitting(true);
    setFormError(null);
    try {
      const payload: CRMContactUpdateInput = {
        name: name.trim(),
        email: email.trim() || null,
        phone: phone.trim() || null,
        designation: designation.trim() || null,
        notes: notes.trim() || null,
        is_primary: isPrimary,
      };

      await updateContact(orgId, editingContact.id, payload);
      closeModal();
      await refreshContacts();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFormError(msg || "Failed to update contact.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Confirm Delete Contact
  const handleDeleteConfirm = async () => {
    if (!deletingContact) return;
    setIsDeleting(true);
    try {
      await deleteContact(orgId, deletingContact.id);
      setDeletingContact(null);
      await refreshContacts();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to delete contact.");
      setDeletingContact(null);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 mb-6 border-b border-border/50">
        <div>
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-500" />
            <h2 className="text-lg font-semibold text-foreground">
              Key Trade &amp; CRM Contacts
            </h2>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground border border-border/40">
              {contacts.length}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Key account managers, sales leads, logistics coordinators, and trade desk representatives.
          </p>
        </div>

        {canEdit && (
          <Button
            size="sm"
            onClick={openAddModal}
            className="gap-1.5 bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
          >
            <Plus className="h-3.5 w-3.5" />
            Add Contact
          </Button>
        )}
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="mb-6 flex items-center justify-between p-3.5 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
          <Button
            variant="ghost"
            size="xs"
            onClick={refreshContacts}
            className="text-destructive hover:bg-destructive/20"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-32 rounded-xl bg-muted/50 animate-pulse border border-border/40" />
          <div className="h-32 rounded-xl bg-muted/50 animate-pulse border border-border/40" />
        </div>
      ) : contacts.length === 0 ? (
        /* Empty State */
        <div className="rounded-xl border border-dashed border-border p-8 text-center">
          <Users className="h-8 w-8 mx-auto mb-2 text-muted-foreground/40" />
          <h3 className="text-sm font-medium text-foreground mb-1">
            No contacts recorded
          </h3>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto mb-4">
            Record company personnel to maintain direct correspondence for negotiations, RFQs, and logistics.
          </p>
          {canEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={openAddModal}
              className="gap-1.5 text-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              Add First Contact
            </Button>
          )}
        </div>
      ) : (
        /* Populated State */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {contacts.map((contact) => (
            <div
              key={contact.id}
              className={`rounded-xl border p-4.5 transition-colors relative flex flex-col justify-between ${
                contact.is_primary
                  ? "border-blue-500/40 bg-blue-500/5 shadow-xs"
                  : "border-border/70 bg-card hover:border-border"
              }`}
            >
              <div>
                {/* Contact Top Info */}
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-foreground">
                        {contact.name}
                      </h4>
                      {contact.is_primary && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                          <Star className="h-2.5 w-2.5 fill-current" />
                          Primary Contact
                        </span>
                      )}
                    </div>
                    {contact.designation && (
                      <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                        <Briefcase className="h-3 w-3 text-muted-foreground/70" />
                        {contact.designation}
                      </p>
                    )}
                  </div>

                  {canEdit && (
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => openEditModal(contact)}
                        className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                        title="Edit Contact"
                        aria-label={`Edit ${contact.name}`}
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeletingContact(contact)}
                        className="p-1 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                        title="Delete Contact"
                        aria-label={`Delete ${contact.name}`}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Contact Details */}
                <div className="space-y-1.5 text-xs text-muted-foreground mt-3">
                  {contact.email && (
                    <div className="flex items-center gap-2">
                      <Mail className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
                      <a
                        href={`mailto:${contact.email}`}
                        className="hover:text-blue-500 transition-colors truncate"
                      >
                        {contact.email}
                      </a>
                    </div>
                  )}
                  {contact.phone && (
                    <div className="flex items-center gap-2">
                      <Phone className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0" />
                      <a
                        href={`tel:${contact.phone}`}
                        className="hover:text-blue-500 transition-colors"
                      >
                        {contact.phone}
                      </a>
                    </div>
                  )}
                </div>

                {/* Notes */}
                {contact.notes && (
                  <div className="mt-3 pt-2.5 border-t border-border/40 text-[11px] text-muted-foreground flex items-start gap-1.5">
                    <FileText className="h-3 w-3 text-muted-foreground/60 shrink-0 mt-0.5" />
                    <p className="line-clamp-2 leading-relaxed">{contact.notes}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Add or Edit Contact */}
      {(showAddModal || editingContact) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-border/50">
              <h3 className="text-base font-bold text-foreground">
                {editingContact ? "Edit Contact" : "Add New Contact"}
              </h3>
              <button
                type="button"
                onClick={closeModal}
                className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                aria-label="Close dialog"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {formError && (
              <div className="mb-4 flex items-center gap-2 p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form
              onSubmit={editingContact ? handleEditSubmit : handleAddSubmit}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. John Doe"
                  className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </div>

              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                  Designation / Role
                </label>
                <input
                  type="text"
                  value={designation}
                  onChange={(e) => setDesignation(e.target.value)}
                  placeholder="e.g. Head of Procurement / Sales Director"
                  className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="john@example.com"
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                    Phone
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+1 (555) 000-0000"
                    className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium uppercase tracking-wider text-muted-foreground mb-1">
                  Notes
                </label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Direct extension, timezone, communication preferences"
                  className="w-full px-3 py-2 rounded-xl border border-input bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="is_primary_checkbox"
                  checked={isPrimary}
                  onChange={(e) => setIsPrimary(e.target.checked)}
                  className="h-4 w-4 rounded border-input text-blue-600 focus:ring-blue-500"
                />
                <label
                  htmlFor="is_primary_checkbox"
                  className="text-xs font-medium text-foreground cursor-pointer select-none"
                >
                  Mark as primary contact
                </label>
              </div>

              <div className="pt-3 border-t border-border/50 flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={closeModal}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={isSubmitting}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isSubmitting
                    ? "Saving..."
                    : editingContact
                    ? "Update Contact"
                    : "Add Contact"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Delete Contact Confirmation */}
      {deletingContact && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-sm rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <h3 className="text-base font-bold text-foreground mb-2">
              Delete Contact
            </h3>
            <p className="text-xs text-muted-foreground mb-5 leading-relaxed">
              Are you sure you want to delete{" "}
              <strong className="text-foreground">{deletingContact.name}</strong>?
              This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setDeletingContact(null)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                variant="destructive"
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
              >
                {isDeleting ? "Deleting..." : "Delete Contact"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
