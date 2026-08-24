const BRAND = {
  deepForest: "#0B2A1E",
  emerald: "#168B62",
};

export default function EvolisLogo({ size = 40, showTagline = false }: { size?: number; showTagline?: boolean }) {
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 12 }}>
      <svg viewBox="0 0 512 512" width={size} height={size} aria-hidden="true" style={{ flexShrink: 0 }}>
        <defs>
          <linearGradient id="evolis-g1" x1="124" y1="84" x2="386" y2="162" gradientUnits="userSpaceOnUse">
            <stop stopColor="#C7F36A" />
            <stop offset="1" stopColor="#4AAE70" />
          </linearGradient>
          <linearGradient id="evolis-g2" x1="126" y1="196" x2="389" y2="258" gradientUnits="userSpaceOnUse">
            <stop stopColor="#168B62" />
            <stop offset="1" stopColor="#5DBA7E" />
          </linearGradient>
          <linearGradient id="evolis-g3" x1="128" y1="300" x2="390" y2="386" gradientUnits="userSpaceOnUse">
            <stop stopColor="#0B2A1E" />
            <stop offset="1" stopColor="#69B968" />
          </linearGradient>
        </defs>
        <path
          d="M137 119C163 84 201 68 245 68H389C391 109 368 132 329 132H243C207 132 178 145 157 170L137 194V119Z"
          fill="url(#evolis-g1)"
        />
        <path
          d="M137 213C163 178 201 162 245 162H389C391 203 368 226 329 226H243C207 226 178 239 157 264L137 288V213Z"
          fill="url(#evolis-g2)"
        />
        <path
          d="M137 307C162 274 200 256 243 256H324C365 256 389 279 389 320H251C221 320 198 330 180 350C194 372 219 384 253 384H345C374 384 392 400 398 433H249C184 433 137 393 137 334V307Z"
          fill="url(#evolis-g3)"
        />
      </svg>

      <div>
        {/* text-ink (not a hardcoded hex) so the wordmark stays legible
         * against both the light and dark sidebar background — section 47. */}
        <div
          className="text-ink"
          style={{ fontSize: size < 32 ? 16 : 22, fontWeight: 500, letterSpacing: "0.14em", lineHeight: 1.1 }}
        >
          EVOLIS
        </div>
        {showTagline && (
          <div style={{ marginTop: 2, fontSize: 9, fontWeight: 600, letterSpacing: "0.22em", color: BRAND.emerald }}>
            PERSONAL EVOLUTION INTELLIGENCE
          </div>
        )}
      </div>
    </div>
  );
}
