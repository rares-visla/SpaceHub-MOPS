// Toate cererile merg catre backend-ul nostru (/api), niciodata direct la NASA.

async function getJson(path) {
  let response;
  try {
    response = await fetch(path);
  } catch {
    throw new Error("Serverul nu poate fi contactat.");
  }
  let body = null;
  try {
    body = await response.json();
  } catch {
    /* raspuns fara JSON */
  }
  if (!response.ok) {
    const error = new Error(body?.detail || "A apărut o eroare.");
    error.status = response.status;
    throw error;
  }
  return body;
}

export function fetchApod(date) {
  return getJson(date ? `/api/apod/?date=${encodeURIComponent(date)}` : "/api/apod/");
}

export function searchImages({ q, yearStart, yearEnd, page = 1 }) {
  const params = new URLSearchParams({ q, page: String(page) });
  if (yearStart) params.set("year_start", yearStart);
  if (yearEnd) params.set("year_end", yearEnd);
  return getJson(`/api/images/search/?${params}`);
}

export function fetchImage(nasaId) {
  return getJson(`/api/images/${encodeURIComponent(nasaId)}/`);
}

export function imageDownloadUrl(nasaId) {
  return `/api/images/${encodeURIComponent(nasaId)}/download/`;
}

export function apodDownloadUrl(date) {
  return `/api/apod/download/?date=${encodeURIComponent(date)}`;
}
