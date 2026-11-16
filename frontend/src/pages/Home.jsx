import { Link } from "react-router-dom";
import { fetchApod } from "../api.js";
import { formatDate, shorten } from "../format.js";
import SearchBar from "../components/SearchBar.jsx";
import useFetch from "../useFetch.js";

/** Pagina principala: APOD se incarca automat (US01) + bara de cautare (US02). */
export default function Home() {
  const { data: apod, error, loading } = useFetch(() => fetchApod(), []);

  return (
    <>
      <SearchBar />

      <section className="apod" aria-labelledby="apod-heading">
        <p className="eyebrow" id="apod-heading">
          Imaginea Astronomică a Zilei
        </p>
        {loading && <p className="message">Se încarcă…</p>}
        {error && (
          <p className="message" role="alert">
            Imaginea zilei nu a putut fi încărcată. {error.message}
          </p>
        )}
        {apod && (
          <>
            <Link to={`/apod/${apod.date}`} className="apod-link">
              {apod.image_url ? (
                <img className="apod-image" src={apod.image_url} alt={apod.title} />
              ) : (
                <span className="message">Azi APOD este un video. Vezi detalii.</span>
              )}
            </Link>
            <h1>{apod.title}</h1>
            <p className="muted">{formatDate(apod.date)}</p>
            <p className="description">{shorten(apod.explanation)}</p>
            <Link to={`/apod/${apod.date}`}>Citește descrierea completă</Link>
          </>
        )}
      </section>
    </>
  );
}
