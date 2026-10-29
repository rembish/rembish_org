import { MODES, modeColor, type LegMode } from "./gpsModes";

export default function ModeSwatch({ mode }: { mode: LegMode }) {
  const color = modeColor(mode);
  if (mode === "stop") {
    return (
      <svg className="gps-swatch" width="22" height="10" aria-hidden="true">
        <circle
          cx="11"
          cy="5"
          r="4"
          fill={color}
          stroke="#fff"
          strokeWidth="1.5"
        />
      </svg>
    );
  }
  return (
    <svg className="gps-swatch" width="22" height="10" aria-hidden="true">
      {mode !== "gap" && (
        <line
          x1="3"
          y1="5"
          x2="19"
          y2="5"
          stroke="#fff"
          strokeWidth="6"
          strokeLinecap="round"
        />
      )}
      <line
        x1="3"
        y1="5"
        x2="19"
        y2="5"
        stroke={color}
        strokeWidth={mode === "gap" ? 2 : 3}
        strokeDasharray={MODES[mode].dash}
        strokeLinecap="round"
      />
    </svg>
  );
}
