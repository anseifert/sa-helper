/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        rh: {
          red: "#ee0000",
          dark: "#1a1a1a",
          gray: "#4d4d4d",
        },
      },
    },
  },
  plugins: [],
};
