import axios from "axios";

// Centralized axios instance.
//
// In development this falls back to http://localhost:8000. In production,
// set REACT_APP_API_URL as a build-time environment variable (e.g. in your
// Vercel/Netlify project settings) pointing at the deployed backend URL.
//
// Note: Create React App only inlines REACT_APP_* variables at BUILD time,
// not runtime -- if you change REACT_APP_API_URL on your host, you need to
// trigger a new build/deploy, not just restart the app.
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
});

export default api;