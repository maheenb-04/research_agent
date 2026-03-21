import { useState, useEffect } from "react";
import axios from "axios";

export default function App() {
  const [topic, setTopic] = useState("");
  const [data, setData] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState("search"); // search or history

  // 🔥 fetch history
  const loadHistory = async () => {
    const res = await axios.get("http://localhost:8000/reports");
    setHistory(res.data.reverse());
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const run = async () => {
    if (!topic) return;

    setLoading(true);
    setData(null);

    try {
      const res = await axios.get(`http://localhost:8000/run/${topic}`);
      setData(res.data.data);
      loadHistory(); // refresh history
    } catch (err) {
      console.error(err);
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-5xl mx-auto">

        {/* NAV */}
        <div className="flex gap-4 mb-6">
          <button onClick={() => setView("search")} className="bg-blue-600 px-4 py-2 rounded">
            Search
          </button>
          <button onClick={() => setView("history")} className="bg-gray-700 px-4 py-2 rounded">
            History
          </button>
        </div>

        {/* SEARCH VIEW */}
        {view === "search" && (
          <>
            <h1 className="text-3xl font-bold mb-6">AI Research Agent</h1>

            <div className="flex gap-2 mb-6">
              <input
                className="p-3 rounded bg-gray-800 w-full"
                placeholder="Enter any topic..."
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              />
              <button onClick={run} className="bg-blue-600 px-6 py-3 rounded">
                Run
              </button>
            </div>

            {loading && <p className="text-gray-400">Analyzing...</p>}

            {data && (
              <div className="space-y-6">

                {/* SOURCES */}
                <div>
                  <h2 className="text-xl font-semibold">Sources</h2>
                  {data.sources_analysis?.map((s, i) => (
                    <div key={i} className="bg-gray-800 p-4 rounded mt-2">
                      <a href={s.link} target="_blank" className="text-blue-400 font-bold">
                        {s.title}
                      </a>
                      <p>{s.why_it_matters}</p>
                    </div>
                  ))}
                </div>

                {/* INSIGHTS */}
                <div>
                  <h2 className="text-xl font-semibold">Insights</h2>
                  {data.insights?.map((i, idx) => (
                    <p key={idx}>• {i}</p>
                  ))}
                </div>

              </div>
            )}
          </>
        )}

        {/* HISTORY VIEW */}
        {view === "history" && (
          <>
            <h1 className="text-3xl font-bold mb-6">Saved Reports</h1>

            <div className="space-y-4">
              {history.map((h, i) => (
                <div key={i} className="bg-gray-800 p-4 rounded">
                  <h2 className="font-bold">{h.topic}</h2>
                  <p className="text-gray-400 text-sm">{h.date}</p>

                  <button
                    className="mt-2 text-blue-400"
                    onClick={() => setData(JSON.parse(h.summary))}
                  >
                    View Report
                  </button>
                </div>
              ))}
            </div>
          </>
        )}

      </div>
    </div>
  );
}