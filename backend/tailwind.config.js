/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
  "./backend/templates/**/*.html",
  "./backend/apps/**/templates/**/*.html",
  "./backend/static/**/*.js",

  // если вдруг запускаешь из backend/
  "./templates/**/*.html",
  "./apps/**/templates/**/*.html",
  "./static/**/*.js",
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