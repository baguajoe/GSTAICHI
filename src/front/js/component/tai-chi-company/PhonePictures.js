import React from "react";

// Simple drawings of what the member sees on their phone, used by the "Add to your phone" help page.
// The thing to tap is drawn in the primary color with a thick ring around it.

const HIGHLIGHT = "var(--primary-color)";

const Phone = ({ children, label }) => (
    <svg viewBox="0 0 200 360" className="tcc-phone-picture" role="img" aria-label={label}>
        <rect x="4" y="4" width="192" height="352" rx="26" fill="#ffffff" stroke="#1a1a1a" strokeWidth="6" />
        <rect x="16" y="22" width="168" height="316" rx="8" fill="#f2f2f2" />
        {children}
    </svg>
);

const Ring = ({ cx, cy, r = 20 }) => (
    <circle cx={cx} cy={cy} r={r} fill="none" stroke={HIGHLIGHT} strokeWidth="5" />
);

const PageLines = ({ top = 50 }) => (
    <g fill="#c9c9c9">
        <rect x="30" y={top} width="140" height="10" rx="3" />
        <rect x="30" y={top + 20} width="110" height="10" rx="3" />
        <rect x="30" y={top + 40} width="125" height="10" rx="3" />
        <rect x="30" y={top + 60} width="90" height="10" rx="3" />
    </g>
);

// Safari's share button: a square with an arrow pointing up
const ShareIcon = ({ x, y, color = "#1a5fb4" }) => (
    <g stroke={color} strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round">
        <path d={`M${x - 8} ${y - 2} h-4 v18 h24 v-18 h-4`} />
        <path d={`M${x} ${y + 6} v-18 M${x - 6} ${y - 6} l6 -6 l6 6`} />
    </g>
);

// The Safari app icon: a blue compass
export const SafariStep = () => (
    <Phone label="An iPhone home screen. The Safari app, a blue compass, is highlighted.">
        <g fill="#c9c9c9">
            {[0, 1, 2].map(row => [0, 1, 2, 3].map(col => (
                <rect key={`${row}-${col}`} x={30 + col * 38} y={48 + row * 58} width="28" height="28" rx="7" />
            )))}
        </g>
        <rect x="16" y="282" width="168" height="56" fill="#e4e4e4" />
        <rect x="68" y="292" width="36" height="36" rx="9" fill="#ffffff" stroke="#c9c9c9" />
        <circle cx="86" cy="310" r="14" fill="#1a8cff" />
        <path d="M86 300 l4 10 l-4 10 l-4 -10 z" fill="#ffffff" transform="rotate(45 86 310)" />
        <Ring cx={86} cy={310} r={25} />
        <text x="86" y="270" fontSize="13" textAnchor="middle" fontWeight="700" fill={HIGHLIGHT}>Open Safari</text>
    </Phone>
);

export const IphoneShareStep = () => (
    <Phone label="Safari on iPhone. The Share button, a square with an arrow pointing up, is at the bottom of the screen.">
        <rect x="30" y="30" width="140" height="18" rx="9" fill="#dddddd" />
        <PageLines top={70} />
        <rect x="16" y="290" width="168" height="48" fill="#ffffff" />
        <ShareIcon x={100} y={312} color={HIGHLIGHT} />
        <Ring cx={100} cy={312} r={22} />
        <text x="100" y="282" textAnchor="middle" fontSize="13" fontWeight="700" fill={HIGHLIGHT}>Tap Share</text>
    </Phone>
);

export const IphoneAddStep = () => (
    <Phone label="The Share menu is open. Scroll down and tap Add to Home Screen.">
        <PageLines top={40} />
        <rect x="16" y="140" width="168" height="198" rx="12" fill="#ffffff" />
        <g fontSize="13" fill="#1a1a1a">
            <text x="30" y="170">Copy</text>
            <line x1="30" y1="182" x2="170" y2="182" stroke="#dddddd" />
            <text x="30" y="204">Add to Reading List</text>
            <line x1="30" y1="216" x2="170" y2="216" stroke="#dddddd" />
            <rect x="22" y="224" width="156" height="34" rx="6" fill="#f6eeee" stroke={HIGHLIGHT} strokeWidth="4" />
            <text x="30" y="246" fontSize="11.5" fontWeight="700" fill={HIGHLIGHT} textLength="118" lengthAdjust="spacingAndGlyphs">Add to Home Screen</text>
            <rect x="156" y="233" width="15" height="15" rx="3" fill="none" stroke={HIGHLIGHT} strokeWidth="2.5" />
            <path d="M163.5 236 v9 M159 240.5 h9" stroke={HIGHLIGHT} strokeWidth="2.5" />
            <line x1="30" y1="270" x2="170" y2="270" stroke="#dddddd" />
            <text x="30" y="292">Print</text>
        </g>
    </Phone>
);

export const ConfirmStep = ({ appName, button }) => (
    <Phone label={`A box shows the app name, ${appName}. Tap ${button} in the top right corner.`}>
        <rect x="16" y="22" width="168" height="70" fill="#ffffff" />
        <text x="22" y="58" fontSize="11" fill="#1a5fb4" textLength="34" lengthAdjust="spacingAndGlyphs">Cancel</text>
        <text x="95" y="58" fontSize="11" textAnchor="middle" fontWeight="700" textLength="64" lengthAdjust="spacingAndGlyphs">{button === "Add" ? "Add to Home" : "Install app"}</text>
        <rect x="126" y="40" width="56" height="26" rx="6" fill="#f6eeee" stroke={HIGHLIGHT} strokeWidth="4" />
        <text x="154" y="58" fontSize="12" textAnchor="middle" fontWeight="700" fill={HIGHLIGHT} textLength={button.length * 6.5} lengthAdjust="spacingAndGlyphs">{button}</text>
        <rect x="26" y="110" width="40" height="40" rx="10" fill={HIGHLIGHT} />
        <text x="74" y="135" fontSize="11" fontWeight="700">{appName}</text>
        <PageLines top={180} />
    </Phone>
);

export const HomeScreenStep = ({ appName }) => (
    <Phone label={`Your home screen now has an icon called ${appName}. Tap it to open the app.`}>
        <g fill="#c9c9c9">
            {[0, 1, 2].map(row => [0, 1, 2, 3].map(col => (
                <rect key={`${row}-${col}`} x={30 + col * 38} y={48 + row * 58} width="28" height="28" rx="7" />
            )))}
        </g>
        <rect x="68" y="222" width="28" height="28" rx="7" fill={HIGHLIGHT} />
        <Ring cx={82} cy={236} r={24} />
        <text x="82" y="276" fontSize="11" textAnchor="middle" fontWeight="700" fill={HIGHLIGHT}>{appName}</text>
    </Phone>
);

export const AndroidMenuStep = () => (
    <Phone label="Chrome on Android. The menu button, three dots, is in the top right corner.">
        <rect x="16" y="22" width="168" height="40" fill="#ffffff" />
        <rect x="26" y="32" width="120" height="20" rx="10" fill="#dddddd" />
        <g fill={HIGHLIGHT}>
            <circle cx="166" cy="34" r="3" />
            <circle cx="166" cy="42" r="3" />
            <circle cx="166" cy="50" r="3" />
        </g>
        <Ring cx={166} cy={42} r={16} />
        <text x="178" y="80" fontSize="12" textAnchor="end" fontWeight="700" fill={HIGHLIGHT}>Tap the menu</text>
        <PageLines top={110} />
    </Phone>
);

export const AndroidAddStep = () => (
    <Phone label="The menu is open. Tap Add to Home screen or Install app.">
        <PageLines top={40} />
        <rect x="60" y="26" width="124" height="196" rx="8" fill="#ffffff" stroke="#c9c9c9" />
        <g fontSize="12" fill="#1a1a1a">
            <text x="72" y="52">New tab</text>
            <text x="72" y="82">Bookmarks</text>
            <text x="72" y="112">History</text>
            <rect x="64" y="128" width="116" height="34" rx="6" fill="#f6eeee" stroke={HIGHLIGHT} strokeWidth="4" />
            <text x="70" y="150" fontSize="10.5" fontWeight="700" fill={HIGHLIGHT} textLength="104" lengthAdjust="spacingAndGlyphs">Add to Home screen</text>
            <text x="72" y="190">Settings</text>
        </g>
    </Phone>
);
