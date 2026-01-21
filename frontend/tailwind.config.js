/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{svelte,js,ts,jsx,tsx}"],
	theme: {
		extend: {
			colors: {
				// Vanderbilt colors
				vandy: {
					gold: "#CFAE70",
					black: "#000000",
				},
			},
			fontFamily: {
				sans: ["Inter", "system-ui", "sans-serif"],
			},
		},
	},
	plugins: [],
};
