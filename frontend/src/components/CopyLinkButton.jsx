import { useEffect, useState } from "react";

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  // Rezerva pentru pagini servite fara https, unde Clipboard API lipseste.
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  const ok = document.execCommand("copy");
  document.body.removeChild(area);
  if (!ok) throw new Error("copy failed");
}

/** US15 - copiaza URL-ul paginii curente in clipboard. */
export default function CopyLinkButton() {
  const [state, setState] = useState("idle"); // idle | copied | failed

  useEffect(() => {
    if (state === "idle") return undefined;
    const timer = setTimeout(() => setState("idle"), 2500);
    return () => clearTimeout(timer);
  }, [state]);

  async function handleClick() {
    try {
      await copyText(window.location.href);
      setState("copied");
    } catch {
      setState("failed");
    }
  }

  return (
    <>
      <button type="button" className="btn" onClick={handleClick}>
        {state === "copied" ? "Link copiat!" : "Copy Link"}
      </button>
      {state === "failed" && (
        <span className="form-error" role="alert">
          Nu am putut copia. Copiază adresa din bara browserului.
        </span>
      )}
    </>
  );
}
