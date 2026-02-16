import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import CV from "./pages/CV";
import Projects from "./pages/Projects";
import Photos from "./pages/Photos";
import Travels from "./pages/Travels";
import Admin from "./pages/Admin";
import TripFormPage from "./pages/TripFormPage";
import Contact from "./pages/Contact";
import Changelog from "./pages/Changelog";

function App() {
  return (
    <Layout>
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
        <Route path="/admin" element={<Admin />} />
        <Route path="/admin/:tab" element={<Admin />} />
        <Route path="/admin/:tab/:year" element={<Admin />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/changelog" element={<Changelog />} />
      </Routes>
    </Layout>
  );
}

export default App;
