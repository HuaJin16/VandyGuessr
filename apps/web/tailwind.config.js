/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{svelte,js,ts,jsx,tsx}"],
	theme: {
		extend: {
			colors: {
				brand: {
					DEFAULT: "#2e933c",
					dark: "#1f7a2b",
					light: "rgba(46,147,60,0.10)",
				},
				gold: {
					DEFAULT: "#e8a817",
					dark: "#b4820d",
					light: "rgba(232,168,23,0.12)",
					ink: "#745000",
				},
				ink: "#1c1917",
				muted: "#78716c",
				line: {
					DEFAULT: "#e7e5e4",
					strong: "#d6d3d1",
				},
				surface: {
					DEFAULT: "#ffffff",
					subtle: "#fafaf9",
					strong: "#f5f5f4",
				},
				canvas: "#fafaf9",
				danger: {
					DEFAULT: "#dc2626",
					dark: "#b91c1c",
					light: "rgba(220,38,38,0.06)",
					ink: "#991b1b",
				},
				success: {
					light: "rgba(46,147,60,0.06)",
					ink: "#166534",
				},
				warning: {
					light: "rgba(232,168,23,0.10)",
					ink: "#745000",
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
				xs: "0 1px 2px rgba(0,0,0,0.05)",
				sm: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
				md: "0 4px 12px rgba(0,0,0,0.08)",
				lg: "0 12px 32px rgba(0,0,0,0.10)",
				ring: "0 0 0 3px rgba(46,147,60,0.20)",
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
