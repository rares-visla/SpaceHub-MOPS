import { useSearchParams } from "react-router-dom";
import { searchImages } from "../api.js";
import ImageGrid from "../components/ImageGrid.jsx";
import SearchBar from "../components/SearchBar.jsx";
import useFetch from "../useFetch.js";

/** Rezultatele cautarii (US02), cu filtre de an (US10). Starea sta in URL. */
export default function Search() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const yearStart = params.get("year_start") || "";
  const yearEnd = params.get("year_end") || "";
  const page = Math.max(1, Number(params.get("page")) || 1);

  const { data, error, loading } = useFetch(
    () =>
      q
        ? searchImages({ q, yearStart, yearEnd, page })
        : Promise.resolve({ results: [], total: 0, has_next: false }),
    [q, yearStart, yearEnd, page]
  );

  function goToPage(next) {
    const updated = new URLSearchParams(params);
    updated.set("page", String(next));
    setParams(updated);
    window.scrollTo?.(0, 0);
  }

  const period =
    yearStart || yearEnd ? ` (${yearStart || "…"}–${yearEnd || "…"})` : "";

  return (
    <>
      <SearchBar key={params.toString()} initial={{ q, yearStart, yearEnd }} />

      {loading && <p className="message">Se caută…</p>}
      {error && (
        <p className="message" role="alert">
          {error.message}
        </p>
      )}

      {data && data.results.length === 0 && <p className="message">Niciun rezultat</p>}

      {data && data.results.length > 0 && (
        <>
          <p className="muted">
            {data.total} rezultate pentru „{q}”{period}
          </p>
          <ImageGrid images={data.results} />
          <nav className="pagination" aria-label="Paginare">
            <button className="btn" disabled={page <= 1} onClick={() => goToPage(page - 1)}>
              Înapoi
            </button>
            <span>Pagina {page}</span>
            <button className="btn" disabled={!data.has_next} onClick={() => goToPage(page + 1)}>
              Înainte
            </button>
          </nav>
        </>
      )}
    </>
  );
}
