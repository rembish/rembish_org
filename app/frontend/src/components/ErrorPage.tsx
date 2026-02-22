import { useState } from "react";

interface ErrorPageProps {
  status?: number;
  title?: string;
  message?: string;
}

const messages: Record<number, { title: string; lines: string[] }> = {
  404: {
    title: "Page not found",
    lines: [
      "Looks like you've wandered off the map",
      "This page packed its bags and left",
      "404: Destination not found in any guidebook",
      "Even Google Maps can't find this page",
      "This route has been decommissioned",
      "No visa can get you into this page",
    ],
  },
  403: {
    title: "Access denied",
    lines: [
      "This area requires a VIP pass",
      "Your boarding pass doesn't cover this zone",
      "Passport control says no",
      "This lounge is invitation-only",
    ],
  },
  500: {
    title: "Something went wrong",
    lines: [
      "Houston, we have a turbulence",
      "The server took an unscheduled layover",
      "Something crashed — and it wasn't a plane",
      "This page needs an emergency landing",
    ],
  },
};

function pick(lines: string[]): string {
  return lines[Math.floor(Math.random() * lines.length)];
}

export default function ErrorPage({
  status = 404,
  title,
  message,
}: ErrorPageProps) {
  const defaults = messages[status] ?? messages[404];
  const [line] = useState(() => message ?? pick(defaults.lines));

  return (
    <div className="error-boundary">
      <div>
        <div className="error-code">{status}</div>
        <h2>{title ?? defaults.title}</h2>
        <p>{line}</p>
        <a href="/" className="error-home-link">
          Take me home
        </a>
      </div>
    </div>
  );
}
