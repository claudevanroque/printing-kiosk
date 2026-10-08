import {Route, Routes} from "react-router-dom";

import HomePage from "../pages/Homepage";
import PrintPage from "../pages/PrintPage";

function AppRoutes() {
    return (
        <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/print" element={<PrintPage />} />
        </Routes>
    );
}

export default AppRoutes;