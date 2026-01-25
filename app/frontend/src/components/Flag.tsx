/**
 * Flag component using SVG flags from /public/flags/.
 * Base flags from lipis/flag-icons, custom territories added manually.
 */

// Custom territory codes mapped to their SVG filenames
// These territories don't have standard ISO codes in flag-icons
const CUSTOM_CODES: Record<string, string> = {
  xs: "somaliland", // Somaliland (custom code)
  xn: "northern-cyprus", // Northern Cyprus (custom code)
};

interface FlagProps {
  code: string | null;
  size?: number;
  className?: string;
  title?: string;
}

export default function Flag({
  code,
  size = 16,
  className = "",
  title,
}: FlagProps) {
  if (!code || code === "-") {
    return null;
  }

  const lowerCode = code.toLowerCase();
  const filename = CUSTOM_CODES[lowerCode] || lowerCode;

  return (
    <img
      src={`/flags/${filename}.svg`}
      alt={title || code}
      title={title}
      className={`flag-icon ${className}`}
      style={{
        width: size,
        height: size * 0.75,
        objectFit: "cover",
        borderRadius: 2,
        verticalAlign: "middle",
      }}
      onError={(e) => {
        // Hide broken images
        (e.target as HTMLImageElement).style.display = "none";
      }}
    />
  );
}
