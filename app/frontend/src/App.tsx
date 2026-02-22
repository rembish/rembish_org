import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import ErrorPage from "./components/ErrorPage";
import Layout from "./components/Layout";
import { ViewAsProvider } from "./hooks/useViewAs";
import Home from "./pages/Home";

const CV = lazy(() => import("./pages/CV"));
const Projects = lazy(() => import("./pages/Projects"));
const Photos = lazy(() => import("./pages/Photos"));
const Travels = lazy(() => import("./pages/Travels"));
const Admin = lazy(() => import("./pages/Admin"));
const TripFormPage = lazy(() => import("./pages/TripFormPage"));
const EventFormPage = lazy(() => import("./pages/EventFormPage"));
const Contact = lazy(() => import("./pages/Contact"));
const Changelog = lazy(() => import("./pages/Changelog"));

function App() {
  return (
    <ErrorBoundary>
      <ViewAsProvider>
        <Layout>
          <Suspense
            fallback={<div className="loading-page">Loading&hellip;</div>}
          >
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/cv" element={<CV />} />
              <Route path="/projects" element={<Projects />} />
              <Route
                path="/photos"
                element={<Navigate to="/photos/albums" replace />}
              />
              <Route path="/photos/albums" element={<Photos />} />
              <Route path="/photos/albums/:param" element={<Photos />} />
              <Route path="/photos/map" element={<Photos />} />
              <Route path="/photos/map/:countryId" element={<Photos />} />
              <Route path="/travels" element={<Travels />} />
              <Route path="/travels/:tab" element={<Travels />} />
              <Route path="/admin/events/new" element={<EventFormPage />} />
              <Route
                path="/admin/events/:eventId/edit"
                element={<EventFormPage />}
              />
              <Route path="/admin/trips/new" element={<TripFormPage />} />
              <Route
                path="/admin/trips/:tripId/edit"
                element={<TripFormPage />}
              />
              <Route
                path="/admin/trips/:tripId/info"
                element={<TripFormPage />}
              />
              <Route
                path="/admin/trips/:tripId/transport"
                element={<TripFormPage />}
              />
              <Route
                path="/admin/trips/:tripId/stays"
                element={<TripFormPage />}
              />
              <Route path="/admin" element={<Admin />} />
              <Route path="/admin/:tab" element={<Admin />} />
              <Route path="/admin/:tab/:year" element={<Admin />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="/changelog" element={<Changelog />} />
              <Route path="*" element={<ErrorPage />} />
            </Routes>
          </Suspense>
        </Layout>
      </ViewAsProvider>
    </ErrorBoundary>
  );
}

export default App;
