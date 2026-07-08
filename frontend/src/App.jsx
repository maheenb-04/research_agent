import { useState, useEffect } from "react";
import axios from "axios";

const LOADING_LINES = [
  "beaming up sources...",
  "consulting the crystal ball...",
  "dialing up the mainframe...",
  "summoning the research spirits...",
  "rewinding the tape...",
];

export default function App() {
  const [topic, setTopic] = useState("");
  const [data, setData] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState("search");
  const [loadingLine, setLoadingLine] = useState(LOADING_LINES[0]);

  const loadHistory = async () => {
    try {
      const res = await axios.get("http://localhost:8000/reports");
      setHistory(res.data.reverse());
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    if (!loading) return;
    let i = 0;
    const id = setInterval(() => {
      i = (i + 1) % LOADING_LINES.length;
      setLoadingLine(LOADING_LINES[i]);
    }, 1400);
    return () => clearInterval(id);
  }, [loading]);

  const run = async () => {
    if (!topic) return;

    setLoading(true);
    setData(null);

    try {
      const res = await axios.get("http://localhost:8000/run/" + encodeURIComponent(topic));
      setData(res.data.data);
      loadHistory();
    } catch (err) {
      console.error(err);
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen font-body text-ink bg-cream">
      <div className="max-w-5xl mx-auto px-6 py-10">

        {/* NAV */}
        <div className="flex justify-center mb-12">
          <div className="sticker-pill p-1.5 flex gap-1">
            <button
              onClick={() => setView("search")}
              className={"px-6 py-2 rounded-full font-display font-semibold transition-all duration-150 " + (view === "search" ? "bg-periwinkle text-ink" : "text-ink/70 hover:text-ink")}
            >
              Search
            </button>
            <button
              onClick={() => setView("history")}
              className={"px-6 py-2 rounded-full font-display font-semibold transition-all duration-150 " + (view === "history" ? "bg-periwinkle text-ink" : "text-ink/70 hover:text-ink")}
            >
              History
            </button>
          </div>
        </div>

        {/* SEARCH VIEW */}
        {view === "search" && (
          <>
            <div className="text-center mb-10 relative">
              <span className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-6 bg-periwinkle text-ink text-xs font-display font-semibold px-3 py-1 rounded-full border-2 border-ink rotate-6 hidden md:inline-block">
                beta!
              </span>
              <h1 className="marker-heading text-4xl md:text-6xl -rotate-2 inline-block px-4">
                Research Agent<span className="text-periwinkle">.</span>
              </h1>
              <p className="font-display text-muted text-sm mt-2 font-medium">
                Your Research, Wrangled
              </p>
            </div>

            <div className="max-w-2xl mx-auto mb-12">
              <div className="sticker-pill flex gap-2 p-1.5">
                <input
                  className="flex-1 px-5 py-3 rounded-full bg-transparent placeholder-placeholder outline-none font-body text-base"
                  placeholder="ask research agent anything..."
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && run()}
                />
                <button
                  onClick={run}
                  className="px-7 py-3 rounded-full font-display font-semibold border-2 border-ink bg-periwinkle text-ink hover:-translate-y-0.5 hover:-translate-x-0.5 hover:shadow-[2px_2px_0_#1A1A1A] transition-all duration-150"
                >
                  Go →
                </button>
              </div>
            </div>

            {loading && (
              <div className="flex flex-col items-center gap-4 py-10">
                <div className="w-12 h-12 rounded-full border-4 border-ink/10 border-t-periwinkle animate-spin" />
                <p className="font-display text-muted">{loadingLine}</p>
              </div>
            )}

            {data && (
              <div className="space-y-10">

                {/* SOURCES */}
                <div>
                  <h2 className="font-display font-semibold text-xl mb-4">
                    <span className="text-periwinkle">✦</span> Sources
                  </h2>
                  <div className="grid md:grid-cols-2 gap-4">
                    {data.sources_analysis?.map((s, i) => (
                      <div key={i} className="sticker-card p-5">
                        <a
                          href={s.link}
                          target="_blank"
                          rel="noreferrer"
                          className="font-display font-semibold border-b-2 border-periwinkle pb-0.5"
                        >
                          {s.title}
                        </a>
                        {s.why_it_matters && (
                          <p className="text-muted text-sm mt-2.5 leading-relaxed">{s.why_it_matters}</p>
                        )}
                        {s.key_takeaway && (
                          <p className="text-sm mt-2.5 inline-block bg-periwinkleLight px-2.5 py-1 rounded-lg">
                            ↳ {s.key_takeaway}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* INSIGHTS */}
                {data.insights?.length > 0 && (
                  <div>
                    <h2 className="font-display font-semibold text-xl mb-4">
                      <span className="text-periwinkle">✦</span> Insights
                    </h2>
                    <div className="flex flex-wrap gap-2.5">
                      {data.insights.map((item, idx) => (
                        <span
                          key={idx}
                          className={"px-4 py-2.5 rounded-full text-sm font-medium border-2 border-ink bg-white stamp " + (idx % 2 === 0 ? "-rotate-1" : "rotate-1")}
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* TRENDS */}
                {data.trends?.length > 0 && (
                  <div>
                    <h2 className="font-display font-semibold text-xl mb-4">
                      <span className="text-periwinkle">✦</span> Trends
                    </h2>
                    <div className="flex flex-wrap gap-2.5">
                      {data.trends.map((item, idx) => (
                        <span
                          key={idx}
                          className={"px-4 py-2.5 rounded-full text-sm font-medium border-2 border-ink bg-white stamp " + (idx % 2 === 0 ? "-rotate-1" : "rotate-1")}
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* APPLICATIONS */}
                {data.applications?.length > 0 && (
                  <div>
                    <h2 className="font-display font-semibold text-xl mb-4">
                      <span className="text-periwinkle">✦</span> Applications
                    </h2>
                    <div className="flex flex-wrap gap-2.5">
                      {data.applications.map((item, idx) => (
                        <span
                          key={idx}
                          className="px-4 py-2.5 rounded-full text-sm font-medium border-2 border-ink bg-periwinkle text-ink"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            )}
          </>
        )}

        {/* HISTORY VIEW */}
        {view === "history" && (
          <>
            <h1 className="marker-heading text-4xl text-center mb-10 -rotate-1">
              Saved Reports
            </h1>

            <div className="grid md:grid-cols-2 gap-4">
              {history.length === 0 && (
                <p className="text-muted font-body text-center col-span-2">
                  Nothing here yet... go run a search!
                </p>
              )}
              {history.map((h, i) => (
                <div key={i} className="sticker-card p-5">
                  <h2 className="font-display font-semibold text-lg">{h.topic}</h2>
                  <p className="text-placeholder text-xs mt-1">{h.date}</p>

                  <button
                    className="mt-3 px-4 py-1.5 rounded-full text-sm font-display font-semibold border-2 border-ink bg-periwinkleLight"
                    onClick={() => {
                      setData(JSON.parse(h.summary));
                      setView("search");
                    }}
                  >
                    View Report →
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
