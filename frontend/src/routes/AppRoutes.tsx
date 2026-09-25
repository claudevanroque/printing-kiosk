import {Route, Routes} from "react-router-dom";

import HomePage from "../pages/Homepage";

function AppRoutes() {
    return (
        <Routes>
            <Route path="/" element={<HomePage />} />
        </Routes>
    );
}

export default AppRoutes;