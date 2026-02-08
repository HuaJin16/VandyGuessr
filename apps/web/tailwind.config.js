/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{svelte,js,ts,jsx,tsx}"],
	theme: {
		extend: {
			colors: {
				jungle: "#2E933C",
				"jungle-dark": "#236E2D",
				gold: "#F4C430",
				terrain: "#F5F2E9",
				charcoal: "#18181B",
				clay: "#D95D39",
			},
			fontFamily: {
				heading: ["Rubik", "sans-serif"],
				body: ["Inter", "sans-serif"],
			},
			boxShadow: {
				hard: "4px 4px 0px 0px rgba(0,0,0,0.1)",
				"hard-lg": "6px 6px 0px 0px rgba(0,0,0,0.12)",
				"3d": "0 6px 0 #236E2D",
			},
		},
	},
	plugins: [],
};
