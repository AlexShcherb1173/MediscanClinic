/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./static/**/*.js"
  ],
  safelist: [
    "bg-green-100",
    "bg-green-200",
    "bg-red-100",
    "bg-red-200",
    "bg-blue-500",
    "ring-blue-100",
    "border-blue-500",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};