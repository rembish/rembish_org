import { useEffect, useRef, useState } from "react";
import {
  BiBuildings,
  BiTrash,
  BiSearch,
  BiPencil,
  BiCopy,
  BiFile,
  BiCloudUpload,
  BiX,
} from "react-icons/bi";
import type {
  TripFormData,
  TCCDestinationOption,
  AccommodationItem,
} from "./types";
import { PLATFORM_LABELS, PAYMENT_STATUS_LABELS } from "./helpers";
import AccommodationModal from "./AccommodationModal";
import { apiFetch } from "../../lib/api";

interface StaysTabProps {
  tripId: string;
  formData: TripFormData;
  tccOptions: TCCDestinationOption[];
  readOnly: boolean;
}

export default function StaysTab({
  tripId,
  formData,
  tccOptions,
  readOnly,
}: StaysTabProps) {
  const [accommodations, setAccommodations] = useState<AccommodationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [vaultUnlocked, setVaultUnlocked] = useState(false);
  const [showAccommodationModal, setShowAccommodationModal] = useState(false);
  const [editingAccommodation, setEditingAccommodation] =
    useState<AccommodationItem | null>(null);
  const [uploadingAccommodationDoc, setUploadingAccommodationDoc] = useState<
    number | null
  >(null);
  const accommodationDocInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setLoading(true);
    apiFetch(`/api/v1/travels/trips/${tripId}/accommodations`)
      .then((r) => r.json())
      .then((data) => setAccommodations(data.accommodations || []))
      .catch((err) => console.error("Failed to load accommodations:", err))
      .finally(() => setLoading(false));

    apiFetch("/api/auth/vault/status")
      .then((r) => r.json())
      .then((data) => setVaultUnlocked(data.unlocked === true))
      .catch(() => setVaultUnlocked(false));
  }, [tripId]);

  useEffect(() => {
    const onVaultChange = () => {
      apiFetch("/api/auth/vault/status")
        .then((r) => r.json())
        .then((data) => setVaultUnlocked(data.unlocked === true))
        .catch(() => setVaultUnlocked(false));
    };
    window.addEventListener("vault-status-changed", onVaultChange);
    return () =>
      window.removeEventListener("vault-status-changed", onVaultChange);
  }, []);

  const handleDeleteAccommodation = async (accId: number) => {
    if (!confirm("Delete this accommodation?")) return;
    try {
      await apiFetch(`/api/v1/travels/accommodations/${accId}`, {
        method: "DELETE",
      });
      setAccommodations((prev) => prev.filter((a) => a.id !== accId));
    } catch (err) {
      console.error("Failed to delete accommodation:", err);
    }
  };

  const handleAccommodationDocUpload = async (accId: number, file: File) => {
    setUploadingAccommodationDoc(accId);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await apiFetch(
        `/api/v1/travels/accommodations/${accId}/document`,
        { method: "POST", body: form },
      );
      if (!res.ok) throw new Error("Upload failed");
      const listRes = await apiFetch(
        `/api/v1/travels/trips/${tripId}/accommodations`,
      );
      const data = await listRes.json();
      setAccommodations(data.accommodations || []);
    } catch (err) {
      console.error("Failed to upload document:", err);
    } finally {
      setUploadingAccommodationDoc(null);
      if (accommodationDocInputRef.current)
        accommodationDocInputRef.current.value = "";
    }
  };

  const handleViewAccommodationDoc = (accId: number) => {
    window.open(`/api/v1/travels/accommodations/${accId}/document`, "_blank");
  };

  const handleDeleteAccommodationDoc = async (accId: number) => {
    if (!confirm("Delete the attached document?")) return;
    try {
      await apiFetch(`/api/v1/travels/accommodations/${accId}/document`, {
        method: "DELETE",
      });
      const listRes = await apiFetch(
        `/api/v1/travels/trips/${tripId}/accommodations`,
      );
      const data = await listRes.json();
      setAccommodations(data.accommodations || []);
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  if (loading) {
    return (
      <div className="trip-transport-tab">
        <p>Loading stays...</p>
      </div>
    );
  }

  const tripDests = formData.destinations
    .map((d) => tccOptions.find((o) => o.id === d.tcc_destination_id)?.name)
    .filter(Boolean);
  const dateFrom = formData.start_date
    ? new Date(formData.start_date + "T00:00:00").toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "";
  const dateTo = formData.end_date
    ? new Date(formData.end_date + "T00:00:00").toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "";

  return (
    <div className="trip-transport-tab">
      {/* Trip context */}
      {!readOnly && (
        <div className="transport-trip-context">
          <span className="transport-dates">
            {dateFrom}
            {dateTo && ` – ${dateTo}`}
          </span>
          {tripDests.length > 0 && (
            <span className="transport-destinations">
              {tripDests.join(", ")}
            </span>
          )}
        </div>
      )}

      {/* Accommodations section */}
      <div className="form-section">
        <h3 className="section-header-with-action">
          <span>
            <BiBuildings style={{ verticalAlign: "middle", marginRight: 6 }} />
            Stays ({accommodations.length})
          </span>
          {!readOnly && (
            <button
              type="button"
              className="btn-add-inline"
              onClick={() => {
                setEditingAccommodation(null);
                setShowAccommodationModal(true);
              }}
            >
              + Add
            </button>
          )}
        </h3>
        {accommodations.length === 0 ? (
          <p className="flight-empty">No accommodations added yet.</p>
        ) : (
          <div className="transport-booking-list">
            {accommodations.map((a) => (
              <div key={a.id} className="transport-booking-card">
                <div className="transport-booking-main">
                  <div className="transport-booking-header">
                    <span className="transport-booking-operator">
                      {a.property_name}
                    </span>
                    {a.platform && (
                      <span className="accommodation-platform">
                        {PLATFORM_LABELS[a.platform] || a.platform}
                      </span>
                    )}
                  </div>
                  {(a.checkin_date || a.checkout_date || a.address) && (
                    <div className="transport-booking-route">
                      {(a.checkin_date || a.checkout_date) && (
                        <div className="transport-booking-route-row">
                          <span className="transport-booking-route-label">
                            Dates
                          </span>
                          <span>
                            {a.checkin_date &&
                              new Date(
                                a.checkin_date + "T00:00:00",
                              ).toLocaleDateString("en-GB", {
                                day: "numeric",
                                month: "short",
                              })}
                            {a.checkin_date && a.checkout_date && " – "}
                            {a.checkout_date &&
                              new Date(
                                a.checkout_date + "T00:00:00",
                              ).toLocaleDateString("en-GB", {
                                day: "numeric",
                                month: "short",
                              })}
                          </span>
                        </div>
                      )}
                      {a.address && (
                        <div className="transport-booking-route-row">
                          <span className="transport-booking-route-label">
                            Addr
                          </span>
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(a.address)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="transport-booking-station-link"
                          >
                            {a.address}
                          </a>
                        </div>
                      )}
                    </div>
                  )}
                  <div className="transport-booking-details">
                    {a.payment_status && (
                      <span
                        className={`accommodation-payment-status accommodation-payment-${a.payment_status}`}
                      >
                        {PAYMENT_STATUS_LABELS[a.payment_status] ||
                          a.payment_status}
                        {a.payment_status === "pay_by_date" &&
                          a.payment_date &&
                          ` (${new Date(a.payment_date + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short" })})`}
                      </span>
                    )}
                    {a.total_amount && (
                      <span className="flight-badge">{a.total_amount}</span>
                    )}
                    {a.rooms && a.rooms > 1 && (
                      <span className="flight-badge">
                        {a.rooms} room{a.rooms > 1 ? "s" : ""}
                      </span>
                    )}
                    {a.guests && (
                      <span className="flight-badge">
                        {a.guests} guest{a.guests > 1 ? "s" : ""}
                      </span>
                    )}
                    {a.confirmation_code && vaultUnlocked && (
                      <span className="flight-badge">
                        {a.confirmation_code}
                        <button
                          className="btn-icon-inline"
                          title="Copy"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigator.clipboard.writeText(a.confirmation_code!);
                          }}
                        >
                          <BiCopy />
                        </button>
                      </span>
                    )}
                  </div>
                </div>
                <div className="transport-booking-actions">
                  {a.has_document && (
                    <button
                      className="transport-booking-doc-btn"
                      onClick={() => handleViewAccommodationDoc(a.id)}
                      title={`View ${a.document_name || "document"}`}
                    >
                      <BiFile size={16} />
                    </button>
                  )}
                  {a.booking_url && (
                    <a
                      className="transport-booking-doc-btn"
                      href={
                        a.booking_url.startsWith("http")
                          ? a.booking_url
                          : `https://${a.booking_url}`
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Open booking"
                    >
                      <BiSearch size={16} />
                    </a>
                  )}
                  {!readOnly && (
                    <>
                      <label
                        className="transport-booking-doc-btn"
                        title="Attach document"
                        style={{ cursor: "pointer" }}
                      >
                        <BiCloudUpload size={16} />
                        <input
                          type="file"
                          accept=".pdf,image/*"
                          style={{ display: "none" }}
                          disabled={uploadingAccommodationDoc === a.id}
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) handleAccommodationDocUpload(a.id, file);
                          }}
                        />
                      </label>
                      {a.has_document && (
                        <button
                          className="transport-booking-doc-btn"
                          onClick={() => handleDeleteAccommodationDoc(a.id)}
                          title="Remove document"
                        >
                          <BiX size={16} />
                        </button>
                      )}
                      <button
                        className="flight-delete-btn"
                        onClick={() => {
                          setEditingAccommodation(a);
                          setShowAccommodationModal(true);
                        }}
                        title="Edit accommodation"
                      >
                        <BiPencil />
                      </button>
                      <button
                        className="flight-delete-btn"
                        onClick={() => handleDeleteAccommodation(a.id)}
                        title="Delete accommodation"
                      >
                        <BiTrash />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Accommodation Modal */}
      {showAccommodationModal && (
        <AccommodationModal
          tripId={tripId}
          editingAccommodation={editingAccommodation}
          onChanged={(updated) => {
            setAccommodations(updated);
            setEditingAccommodation(null);
          }}
          onClose={() => {
            setShowAccommodationModal(false);
            setEditingAccommodation(null);
          }}
        />
      )}
    </div>
  );
}
