/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{svelte,js,ts,jsx,tsx}"],
	theme: {
		extend: {
			colors: {
				brand: {
					DEFAULT: "#2e933c",
					dark: "#236e2d",
					light: "rgba(46,147,60,0.10)",
				},
				gold: {
					DEFAULT: "#e8a817",
					dark: "#c48d10",
					light: "rgba(232,168,23,0.12)",
					ink: "#6b4c00",
				},
				ink: "#1a1a1a",
				muted: "#5c6370",
				line: {
					DEFAULT: "#e5e2db",
					strong: "#c4c0b8",
				},
				surface: "#ffffff",
				canvas: "#f7f5f0",
				danger: {
					DEFAULT: "#dc4a3a",
					dark: "#b33a2c",
					light: "rgba(220,74,58,0.08)",
					ink: "#8b2820",
				},
				success: {
					light: "rgba(46,147,60,0.08)",
					ink: "#1a5c24",
				},
				warning: {
					light: "rgba(232,168,23,0.12)",
					ink: "#6b4c00",
				},
				mp: "#3b82f6",
				player: {
					blue: "#3b82f6",
					purple: "#8b5cf6",
					orange: "#f97316",
					cyan: "#06b6d4",
					pink: "#ec4899",
				},
			},
			fontFamily: {
				sans: ["Inter", "system-ui", "sans-serif"],
				mono: ["IBM Plex Mono", "monospace"],
			},
			borderRadius: {
				sm: "8px",
				md: "12px",
				lg: "16px",
				pill: "9999px",
			},
			boxShadow: {
				sm: "3px 3px 0 0 rgba(0,0,0,0.06)",
				md: "4px 4px 0 0 rgba(0,0,0,0.08)",
				lg: "6px 6px 0 0 rgba(0,0,0,0.10)",
				"3d": "0 4px 0 var(--brand-dark)",
				"3d-gold": "0 4px 0 var(--gold-dark)",
				"3d-danger": "0 4px 0 var(--danger-dark)",
				ring: "0 0 0 3px rgba(46,147,60,0.35)",
			},
			transitionTimingFunction: {
				DEFAULT: "cubic-bezier(0.4,0,0.2,1)",
			},
			transitionDuration: {
				fast: "120ms",
				DEFAULT: "180ms",
			},
		},
	},
	plugins: [],
};
