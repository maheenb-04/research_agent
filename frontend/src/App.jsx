import { useState, useEffect } from "react";
import axios from "axios";

const LOADING_LINES = [
  "beaming up sources...",
  "consulting the crystal ball...",
  "dialing up the mainframe...",
  "summoning the research spirits...",
  "rewinding the tape...",
];

const SCAN_TOPICS = [
  "scanning: quantum computing breakthroughs",
  "scanning: cybersecurity threat trends 2026",
  "scanning: AI agent architectures",
  "scanning: climate tech innovations",
];

const API = "http://localhost:8000";

const DAYS = [
  { value: "mon", label: "Monday" },
  { value: "tue", label: "Tuesday" },
  { value: "wed", label: "Wednesday" },
  { value: "thu", label: "Thursday" },
  { value: "fri", label: "Friday" },
  { value: "sat", label: "Saturday" },
  { value: "sun", label: "Sunday" },
];

const HOURS = Array.from({ length: 24 }, (_, h) => {
  const label = h === 0 ? "12:00 AM" : h < 12 ? `${h}:00 AM` : h === 12 ? "12:00 PM" : `${h - 12}:00 PM`;
  return { value: h, label };
});

const TIMEZONES = [
  { value: "America/New_York", label: "Eastern (ET)" },
  { value: "America/Chicago", label: "Central (CT)" },
  { value: "America/Denver", label: "Mountain (MT)" },
  { value: "America/Los_Angeles", label: "Pacific (PT)" },
  { value: "America/Anchorage", label: "Alaska (AKT)" },
  { value: "Pacific/Honolulu", label: "Hawaii (HST)" },
  { value: "UTC", label: "UTC" },
  { value: "Europe/London", label: "London (GMT/BST)" },
  { value: "Europe/Paris", label: "Central Europe (CET)" },
  { value: "Asia/Tokyo", label: "Tokyo (JST)" },
  { value: "Asia/Shanghai", label: "Shanghai (CST)" },
  { value: "Asia/Kolkata", label: "India (IST)" },
  { value: "Australia/Sydney", label: "Sydney (AET)" },
];

const FREQUENCIES = [
  { value: "weekly", label: "Weekly" },
  { value: "biweekly", label: "Biweekly" },
  { value: "monthly", label: "Monthly" },
];

function VintageComputer() {
  return (
    <svg className="vintage-computer" viewBox="0 0 200 220" xmlns="http://www.w3.org/2000/svg">
      <rect x="20" y="10" width="160" height="120" rx="14" fill="none" stroke="#22201A" strokeWidth="4"/>
      <rect x="36" y="26" width="128" height="88" rx="4" fill="none" stroke="#22201A" strokeWidth="3"/>
      <line x1="70" y1="90" x2="130" y2="90" stroke="#22201A" strokeWidth="2"/>
      <line x1="60" y1="102" x2="140" y2="102" stroke="#22201A" strokeWidth="2"/>
      <circle cx="100" cy="120" r="4" fill="#22201A"/>
      <rect x="85" y="130" width="30" height="18" fill="none" stroke="#22201A" strokeWidth="4"/>
      <rect x="50" y="148" width="100" height="14" rx="6" fill="none" stroke="#22201A" strokeWidth="4"/>
      <rect x="30" y="168" width="140" height="42" rx="8" fill="none" stroke="#22201A" strokeWidth="4"/>
      {[48, 60, 72, 84, 96, 108, 120, 132, 144].map((x) => (
        <circle key={"r1-" + x} cx={x} cy="182" r="3" fill="#22201A" />
      ))}
      {[48, 60, 72, 84, 96, 108, 120, 132, 144].map((x) => (
        <circle key={"r2-" + x} cx={x} cy="194" r="3" fill="#22201A" />
      ))}
    </svg>
  );
}

function useTypewriter(topics) {
  const [text, setText] = useState("");

  useEffect(() => {
    let topicIdx = 0;
    let charIdx = 0;
    let deleting = false;
    let timeoutId;

    function loop() {
      const current = topics[topicIdx];

      if (!deleting) {
        charIdx++;
        setText(current.slice(0, charIdx));
        if (charIdx === current.length) {
          deleting = true;
          timeoutId = setTimeout(loop, 1400);
          return;
        }
      } else {
        charIdx--;
        setText(current.slice(0, charIdx));
        if (charIdx === 0) {
          deleting = false;
          topicIdx = (topicIdx + 1) % topics.length;
        }
      }

      timeoutId = setTimeout(loop, deleting ? 30 : 55);
    }

    loop();
    return () => clearTimeout(timeoutId);
  }, [topics]);

  return text;
}

function CiteButtons({ citations, sourceKey, copiedKey, onCopy }) {
  if (!citations) return null;
  const formats = [
    { key: "apa", label: "APA" },
    { key: "mla", label: "MLA" },
    { key: "chicago", label: "Chicago" },
  ];
  return (
    <div className="flex gap-1.5 mt-3">
      {formats.map((f) => {
        const thisKey = sourceKey + "-" + f.key;
        const isCopied = copiedKey === thisKey;
        return (
          <button
            key={f.key}
            onClick={() => onCopy(citations[f.key], thisKey)}
            className="text-[11px] font-display font-bold px-2.5 py-1 rounded-md border-[1.5px] border-ink text-ink hover:border-[2.5px] hover:tracking-wide transition-all"
          >
            {isCopied ? "Copied!" : f.label}
          </button>
        );
      })}
    </div>
  );
}

export default function App() {
  const [topic, setTopic] = useState("");
  const [currentTopic, setCurrentTopic] = useState("");
  const [data, setData] = useState(null);
  const [currentReportId, setCurrentReportId] = useState(null);
  const [history, setHistory] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState("search");
  const [loadingLine, setLoadingLine] = useState(LOADING_LINES[0]);
  const [statusMessage, setStatusMessage] = useState(null);
  const [wasCached, setWasCached] = useState(false);
  const scanText = useTypewriter(SCAN_TOPICS);

  const [copiedKey, setCopiedKey] = useState(null);
  const [tagDrafts, setTagDrafts] = useState({});
  const [tagFilter, setTagFilter] = useState("");

  const [followupQuestion, setFollowupQuestion] = useState("");
  const [followupLoading, setFollowupLoading] = useState(false);
  const [followupThread, setFollowupThread] = useState([]);

  const [digestEmail, setDigestEmail] = useState("");
  const [digestToken, setDigestToken] = useState("");
  const [digestTopic, setDigestTopic] = useState("");
  const [digestDay, setDigestDay] = useState("mon");
  const [digestHour, setDigestHour] = useState(8);
  const [digestTimezone, setDigestTimezone] = useState("America/New_York");
  const [digestFrequency, setDigestFrequency] = useState("weekly");
  const [digestSubscriptions, setDigestSubscriptions] = useState([]);
  const [digestHistory, setDigestHistory] = useState([]);
  const [digestStatusMessage, setDigestStatusMessage] = useState(null);
  const [digestActionLoading, setDigestActionLoading] = useState(null);
  const [digestPreview, setDigestPreview] = useState(null);
  const [digestPreviewLoading, setDigestPreviewLoading] = useState(false);
  const [digestPendingId, setDigestPendingId] = useState(null);

  const loadHistory = async () => {
    try {
      const res = await axios.get(API + "/reports");
      setHistory(res.data.reverse());
    } catch (err) {
      console.error(err);
    }
  };

  const loadFavorites = async () => {
    try {
      const res = await axios.get(API + "/favorites");
      setFavorites(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadHistory();
    loadFavorites();

    // if we arrived here from a confirmation-email link, the URL will carry
    // ?digest_email=...&digest_token=... - pick those up automatically so
    // the person lands directly in their subscription management view
    const params = new URLSearchParams(window.location.search);
    const emailParam = params.get("digest_email");
    const tokenParam = params.get("digest_token");
    if (emailParam && tokenParam) {
      setDigestEmail(emailParam);
      setDigestToken(tokenParam);
      setView("digests");
      loadDigestsWithToken(emailParam, tokenParam);
    }
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
    setStatusMessage(null);
    setWasCached(false);
    setFollowupThread([]);

    try {
      const res = await axios.get(API + "/run/" + encodeURIComponent(topic));

      if (res.data.error) {
        setStatusMessage(res.data.error);
      } else if (res.data.message) {
        setStatusMessage(res.data.message);
      } else {
        setData(res.data.data);
        setCurrentReportId(res.data.report_id || null);
        setCurrentTopic(topic);
        setWasCached(!!res.data.cached);
      }

      loadHistory();
    } catch (err) {
      const detail = err.response && err.response.data && err.response.data.detail;
      setStatusMessage(
        detail || "Couldn't reach the server. Make sure the backend is running and try again."
      );
    }

    setLoading(false);
  };

  const copyCitation = async (text, key) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 1600);
    } catch (err) {
      console.error(err);
    }
  };

  const isFavorited = (link) => favorites.some((f) => f.link === link);

  const toggleFavorite = async (source) => {
    const existing = favorites.find((f) => f.link === source.link);
    if (existing) {
      try {
        await axios.delete(API + "/favorites/" + existing.id);
        loadFavorites();
      } catch (err) {
        console.error(err);
      }
      return;
    }
    try {
      await axios.post(API + "/favorites", {
        title: source.title,
        link: source.link,
        topic: currentTopic || "unknown",
      });
      loadFavorites();
    } catch (err) {
      console.error(err);
    }
  };

  const saveTags = async (reportId) => {
    const value = tagDrafts[reportId] ?? "";
    try {
      await axios.patch(API + "/reports/" + reportId + "/tags", { tags: value });
      loadHistory();
    } catch (err) {
      console.error(err);
    }
  };

  const askFollowup = async () => {
    if (!followupQuestion.trim() || !currentReportId) return;
    const question = followupQuestion.trim();
    setFollowupLoading(true);
    setFollowupQuestion("");

    try {
      const res = await axios.post(API + "/followup", {
        report_id: currentReportId,
        question,
      });
      setFollowupThread((prev) => [...prev, { question, ...res.data }]);
    } catch (err) {
      const detail = err.response && err.response.data && err.response.data.detail;
      setFollowupThread((prev) => [
        ...prev,
        { question, answer: detail || "Something went wrong answering that.", supporting_sources: [] },
      ]);
    }

    setFollowupLoading(false);
  };

  const loadDigestsWithToken = async (email, token) => {
    if (!email || !token) {
      setDigestSubscriptions([]);
      setDigestHistory([]);
      return;
    }
    try {
      const res = await axios.get(API + "/digests", { params: { email, token } });
      setDigestSubscriptions(res.data);
    } catch (err) {
      console.error(err);
    }
    try {
      const res2 = await axios.get(API + "/digests/history", { params: { email, token } });
      setDigestHistory(res2.data);
    } catch (err) {
      console.error(err);
    }
  };

  const subscribeDigest = async () => {
    const email = digestEmail.trim();
    const topicVal = digestTopic.trim();
    if (!email || !topicVal) return;

    setDigestStatusMessage(null);
    try {
      const res = await axios.post(API + "/digests", {
        email,
        topic: topicVal,
        day_of_week: digestDay,
        hour: digestHour,
        timezone: digestTimezone,
        frequency: digestFrequency,
      });
      setDigestStatusMessage(
        res.data.already_subscribed
          ? (res.data.pending_confirmation
              ? "You're already subscribed, but haven't confirmed yet - check your email for the confirmation link, or resend it below."
              : "You're already subscribed to this topic.")
          : "Check your email to confirm this subscription - it won't start sending until you click the confirmation link."
      );
      setDigestPendingId(res.data.pending_confirmation ? res.data.id : null);
      setDigestTopic("");
      setDigestPreview(null);
    } catch (err) {
      const detail = err.response && err.response.data && err.response.data.detail;
      setDigestStatusMessage(detail || "Something went wrong subscribing.");
    }
  };

  const resendConfirmation = async () => {
    if (!digestPendingId) return;
    try {
      const res = await axios.post(API + "/digests/" + digestPendingId + "/resend-confirmation", {
        email: digestEmail.trim(),
      });
      setDigestStatusMessage(
        res.data.already_confirmed
          ? "This subscription is already confirmed."
          : "Confirmation email resent - check your inbox."
      );
    } catch (err) {
      const detail = err.response && err.response.data && err.response.data.detail;
      setDigestStatusMessage(detail || "Couldn't resend the confirmation email.");
    }
  };

  const previewDigest = async () => {
    const topicVal = digestTopic.trim();
    if (!topicVal) return;
    setDigestPreviewLoading(true);
    setDigestPreview(null);
    try {
      const res = await axios.get(API + "/digests/preview", { params: { topic: topicVal } });
      setDigestPreview(res.data);
    } catch (err) {
      const detail = err.response && err.response.data && err.response.data.detail;
      setDigestStatusMessage(detail || "Couldn't generate a preview for that topic.");
    }
    setDigestPreviewLoading(false);
  };

  const unsubscribeDigest = async (id) => {
    try {
      await axios.delete(API + "/digests/" + id, {
        params: { email: digestEmail.trim(), token: digestToken },
      });
      loadDigestsWithToken(digestEmail.trim(), digestToken);
    } catch (err) {
      console.error(err);
    }
  };

  const sendDigestNow = async (id) => {
    setDigestActionLoading(id);
    try {
      await axios.post(
        API + "/digests/" + id + "/send-now",
        {},
        { params: { email: digestEmail.trim(), token: digestToken } }
      );
      setDigestStatusMessage("Sent! Check your inbox.");
      loadDigestsWithToken(digestEmail.trim(), digestToken);
    } catch (err) {
      const detail = err.response && err.response.data && err.response.data.detail;
      setDigestStatusMessage(detail || "Failed to send. Check that Gmail is set up correctly on the backend.");
    }
    setDigestActionLoading(null);
  };

  const dayLabel = (v) => DAYS.find((d) => d.value === v)?.label || v;
  const hourLabel = (v) => HOURS.find((h) => h.value === v)?.label || v;
  const tzLabel = (v) => TIMEZONES.find((t) => t.value === v)?.label || v;
  const freqLabel = (v) => FREQUENCIES.find((f) => f.value === v)?.label || v;

  const allTags = Array.from(
    new Set(
      history
        .flatMap((h) => (h.tags || "").split(",").map((t) => t.trim()))
        .filter(Boolean)
    )
  );

  const filteredHistory = tagFilter
    ? history.filter((h) => (h.tags || "").split(",").map((t) => t.trim()).includes(tagFilter))
    : history;

  return (
    <div className="min-h-screen font-body text-ink bg-page relative">
      <VintageComputer />

      <div className="max-w-5xl mx-auto px-7 pt-10 pb-20 relative z-10">

        <div className="flex justify-between items-center mb-20">
          <div className="font-display font-bold text-sm">RESEARCH AGENT</div>
          <div className="box-pill p-1.5 flex gap-1">
            <button
              onClick={() => setView("search")}
              className={"px-5 py-2 rounded-full font-display font-bold text-xs transition-all duration-150 " + (view === "search" ? "bg-blue text-blueDark" : "text-ink/70 hover:text-ink")}
            >
              Search
            </button>
            <button
              onClick={() => setView("history")}
              className={"px-5 py-2 rounded-full font-display font-bold text-xs transition-all duration-150 " + (view === "history" ? "bg-blue text-blueDark" : "text-ink/70 hover:text-ink")}
            >
              History
            </button>
            <button
              onClick={() => setView("favorites")}
              className={"px-5 py-2 rounded-full font-display font-bold text-xs transition-all duration-150 " + (view === "favorites" ? "bg-blue text-blueDark" : "text-ink/70 hover:text-ink")}
            >
              Favorites
            </button>
            <button
              onClick={() => setView("digests")}
              className={"px-5 py-2 rounded-full font-display font-bold text-xs transition-all duration-150 " + (view === "digests" ? "bg-blue text-blueDark" : "text-ink/70 hover:text-ink")}
            >
              Digests
            </button>
          </div>
        </div>

        {view === "search" && (
          <>
            <div className="mb-16">
              <h1 className="font-display font-bold uppercase leading-[0.95] tracking-tight text-[clamp(48px,9vw,108px)]">
                Ask.<br/>Search.<br/>Keep learning.
              </h1>

              <div className="mt-10 max-w-2xl">
                <div className="font-body text-muted text-sm font-semibold mb-3 h-[18px]">
                  {scanText}<span className="inline-block w-2 h-3.5 bg-muted ml-0.5 align-middle cursor-blink"></span>
                </div>
                <div className="box-pill flex gap-2 p-1.5">
                  <input
                    className="flex-1 px-5 py-3.5 rounded-full bg-transparent placeholder-placeholder outline-none font-body text-base"
                    placeholder="Ask anything..."
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && run()}
                  />
                  <button
                    onClick={run}
                    className="px-8 py-3.5 rounded-full font-display font-bold text-xs text-blueDark bg-blue shadow-[0_4px_14px_rgba(107,143,224,0.45)] hover:brightness-105 transition-all duration-150"
                  >
                    GO
                  </button>
                </div>
              </div>
            </div>

            {loading && (
              <div className="flex flex-col items-center gap-4 py-10">
                <div className="w-12 h-12 rounded-full border-4 border-ink/10 border-t-blue animate-spin" />
                <p className="font-display text-muted text-sm">{loadingLine}</p>
              </div>
            )}

            {!loading && statusMessage && (
              <div className="box-card p-5 max-w-2xl text-center">
                <p className="font-display font-bold text-sm">{statusMessage}</p>
              </div>
            )}

            {data && (
              <div className="space-y-16">

                {wasCached && (
                  <p className="font-display text-xs text-muted -mt-10 mb-4">⚡ served from cache (searched within the last 24h)</p>
                )}

                <section className="mb-16">
                  <div className="flex items-baseline gap-4 mb-7 border-b-[3px] border-ink pb-3.5">
                    <span className="font-display font-bold text-xs text-ink bg-page border-[1.5px] border-ink px-2.5 py-1 rounded-md">01</span>
                    <h2 className="font-display font-bold uppercase tracking-tight text-[clamp(28px,5vw,44px)]">Sources</h2>
                  </div>
                  <div className="grid md:grid-cols-2 gap-3.5">
                    {data.sources_analysis?.map((s, i) => (
                      <div key={i} className="box-card p-7">
                        <div className="flex items-start justify-between mb-2.5">
                          <div className="font-display font-bold text-xs text-placeholder">
                            {String(i + 1).padStart(2, "0")}
                          </div>
                          <button
                            onClick={() => toggleFavorite(s)}
                            className="font-display text-lg leading-none hover:scale-110 transition-transform"
                            title={isFavorited(s.link) ? "Remove from favorites" : "Save to favorites"}
                          >
                            {isFavorited(s.link) ? "★" : "☆"}
                          </button>
                        </div>
                        <a
                          href={s.link}
                          target="_blank"
                          rel="noreferrer"
                          className="block font-display font-bold text-lg mb-3 hover:underline decoration-2 underline-offset-4 transition-all"
                        >
                          {s.title}
                        </a>
                        {s.why_it_matters && (
                          <p className="text-muted text-sm mb-3 leading-relaxed">{s.why_it_matters}</p>
                        )}
                        {s.key_takeaway && (
                          <p className="text-sm inline-block bg-blue text-blueDark font-semibold px-3.5 py-1.5 rounded-lg">
                            ↳ {s.key_takeaway}
                          </p>
                        )}
                        <CiteButtons
                          citations={s.citations}
                          sourceKey={"src-" + i}
                          copiedKey={copiedKey}
                          onCopy={copyCitation}
                        />
                      </div>
                    ))}
                  </div>
                </section>

                {data.insights?.length > 0 && (
                  <section className="mb-16">
                    <div className="flex items-baseline gap-4 mb-7 border-b-[3px] border-ink pb-3.5">
                      <span className="font-display font-bold text-xs text-ink bg-page border-[1.5px] border-ink px-2.5 py-1 rounded-md">02</span>
                      <h2 className="font-display font-bold uppercase tracking-tight text-[clamp(28px,5vw,44px)]">Insights</h2>
                    </div>
                    <div className="grid gap-0.5" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}>
                      {data.insights.map((item, idx) => {
                        const text = typeof item === "string" ? item : item.text;
                        const source = typeof item === "string" ? null : item.source;
                        return (
                          <div key={idx} className="bg-blue p-5">
                            <span className="tag-icon">insight</span>
                            <p className="text-blueDark font-semibold text-[15px] leading-snug m-0">{text}</p>
                            {source && (
                              <a
                                href={source}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-block mt-2 text-xs font-display font-bold text-blueDark underline decoration-dotted underline-offset-2 hover:opacity-70"
                              >
                                source ↗
                              </a>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </section>
                )}

                {data.trends?.length > 0 && (
                  <section className="mb-16">
                    <div className="flex items-baseline gap-4 mb-7 border-b-[3px] border-ink pb-3.5">
                      <span className="font-display font-bold text-xs text-ink bg-page border-[1.5px] border-ink px-2.5 py-1 rounded-md">03</span>
                      <h2 className="font-display font-bold uppercase tracking-tight text-[clamp(28px,5vw,44px)]">Trends</h2>
                    </div>
                    <div className="grid gap-0.5" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}>
                      {data.trends.map((item, idx) => {
                        const text = typeof item === "string" ? item : item.text;
                        const source = typeof item === "string" ? null : item.source;
                        return (
                          <div key={idx} className="bg-blue p-5">
                            <span className="tag-icon">trend</span>
                            <p className="text-blueDark font-semibold text-[15px] leading-snug m-0">{text}</p>
                            {source && (
                              <a
                                href={source}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-block mt-2 text-xs font-display font-bold text-blueDark underline decoration-dotted underline-offset-2 hover:opacity-70"
                              >
                                source ↗
                              </a>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </section>
                )}

                {data.applications?.length > 0 && (
                  <section className="mb-16">
                    <div className="flex items-baseline gap-4 mb-7 border-b-[3px] border-ink pb-3.5">
                      <span className="font-display font-bold text-xs text-ink bg-page border-[1.5px] border-ink px-2.5 py-1 rounded-md">04</span>
                      <h2 className="font-display font-bold uppercase tracking-tight text-[clamp(28px,5vw,44px)]">Applications</h2>
                    </div>
                    <div className="grid gap-0.5" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}>
                      {data.applications.map((item, idx) => {
                        const text = typeof item === "string" ? item : item.text;
                        const source = typeof item === "string" ? null : item.source;
                        return (
                          <div key={idx} className="bg-blue p-5">
                            <span className="tag-icon">use case</span>
                            <p className="text-blueDark font-semibold text-[15px] leading-snug m-0">{text}</p>
                            {source && (
                              <a
                                href={source}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-block mt-2 text-xs font-display font-bold text-blueDark underline decoration-dotted underline-offset-2 hover:opacity-70"
                              >
                                source ↗
                              </a>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </section>
                )}

                {currentReportId && (
                  <section className="mb-16">
                    <div className="flex items-baseline gap-4 mb-7 border-b-[3px] border-ink pb-3.5">
                      <span className="font-display font-bold text-xs text-ink bg-page border-[1.5px] border-ink px-2.5 py-1 rounded-md">05</span>
                      <h2 className="font-display font-bold uppercase tracking-tight text-[clamp(28px,5vw,44px)]">Ask a follow-up</h2>
                    </div>

                    {followupThread.length > 0 && (
                      <div className="space-y-3 mb-5">
                        {followupThread.map((t, idx) => (
                          <div key={idx} className="box-card p-5">
                            <p className="font-display font-bold text-sm mb-2">Q: {t.question}</p>
                            <p className="text-muted text-sm leading-relaxed mb-2">{t.answer}</p>
                            {t.supporting_sources?.length > 0 && (
                              <div className="flex flex-wrap gap-2">
                                {t.supporting_sources.map((s, sidx) => (
                                  <a
                                    key={sidx}
                                    href={s.link}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-xs font-display font-bold text-blueDark underline decoration-dotted underline-offset-2"
                                  >
                                    {s.title} ↗
                                  </a>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="box-pill flex gap-2 p-1.5 max-w-2xl">
                      <input
                        className="flex-1 px-5 py-3 rounded-full bg-transparent placeholder-placeholder outline-none font-body text-sm"
                        placeholder="Ask something about these sources..."
                        value={followupQuestion}
                        onChange={(e) => setFollowupQuestion(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && askFollowup()}
                      />
                      <button
                        onClick={askFollowup}
                        disabled={followupLoading}
                        className="px-6 py-3 rounded-full font-display font-bold text-xs text-blueDark bg-blue hover:brightness-105 transition-all duration-150 disabled:opacity-50"
                      >
                        {followupLoading ? "..." : "Ask"}
                      </button>
                    </div>
                  </section>
                )}

              </div>
            )}
          </>
        )}

        {view === "history" && (
          <>
            <h1 className="font-display font-bold uppercase leading-[0.95] tracking-tight text-[clamp(40px,7vw,72px)] mb-10">
              Saved<br/>Reports.
            </h1>

            {allTags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-8">
                <button
                  onClick={() => setTagFilter("")}
                  className={"px-4 py-1.5 rounded-full text-xs font-display font-bold border-[1.5px] border-ink " + (tagFilter === "" ? "bg-ink text-page" : "text-ink")}
                >
                  All
                </button>
                {allTags.map((t) => (
                  <button
                    key={t}
                    onClick={() => setTagFilter(t)}
                    className={"px-4 py-1.5 rounded-full text-xs font-display font-bold border-[1.5px] border-ink " + (tagFilter === t ? "bg-ink text-page" : "text-ink")}
                  >
                    {t}
                  </button>
                ))}
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-3.5">
              {filteredHistory.length === 0 && (
                <p className="text-muted font-body text-center col-span-2">
                  Nothing here yet... go run a search!
                </p>
              )}
              {filteredHistory.map((h, i) => (
                <div key={i} className="box-card p-6">
                  <h2 className="font-display font-bold text-lg">{h.topic}</h2>
                  <p className="text-placeholder text-xs mt-2">{h.date}</p>

                  <div className="flex gap-2 mt-3">
                    <input
                      className="flex-1 px-3 py-1.5 rounded-lg bg-page border-[1.5px] border-boxBorder outline-none text-xs font-body"
                      placeholder="tags, comma separated"
                      value={tagDrafts[h.id] ?? h.tags ?? ""}
                      onChange={(e) => setTagDrafts((prev) => ({ ...prev, [h.id]: e.target.value }))}
                    />
                    <button
                      onClick={() => saveTags(h.id)}
                      className="px-3 py-1.5 rounded-lg text-xs font-display font-bold border-[1.5px] border-ink text-ink hover:border-[2.5px] hover:tracking-wide transition-all"
                    >
                      Save
                    </button>
                  </div>

                  <button
                    className="mt-4 px-5 py-2 rounded-full text-xs font-display font-bold text-blueDark bg-blue"
                    onClick={() => {
                      setData(JSON.parse(h.summary));
                      setCurrentReportId(h.id);
                      setCurrentTopic(h.topic);
                      setFollowupThread([]);
                      setWasCached(false);
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

        {view === "favorites" && (
          <>
            <h1 className="font-display font-bold uppercase leading-[0.95] tracking-tight text-[clamp(40px,7vw,72px)] mb-14">
              Saved<br/>Sources.
            </h1>

            <div className="grid md:grid-cols-2 gap-3.5">
              {favorites.length === 0 && (
                <p className="text-muted font-body text-center col-span-2">
                  No favorites yet - star a source to save it here.
                </p>
              )}
              {favorites.map((f) => (
                <div key={f.id} className="box-card p-6">
                  <a
                    href={f.link}
                    target="_blank"
                    rel="noreferrer"
                    className="block font-display font-bold text-base mb-2 hover:underline decoration-2 underline-offset-4 transition-all"
                  >
                    {f.title}
                  </a>
                  <p className="text-placeholder text-xs mb-3">from: {f.topic}</p>
                  <button
                    onClick={async () => {
                      await axios.delete(API + "/favorites/" + f.id);
                      loadFavorites();
                    }}
                    className="px-4 py-1.5 rounded-full text-xs font-display font-bold border-[1.5px] border-ink text-ink hover:border-[2.5px] hover:tracking-wide transition-all"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </>
        )}

        {view === "digests" && (
          <>
            <h1 className="font-display font-bold uppercase leading-[0.95] tracking-tight text-[clamp(40px,7vw,72px)] mb-8">
              Weekly<br/>Digests.
            </h1>
            <p className="text-muted text-sm mb-10 max-w-xl">
              Get an email with the newest, most relevant sources for a topic you care about — on your schedule.
            </p>

            <div className="box-card p-6 max-w-xl mb-6">
              <div className="mb-3">
                <label className="font-display font-bold text-xs uppercase tracking-wide text-muted block mb-1.5">Your email</label>
                <input
                  className="w-full px-4 py-2.5 rounded-lg bg-page border-[1.5px] border-boxBorder outline-none text-sm font-body"
                  placeholder="you@example.com"
                  value={digestEmail}
                  onChange={(e) => setDigestEmail(e.target.value)}
                />
              </div>
              <div className="mb-3">
                <label className="font-display font-bold text-xs uppercase tracking-wide text-muted block mb-1.5">Topic to track</label>
                <input
                  className="w-full px-4 py-2.5 rounded-lg bg-page border-[1.5px] border-boxBorder outline-none text-sm font-body"
                  placeholder="e.g. cybersecurity internships"
                  value={digestTopic}
                  onChange={(e) => setDigestTopic(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && subscribeDigest()}
                />
              </div>

              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="font-display font-bold text-xs uppercase tracking-wide text-muted block mb-1.5">Frequency</label>
                  <select
                    className="w-full px-4 py-2.5 rounded-lg bg-page border-[1.5px] border-boxBorder outline-none text-sm font-body"
                    value={digestFrequency}
                    onChange={(e) => setDigestFrequency(e.target.value)}
                  >
                    {FREQUENCIES.map((f) => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="font-display font-bold text-xs uppercase tracking-wide text-muted block mb-1.5">Day</label>
                  <select
                    className="w-full px-4 py-2.5 rounded-lg bg-page border-[1.5px] border-boxBorder outline-none text-sm font-body"
                    value={digestDay}
                    onChange={(e) => setDigestDay(e.target.value)}
                  >
                    {DAYS.map((d) => (
                      <option key={d.value} value={d.value}>{d.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="font-display font-bold text-xs uppercase tracking-wide text-muted block mb-1.5">Time</label>
                  <select
                    className="w-full px-4 py-2.5 rounded-lg bg-page border-[1.5px] border-boxBorder outline-none text-sm font-body"
                    value={digestHour}
                    onChange={(e) => setDigestHour(parseInt(e.target.value, 10))}
                  >
                    {HOURS.map((h) => (
                      <option key={h.value} value={h.value}>{h.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="font-display font-bold text-xs uppercase tracking-wide text-muted block mb-1.5">Timezone</label>
                  <select
                    className="w-full px-4 py-2.5 rounded-lg bg-page border-[1.5px] border-boxBorder outline-none text-sm font-body"
                    value={digestTimezone}
                    onChange={(e) => setDigestTimezone(e.target.value)}
                  >
                    {TIMEZONES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex gap-2.5">
                <button
                  onClick={subscribeDigest}
                  className="px-6 py-2.5 rounded-full font-display font-bold text-xs text-blueDark bg-blue hover:brightness-105 transition-all"
                >
                  Subscribe
                </button>
                <button
                  onClick={previewDigest}
                  disabled={digestPreviewLoading}
                  className="px-6 py-2.5 rounded-full font-display font-bold text-xs text-ink border-[1.5px] border-ink hover:border-[2.5px] hover:tracking-wide transition-all disabled:opacity-50"
                >
                  {digestPreviewLoading ? "Loading..." : "Preview digest"}
                </button>
              </div>

              {digestStatusMessage && (
                <div className="mt-3">
                  <p className="font-display text-xs text-muted">{digestStatusMessage}</p>
                  {digestPendingId && (
                    <button
                      onClick={resendConfirmation}
                      className="mt-2 px-4 py-1.5 rounded-full text-xs font-display font-bold border-[1.5px] border-ink text-ink hover:border-[2.5px] hover:tracking-wide transition-all"
                    >
                      Resend confirmation email
                    </button>
                  )}
                </div>
              )}

              {digestPreview && (
                <div className="bg-white border-2 border-dashed border-boxBorder rounded-xl p-4 mt-4">
                  <p className="text-[10px] uppercase tracking-wide text-placeholder font-bold mb-2.5">Sample preview — not sent</p>
                  <p className="text-muted text-sm mb-3">{digestPreview.intro}</p>
                  {digestPreview.sources.map((s, i) => (
                    <div key={i} className="py-1.5 border-b border-gray-100 text-sm">
                      <a href={s.link} target="_blank" rel="noreferrer" className="text-blueDark font-semibold hover:underline">
                        {s.title}
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {digestEmail.trim() && !digestToken && (
              <p className="text-muted text-sm max-w-xl">
                After subscribing, check your email and click the confirmation link - it'll bring you
                back here with access to manage your subscriptions. For privacy, subscriptions can only
                be viewed or changed from that confirmed link, not just by typing an email address.
              </p>
            )}

            {digestEmail.trim() && digestToken && (
              <>
                <h2 className="font-display font-bold text-sm uppercase tracking-wide mt-10 mb-4">Your subscriptions</h2>
                {digestSubscriptions.length === 0 && (
                  <p className="text-muted text-sm">No subscriptions yet for this email.</p>
                )}
                <div className="space-y-3 max-w-xl">
                  {digestSubscriptions.map((d) => (
                    <div key={d.id} className="box-card p-5">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="font-display font-bold text-sm">{d.topic}</p>
                          <p className="text-placeholder text-xs mt-1">
                            {freqLabel(d.frequency)} · {dayLabel(d.day_of_week)}s · {hourLabel(d.hour)} {tzLabel(d.timezone)}
                            {" · "}{d.last_sent_at ? "Last sent " + d.last_sent_at.slice(0, 10) : "Not sent yet"}
                          </p>
                        </div>
                        <div className="flex gap-2 shrink-0">
                          <button
                            onClick={() => sendDigestNow(d.id)}
                            disabled={digestActionLoading === d.id}
                            className="px-3 py-1.5 rounded-full text-xs font-display font-bold border-[1.5px] border-ink text-ink hover:border-[2.5px] hover:tracking-wide transition-all disabled:opacity-50"
                          >
                            {digestActionLoading === d.id ? "..." : "Send now"}
                          </button>
                          <button
                            onClick={() => unsubscribeDigest(d.id)}
                            className="px-3 py-1.5 rounded-full text-xs font-display font-bold border-[1.5px] border-ink text-ink hover:border-[2.5px] hover:tracking-wide transition-all"
                          >
                            Unsubscribe
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <h2 className="font-display font-bold text-sm uppercase tracking-wide mt-10 mb-4">Digest history</h2>
                {digestHistory.length === 0 && (
                  <p className="text-muted text-sm">No digests sent yet.</p>
                )}
                {digestHistory.length > 0 && (
                  <div className="box-card p-5 max-w-xl">
                    {digestHistory.map((log, i) => (
                      <div
                        key={log.id}
                        className={"flex justify-between items-center py-2.5 text-sm " + (i < digestHistory.length - 1 ? "border-b border-boxBorder/60" : "")}
                      >
                        <span className="font-display font-bold">{log.topic}</span>
                        <span className="text-placeholder text-xs">{log.sent_at.slice(0, 10)} · {log.source_count} sources</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </>
        )}

      </div>
    </div>
  );
}
