import { useParams } from "react-router-dom";
import { fetchImage, imageDownloadUrl } from "../api.js";
import DetailView from "../components/DetailView.jsx";
import { formatDate } from "../format.js";
import useFetch from "../useFetch.js";

/** /image/:nasaId - URL unic, public, care poate fi trimis altora (US03, US15). */
export default function ImageDetail() {
  const { nasaId } = useParams();
  const { data: image, error, loading } = useFetch(() => fetchImage(nasaId), [nasaId]);

  if (loading) return <p className="message">Se încarcă…</p>;
  if (error) {
    return (
      <p className="message" role="alert">
        {error.status === 404 ? "Imaginea nu a fost găsită." : error.message}
      </p>
    );
  }

  return (
    <DetailView
      title={image.title}
      imageUrl={image.image_url}
      description={image.description}
      downloadUrl={image.download_url ? imageDownloadUrl(image.nasa_id) : null}
      facts={[
        ["Data capturii", formatDate(image.date_created)],
        ["Fotograf", image.photographer],
        ["Instrument / sursă", image.secondary_creator],
        ["Centru NASA", image.center],
        ["ID NASA", image.nasa_id],
      ]}
    />
  );
}
