import { useState, useRef, useEffect, FormEvent } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import {
  BiMap,
  BiPhone,
  BiEnvelope,
  BiLogoTelegram,
  BiLogoWhatsapp,
  BiIdCard,
  BiKey,
} from "react-icons/bi";
import "leaflet/dist/leaflet.css";

// Fix for default marker icon in Leaflet + Vite
const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Wichterlova 2372/8, Prague 8
const LOCATION: [number, number] = [50.12237421115734, 14.467198995032321];
// Prague center (Old Town Square area)
const PRAGUE_CENTER: [number, number] = [50.0875, 14.4213];

// Cloudflare Turnstile site key (production only)
const TURNSTILE_SITE_KEY =
  window.location.hostname === "rembish.org" ? "0x4AAAAAACOtDa7rH4uKbUZD" : "";

declare global {
  interface Window {
    turnstile?: {
      render: (
        container: string | HTMLElement,
        options: { sitekey: string; callback: (token: string) => void },
      ) => string;
      reset: (widgetId: string) => void;
    };
  }
}

interface FormState {
  status: "idle" | "submitting" | "success" | "error";
  message?: string;
}

export default function Contact() {
  const [formState, setFormState] = useState<FormState>({ status: "idle" });
  const [turnstileToken, setTurnstileToken] = useState("");
  const loadedAt = useRef(Date.now());
  const turnstileRef = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string>("");

  useEffect(() => {
    if (!TURNSTILE_SITE_KEY || !turnstileRef.current) return;

    const renderWidget = () => {
      if (window.turnstile && turnstileRef.current && !widgetId.current) {
        widgetId.current = window.turnstile.render(turnstileRef.current, {
          sitekey: TURNSTILE_SITE_KEY,
          callback: (token: string) => setTurnstileToken(token),
        });
      }
    };

    // Turnstile script might not be loaded yet
    if (window.turnstile) {
      renderWidget();
    } else {
      const interval = setInterval(() => {
        if (window.turnstile) {
          renderWidget();
          clearInterval(interval);
        }
      }, 100);
      return () => clearInterval(interval);
    }
  }, []);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormState({ status: "submitting" });

    const form = e.currentTarget;
    const formData = new FormData(form);

    // Add timing data for spam protection
    formData.set("ts", loadedAt.current.toString());

    // Add Turnstile token if available
    if (turnstileToken) {
      formData.set("cf_turnstile_response", turnstileToken);
    }

    try {
      const response = await fetch("/api/v1/contact", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setFormState({
          status: "success",
          message: "Your message has been sent. Thank you!",
        });
        form.reset();
        loadedAt.current = Date.now(); // Reset timer for next submission
        // Reset Turnstile widget
        if (window.turnstile && widgetId.current) {
          window.turnstile.reset(widgetId.current);
          setTurnstileToken("");
        }
      } else {
        setFormState({
          status: "error",
          message: data.detail || "Failed to send message",
        });
      }
    } catch {
      setFormState({
        status: "error",
        message: "Network error. Please try again.",
      });
    }
  };

  return (
    <section id="contact" className="contact">
      <div className="container">
        <div className="section-title">
          <h2>Contact</h2>
          <p>Feel free to reach out</p>
        </div>

        <div className="contact-map">
          <MapContainer
            center={PRAGUE_CENTER}
            zoom={10}
            scrollWheelZoom={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Marker position={LOCATION} icon={markerIcon}>
              <Popup>Wichterlova 2372/8, Prague 8</Popup>
            </Marker>
          </MapContainer>
        </div>

        <div className="contact-grid">
          <div className="contact-info">
            <div className="info-item">
              <BiMap className="info-icon" />
              <div>
                <h4>Location</h4>
                <p>Wichterlova 2372/8, Prague 8, Czechia</p>
              </div>
            </div>

            <div className="info-item">
              <BiEnvelope className="info-icon" />
              <div>
                <h4>Email</h4>
                <p>
                  <a href="mailto:alex@rembish.org">alex@rembish.org</a>
                </p>
              </div>
            </div>

            <div className="info-item">
              <BiPhone className="info-icon" />
              <div>
                <h4>Phone</h4>
                <p>
                  <a href="tel:00420775054554">+420 775 054 554</a>
                </p>
              </div>
            </div>

            <div className="contact-socials">
              <a
                href="https://t.me/rembish"
                title="Telegram"
                aria-label="Telegram"
              >
                <BiLogoTelegram />
              </a>
              <a
                href="https://wa.me/420775054554"
                title="WhatsApp"
                aria-label="WhatsApp"
              >
                <BiLogoWhatsapp />
              </a>
              <a
                href="/alex-rembish.vcf"
                title="Download vCard"
                aria-label="Download vCard"
                download
              >
                <BiIdCard />
              </a>
              <a
                href="/alex-rembish.asc"
                title="PGP Public Key"
                aria-label="PGP Public Key"
              >
                <BiKey />
              </a>
            </div>
          </div>

          <form className="contact-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <input
                  type="text"
                  name="name"
                  placeholder="Your Name"
                  required
                  minLength={2}
                  autoComplete="name"
                />
              </div>
              <div className="form-group">
                <input
                  type="email"
                  name="email"
                  placeholder="Your Email"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="form-group">
              <input
                type="text"
                name="subject"
                placeholder="Subject"
                autoComplete="off"
              />
            </div>

            <div className="form-group">
              <textarea
                name="message"
                placeholder="Your Message"
                rows={6}
                required
                minLength={10}
              />
            </div>

            {/* Honeypot field - hidden from humans, bots will fill it */}
            <div className="form-group-hp" aria-hidden="true">
              <label htmlFor="website">Leave this empty</label>
              <input
                type="text"
                name="website"
                id="website"
                tabIndex={-1}
                autoComplete="off"
              />
            </div>

            {/* Cloudflare Turnstile widget (production only) */}
            {TURNSTILE_SITE_KEY && (
              <div ref={turnstileRef} className="turnstile-widget" />
            )}

            {formState.status === "error" && (
              <div className="form-message form-error">{formState.message}</div>
            )}

            {formState.status === "success" && (
              <div className="form-message form-success">
                {formState.message}
              </div>
            )}

            <button
              type="submit"
              className="btn-submit"
              disabled={formState.status === "submitting"}
            >
              {formState.status === "submitting"
                ? "Sending..."
                : "Send Message"}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
