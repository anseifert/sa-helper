/** Cheerful sponge-at-keyboard illustration (original artwork for onboarding). */
export default function SpongeComputerIllustration({ className = "" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 420 320"
      role="img"
      aria-label="Cartoon sponge in a red hat typing at a computer"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="420" height="320" fill="#e8f4fc" rx="16" />
      <ellipse cx="210" cy="290" rx="140" ry="18" fill="#c5d9e8" opacity="0.6" />

      {/* Desk */}
      <rect x="60" y="220" width="300" height="14" fill="#6b4f3a" rx="4" />
      <rect x="80" y="234" width="20" height="50" fill="#5a4030" />
      <rect x="320" y="234" width="20" height="50" fill="#5a4030" />

      {/* Monitor */}
      <rect x="130" y="130" width="160" height="100" fill="#2d3748" rx="6" />
      <rect x="138" y="138" width="144" height="76" fill="#63b3ed" rx="2" />
      <rect x="150" y="150" width="40" height="6" fill="#bee3f8" rx="2" />
      <rect x="150" y="162" width="90" height="4" fill="#bee3f8" rx="2" />
      <rect x="150" y="172" width="70" height="4" fill="#bee3f8" rx="2" />
      <rect x="195" y="230" width="30" height="18" fill="#4a5568" />
      <rect x="170" y="248" width="80" height="8" fill="#4a5568" rx="2" />

      {/* Keyboard */}
      <rect x="155" y="208" width="110" height="14" fill="#718096" rx="3" />
      <g fill="#a0aec0">
        {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
          <rect key={i} x={160 + i * 12} y="211" width="8" height="5" rx="1" />
        ))}
      </g>

      {/* Sponge body */}
      <rect x="155" y="95" width="110" height="95" fill="#FFE566" rx="18" />
      <g fill="#E6C200" opacity="0.45">
        <circle cx="175" cy="120" r="5" />
        <circle cx="200" cy="135" r="4" />
        <circle cx="230" cy="118" r="5" />
        <circle cx="245" cy="150" r="4" />
        <circle cx="170" cy="155" r="4" />
        <circle cx="255" cy="175" r="5" />
      </g>

      {/* Red fedora */}
      <ellipse cx="210" cy="88" rx="62" ry="10" fill="#C41E3A" />
      <path d="M168 88 Q210 52 252 88 L248 98 Q210 68 172 98 Z" fill="#E52B45" />
      <rect x="198" y="72" width="24" height="18" fill="#E52B45" rx="2" />
      <ellipse cx="210" cy="72" rx="28" ry="8" fill="#A31730" />

      {/* Face */}
      <ellipse cx="188" cy="128" rx="14" ry="16" fill="#fff" />
      <ellipse cx="232" cy="128" rx="14" ry="16" fill="#fff" />
      <circle cx="188" cy="130" r="5" fill="#1a202c" />
      <circle cx="232" cy="130" r="5" fill="#1a202c" />
      <circle cx="190" cy="128" r="1.5" fill="#fff" />
      <circle cx="234" cy="128" r="1.5" fill="#fff" />
      <path
        d="M195 155 Q210 168 225 155"
        stroke="#1a202c"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      <ellipse cx="178" cy="148" rx="8" ry="4" fill="#ffb8b8" opacity="0.6" />
      <ellipse cx="242" cy="148" rx="8" ry="4" fill="#ffb8b8" opacity="0.6" />

      {/* Arms hammering keyboard */}
      <rect x="118" y="198" width="36" height="12" fill="#FFE566" rx="6" transform="rotate(-25 118 198)" />
      <circle cx="112" cy="210" r="10" fill="#FFE566" />
      <rect x="266" y="198" width="36" height="12" fill="#FFE566" rx="6" transform="rotate(25 302 198)" />
      <circle cx="308" cy="210" r="10" fill="#FFE566" />

      {/* Motion lines */}
      <path
        d="M95 185 L105 195 M88 200 L100 200"
        stroke="#718096"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <path
        d="M325 185 L315 195 M332 200 L320 200"
        stroke="#718096"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
