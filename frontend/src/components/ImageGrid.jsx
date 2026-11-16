import { Link } from "react-router-dom";

/** Rezultatele cautarii sub forma de grid (US02). Click pe imagine => detalii (US03). */
export default function ImageGrid({ images }) {
  return (
    <ul className="grid">
      {images.map((image) => (
        <li key={image.nasa_id}>
          <Link to={`/image/${encodeURIComponent(image.nasa_id)}`} className="card">
            {image.thumbnail_url ? (
              <img src={image.thumbnail_url} alt={image.title} loading="lazy" />
            ) : (
              <div className="card-placeholder" aria-hidden="true" />
            )}
            <span className="card-title">{image.title}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
