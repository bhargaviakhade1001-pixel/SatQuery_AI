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

  const selectFeature = (feature) => {
    setSelectedFeature(feature);
    setImage(null);
    setAnswer("");
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: "smooth",
    });
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
      const spokenText = event.results[0][0].transcript;
      setQuestion(spokenText);
      setListening(false);
    };

    recognition.onerror = () => {
      setListening(false);
      alert("Could not understand your voice. Please try again.");
    };

    recognition.onend = () => {
      setListening(false);
    };
  };

  const askSatQuery = async () => {
    if (!question.trim()) {
      alert("Please enter a question first.");
      return;
    }

    setLoading(true);
    setAnswer("");

    const formData = new FormData();
    formData.append("question", question);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setAnswer(data.response);
      } else {
        setAnswer(data.detail || "Something went wrong.");
      }
    } catch (error) {
      setAnswer(
        "Cannot connect to SatQuery AI. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

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
      alert("This feature requires two images and will be added next.");
      return;
    }

    setLoading(true);
    setAnswer("");

    const formData = new FormData();
    formData.append("image", image);

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setAnswer(data.analysis);
      } else {
        setAnswer(data.detail || "Analysis failed.");
      }
    } catch (error) {
      setAnswer(
        "Cannot connect to SatQuery AI. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

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
            body: JSON.stringify({
              latitude,
              longitude,
            }),
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

          {/* LOCATION SEARCH */}
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
            <small>
              Search a location to begin exploring
            </small>
          </div>
        </section>

        {/* FEATURES */}
        <section>
          <div className="section-title">
            <h2>What do you want to investigate?</h2>
            <p>
              Choose a purpose and let SatQuery AI analyze the area.
            </p>
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

        {/* IMAGE ANALYSIS */}
        {selectedFeature && (
          <section className="upload-section">
            <div className="analysis-heading">
              <div>
                <div className="selected-label">
                  SELECTED ANALYSIS
                </div>

                <h2>
                  {selectedFeature}
                </h2>
              </div>

              <button
                className="close-button"
                onClick={() => {
                  setSelectedFeature("");
                  setImage(null);
                  setAnswer("");
                }}
              >
                ✕
              </button>
            </div>

            {selectedFeature === "What Changed?" ? (
              <div className="coming-soon">
                <div>🔍</div>
                <h3>Before & After Analysis</h3>
                <p>
                  This feature requires two satellite images and will
                  be connected next.
                </p>
              </div>
            ) : (
              <>
                <p>
                  Upload an overhead or satellite image for{" "}
                  <strong>{selectedFeature}</strong>.
                </p>

                <label className="upload-box">
                  <div className="upload-icon">☁️</div>

                  <strong>
                    {image
                      ? image.name
                      : "Drop your satellite image here"}
                  </strong>

                  <span>
                    {image
                      ? "Image selected"
                      : "or click to browse • JPG, PNG, WEBP"}
                  </span>

                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/jpg,image/webp"
                    onChange={(e) =>
                      setImage(e.target.files[0])
                    }
                  />
                </label>

                <button
                  className="analyze-button"
                  onClick={analyzeImage}
                  disabled={loading}
                >
                  {loading
                    ? "🔄 Analyzing..."
                    : "🔍 Analyze with SatQuery AI"}
                </button>
              </>
            )}
          </section>
        )}

        {/* RESULT */}
        {(loading || answer) && (
          <section className="result-section">
            <div className="result-header">
              <div>
                <div className="selected-label">
                  SATQUERY AI ANALYSIS
                </div>

                <h2>🛰️ Intelligence Result</h2>
              </div>

              <div className="ai-badge">AI ASSISTED</div>
            </div>

            <div className="result-content">
              {loading ? (
                <div className="loading">
                  <div className="loading-icon">🛰️</div>
                  <h3>Analyzing your request...</h3>
                  <p>
                    SatQuery AI is examining the available information.
                  </p>
                </div>
              ) : (
                <p>{answer}</p>
              )}
            </div>
          </section>
        )}

        {/* ASK SATQUERY */}
        <section className="chat-section">
          <div className="section-title">
            <h2>💬 Ask SatQuery</h2>
            <p>
              Have a question? Ask it naturally.
            </p>
          </div>

          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Example: What should I check before buying land in this area?"
          />

          <div className="button-row">
            <button onClick={startVoice}>
              {listening
                ? "🎤 Listening..."
                : "🎤 Speak"}
            </button>

            <button
              onClick={askSatQuery}
              disabled={loading}
            >
              {loading
                ? "🔄 Thinking..."
                : "Ask SatQuery →"}
            </button>
          </div>
        </section>

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
