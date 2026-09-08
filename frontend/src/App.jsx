import { useState } from "react";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [image, setImage] = useState(null);
  const [listening, setListening] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState("");

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

  const selectFeature = (feature) => {
    setSelectedFeature(feature);
    setAnswer("");
  };

  const analyzeImage = async () => {
    if (!image) {
      alert("Please upload an image first.");
      return;
    }

    let endpoint = "";

    if (selectedFeature === "Check My Area") {
      endpoint = "/api/property-risk";
    } else if (selectedFeature === "Flood Risk") {
      endpoint = "/api/flood-risk";
    } else if (selectedFeature === "Construction") {
      endpoint = "/api/construction-check";
    } else if (selectedFeature === "Environment") {
      endpoint = "/api/environment";
    } else if (selectedFeature === "Agriculture") {
      endpoint = "/api/agriculture";
    } else if (selectedFeature === "Disaster") {
      endpoint = "/api/disaster";
    }

    if (!endpoint) {
      alert("Please select an analysis feature first.");
      return;
    }

    const formData = new FormData();
    formData.append("image", image);

    setLoading(true);
    setAnswer("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000${endpoint}`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (response.ok) {
        setAnswer(data.analysis);
      } else {
        setAnswer(
          data.detail || "Something went wrong. Please try again."
        );
      }
    } catch (error) {
      setAnswer(
        "Cannot connect to SatQuery backend. Make sure the backend server is running."
      );
    }

    setLoading(false);
  };

  const askSatQuery = async () => {
    if (!question.trim()) {
      alert("Please enter or speak a question.");
      return;
    }

    const formData = new FormData();
    formData.append("question", question);

    setLoading(true);
    setAnswer("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/chat",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (response.ok) {
        setAnswer(data.response);
      } else {
        setAnswer(
          data.detail || "Something went wrong. Please try again."
        );
      }
    } catch (error) {
      setAnswer(
        "Cannot connect to SatQuery backend. Make sure the backend server is running."
      );
    }

    setLoading(false);
  };

  return (
    <div className="app">

      <header>
        <h1>🛰️ SatQuery AI</h1>
        <p>Satellite Intelligence, Simplified</p>
      </header>

      <main>

        <h2>What would you like to do?</h2>

        <div className="feature-grid">

          <button onClick={() => selectFeature("Check My Area")}>
            🏠 Check My Area
          </button>

          <button onClick={() => selectFeature("Flood Risk")}>
            🌊 Flood Risk
          </button>

          <button onClick={() => selectFeature("Construction")}>
            🏗️ Construction
          </button>

          <button onClick={() => selectFeature("What Changed?")}>
            🔍 What Changed?
          </button>

          <button onClick={() => selectFeature("Environment")}>
            🌳 Environment
          </button>

          <button onClick={() => selectFeature("Agriculture")}>
            🌾 Agriculture
          </button>

          <button onClick={() => selectFeature("Disaster")}>
            🚨 Disaster
          </button>

        </div>

        {selectedFeature && (
          <section className="upload-section">

            <h2>📷 {selectedFeature}</h2>

            <p>
              Upload a satellite or aerial image to analyze this area.
            </p>

            <input
              type="file"
              accept="image/png,image/jpeg,image/jpg,image/webp"
              onChange={(e) => setImage(e.target.files[0])}
            />

            {image && (
              <p className="file-name">
                📄 Selected: {image.name}
              </p>
            )}

            <button
              className="analyze-button"
              onClick={analyzeImage}
              disabled={loading}
            >
              {loading ? "🔄 Analyzing..." : "🔎 Analyze Image"}
            </button>

          </section>
        )}

        <section className="chat-section">

          <h2>💬 Ask SatQuery</h2>

          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask something about satellite imagery, your area, floods, construction..."
          />

          <div className="button-row">

            <button onClick={startVoice}>
              {listening ? "🎤 Listening..." : "🎤 Speak"}
            </button>

            <button onClick={askSatQuery}>
              Ask SatQuery
            </button>

          </div>

        </section>

        {answer && (
          <section className="answer">

            <h3>🛰️ SatQuery Response</h3>

            <p>{answer}</p>

          </section>
        )}

        <section className="location-section">

          <h2>📍 Location</h2>

          <button>
            📍 Use My Location
          </button>

          <p>
            Your location will be requested only when you choose this option.
          </p>

        </section>

      </main>

    </div>
  );
}

export default App;
{answer && (
  <section className="answer">

    <h3>🛰️ SatQuery Response</h3>

    <p>{answer}</p>

  </section>
)}
