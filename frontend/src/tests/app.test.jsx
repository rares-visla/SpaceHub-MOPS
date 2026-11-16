import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { APOD, IMAGE, mockApi, renderApp, searchResponse } from "./helpers.jsx";

const location = () => screen.getByTestId("location").textContent;

describe("US01 - APOD pe pagina principală", () => {
  it("încarcă automat imaginea, titlul și descrierea", async () => {
    mockApi({ "/api/apod/": APOD });
    renderApp("/");

    expect(await screen.findByRole("heading", { name: "Nebuloasa Orion" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Nebuloasa Orion" })).toHaveAttribute("src", APOD.image_url);
    expect(screen.getByText("O regiune de formare stelară.")).toBeInTheDocument();
  });

  it("afișează un mesaj dacă APOD nu poate fi încărcat", async () => {
    mockApi({ "/api/apod/": { status: 502, body: { detail: "NASA a raspuns cu status 500." } } });
    renderApp("/");

    expect(await screen.findByRole("alert")).toHaveTextContent("nu a putut fi încărcată");
  });
});

describe("US02 - Căutare imagini", () => {
  it("trimite cuvântul cheie și afișează rezultatele în grid", async () => {
    const fetchMock = mockApi({
      "/api/apod/": APOD,
      "/api/images/search/": searchResponse([IMAGE, { ...IMAGE, nasa_id: "PIA2", title: "Olympus Mons" }]),
    });
    renderApp("/");

    await userEvent.type(screen.getByLabelText("Cuvânt cheie"), "Mars");
    await userEvent.click(screen.getByRole("button", { name: "Caută" }));

    expect(await screen.findByText("Olympus Mons")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(location()).toBe("/search?q=Mars");
    expect(fetchMock.mock.calls.at(-1)[0]).toContain("q=Mars");
  });

  it('afișează „Niciun rezultat” când API-ul nu returnează nimic', async () => {
    mockApi({ "/api/images/search/": searchResponse([]) });
    renderApp("/search?q=zzzz");

    expect(await screen.findByText("Niciun rezultat")).toBeInTheDocument();
  });

  it("nu caută fără cuvânt cheie", async () => {
    const fetchMock = mockApi({ "/api/apod/": APOD });
    renderApp("/");
    await screen.findByRole("heading", { name: "Nebuloasa Orion" });

    await userEvent.click(screen.getByRole("button", { name: "Caută" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Introdu un cuvânt cheie");
    expect(location()).toBe("/");
    expect(fetchMock).toHaveBeenCalledTimes(1); // doar APOD
  });

  it("trece la pagina următoare", async () => {
    const fetchMock = mockApi({ "/api/images/search/": searchResponse([IMAGE], { has_next: true }) });
    renderApp("/search?q=Mars");

    await userEvent.click(await screen.findByRole("button", { name: "Înainte" }));

    await waitFor(() => expect(fetchMock.mock.calls.at(-1)[0]).toContain("page=2"));
    expect(screen.getByRole("button", { name: "Înapoi" })).toBeEnabled();
  });
});

describe("US10 - Filtrare după an", () => {
  it("trimite anul de început și de sfârșit către API", async () => {
    const fetchMock = mockApi({ "/api/images/search/": searchResponse([IMAGE]) });
    renderApp("/search?q=Mars");
    await screen.findByText("Mars la apus");

    await userEvent.type(screen.getByLabelText("An de început"), "2010");
    await userEvent.type(screen.getByLabelText("An de sfârșit"), "2015");
    await userEvent.click(screen.getByRole("button", { name: "Caută" }));

    await waitFor(() => expect(location()).toBe("/search?q=Mars&year_start=2010&year_end=2015"));
    const lastUrl = fetchMock.mock.calls.at(-1)[0];
    expect(lastUrl).toContain("year_start=2010");
    expect(lastUrl).toContain("year_end=2015");
  });

  it("respinge intervalul inversat fără să apeleze API-ul", async () => {
    const fetchMock = mockApi({ "/api/images/search/": searchResponse([IMAGE]) });
    renderApp("/search?q=Mars");
    await screen.findByText("Mars la apus");

    await userEvent.type(screen.getByLabelText("An de început"), "2020");
    await userEvent.type(screen.getByLabelText("An de sfârșit"), "2010");
    await userEvent.click(screen.getByRole("button", { name: "Caută" }));

    expect(screen.getByRole("alert")).toHaveTextContent("nu poate fi după");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("păstrează filtrele din URL în câmpuri", async () => {
    mockApi({ "/api/images/search/": searchResponse([IMAGE]) });
    renderApp("/search?q=Mars&year_start=2010&year_end=2015");

    expect(screen.getByLabelText("An de început")).toHaveValue(2010);
    expect(screen.getByLabelText("An de sfârșit")).toHaveValue(2015);
    expect(await screen.findByText(/2010–2015/)).toBeInTheDocument();
  });
});

describe("US03 - Detalii imagine", () => {
  it("click pe o imagine din grid deschide pagina dedicată", async () => {
    mockApi({ "/api/images/search/": searchResponse([IMAGE]), "/api/images/PIA00001/": IMAGE });
    renderApp("/search?q=Mars");

    await userEvent.click(await screen.findByRole("link", { name: /Mars la apus/ }));

    expect(await screen.findByRole("heading", { name: "Mars la apus" })).toBeInTheDocument();
    expect(location()).toBe("/image/PIA00001");
  });

  it("afișează imaginea mare, data, fotograful/instrumentul și descrierea", async () => {
    mockApi({ "/api/images/PIA00001/": IMAGE });
    renderApp("/image/PIA00001");

    expect(await screen.findByRole("img", { name: "Mars la apus" })).toHaveAttribute("src", IMAGE.image_url);
    expect(screen.getByText("4 martie 2015")).toBeInTheDocument();
    expect(screen.getByText("Bill Ingalls")).toBeInTheDocument();
    expect(screen.getByText("Curiosity Mastcam")).toBeInTheDocument();
    expect(screen.getByText("Descriere completă a imaginii.")).toBeInTheDocument();
  });

  it("click pe APOD deschide pagina lui de detalii", async () => {
    mockApi({ "/api/apod/": APOD });
    renderApp("/");

    await userEvent.click(await screen.findByRole("link", { name: "Nebuloasa Orion" }));

    expect(location()).toBe("/apod/2026-11-15");
    expect(await screen.findByText("Jane Doe")).toBeInTheDocument();
  });

  it("afișează un mesaj pentru o imagine inexistentă", async () => {
    mockApi({ "/api/images/": { status: 404, body: { detail: "Imaginea nu a fost gasita." } } });
    renderApp("/image/NU-EXISTA");

    expect(await screen.findByRole("alert")).toHaveTextContent("Imaginea nu a fost găsită.");
  });
});

describe("US15 - Copy Link", () => {
  it("copiază URL-ul curent în clipboard și confirmă", async () => {
    mockApi({ "/api/images/PIA00001/": IMAGE });
    const user = userEvent.setup();
    const writeText = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue();
    renderApp("/image/PIA00001");

    await user.click(await screen.findByRole("button", { name: "Copy Link" }));

    expect(writeText).toHaveBeenCalledWith(window.location.href);
    expect(await screen.findByRole("button", { name: "Link copiat!" })).toBeInTheDocument();
  });

  it("anunță utilizatorul dacă nu se poate copia", async () => {
    mockApi({ "/api/images/PIA00001/": IMAGE });
    const user = userEvent.setup();
    vi.spyOn(navigator.clipboard, "writeText").mockRejectedValue(new Error("refuzat"));
    renderApp("/image/PIA00001");

    await user.click(await screen.findByRole("button", { name: "Copy Link" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Nu am putut copia");
  });

  it("pagina de detalii se deschide direct din link, fără cont", async () => {
    const fetchMock = mockApi({ "/api/images/PIA00001/": IMAGE });
    renderApp("/image/PIA00001");

    expect(await screen.findByRole("heading", { name: "Mars la apus" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/images/PIA00001/");
  });
});

describe("US16 - Descărcare imagine", () => {
  it('butonul „Download image” duce la endpoint-ul de descărcare', async () => {
    mockApi({ "/api/images/PIA00001/": IMAGE });
    renderApp("/image/PIA00001");

    const link = await screen.findByRole("link", { name: "Download image" });

    expect(link).toHaveAttribute("href", "/api/images/PIA00001/download/");
    expect(link).toHaveAttribute("download");
  });

  it("APOD are buton de descărcare pentru data respectivă", async () => {
    mockApi({ "/api/apod/": APOD });
    renderApp("/apod/2026-11-15");

    expect(await screen.findByRole("link", { name: "Download image" })).toHaveAttribute(
      "href",
      "/api/apod/download/?date=2026-11-15"
    );
  });

  it("nu oferă descărcare când APOD este video", async () => {
    mockApi({
      "/api/apod/": { ...APOD, media_type: "video", video_url: "https://www.youtube.com/embed/abc" },
    });
    renderApp("/apod/2026-11-15");

    expect(await screen.findByRole("link", { name: "Deschide video" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Download image" })).not.toBeInTheDocument();
  });
});
