import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";

const CV = lazy(() => import("./pages/CV"));
const Projects = lazy(() => import("./pages/Projects"));
const Photos = lazy(() => import("./pages/Photos"));
const Travels = lazy(() => import("./pages/Travels"));
const Admin = lazy(() => import("./pages/Admin"));
const TripFormPage = lazy(() => import("./pages/TripFormPage"));
const Contact = lazy(() => import("./pages/Contact"));
const Changelog = lazy(() => import("./pages/Changelog"));

function App() {
  return (
    <Layout>
      <Suspense fallback={<div className="loading-page">Loading&hellip;</div>}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/cv" element={<CV />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/photos" element={<Photos />} />
          <Route path="/photos/:tripId" element={<Photos />} />
          <Route path="/travels" element={<Travels />} />
          <Route path="/travels/:tab" element={<Travels />} />
          <Route path="/admin/trips/new" element={<TripFormPage />} />
          <Route path="/admin/trips/:tripId/edit" element={<TripFormPage />} />
          <Route path="/admin/trips/:tripId/info" element={<TripFormPage />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/admin/:tab" element={<Admin />} />
          <Route path="/admin/:tab/:year" element={<Admin />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/changelog" element={<Changelog />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}

export default App;
