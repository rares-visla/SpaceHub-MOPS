import { useParams } from "react-router-dom";
import { apodDownloadUrl, fetchApod } from "../api.js";
import DetailView from "../components/DetailView.jsx";
import { formatDate } from "../format.js";
import useFetch from "../useFetch.js";

/** /apod/:date - pagina de detalii pentru Imaginea Zilei (US03 pornind din US01). */
export default function ApodDetail() {
  const { date } = useParams();
  const { data: apod, error, loading } = useFetch(() => fetchApod(date), [date]);

  if (loading) return <p className="message">Se încarcă…</p>;
  if (error) {
    return (
      <p className="message" role="alert">
        {error.message}
      </p>
    );
  }

  const isImage = apod.media_type === "image";
  return (
    <DetailView
      title={apod.title}
      imageUrl={apod.hd_image_url}
      description={apod.explanation}
      downloadUrl={isImage ? apodDownloadUrl(apod.date) : null}
      facts={[
        ["Data", formatDate(apod.date)],
        ["Autor", apod.copyright],
        ["Sursă", "NASA Astronomy Picture of the Day"],
      ]}
    >
      {apod.video_url && (
        <a className="btn" href={apod.video_url} target="_blank" rel="noreferrer">
          Deschide video
        </a>
      )}
    </DetailView>
  );
}
