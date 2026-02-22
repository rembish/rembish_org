import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BiSignal5 } from "react-icons/bi";
import { apiFetch } from "../../lib/api";
import Flag from "../Flag";
import type { CountryInfoData } from "./types";
import {
  formatSocketName,
  formatCurrencyRate,
  formatLocalTime,
  tapWaterLabel,
} from "./helpers";

interface InfoTabProps {
  tripId: string;
  readOnly: boolean;
}

export default function InfoTab({ tripId, readOnly }: InfoTabProps) {
  const navigate = useNavigate();
  const [countryInfo, setCountryInfo] = useState<CountryInfoData[]>([]);
  const [loadingInfo, setLoadingInfo] = useState(true);
  const [selectedInfoCountry, setSelectedInfoCountry] = useState(0);

  useEffect(() => {
    setLoadingInfo(true);
    apiFetch(`/api/v1/travels/trips/${tripId}/country-info`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load country info");
        return r.json();
      })
      .then((data) => {
        setCountryInfo(data.countries || []);
        setSelectedInfoCountry(0);
      })
      .catch((err) => console.error("Failed to load country info:", err))
      .finally(() => setLoadingInfo(false));
  }, [tripId]);

  const refetchCountryInfo = () => {
    apiFetch(`/api/v1/travels/trips/${tripId}/country-info`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to reload country info");
        return r.json();
      })
      .then((data) => setCountryInfo(data.countries || []))
      .catch((err) => console.error("Failed to reload country info:", err));
  };

  if (loadingInfo) {
    return (
      <div className="country-info-panel">
        <p className="country-info-loading">Loading country info...</p>
      </div>
    );
  }

  if (countryInfo.length === 0) {
    return (
      <div className="country-info-panel">
        <p className="country-info-empty">
          No destination countries for this trip.
        </p>
      </div>
    );
  }

  const safeIndex =
    selectedInfoCountry < countryInfo.length ? selectedInfoCountry : 0;

  const renderCountryCard = (country: CountryInfoData) => (
    <div className="country-info-card">
      <div className="country-info-header">
        <Flag code={country.iso_alpha2} size={24} />
        <h3>{country.country_name}</h3>
      </div>

      {country.tcc_destinations.length > 0 && (
        <div className="country-tcc-tags">
          {country.tcc_destinations.map((d) => (
            <span
              key={d.name}
              className={`country-tcc-tag ${d.is_partial ? "partial" : ""}`}
            >
              {d.name}
            </span>
          ))}
        </div>
      )}

      <div className="country-info-grid">
        {country.socket_types && (
          <div className="country-info-item">
            <span className="info-label">
              Sockets
              {country.adapter_needed !== null && (
                <span
                  className={`adapter-badge ${country.adapter_needed ? "adapter-yes" : "adapter-no"}`}
                >
                  {country.adapter_needed
                    ? " — adapter needed"
                    : " — compatible"}
                </span>
              )}
            </span>
            <span className="info-value socket-types">
              {country.socket_types.split(",").map((t) => (
                <span
                  key={t}
                  className="socket-type"
                  title={`Type ${t} (${formatSocketName(t)})`}
                >
                  <img
                    src={`/sockets/${t.toLowerCase()}.svg`}
                    alt={formatSocketName(t)}
                    className="socket-icon"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                  <span className="socket-label">{formatSocketName(t)}</span>
                </span>
              ))}
            </span>
          </div>
        )}

        {country.voltage && (
          <div className="country-info-item">
            <span className="info-label">Voltage</span>
            <span className="info-value">{country.voltage}</span>
          </div>
        )}

        {country.phone_code && (
          <div className="country-info-item">
            <span className="info-label">Phone</span>
            <span className="info-value phone-info">
              <span>{country.phone_code}</span>
              {country.eu_roaming !== null && (
                <span
                  className={`roaming-badge ${country.eu_roaming ? "roaming-eu" : "roaming-local"}`}
                >
                  <BiSignal5 />
                  {country.eu_roaming ? "EU roaming" : "Local SIM"}
                </span>
              )}
            </span>
          </div>
        )}

        {country.driving_side && (
          <div className="country-info-item">
            <span className="info-label">Driving</span>
            <span className="info-value driving-info">
              <span>
                {country.driving_side === "left" ? "Left side" : "Right side"}
              </span>
              {country.speed_limits && (
                <span className="speed-limits">
                  {(() => {
                    const [city, rural, hwy] = country.speed_limits.split("/");
                    return `${city}/${rural}/${hwy === "none" ? "∞" : hwy} km/h`;
                  })()}
                </span>
              )}
            </span>
          </div>
        )}

        {country.emergency_number && (
          <div className="country-info-item">
            <span className="info-label">Emergency</span>
            <span className="info-value emergency-number">
              {country.emergency_number}
            </span>
          </div>
        )}

        {country.tap_water && (
          <div className="country-info-item">
            <span className="info-label">Tap Water</span>
            <span
              className={`info-value ${tapWaterLabel(country.tap_water).className}`}
            >
              {tapWaterLabel(country.tap_water).text}
            </span>
          </div>
        )}

        {country.currency && (
          <div className="country-info-item">
            <span className="info-label">Currency</span>
            <span className="info-value">
              {country.currency.code}
              {country.currency.name && (
                <span className="currency-name">
                  {" "}
                  ({country.currency.name})
                </span>
              )}
              {country.currency.rates && (
                <span className="currency-rates">
                  {formatCurrencyRate(
                    country.currency.code,
                    country.currency.rates,
                  )}
                </span>
              )}
              {country.tipping && (
                <span className="tipping-info">Tip: {country.tipping}</span>
              )}
            </span>
          </div>
        )}

        {country.weather && (
          <div className="country-info-item">
            <span className="info-label">
              Weather ({country.weather.month})
            </span>
            <span className="info-value weather-details">
              {country.weather.min_temp_c !== null &&
                country.weather.max_temp_c !== null && (
                  <span className="weather-temp">
                    {country.weather.min_temp_c}°…
                    {country.weather.max_temp_c}°C
                  </span>
                )}
              {country.weather.min_temp_c === null &&
                country.weather.avg_temp_c !== null && (
                  <span className="weather-temp">
                    {country.weather.avg_temp_c}°C
                  </span>
                )}
              {country.weather.rainy_days !== null && (
                <span className="weather-rain">
                  {country.weather.rainy_days} rainy days
                </span>
              )}
              {country.weather.rainy_days === null &&
                country.weather.avg_precipitation_mm !== null && (
                  <span className="weather-rain">
                    {country.weather.avg_precipitation_mm} mm/day
                  </span>
                )}
            </span>
          </div>
        )}

        {country.timezone_offset_hours !== null && (
          <div className="country-info-item">
            <span className="info-label">Local Time</span>
            <span className="info-value">
              {formatLocalTime(country.timezone_offset_hours)}
            </span>
          </div>
        )}

        {country.languages && (
          <div className="country-info-item">
            <span className="info-label">Languages</span>
            <span className="info-value">{country.languages}</span>
          </div>
        )}

        {country.visa_free_days !== null && (
          <div className="country-info-item">
            <span className="info-label">Visa (CZ)</span>
            <span
              className={`info-value ${country.visa_free_days === 0 ? "visa-required" : "visa-free"}`}
            >
              {country.visa_free_days === 0
                ? "Visa required"
                : `${country.visa_free_days} days`}
            </span>
          </div>
        )}
        {country.visa_free_days === null && country.eu_roaming && (
          <div className="country-info-item">
            <span className="info-label">Visa (CZ)</span>
            <span className="info-value visa-free">EU / Unlimited</span>
          </div>
        )}

        {country.sunrise_sunset && (
          <div className="country-info-item">
            <span className="info-label">Daylight</span>
            <span className="info-value sunrise-sunset">
              {country.sunrise_sunset.sunrise} – {country.sunrise_sunset.sunset}{" "}
              ({country.sunrise_sunset.day_length_hours}h)
            </span>
          </div>
        )}
      </div>

      {country.holidays.length > 0 && (
        <div className="country-info-holidays">
          <span className="info-label">Public Holidays</span>
          <div className="country-holidays-list">
            {country.holidays.map((h, i) => (
              <div key={`${h.date}-${i}`} className="country-holiday-item">
                <span className="country-holiday-date">
                  {new Date(h.date + "T00:00:00").toLocaleDateString("en-GB", {
                    day: "numeric",
                    month: "short",
                  })}
                </span>
                <span
                  className="country-holiday-name"
                  title={h.local_name || ""}
                >
                  {h.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {country.health && (
        <div className="country-info-health">
          {country.health.vaccinations_required.length > 0 && (
            <div className="health-section">
              <span className="info-label">Required Vaccinations</span>
              <div className="health-vaccines">
                {country.health.vaccinations_required.map((v) => (
                  <span
                    key={v.vaccine}
                    className={`health-vaccine ${v.covered ? "health-vaccine-covered" : "health-vaccine-required"}`}
                    title={v.notes || ""}
                  >
                    {v.covered && "✓ "}
                    {v.vaccine}
                  </span>
                ))}
              </div>
            </div>
          )}

          {country.health.vaccinations_recommended.length > 0 && (
            <div className="health-section">
              <span className="info-label">Recommended Vaccinations</span>
              <div className="health-vaccines">
                {country.health.vaccinations_recommended.map((v) => (
                  <span
                    key={v.vaccine}
                    className={`health-vaccine ${v.covered ? "health-vaccine-covered" : v.priority === "consider" ? "health-vaccine-consider" : "health-vaccine-recommended"}`}
                    title={v.notes || ""}
                  >
                    {v.covered && "✓ "}
                    {v.vaccine}
                  </span>
                ))}
              </div>
            </div>
          )}

          {country.health.malaria && country.health.malaria.risk && (
            <div className="health-section health-malaria">
              <span className="info-label">Malaria Risk</span>
              <div className="health-malaria-details">
                {country.health.malaria.areas && (
                  <span className="health-malaria-areas">
                    {country.health.malaria.areas}
                  </span>
                )}
                {country.health.malaria.prophylaxis.length > 0 && (
                  <span className="health-malaria-prophylaxis">
                    Prophylaxis: {country.health.malaria.prophylaxis.join(", ")}
                  </span>
                )}
                {country.health.malaria.drug_resistance.length > 0 && (
                  <span className="health-malaria-resistance">
                    Resistance:{" "}
                    {country.health.malaria.drug_resistance.join(", ")}
                  </span>
                )}
              </div>
            </div>
          )}

          {country.health.other_risks.length > 0 && (
            <div className="health-section">
              <span className="info-label">Other Risks</span>
              <div className="health-risks">
                {country.health.other_risks.map((r) => (
                  <span key={r} className="health-risk-tag">
                    {r}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      {country.travel_docs && country.travel_docs.length > 0 && (
        <div className="country-info-travel-docs">
          <span className="info-label">Travel Documents</span>
          <div className="travel-doc-badges">
            {country.travel_docs.map((td) => (
              <span
                key={td.id}
                className={`travel-doc-badge${td.expires_before_trip ? " travel-doc-expiring" : ""}`}
                onClick={() => navigate("/admin/documents/visas")}
              >
                {td.label}
                {td.entry_type && (
                  <span className="travel-doc-entry-type">{td.entry_type}</span>
                )}
                {td.passport_label && (
                  <span className="travel-doc-passport">
                    {td.passport_label}
                  </span>
                )}
                {td.valid_until && (
                  <span className="travel-doc-validity">
                    until {td.valid_until}
                  </span>
                )}
                {td.expires_before_trip && (
                  <span className="travel-doc-warning">expires!</span>
                )}
                {td.has_files && <span className="travel-doc-file">📎</span>}
              </span>
            ))}
          </div>
        </div>
      )}
      {country.travel_docs &&
        country.travel_docs.length === 0 &&
        country.visa_free_days === 0 && (
          <div className="travel-doc-suggest-banner">
            No visa/travel document assigned for this country
            {country.iso_alpha2 && (
              <button
                className="travel-doc-add-btn"
                onClick={() =>
                  navigate(
                    `/admin/documents/visas?newTravelDoc=${country.iso_alpha2}`,
                  )
                }
              >
                + Add
              </button>
            )}
          </div>
        )}
      {country.fixers && country.fixers.length > 0 && (
        <div className="country-info-fixers">
          <span className="info-label">Fixers</span>
          <div className="fixer-info-badges">
            {country.fixers.map((f) => (
              <span
                key={f.id}
                className={`fixer-info-badge${!f.is_assigned ? " available" : ""}`}
              >
                <span
                  className="fixer-info-name"
                  onClick={() => navigate("/admin/people/fixers")}
                >
                  {f.name}
                </span>
                <span className="fixer-info-type">{f.type}</span>
                {f.rating != null && (
                  <span className="fixer-info-rating">
                    {"★".repeat(f.rating)}
                  </span>
                )}
                {f.whatsapp && (
                  <a
                    className="fixer-info-whatsapp"
                    href={`https://wa.me/${f.whatsapp.replace(/[^0-9]/g, "")}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    WA
                  </a>
                )}
                {f.phone && !f.whatsapp && (
                  <a
                    className="fixer-info-phone"
                    href={`tel:${f.phone}`}
                    onClick={(e) => e.stopPropagation()}
                  >
                    Tel
                  </a>
                )}
                {!readOnly && f.is_assigned && (
                  <button
                    className="fixer-info-remove-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      apiFetch(`/api/v1/admin/fixers/${f.id}/trips/${tripId}`, {
                        method: "DELETE",
                      }).then(() => refetchCountryInfo());
                    }}
                  >
                    ×
                  </button>
                )}
                {!readOnly && !f.is_assigned && (
                  <button
                    className="fixer-info-assign-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      apiFetch(`/api/v1/admin/fixers/${f.id}/trips/${tripId}`, {
                        method: "POST",
                      }).then(() => refetchCountryInfo());
                    }}
                  >
                    +
                  </button>
                )}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  if (countryInfo.length === 1) {
    return (
      <div className="country-info-panel">
        {renderCountryCard(countryInfo[0])}
      </div>
    );
  }

  return (
    <div className="country-info-panel country-info-tabbed">
      <div className="country-flag-tabs">
        {countryInfo.map((c, i) => (
          <button
            key={c.iso_alpha2 || c.country_name}
            className={`country-flag-tab ${i === safeIndex ? "active" : ""}`}
            onClick={() => setSelectedInfoCountry(i)}
            title={c.country_name}
          >
            <Flag code={c.iso_alpha2} size={20} />
          </button>
        ))}
      </div>
      {renderCountryCard(countryInfo[safeIndex])}
    </div>
  );
}
