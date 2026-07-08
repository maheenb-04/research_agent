/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{js,jsx}"],
    theme: {
      extend: {
        colors: {
          cream: "#FAF3E7",
          ink: "#1A1A1A",
          periwinkle: "#8EA6FF",
          periwinkleLight: "#EDF1FF",
          muted: "#6b6459",
          placeholder: "#b0a99c",
        },
        fontFamily: {
          display: ["Fredoka", "sans-serif"],
          marker: ["Permanent Marker", "cursive"],
          body: ["Geist Pixel", "sans-serif"],
        },
      },
    },
    plugins: [],
  }
