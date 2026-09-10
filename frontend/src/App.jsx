import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const features = [
  {
    name: "Check My Area",
    icon: "🏠",
    description: "Investigate a location before making a decision.",
  },
  {
    name: "Flood Risk",
    icon: "🌊",
    description: "Look for visible water and flood indicators.",
  },
  {
    name: "Construction",
    icon: "🏗️",
    description: "Check visible development and construction.",
  },
  {
    name: "What Changed?",
    icon: "🔍",
    description: "Compare imagery and discover visible changes.",
  },
  {
    name: "Environment",
    icon: "🌳",
    description: "Explore greenery, vegetation and open land.",
  },
  {
    name: "Agriculture",
    icon: "🌾",
    description: "Analyze visible agricultural areas.",
  },
  {
    name: "Disaster",
    icon: "🚨",
    description: "Look for visible disaster-related indicators.",
  },
];

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [image, setImage] = useState(null);
  const [selectedFeature, setSelectedFeature] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [location, setLocation] = useState(null);
  const [locationText, setLocationText] = useState("");

  // Gemini/VLM and YOLO use separate result states.
  const [vlmResult, setVlmResult] = useState("");
  const [detectionResult, setDetectionResult] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const selectFeature = (feature) => {
    setSelectedFeature(feature);
    setImage(null);
    setAnswer("");
    setVlmResult("");
    setDetectionResult(null);

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);

    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: "smooth",
    });
  };

  const handleImageChange = (file) => {
    if (!file) return;

    if (previewUrl) URL.revokeObjectURL(previewUrl);

    setImage(file);
    setAnswer("");
    setVlmResult("");
    setDetectionResult(null);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const startVoice = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Voice input is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.continuous = false;

    setListening(true);
    recognition.start();

    recognition.onresult = (event) => {
      setQuestion(event.results[0][0].transcript);
      setListening(false);
    };

    recognition.onerror = () => {
      setListening(false);
      alert("Could not understand your voice. Please try again.");
    };

    recognition.onend = () => setListening(false);
  };

  // ============================================================
  // GEMINI / VLM - TEXT ONLY
  // ============================================================

  const askImageQuestion = async () => {
    if (!image) {
      alert("Please select a satellite image first.");
      return;
    }

    if (!question.trim()) {
      alert("Please enter a question about the image.");
      return;
    }

    setLoading(true);
    setAnswer("");
    setVlmResult("");
    setDetectionResult(null);

    const formData = new FormData();
    formData.append("image", image);
    formData.append("query", question);

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setVlmResult(data.detail || "Image analysis failed.");
        return;
      }

      // Gemini/VLM is always displayed as normal text.
      setVlmResult(
        data.analysis || "SatQuery AI could not generate an analysis."
      );

      // Never populate the YOLO result state here.
      setDetectionResult(null);
    } catch (error) {
      console.error("VLM error:", error);
      setVlmResult(
        "Cannot connect to SatQuery AI. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // FEATURE ANALYSIS
  // ============================================================

  const analyzeImage = async () => {
    if (!image) {
      alert("Please select an image first.");
      return;
    }

    const endpoints = {
      "Check My Area": "/api/property-risk",
      "Flood Risk": "/api/flood-risk",
      Construction: "/api/construction-check",
      Environment: "/api/environment",
      Agriculture: "/api/agriculture",
      Disaster: "/api/disaster",
    };

    const endpoint = endpoints[selectedFeature];

    if (!endpoint) {
      alert("This feature requires additional image processing.");
      return;
    }

    setLoading(true);
    setAnswer("");
    setVlmResult("");
    setDetectionResult(null);

    const formData = new FormData();
    formData.append("image", image);

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setVlmResult(data.analysis || "Analysis completed.");
      } else {
        setVlmResult(data.detail || "Analysis failed.");
      }
    } catch (error) {
      console.error("Feature analysis error:", error);
      setVlmResult(
        "Cannot connect to SatQuery AI. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // YOLO OBJECT DETECTION
  // ============================================================

  const runDetection = async () => {
    if (!image) {
      alert("Please select a satellite image first.");
      return;
    }

    setLoading(true);
    setAnswer("");
    setVlmResult("");
    setDetectionResult(null);

    const query =
      question.trim() ||
      "Detect buildings, roads, vehicles and other visible objects.";

    const formData = new FormData();
    formData.append("image", image);
    formData.append("query", query);

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setAnswer(data.detail || "Object detection failed.");
        return;
      }

      // Only create YOLO state when actual YOLO data is returned.
      if (
        data.route === "detection" &&
        data.annotated_image &&
        Array.isArray(data.detections)
      ) {
        setDetectionResult(data);
        setAnswer(data.analysis || "Objects detected successfully.");
        setVlmResult("");
      } else {
        // Never show an empty YOLO dashboard for VLM output.
        setDetectionResult(null);
        setVlmResult(data.analysis || "The image was analyzed.");
      }
    } catch (error) {
      console.error("Detection error:", error);
      setAnswer(
        "Cannot connect to SatQuery AI. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // LOCATION
  // ============================================================

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      alert("Location is not supported by this browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        setLocation({ latitude, longitude });
        setLocationText("Location detected successfully.");

        try {
          await fetch(`${API_URL}/api/location`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ latitude, longitude }),
          });
        } catch (error) {
          console.log("Location backend connection failed.");
        }
      },
      () => {
        alert(
          "Unable to get your location. Please allow location access and try again."
        );
      }
    );
  };

  // ============================================================
  // DETECTION STATISTICS
  // ============================================================

  const detectionEntries = detectionResult
    ? Object.entries(detectionResult.counts || {}).sort(
      ([, a], [, b]) => b - a
    )
    : [];

  const totalDetections = detectionEntries.reduce(
    (total, [, count]) => total + count,
    0
  );

  const vehicleClasses = [
    "Small Car",
    "Passenger Car",
    "Truck",
    "Cargo Truck",
    "Truck w/Box",
    "Bus",
  ];

  const vehicleCount = vehicleClasses.reduce(
    (total, className) =>
      total + (detectionResult?.counts?.[className] || 0),
    0
  );

  const averageConfidence =
    detectionResult?.detections?.length > 0
      ? Math.round(
        (detectionResult.detections.reduce(
          (sum, item) => sum + item.confidence,
          0
        ) /
          detectionResult.detections.length) *
        100
      )
      : 0;

  // ============================================================
  // FORMAT GEMINI ANSWER
  // ============================================================

  const formatAnswer = (text) => {
    if (!text) return null;

    const lines = text
      .replace(/\*\*/g, "")
      .replace(/^#+\s*/gm, "")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    return lines.map((line, index) => {
      const lower = line.toLowerCase();

      if (
        lower.includes("detailed observations") ||
        lower.includes("key observations") ||
        lower.includes("visible observations") ||
        lower.includes("overall assessment") ||
        lower.includes("recommendation")
      ) {
        return (
          <h3 key={index} className="answer-heading">
            {line.replace(/:$/, "")}
          </h3>
        );
      }

      if (/^[-*•]\s*/.test(line)) {
        const cleaned = line.replace(/^[-*•]\s*/, "");
        const colonIndex = cleaned.indexOf(":");

        if (colonIndex > 0 && colonIndex < 45) {
          return (
            <div key={index} className="answer-point">
              <span className="answer-bullet">•</span>
              <p>
                <strong>{cleaned.slice(0, colonIndex)}:</strong>{" "}
                {cleaned.slice(colonIndex + 1).trim()}
              </p>
            </div>
          );
        }

        return (
          <div key={index} className="answer-point">
            <span className="answer-bullet">•</span>
            <p>{cleaned}</p>
          </div>
        );
      }

      return (
        <p key={index} className="answer-paragraph">
          {line}
        </p>
      );
    });
  };

  return (
    <div className="app">
      {/* HEADER */}
      <header>
        <div className="brand">
          <div className="brand-icon">🛰️</div>
          <div>
            <h1>
              Sat<span>Query</span> AI
            </h1>
          </div>
        </div>

        <div className="status">
          <div className="status-dot"></div>
          AI System Online
        </div>
      </header>

      <main>
        {/* HERO */}
        <section className="hero">
          <div className="hero-badge">
            🛰️ AI-POWERED SATELLITE INTELLIGENCE
          </div>

          <h2>
            Understand Your
            <br />
            <span>World From Above.</span>
          </h2>

          <p>
            Search a location, explore satellite imagery and investigate
            your surroundings with simple AI-powered questions.
          </p>

          <div className="location-search">
            <div className="search-icon">🔎</div>

            <input
              type="text"
              value={locationText}
              onChange={(e) => setLocationText(e.target.value)}
              placeholder="Search a city, area or location..."
            />

            <button
              className="search-button"
              onClick={() => {
                if (!locationText.trim()) {
                  alert("Enter a location first.");
                  return;
                }

                alert(
                  "Location search will connect to the interactive map next."
                );
              }}
            >
              Search
            </button>
          </div>

          <div className="location-actions">
            <button onClick={useMyLocation}>
              📍 Use My Location
            </button>

            <button
              onClick={() =>
                alert("Interactive map will be added in the next step.")
              }
            >
              🗺️ Open Interactive Map
            </button>
          </div>

          {location && (
            <p className="location-success">
              ✓ Your location has been detected.
            </p>
          )}
        </section>

        {/* MAP */}
        <section className="map-panel">
          <div className="map-overlay"></div>

          <div className="map-center">
            <div className="map-center-icon">🛰️</div>
            <p>Satellite Intelligence Map</p>
            <small>Search a location to begin exploring</small>
          </div>
        </section>

        {/* FEATURES */}
        <section>
          <div className="section-title">
            <h2>What do you want to investigate?</h2>
            <p>Choose a purpose and let SatQuery AI analyze the area.</p>
          </div>

          <div className="feature-grid">
            {features.map((feature) => (
              <button
                className="feature-card"
                key={feature.name}
                onClick={() => selectFeature(feature.name)}
              >
                <div className="feature-icon">{feature.icon}</div>
                <h3>{feature.name}</h3>
                <p>{feature.description}</p>
              </button>
            ))}
          </div>
        </section>

        {/* QUICK OBJECT DETECTION */}
        <section className="detection-section">
          <div className="section-title">
            <div>
              <div className="selected-label">COMPUTER VISION</div>

              <h2>📦 Object Detection</h2>

              <p>
                Detect buildings, vehicles and other objects directly from
                satellite imagery.
              </p>
            </div>
          </div>

          <label className="upload-box">
            <div className="upload-icon">🛰️</div>

            <strong>
              {image ? image.name : "Drop your satellite image here"}
            </strong>

            <span>
              {image
                ? "Image selected"
                : "or click to browse • JPG, PNG, WEBP"}
            </span>

            <input
              type="file"
              accept="image/png,image/jpeg,image/jpg,image/webp"
              onChange={(e) => handleImageChange(e.target.files[0])}
            />
          </label>

          {previewUrl && (
            <div className="image-preview">
              <div className="preview-header">
                <span>INPUT IMAGE</span>
                <span>READY FOR ANALYSIS</span>
              </div>

              <img src={previewUrl} alt="Uploaded satellite" />
            </div>
          )}

          <div className="detection-query">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Example: Detect buildings, cars and trucks..."
            />

            <button
              className="analyze-button"
              onClick={runDetection}
              disabled={loading || !image}
            >
              {loading ? "Running..." : "Result"}
            </button>
          </div>
        </section>

        {/* OTHER FEATURE ANALYSIS */}
        {selectedFeature && selectedFeature !== "What Changed?" && (
          <section className="upload-section">
            <div className="analysis-heading">
              <div>
                <div className="selected-label">SELECTED ANALYSIS</div>
                <h2>{selectedFeature}</h2>
              </div>

              <button
                className="close-button"
                onClick={() => {
                  setSelectedFeature("");
                  setImage(null);
                  setAnswer("");
                  setVlmResult("");
                  setDetectionResult(null);

                  if (previewUrl) URL.revokeObjectURL(previewUrl);
                  setPreviewUrl(null);
                }}
              >
                ✕
              </button>
            </div>

            <p>
              Upload an overhead or satellite image for{" "}
              <strong>{selectedFeature}</strong>.
            </p>

            <label className="upload-box">
              <div className="upload-icon">☁️</div>

              <strong>
                {image ? image.name : "Drop your satellite image here"}
              </strong>

              <span>
                {image
                  ? "Image selected"
                  : "or click to browse • JPG, PNG, WEBP"}
              </span>

              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/webp"
                onChange={(e) => handleImageChange(e.target.files[0])}
              />
            </label>

            <button
              className="analyze-button"
              onClick={analyzeImage}
              disabled={loading || !image}
            >
              {loading ? "🔄 Analyzing..." : "🔍 Analyze with SatQuery AI"}
            </button>

            {/* GEMINI IMAGE QUESTION */}
            <div className="image-question-box">
              <div className="question-label">
                💬 Ask about this image
              </div>

              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Example: Is this area urban or rural?"
                rows={3}
              />

              <div className="question-actions">
                <button
                  type="button"
                  className="voice-button"
                  onClick={startVoice}
                  disabled={loading}
                >
                  {listening ? "🎤 Listening..." : "🎤 Speak"}
                </button>

                <button
                  type="button"
                  className="ask-button"
                  onClick={askImageQuestion}
                  disabled={loading || !image}
                >
                  {loading ? "🛰️ Analyzing..." : "Ask SatQuery →"}
                </button>
              </div>

              <div className="suggested-questions">
                <button
                  type="button"
                  onClick={() =>
                    setQuestion("Is this area urban or rural?")
                  }
                >
                  Urban or rural?
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setQuestion("Describe the land use in this area.")
                  }
                >
                  Land use
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setQuestion("What vegetation is visible?")
                  }
                >
                  Vegetation
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setQuestion("Are there roads visible?")
                  }
                >
                  Roads
                </button>
              </div>
            </div>
          </section>
        )}

        {/* WHAT CHANGED */}
        {selectedFeature === "What Changed?" && (
          <section className="upload-section">
            <div className="analysis-heading">
              <div>
                <div className="selected-label">CHANGE ANALYSIS</div>
                <h2>🔍 What Changed?</h2>
              </div>

              <button
                className="close-button"
                onClick={() => setSelectedFeature("")}
              >
                ✕
              </button>
            </div>

            <div className="coming-soon">
              <div>🔍</div>
              <h3>Before & After Analysis</h3>
              <p>
                Upload two satellite images to identify visible changes.
                Visual change highlighting will be added next.
              </p>
            </div>
          </section>
        )}

        {/* YOLO DETECTION RESULTS */}
        {detectionResult &&
          detectionResult.route === "detection" &&
          detectionResult.annotated_image &&
          Array.isArray(detectionResult.detections) &&
          !loading && (
            <section className="detection-results">
              <div className="result-header">
                <div>
                  <div className="selected-label">
                    COMPUTER VISION OUTPUT
                  </div>

                  <h2>🛰️ Satellite Intelligence Results</h2>
                </div>

                <div className="ai-badge">YOLO xVIEW</div>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-icon">🎯</span>
                  <span className="stat-label">OBJECTS DETECTED</span>
                  <strong>{totalDetections}</strong>
                </div>

                <div className="stat-card">
                  <span className="stat-icon">🏢</span>
                  <span className="stat-label">BUILDINGS</span>
                  <strong>
                    {detectionResult.counts?.Building || 0}
                  </strong>
                </div>

                <div className="stat-card">
                  <span className="stat-icon">🚗</span>
                  <span className="stat-label">VEHICLES</span>
                  <strong>{vehicleCount}</strong>
                </div>

                <div className="stat-card">
                  <span className="stat-icon">📊</span>
                  <span className="stat-label">AVG CONFIDENCE</span>
                  <strong>{averageConfidence}%</strong>
                </div>
              </div>

              <div className="results-layout">
                <div className="annotated-panel">
                  <div className="panel-heading">
                    <div>
                      <span>PROCESSED IMAGE</span>
                      <h3>Detected Objects</h3>
                    </div>

                    <span className="live-indicator">● ANALYZED</span>
                  </div>

                  <div className="annotated-image-wrapper">
                    <img
                      src={`${API_URL}${detectionResult.annotated_image}`}
                      alt="YOLO object detection result"
                    />
                  </div>
                </div>

                <div className="objects-panel">
                  <div className="panel-heading">
                    <div>
                      <span>DETECTION SUMMARY</span>
                      <h3>Objects Found</h3>
                    </div>
                  </div>

                  <div className="object-count-list">
                    {detectionEntries.length === 0 ? (
                      <div className="empty-detection">
                        No relevant objects detected.
                      </div>
                    ) : (
                      detectionEntries.map(([name, count]) => (
                        <div
                          className="object-count-row"
                          key={name}
                        >
                          <div>
                            <span className="object-dot"></span>
                            <span>{name}</span>
                          </div>

                          <strong>{count}</strong>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="analysis-summary">
                    <span>AI ANALYSIS</span>
                    <p>{answer}</p>
                  </div>
                </div>
              </div>

              <div className="detection-table-panel">
                <div className="panel-heading">
                  <div>
                    <span>RAW COMPUTER VISION RESULTS</span>
                    <h3>Individual Detections</h3>
                  </div>

                  <span>
                    {detectionResult.detections?.length || 0} records
                  </span>
                </div>

                <div className="detection-table">
                  <div className="table-row table-head">
                    <span>#</span>
                    <span>OBJECT</span>
                    <span>CONFIDENCE</span>
                    <span>BOUNDING BOX</span>
                  </div>

                  {(detectionResult.detections || []).map(
                    (detection, index) => (
                      <div
                        className="table-row"
                        key={`${detection.class}-${index}`}
                      >
                        <span>{index + 1}</span>

                        <span className="object-name">
                          {detection.class}
                        </span>

                        <span>
                          <div className="confidence-bar">
                            <div
                              className="confidence-fill"
                              style={{
                                width: `${detection.confidence * 100
                                  }%`,
                              }}
                            ></div>
                          </div>

                          {Math.round(
                            detection.confidence * 100
                          )}
                          %
                        </span>

                        <span className="box-value">
                          [{detection.box.join(", ")}]
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            </section>
          )}

        {/* GEMINI / VLM TEXT RESULT */}
        {(loading || vlmResult) && !detectionResult && (
          <section className="result-section">
            <div className="result-header">
              <div>
                <div className="selected-label">
                  SATQUERY AI ANALYSIS
                </div>

                <h2>🛰️ Intelligence Result</h2>
              </div>

              <div className="ai-badge">GEMINI VLM</div>
            </div>

            <div className="result-content">
              {loading ? (
                <div className="loading">
                  <div className="loading-icon">🛰️</div>

                  <h3>Analyzing your request...</h3>

                  <p>
                    SatQuery AI is examining the satellite imagery.
                  </p>
                </div>
              ) : (
                <div className="formatted-answer">
                  {formatAnswer(vlmResult)}
                </div>
              )}
            </div>
          </section>
        )}

        {/* FOOTER */}
        <footer>
          <div>
            🛰️ <strong>SatQuery AI</strong>
          </div>

          <p>
            Complex technology. Simple questions. Clear answers.
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;
