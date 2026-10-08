import axios from "axios";


const API_URL = import.meta.env.VITE_LOCAL_API_URL;

const localApi = axios.create({
    baseURL: API_URL ?? "http://127.0.0.1:9001/api",
    timeout: 30000,
});


export default localApi;