import type { SVGProps } from "react";

export function HeroIllustration(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 520 420"
      fill="none"
      role="img"
      aria-labelledby="hero-illustration-title"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <title id="hero-illustration-title">강사와 교육 자료 일러스트</title>
      <defs>
        <linearGradient id="hero-blue-gradient" x1="86" y1="38" x2="444" y2="390" gradientUnits="userSpaceOnUse">
          <stop stopColor="#60A5FA" stopOpacity="0.22" />
          <stop offset="1" stopColor="#2563EB" stopOpacity="0.08" />
        </linearGradient>
        <filter id="hero-soft-shadow" x="44" y="38" width="432" height="354" filterUnits="userSpaceOnUse">
          <feDropShadow dx="0" dy="16" stdDeviation="18" floodColor="#18181B" floodOpacity="0.12" />
        </filter>
      </defs>

      <path
        d="M455 210C455 305.545 372.545 383 271 383C169.455 383 65 320.545 65 225C65 129.455 151.455 44 253 44C354.545 44 455 114.455 455 210Z"
        fill="url(#hero-blue-gradient)"
      />
      <path d="M112 356H438" stroke="#D4D4D8" strokeWidth="12" strokeLinecap="round" />
      <path d="M131 382H399" stroke="#E4E4E7" strokeWidth="9" strokeLinecap="round" />

      <g filter="url(#hero-soft-shadow)">
        <rect x="112" y="106" width="286" height="178" rx="18" fill="#FFFFFF" />
        <rect x="132" y="126" width="246" height="138" rx="10" fill="#F4F4F5" />
        <path d="M152 162H259" stroke="#18181B" strokeWidth="10" strokeLinecap="round" />
        <path d="M152 194H306" stroke="#3B82F6" strokeWidth="10" strokeLinecap="round" />
        <path d="M152 226H230" stroke="#D4D4D8" strokeWidth="10" strokeLinecap="round" />
        <circle cx="338" cy="169" r="22" fill="#2563EB" />
        <path d="M329 169L336 176L350 160" stroke="#FFFFFF" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
      </g>

      <path d="M190 286H338L360 354H168L190 286Z" fill="#18181B" />
      <path d="M207 302H323L333 335H197L207 302Z" fill="#3B82F6" />
      <path d="M170 354H358" stroke="#18181B" strokeWidth="14" strokeLinecap="round" />

      <g>
        <circle cx="244" cy="182" r="29" fill="#18181B" />
        <path
          d="M210 282C214 237 225 213 252 213C279 213 291 238 295 282H210Z"
          fill="#2563EB"
        />
        <path d="M222 236L160 210" stroke="#18181B" strokeWidth="13" strokeLinecap="round" />
        <path d="M286 235L347 213" stroke="#18181B" strokeWidth="13" strokeLinecap="round" />
        <path d="M242 219L254 219L248 245L242 219Z" fill="#FFFFFF" />
        <path d="M216 283H290" stroke="#18181B" strokeWidth="13" strokeLinecap="round" />
      </g>

      <g>
        <path d="M70 278L142 255L150 302L78 326L70 278Z" fill="#FFFFFF" stroke="#18181B" strokeWidth="8" />
        <path d="M78 278L148 302" stroke="#3B82F6" strokeWidth="5" />
        <path d="M94 286L130 274" stroke="#D4D4D8" strokeWidth="5" strokeLinecap="round" />
        <path d="M98 306L135 294" stroke="#D4D4D8" strokeWidth="5" strokeLinecap="round" />
      </g>

      <g>
        <rect x="364" y="279" width="62" height="48" rx="7" fill="#2563EB" />
        <path d="M374 279V266C374 254.954 382.954 246 394 246H397C408.046 246 417 254.954 417 266V279" stroke="#18181B" strokeWidth="8" />
        <path d="M381 301H409" stroke="#FFFFFF" strokeWidth="6" strokeLinecap="round" />
      </g>

      <g>
        <circle cx="92" cy="125" r="27" fill="#FFFFFF" stroke="#D4D4D8" strokeWidth="7" />
        <path d="M92 111V139" stroke="#3B82F6" strokeWidth="7" strokeLinecap="round" />
        <path d="M78 125H106" stroke="#3B82F6" strokeWidth="7" strokeLinecap="round" />
      </g>

      <g>
        <rect x="408" y="118" width="58" height="58" rx="14" fill="#FFFFFF" stroke="#D4D4D8" strokeWidth="7" />
        <path d="M424 144H452" stroke="#18181B" strokeWidth="7" strokeLinecap="round" />
        <path d="M424 160H442" stroke="#3B82F6" strokeWidth="7" strokeLinecap="round" />
      </g>

      <path d="M92 194C101 194 101 182 110 182C119 182 119 194 128 194" stroke="#3B82F6" strokeWidth="7" strokeLinecap="round" />
      <path d="M420 226C429 226 429 214 438 214C447 214 447 226 456 226" stroke="#18181B" strokeWidth="7" strokeLinecap="round" />
      <circle cx="404" cy="82" r="8" fill="#3B82F6" />
      <circle cx="128" cy="88" r="7" fill="#18181B" />
      <circle cx="448" cy="272" r="6" fill="#D4D4D8" />
    </svg>
  );
}
