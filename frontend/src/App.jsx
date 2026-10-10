import { BrowserRouter, Route, Routes } from "react-router";

import PublicLayout from "./layouts/PublicLayout";
import { OrganizationProvider } from "./organization/OrganizationProvider";
import AdoptionRequest from "./pages/public/AdoptionRequest";
import AnimalDetail from "./pages/public/AnimalDetail";
import Animals from "./pages/public/Animals";
import Help from "./pages/public/Help";
import Home from "./pages/public/Home";
import NotFound from "./pages/public/NotFound";
import Report from "./pages/public/Report";
import Thanks from "./pages/public/Thanks";

export default function App() {
  return (
    <OrganizationProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route index element={<Home />} />
            <Route path="animales" element={<Animals />} />
            <Route path="animales/:slug" element={<AnimalDetail />} />
            <Route path="animales/:slug/adoptar" element={<AdoptionRequest />} />
            <Route path="ayudar" element={<Help />} />
            <Route path="avisar" element={<Report />} />
            <Route path="gracias" element={<Thanks />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </OrganizationProvider>
  );
}
