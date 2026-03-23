import { useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000/process";
const EXAMPLE_URL = "https://samplelib.com/lib/preview/mp4/sample-5s.mp4";

const operationOptions = [
  { value: "thumbnail", label: "Thumbnail" },
  { value: "compress", label: "Compress" },
  { value: "extract_audio", label: "Extract Audio" },
];

const operationLabels = {
  thumbnail: "Thumbnail",
  compress: "Compress",
  extract_audio: "Extract Audio",
};

const getSuccessMessage = (operation) => {
  switch (operation) {
    case "thumbnail":
      return "✅ Your thumbnail is ready! You can preview or download it below.";
    case "compress":
      return "✅ Your compressed video is ready! You can preview or download it below.";
    case "extract_audio":
      return "✅ Your audio file is ready! You can preview or download it below.";
    default:
      return "✅ Your media is ready!";
  }
};

const getBadgeClass = (operation) => {
  switch (operation) {
    case "thumbnail":
      return "badge badge-thumbnail";
    case "compress":
      return "badge badge-compress";
    case "extract_audio":
      return "badge badge-audio";
    default:
      return "badge";
  }
};

const getBadgeLabel = (operation) => {
  if (operation === "extract_audio") {
    return "Audio";
  }

  return operation.charAt(0).toUpperCase() + operation.slice(1);
};

function App() {
  const [url, setUrl] = useState("");
  const [operation, setOperation] = useState("thumbnail");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const validateUrl = (value) => {
    const trimmedValue = value.trim();

    if (!trimmedValue) {
      return "Please enter a media URL before submitting.";
    }

    try {
      const parsedUrl = new URL(trimmedValue);
      if (!["http:", "https:"].includes(parsedUrl.protocol)) {
        return "Please enter a valid HTTP or HTTPS media URL.";
      }
    } catch {
      return "That URL does not look valid. Please check it and try again.";
    }

    return "";
  };

  const resetState = () => {
    setUrl("");
    setOperation("thumbnail");
    setResult(null);
    setError("");
    setSuccessMessage("");
    setLoading(false);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const validationError = validateUrl(url);
    if (validationError) {
      setError(validationError);
      setSuccessMessage("");
      setResult(null);
      return;
    }

    setLoading(true);
    setError("");
    setSuccessMessage("");
    setResult(null);

    try {
      const response = await fetch(API_BASE_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: url.trim(),
          operation,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Processing failed. Please try again.");
      }

      setResult(data);
      setSuccessMessage(getSuccessMessage(data.operation));
    } catch (requestError) {
      setError(requestError.message || "Something went wrong while processing your media.");
    } finally {
      setLoading(false);
    }
  };

  const renderPreview = () => {
    if (!result) {
      return null;
    }

    if (result.operation === "thumbnail") {
      return <img className="media-preview image-preview" src={result.output} alt="Generated thumbnail preview" />;
    }

    if (result.operation === "compress") {
      return <video className="media-preview video-preview" src={result.output} controls />;
    }

    return <audio className="audio-preview" src={result.output} controls />;
  };

  return (
    <div className="page-shell">
      <main className="app-card">
        <section className="hero-section">
          <h1 className="hero-title">
            <span className="hero-title-icon" aria-hidden="true">
              ▶
            </span>
            <span className="hero-title-text">Media Processing App</span>
          </h1>
          <p className="hero-subtitle">
            Process video links into thumbnails, compressed clips, or extracted audio in one place.
          </p>
        </section>

        <form className="media-form" onSubmit={handleSubmit}>
          <div className="field-group">
            <label htmlFor="media-url" className="field-label">
              Public Video URL
            </label>
            <input
              id="media-url"
              className="text-input"
              type="url"
              placeholder="https://example.com/video.mp4"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
            />
            <p className="helper-text">Example: {EXAMPLE_URL}</p>
          </div>

          <div className="field-group">
            <label htmlFor="operation" className="field-label">
              Choose Operation
            </label>
            <select
              id="operation"
              className="select-input"
              value={operation}
              onChange={(event) => setOperation(event.target.value)}
            >
              {operationOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="button-row">
            <button className="primary" type="submit" disabled={loading}>
              {loading ? "Processing..." : "Generate Output"}
            </button>

            <button className="secondary-button" type="button" onClick={resetState} disabled={loading}>
              Reset
            </button>
          </div>
        </form>

        {error && (
          <div className="message-box error-box" role="alert">
            <strong>Error:</strong> {error}
          </div>
        )}

        {successMessage && <div className="success">{successMessage}</div>}

        {result && (
          <section className="result-card">
            <div className="result-header">
              <div>
                <p className="result-label">Processed Output</p>
                <h2>Your media is ready</h2>
              </div>
              <span className={getBadgeClass(result.operation)}>{getBadgeLabel(result.operation)}</span>
            </div>

            <div className="preview-panel">{renderPreview()}</div>

            <div className="result-actions">
              <a className="result-button" href={result.output} target="_blank" rel="noreferrer">
                Open Output
              </a>
              <a className="result-button secondary-link" href={result.output} download>
                Download Output
              </a>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
