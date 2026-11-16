import { Link, Route, Routes } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Search from "./pages/Search.jsx";
import ImageDetail from "./pages/ImageDetail.jsx";
import ApodDetail from "./pages/ApodDetail.jsx";

export default function App() {
  return (
    <>
      <header className="site-header">
        <Link to="/" className="logo">
          Space<span>Hub</span>
        </Link>
      </header>
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/search" element={<Search />} />
          <Route path="/image/:nasaId" element={<ImageDetail />} />
          <Route path="/apod/:date" element={<ApodDetail />} />
          <Route path="*" element={<p className="message">Pagina nu există.</p>} />
        </Routes>
      </main>
      <footer className="site-footer">Imagini și date oferite de NASA.</footer>
    </>
  );
}
