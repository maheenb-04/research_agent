/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{js,jsx}"],
    theme: {
      extend: {
        colors: {
          cream: "#FFF2C6",
          creamLight: "#FFF8DE",
          ink: "#22201A",
          blue: "#8CA9FF",
          blueSoft: "#AAC4F5",
          blueDark: "#2A4A9E",
          muted: "#6b6455",
          placeholder: "#b3ab96",
        },
        fontFamily: {
          display: ["Unbounded", "sans-serif"],
          body: ["Manrope", "sans-serif"],
        },
      },
    },
    plugins: [],
  }
