import { BrowserRouter, Outlet, Route, Routes } from "react-router";

import { AuthProvider } from "./auth/AuthProvider";
import { RequireAuth } from "./auth/RequireAuth";
import DashboardLayout, { MoreMenu } from "./layouts/DashboardLayout";
import PublicLayout from "./layouts/PublicLayout";
import { OrganizationProvider } from "./organization/OrganizationProvider";
import AnimalPage from "./pages/dashboard/AnimalPage";
import AnimalsList from "./pages/dashboard/AnimalsList";
import Login from "./pages/dashboard/Login";
import Summary from "./pages/dashboard/Summary";
import AdoptionRequest from "./pages/public/AdoptionRequest";
import AnimalDetail from "./pages/public/AnimalDetail";
import Animals from "./pages/public/Animals";
import Help from "./pages/public/Help";
import Home from "./pages/public/Home";
import NotFound from "./pages/public/NotFound";
import Report from "./pages/public/Report";
import Thanks from "./pages/public/Thanks";

/** The session is only checked inside the panel, so the public website never asks who is signed in. */
function DashboardRoot() {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  );
}

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
          <Route path="dashboard" element={<DashboardRoot />}>
            <Route path="login" element={<Login />} />
            <Route element={<RequireAuth><DashboardLayout /></RequireAuth>}>
              <Route index element={<Summary />} />
              <Route path="animales" element={<AnimalsList />} />
              <Route path="animales/:id" element={<AnimalPage />} />
              <Route path="mas" element={<MoreMenu />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </OrganizationProvider>
  );
}
