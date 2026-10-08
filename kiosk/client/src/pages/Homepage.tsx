import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/localApi";
import type { HealthResponse } from "../types/localDocument";



function HomePage() {

    const navigate = useNavigate();

    const [backendStatus, setBackendStatus] =
        useState("Checking...");

    const [databaseStatus, setDatabaseStatus] =
        useState("Checking...");


    useEffect(() => {

        const checkHealth = async () => {

            try {

                const response =
                    await api.get<HealthResponse>(
                        "/health"
                    );

                if (response.data.status === "ok") {
                    setBackendStatus("Online");
                } else {
                    setBackendStatus("Error");
                }


                if (
                    response.data.database ===
                    "connected"
                ) {
                    setDatabaseStatus("Connected");
                } else {
                    setDatabaseStatus("Disconnected");
                }

            } catch (error) {

                console.error(
                    "Health check failed:",
                    error
                );

                setBackendStatus("Offline");
                setDatabaseStatus("Disconnected");

            }

        };


        checkHealth();

    }, []);


    return (
        <main className="kiosk-home">

            <header className="status-bar">

                <div className="brand">
                    Printing Kiosk
                </div>


                <div className="system-status">

                    <span>
                        Backend:
                        {" "}
                        <strong>
                            {backendStatus}
                        </strong>
                    </span>

                    <span>
                        Database:
                        {" "}
                        <strong>
                            {databaseStatus}
                        </strong>
                    </span>

                </div>

            </header>


            <section className="hero">

                <p className="welcome">
                    Welcome
                </p>

                <h1>
                    What would you like to do?
                </h1>

                <p className="subtitle">
                    Select a service to continue.
                </p>

            </section>


            <section className="service-grid">

                <button
                    type="button"
                    className="service-card"
                    onClick={() => navigate("/print")}
                >

                    <div className="service-icon">
                        🖨️
                    </div>

                    <h2>
                        Print
                    </h2>

                    <p>
                        Upload and print your
                        documents or images.
                    </p>

                </button>


                <button
                    type="button"
                    className="service-card"
                >

                    <div className="service-icon">
                        📄
                    </div>

                    <h2>
                        Xerox / Copy
                    </h2>

                    <p>
                        Copy your physical
                        documents.
                    </p>

                </button>


                <button
                    type="button"
                    className="service-card"
                >

                    <div className="service-icon">
                        📑
                    </div>

                    <h2>
                        Scan
                    </h2>

                    <p>
                        Scan documents and
                        save them digitally.
                    </p>

                </button>

            </section>


            <footer className="kiosk-footer">

                <p>
                    Coin and QR payments will
                    be available.
                </p>

            </footer>

        </main>
    );
}


export default HomePage;