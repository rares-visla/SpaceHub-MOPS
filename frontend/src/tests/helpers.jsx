import { render } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { vi } from "vitest";
import App from "../App.jsx";

function LocationProbe() {
  const location = useLocation();
  return <output data-testid="location">{location.pathname + location.search}</output>;
}

/** Porneste aplicatia la o anumita adresa, fara browser real. */
export function renderApp(route = "/") {
  return render(
    <MemoryRouter
      initialEntries={[route]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
      <LocationProbe />
    </MemoryRouter>
  );
}

/** Simuleaza backend-ul: `routes` = { "fragment din URL": raspuns JSON | {status, body} }. */
export function mockApi(routes) {
  const fetchMock = vi.fn(async (url) => {
    const key = Object.keys(routes).find((fragment) => String(url).includes(fragment));
    if (!key) throw new Error(`Cerere neasteptata: ${url}`);
    const entry = routes[key];
    const status = entry?.status ?? 200;
    const body = entry?.status ? entry.body : entry;
    return { ok: status < 400, status, json: async () => body };
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export const APOD = {
  date: "2026-11-15",
  title: "Nebuloasa Orion",
  explanation: "O regiune de formare stelară.",
  media_type: "image",
  image_url: "https://apod.nasa.gov/apod/image/orion_1024.jpg",
  hd_image_url: "https://apod.nasa.gov/apod/image/orion_4096.jpg",
  video_url: null,
  copyright: "Jane Doe",
};

export const IMAGE = {
  nasa_id: "PIA00001",
  title: "Mars la apus",
  description: "Descriere completă a imaginii.",
  date_created: "2015-03-04T00:00:00Z",
  photographer: "Bill Ingalls",
  secondary_creator: "Curiosity Mastcam",
  center: "JPL",
  keywords: ["Mars"],
  thumbnail_url: "https://images-assets.nasa.gov/image/PIA00001/PIA00001~thumb.jpg",
  image_url: "https://images-assets.nasa.gov/image/PIA00001/PIA00001~large.jpg",
  download_url: "https://images-assets.nasa.gov/image/PIA00001/PIA00001~orig.jpg",
};

export function searchResponse(results, extra = {}) {
  return { results, total: results.length, page: 1, page_size: 24, has_next: false, ...extra };
}
