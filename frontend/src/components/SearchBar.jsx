import { useState } from "react";
import { useNavigate } from "react-router-dom";

const MIN_YEAR = 1900;
const CURRENT_YEAR = new Date().getFullYear();

export function validateSearch({ q, yearStart, yearEnd }) {
  if (!q.trim()) return "Introdu un cuvânt cheie.";
  for (const year of [yearStart, yearEnd]) {
    if (year === "") continue;
    const n = Number(year);
    if (!/^\d{4}$/.test(year) || n < MIN_YEAR || n > CURRENT_YEAR) {
      return `Anul trebuie să fie între ${MIN_YEAR} și ${CURRENT_YEAR}.`;
    }
  }
  if (yearStart && yearEnd && Number(yearStart) > Number(yearEnd)) {
    return "Anul de început nu poate fi după anul de sfârșit.";
  }
  return null;
}

/** Bara de cautare (US02) cu filtrele de an langa ea (US10). */
export default function SearchBar({ initial = {} }) {
  const navigate = useNavigate();
  const [q, setQ] = useState(initial.q || "");
  const [yearStart, setYearStart] = useState(initial.yearStart || "");
  const [yearEnd, setYearEnd] = useState(initial.yearEnd || "");
  const [error, setError] = useState(null);

  function handleSubmit(event) {
    event.preventDefault();
    const problem = validateSearch({ q, yearStart, yearEnd });
    setError(problem);
    if (problem) return;

    const params = new URLSearchParams({ q: q.trim() });
    if (yearStart) params.set("year_start", yearStart);
    if (yearEnd) params.set("year_end", yearEnd);
    navigate(`/search?${params}`);
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit} role="search" noValidate>
      <input
        type="search"
        className="search-input"
        placeholder='Caută imagini, de ex. "Jupiter"'
        aria-label="Cuvânt cheie"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <input
        type="number"
        className="year-input"
        placeholder="An început"
        aria-label="An de început"
        min={MIN_YEAR}
        max={CURRENT_YEAR}
        value={yearStart}
        onChange={(e) => setYearStart(e.target.value)}
      />
      <input
        type="number"
        className="year-input"
        placeholder="An sfârșit"
        aria-label="An de sfârșit"
        min={MIN_YEAR}
        max={CURRENT_YEAR}
        value={yearEnd}
        onChange={(e) => setYearEnd(e.target.value)}
      />
      <button type="submit" className="btn btn-primary">
        Caută
      </button>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
