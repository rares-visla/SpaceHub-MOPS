import CopyLinkButton from "./CopyLinkButton.jsx";

/**
 * Pagina dedicata unei imagini (US03): imagine la rezolutie mare, data,
 * autor/instrument, descriere completa, plus Copy Link (US15) si Download (US16).
 */
export default function DetailView({ title, imageUrl, facts, description, downloadUrl, children }) {
  return (
    <article className="detail">
      <h1>{title}</h1>
      {imageUrl ? (
        <a href={imageUrl} target="_blank" rel="noreferrer">
          <img className="detail-image" src={imageUrl} alt={title} />
        </a>
      ) : (
        <p className="message">Imaginea nu este disponibilă.</p>
      )}

      <div className="actions">
        <CopyLinkButton />
        {downloadUrl && (
          <a className="btn btn-primary" href={downloadUrl} download>
            Download image
          </a>
        )}
        {children}
      </div>

      <dl className="facts">
        {facts
          .filter(([, value]) => value)
          .map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
      </dl>

      <p className="description">{description || "Fără descriere."}</p>
    </article>
  );
}
