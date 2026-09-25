import axios from "axios";


const API_URL = import.meta.env.VITE_SERVER_API_URL;


export const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});