import { useEffect, useMemo, useRef, useState } from "react";
import { extractContent, sendMessageStream } from "./api";
import { motion, AnimatePresence } from "framer-motion";

// â”€â”€â”€ Animation Variants â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, y: -16, transition: { duration: 0.28 } }
};
const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.35 } },
  exit: { opacity: 0, transition: { duration: 0.22 } }
};
const popIn = {
  initial: { opacity: 0, scale: 0.94 },
  animate: { opacity: 1, scale: 1, transition: { duration: 0.42, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, scale: 0.96, transition: { duration: 0.22 } }
};
const stagger = { animate: { transition: { staggerChildren: 0.09 } } };

// â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function getErrorMessage(error) {
  return error?.response?.data?.detail || error?.message || "Something went wrong. Please try again.";
}
function platformFromUrl(url) {
  const v = url.toLowerCase();
  if (v.includes("youtube.com") || v.includes("youtu.be")) return "YouTube";
  if (v.includes("instagram.com")) return "Instagram";
  return "Auto detect";
}
function formatMetric(value) {
  if (value === null || value === undefined || value === "") return "N/A";
  if (typeof value === "number")
    return Intl.NumberFormat("en", { notation: value >= 10000 ? "compact" : "standard" }).format(value);
  return String(value);
}
function formatDuration(seconds) {
  if (!seconds) return "N/A";
  const m = Math.floor(seconds / 60), s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}
function formatEngagementRate(value) {
  if (value === null || value === undefined || value === "") return "N/A";
  return `${value}%`;
}

// â”€â”€â”€ Icons â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const PlatformIcon = ({ platform, size = 16 }) => {
  if (platform === "YouTube") return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="#FF0000">
      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.376.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.376-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
    </svg>
  );
  if (platform === "Instagram") return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <defs>
        <linearGradient id="igG" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FCAF45"/>
          <stop offset="50%" stopColor="#E4405F"/>
          <stop offset="100%" stopColor="#833AB4"/>
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="20" height="20" rx="5" fill="url(#igG)"/>
      <circle cx="12" cy="12" r="4" fill="none" stroke="white" strokeWidth="1.8"/>
      <circle cx="17.5" cy="6.5" r="1.2" fill="white"/>
    </svg>
  );
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="2" y="2" width="20" height="20" rx="4"/><circle cx="12" cy="12" r="4"/>
    </svg>
  );
};

const SparkleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
    <path d="M12 2L14.09 8.26L20 9L15.47 13.14L16.97 19L12 15.77L7.03 19L8.53 13.14L4 9L9.91 8.26L12 2Z"/>
  </svg>
);
const SendIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);
const CloseIcon = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);
const EyeIcon = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>;
const HeartIcon = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>;
const ChatBubbleIcon = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>;

// â”€â”€â”€ RAF-based count-up (smooth easing) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function useCountUp(target, duration = 950) {
  const [display, setDisplay] = useState("-");
  useEffect(() => {
    if (target === "N/A" || target === null || target === undefined) { setDisplay("N/A"); return; }
    const num = typeof target === "number" ? target : parseInt(target) || 0;
    if (num === 0) { setDisplay(formatMetric(0)); return; }
    let startTime = null;
    const step = (ts) => {
      if (!startTime) startTime = ts;
      const p = Math.min((ts - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(formatMetric(Math.floor(eased * num)));
      if (p < 1) requestAnimationFrame(step);
      else setDisplay(formatMetric(num));
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return display;
}

// â”€â”€â”€ Metric Tile (sidebar column) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const MetricTile = ({ emoji, label, value, accent = "#2563EB" }) => {
  const display = useCountUp(value);

  return (
    <motion.div
      variants={popIn}
      style={{
        background: "linear-gradient(160deg,#0f1729 0%,#0a0f1e 100%)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: "18px",
        padding: "20px 22px",
        display: "flex",
        alignItems: "center",
        gap: "16px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at left center,${accent}18 0%,transparent 60%)`,
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          width: "44px",
          height: "44px",
          borderRadius: "12px",
          flexShrink: 0,
          background: `${accent}18`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "22px",
          position: "relative",
        }}
      >
        {emoji}
      </div>

      <div style={{ position: "relative" }}>
        <div
          style={{
            fontSize: "10px",
            color: "#64748B",
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            fontWeight: 600,
            marginBottom: "4px",
          }}
        >
          {label}
        </div>

        <div
          style={{
            fontSize: "28px",
            fontWeight: 700,
            color: "#F1F5F9",
            fontFamily: "'DM Mono','Fira Code',monospace",
            letterSpacing: "-0.02em",
            lineHeight: 1,
          }}
        >
          {display}
        </div>
      </div>
    </motion.div>
  );
};

// â”€â”€â”€ Video Card (with glow-border hover from original) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const VideoCard = ({ label, platform, title, channel, metrics, thumbnail, onViewTranscript, onViewMetrics }) => {
  const [imgErr, setImgErr] = useState(false);
  const [hovered, setHovered] = useState(false);

  return (
    <motion.div
      variants={popIn}
      onHoverStart={() => setHovered(true)}
      onHoverEnd={() => setHovered(false)}
      whileHover={{ y: -5, transition: { duration: 0.22, ease: "easeOut" } }}
      style={{ position: "relative", borderRadius: "22px", overflow: "hidden" }}
    >
      {/* Glow gradient border (from original doc3) */}
      <div style={{
        position: "absolute", inset: 0, borderRadius: "22px", padding: "1px",
        background: hovered ? "linear-gradient(135deg,#2563EB,#7C3AED)" : "linear-gradient(135deg,rgba(37,99,235,0.18),rgba(30,58,138,0.18))",
        transition: "background 0.35s ease",
        WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
        WebkitMaskComposite: "xor",
        maskComposite: "exclude",
        pointerEvents: "none", zIndex: 2,
      }}/>

      <div style={{
        background: "linear-gradient(160deg,#111827 0%,#0c1322 100%)",
        borderRadius: "22px", overflow: "hidden",
      }}>
        {/* Thumbnail */}
        <div style={{ position: "relative", height: "158px", background: "#080d1a", overflow: "hidden" }}>
          {!imgErr && thumbnail ? (
            <img src={thumbnail} alt={title} onError={() => setImgErr(true)}
              style={{ width: "100%", height: "100%", objectFit: "cover", display: "block", transition: "transform 0.4s ease", transform: hovered ? "scale(1.04)" : "scale(1)" }}/>
          ) : (
            <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg,#0f1729,#0a0f1e)" }}>
              <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="1.2">
                <rect x="2" y="2" width="20" height="20" rx="3"/><path d="M10 8.5L15.5 12L10 15.5V8.5Z"/>
              </svg>
            </div>
          )}
          <div style={{
            position: "absolute", top: "11px", left: "11px",
            background: "rgba(0,0,0,0.72)", backdropFilter: "blur(8px)",
            borderRadius: "40px", padding: "4px 10px",
            display: "flex", alignItems: "center", gap: "6px",
            border: "1px solid rgba(255,255,255,0.1)",
            fontSize: "11px", fontWeight: 600, color: "#F1F5F9",
          }}>
            <PlatformIcon platform={platform} size={14}/> {platform}
          </div>
          <div style={{
            position: "absolute", top: "11px", right: "11px",
            background: "linear-gradient(135deg,#2563EB,#1e40af)",
            borderRadius: "40px", width: "26px", height: "26px",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "11px", fontWeight: 800, color: "white",
          }}>{label}</div>
        </div>

        {/* Body */}
        <div style={{ padding: "18px" }}>
          <div style={{ fontSize: "13px", fontWeight: 600, color: "#E2E8F0", lineHeight: 1.45, marginBottom: "5px", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
            {title || `Video ${label}`}
          </div>
          {channel && <div style={{ fontSize: "12px", color: "#64748B", marginBottom: "14px" }}>{channel}</div>}

          <div style={{ display: "flex", gap: "7px", marginBottom: "14px" }}>
            {[
              { icon: <EyeIcon/>, val: formatMetric(metrics?.views) },
              { icon: <HeartIcon/>, val: formatMetric(metrics?.likes) },
              { icon: <ChatBubbleIcon/>, val: formatMetric(metrics?.comments) },
            ].map((s, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: "5px", background: "rgba(255,255,255,0.04)", borderRadius: "7px", padding: "5px 8px", fontSize: "12px", color: "#94A3B8" }}>
                {s.icon} {s.val}
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button onClick={onViewTranscript} className="card-action-btn">Transcript</button>
            <button onClick={onViewMetrics} className="card-action-btn primary">Full Metrics</button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// â”€â”€â”€ Modal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const Modal = ({ isOpen, onClose, title, platform, children }) => {
  useEffect(() => {
    document.body.style.overflow = isOpen ? "hidden" : "unset";
    return () => { document.body.style.overflow = "unset"; };
  }, [isOpen]);
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div onClick={onClose} variants={fadeIn} initial="initial" animate="animate" exit="exit"
            style={{ position: "fixed", inset: 0, background: "rgba(2,4,14,0.88)", backdropFilter: "blur(14px)", zIndex: 1000 }}/>
          <motion.div variants={popIn} initial="initial" animate="animate" exit="exit" style={{
            position: "fixed", top: "50%", left: "50%", transform: "translate(-50%,-50%)",
            width: "min(88vw,1100px)", height: "80vh",
            background: "linear-gradient(160deg,#0f1729 0%,#090d1a 100%)",
            borderRadius: "28px",
            border: "1px solid rgba(255,255,255,0.07)",
            boxShadow: "0 40px 100px rgba(0,0,0,0.72),0 0 0 1px rgba(37,99,235,0.14)",
            zIndex: 1001, display: "flex", flexDirection: "column", overflow: "hidden",
          }}>
            <div style={{ padding: "22px 26px", borderBottom: "1px solid rgba(255,255,255,0.06)", display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(0,0,0,0.18)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span style={{ fontSize: "15px", fontWeight: 700, color: "#F1F5F9" }}>{title}</span>
                {platform && (
                  <span style={{ display: "flex", alignItems: "center", gap: "6px", background: "rgba(255,255,255,0.05)", borderRadius: "40px", padding: "3px 11px", fontSize: "11px", color: "#94A3B8", border: "1px solid rgba(255,255,255,0.08)" }}>
                    <PlatformIcon platform={platform} size={13}/> {platform}
                  </span>
                )}
              </div>
              <button onClick={onClose} className="modal-close-btn"><CloseIcon/></button>
            </div>
            <div style={{ flex: 1, overflowY: "auto", padding: "26px" }}>{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

// â”€â”€â”€ Transcript Modal Content â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const TranscriptModal = ({ transcript, source }) => {
  const paragraphs = transcript?.split("\n").filter(p => p.trim()) || [];
  return (
    <div>
      {source && (
        <div style={{ marginBottom: "18px" }}>
          {/* meta-badge from original */}
          <span style={{ fontSize: "11px", color: "#64748B", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "40px", padding: "3px 12px" }}>
            Source: {source}
          </span>
        </div>
      )}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {paragraphs.map((p, i) => (
          <div key={i} style={{ padding: "15px 18px", background: "rgba(255,255,255,0.025)", borderRadius: "12px", borderLeft: "3px solid #2563EB", fontSize: "14px", lineHeight: 1.78, color: "#CBD5E1" }}>
            {p.trim()}
          </div>
        ))}
        {paragraphs.length === 0 && (
          <div style={{ textAlign: "center", padding: "60px", color: "#64748B" }}>No transcript available.</div>
        )}
      </div>
    </div>
  );
};

// â”€â”€â”€ Metrics Modal Content â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const MetricsModal = ({ metrics, metadata }) => {
  const items = [
    { icon: "V", label: "Views", value: formatMetric(metrics?.views) },
    { icon: "L", label: "Likes", value: formatMetric(metrics?.likes) },
    { icon: "C", label: "Comments", value: formatMetric(metrics?.comments) },
    { icon: "T", label: "Duration", value: formatDuration(metrics?.duration_seconds) },
    { icon: "D", label: "Upload Date", value: formatMetric(metrics?.upload_date) },
    { icon: "%", label: "Engagement", value: formatEngagementRate(metrics?.engagement_rate) },
  ];
  const meta = [
    { label: "Channel", value: metadata?.channel || metrics?.channel },
    { label: "Follower Count", value: metrics?.follower_count },
    { label: "Platform", value: metadata?.platform || metrics?.platform },
    { label: "Category", value: metadata?.category || "Not specified" },
    { label: "Language", value: metadata?.language || "Not specified" },
  ].filter(m => m.value);
  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(175px,1fr))", gap: "13px", marginBottom: "28px" }}>
        {items.map((item, i) => (
          <div key={i} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "16px", padding: "18px", display: "flex", alignItems: "center", gap: "13px" }}>
            <span style={{ fontSize: "26px" }}>{item.icon}</span>
            <div>
              <div style={{ fontSize: "10px", color: "#64748B", textTransform: "uppercase", letterSpacing: "0.09em", marginBottom: "4px" }}>{item.label}</div>
              <div style={{ fontSize: "20px", fontWeight: 700, color: "#F1F5F9", fontFamily: "'DM Mono',monospace" }}>{item.value}</div>
            </div>
          </div>
        ))}
      </div>
      {meta.length > 0 && (
        <>
          <div style={{ fontSize: "11px", color: "#64748B", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "12px" }}>Video Information</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: "10px" }}>
            {meta.map((m, i) => (
              <div key={i} style={{ background: "rgba(255,255,255,0.03)", borderRadius: "13px", padding: "15px", textAlign: "center", border: "1px solid rgba(255,255,255,0.05)" }}>
                <div style={{ fontSize: "10px", color: "#64748B", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "6px" }}>{m.label}</div>
                <div style={{ fontSize: "13px", fontWeight: 600, color: "#CBD5E1" }}>{m.value}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// Assistant message
const CitationList = ({ citations = [] }) => {
  if (!citations.length) return null;

  return (
    <div className="assistant-citations">
      <div className="assistant-citations-title">Sources</div>
      {citations.map((citation, index) => (
        <div key={`${citation.video_id}-${citation.chunk_index}-${index}`} className="assistant-citation-card">
          <div className="assistant-citation-meta">
            Video {citation.video_id || "?"} - chunk {citation.chunk_index ?? "?"}
          </div>
          {citation.excerpt && (
            <div className="assistant-citation-excerpt">
              {citation.excerpt}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

function renderInline(text) {
  const parts = [];
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let lastIndex = 0;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    const token = match[0];
    if (token.startsWith("`")) {
      parts.push(<code key={parts.length}>{token.slice(1, -1)}</code>);
    } else if (token.startsWith("**")) {
      parts.push(<strong key={parts.length}>{token.slice(2, -2)}</strong>);
    } else {
      parts.push(<em key={parts.length}>{token.slice(1, -1)}</em>);
    }

    lastIndex = match.index + token.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

function parseAssistantBlocks(content) {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();

    if (!line) {
      index += 1;
      continue;
    }

    const heading = line.match(/^(#{2,4})\s+(.+)$/);
    if (heading) {
      blocks.push({ type: "heading", level: heading[1].length, text: heading[2] });
      index += 1;
      continue;
    }

    const tableLines = [];
    while (index < lines.length && lines[index].trim().startsWith("|") && lines[index].trim().endsWith("|")) {
      tableLines.push(lines[index].trim());
      index += 1;
    }
    if (tableLines.length >= 2) {
      const rows = tableLines
        .filter(row => !/^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|$/.test(row))
        .map(row => row.slice(1, -1).split("|").map(cell => cell.trim()));
      blocks.push({ type: "table", rows });
      continue;
    }

    const listMatch = line.match(/^((?:[-*])|\d+[.)])\s+(.+)$/);
    if (listMatch) {
      const ordered = /^\d/.test(listMatch[1]);
      const items = [];

      while (index < lines.length) {
        const current = lines[index].trim();
        const currentMatch = current.match(/^((?:[-*])|\d+[.)])\s+(.+)$/);
        if (!currentMatch || (/^\d/.test(currentMatch[1]) !== ordered)) break;
        items.push(currentMatch[2]);
        index += 1;
      }

      blocks.push({ type: ordered ? "ordered-list" : "list", items });
      continue;
    }

    const paragraph = [line];
    index += 1;

    while (index < lines.length) {
      const current = lines[index].trim();
      if (
        !current ||
        current.match(/^(#{2,4})\s+(.+)$/) ||
        current.match(/^((?:[-*])|\d+[.)])\s+(.+)$/) ||
        (current.startsWith("|") && current.endsWith("|"))
      ) {
        break;
      }
      paragraph.push(current);
      index += 1;
    }

    const text = paragraph.join(" ");
    const boldOnly = text.match(/^\*\*([^*]+)\*\*:?$/);
    blocks.push({
      type: boldOnly && text.length < 84 ? "subheading" : "paragraph",
      text: boldOnly ? boldOnly[1] : text
    });
  }

  return blocks;
}

const AssistantMessageContent = ({ content, citations }) => {
  const blocks = useMemo(() => parseAssistantBlocks(content || ""), [content]);

  return (
    <motion.div variants={fadeUp} initial="initial" animate="animate" className="assistant-message">
      <div className="assistant-avatar">
        <SparkleIcon/>
      </div>
      <div className="assistant-bubble">
        <div className="assistant-label">Auracle insight</div>
        {blocks.map((block, idx) => {
          if (block.type === "heading") {
            const Tag = block.level === 2 ? "h2" : "h3";
            return <Tag key={idx}>{renderInline(block.text)}</Tag>;
          }

          if (block.type === "subheading") {
            return <h4 key={idx}>{renderInline(block.text)}</h4>;
          }

          if (block.type === "list") {
            return (
              <ul key={idx}>
                {block.items.map((item, itemIndex) => (
                  <li key={itemIndex}>{renderInline(item)}</li>
                ))}
              </ul>
            );
          }

          if (block.type === "ordered-list") {
            return (
              <ol key={idx}>
                {block.items.map((item, itemIndex) => (
                  <li key={itemIndex}>{renderInline(item)}</li>
                ))}
              </ol>
            );
          }

          if (block.type === "table") {
            return (
              <div key={idx} className="assistant-table-wrap">
                <table>
                  <thead>
                    <tr>{block.rows[0]?.map((cell, cellIndex) => <th key={cellIndex}>{renderInline(cell)}</th>)}</tr>
                  </thead>
                  <tbody>
                    {block.rows.slice(1).map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {row.map((cell, cellIndex) => <td key={cellIndex}>{renderInline(cell)}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }

          return <p key={idx}>{renderInline(block.text)}</p>;
        })}
        {!blocks.length && <p className="assistant-streaming">Thinking...</p>}
        <CitationList citations={citations}/>
      </div>
    </motion.div>
  );
};
// Typing indicator
const TypingDots = () => (
  <div style={{ display: "flex", gap: "13px", marginBottom: "22px" }}>
    <div style={{ width: "33px", height: "33px", borderRadius: "11px", background: "linear-gradient(135deg,#2563EB,#1e40af)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
      <SparkleIcon/>
    </div>
    <div style={{ display: "flex", alignItems: "center", gap: "5px", paddingTop: "4px" }}>
      {[0, 0.22, 0.44].map((delay, i) => (
        <motion.span key={i}
          animate={{ opacity: [0.25, 1, 0.25], scale: [0.75, 1.15, 0.75] }}
          transition={{ repeat: Infinity, duration: 1.3, delay, ease: "easeInOut" }}
          style={{ width: "7px", height: "7px", background: "#2563EB", borderRadius: "50%", display: "block" }}
        />
      ))}
    </div>
  </div>
);

// Main app
export default function App() {
  const [videoAUrl, setVideoAUrl] = useState("");
  const [videoBUrl, setVideoBUrl] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [analysisResult, setAnalysisResult] = useState(null);
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [isExtracting, setIsExtracting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [modalState, setModalState] = useState({ isOpen: false, type: null, video: null });
  const chatInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const videoAData = analysisResult?.video_a_data || {};
  const videoBData = analysisResult?.video_b_data || {};
  const canAnalyze = useMemo(() => videoAUrl.trim() && videoBUrl.trim() && !isExtracting, [isExtracting, videoAUrl, videoBUrl]);
  const canSend = useMemo(() => sessionId && query.trim() && !isSending, [isSending, query, sessionId]);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, isSending]);

  async function handleAnalyze(event) {
    event.preventDefault(); setError(""); setIsExtracting(true);
    try {
      const result = await extractContent(videoAUrl.trim(), videoBUrl.trim());
      setAnalysisResult(result); setSessionId(result.session_id);
      setMessages([{ role: "assistant", content: "## Analysis Complete\n\nI've successfully analyzed both videos. Here's what I can help you with:\n\n- **Performance Comparison** - Compare views, engagement, and retention metrics\n- **Content Analysis** - Understand hooks, storytelling, and pacing differences\n- **Audience Insights** - Demographics and viewing patterns\n- **Actionable Recommendations** - Specific improvements for each video\n\nWhat would you like to explore first?" }]);
      setTimeout(() => chatInputRef.current?.focus(), 0);
    } catch (err) {
      setError(getErrorMessage(err)); setSessionId(""); setAnalysisResult(null); setMessages([]);
    } finally { setIsExtracting(false); }
  }

  async function handleSend(event, promptOverride = "") {
    event?.preventDefault?.();
    const q = (promptOverride || query).trim();
    if (!q || !sessionId) return;
    setError(""); setIsSending(true); setQuery("");
    setMessages(prev => [...prev, { role: "user", content: q }]);
    try {
      setMessages(prev => [...prev, { role: "assistant", content: "", citations: [] }]);

      await sendMessageStream(sessionId, q, {
        onToken: (token) => {
          setMessages(prev => {
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = {
              ...last,
              content: `${last.content || ""}${token}`
            };
            return next;
          });
        },
        onCitations: (citations) => {
          setMessages(prev => {
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = {
              ...last,
              citations
            };
            return next;
          });
        }
      });
    } catch (err) {
      const message = getErrorMessage(err);
      if (err?.response?.status === 404 && message === "Session not found.") {
        setSessionId(""); setAnalysisResult(null);
        setError("Session expired. Please analyze the videos again.");
      } else { setError(message); }
      setMessages(prev => [...prev, { role: "assistant", content: err?.response?.status === 404 ? "## Session Expired\n\nThe analysis session is no longer active. Please run the analysis again to continue." : "## Something went wrong\n\nI couldn't process that request. Please try again." }]);
    } finally { setIsSending(false); }
  }

  function handleChatKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (canSend) handleSend(e); }
  }
  function handlePrompt(p) {
    if (!sessionId || isSending) return;
    handleSend(null, p);
  }
  function handleResetAnalysis() { setSessionId(""); setAnalysisResult(null); setMessages([]); setQuery(""); setError(""); }
  function openTranscript(v) { setModalState({ isOpen: true, type: "transcript", video: v }); }
  function openMetrics(v) { setModalState({ isOpen: true, type: "metrics", video: v }); }
  function closeModal() { setModalState({ isOpen: false, type: null, video: null }); }

  const activeVideo = modalState.video === "A" ? videoAData : videoBData;

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700&family=Syne:wght@400;600;700;800&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #050916; font-family: Syne, 'Segoe UI', sans-serif; color: #F1F5F9; -webkit-font-smoothing: antialiased; }
        input, button { font-family: inherit; }
        .chatbot-panel,
        .chatbot-panel input,
        .chatbot-panel button {
          font-family: 'Inter', sans-serif;
        }

        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(37,99,235,0.38); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(37,99,235,0.62); }

        /* Shared input */
        .text-input {
          width: 100%; background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08); border-radius: 13px;
          padding: 13px 16px; color: #F1F5F9; font-size: 14px; outline: none;
          transition: border-color 0.2s, box-shadow 0.2s; font-family: inherit;
        }
        .text-input::placeholder { color: #475569; }
        .text-input:focus { border-color: rgba(37,99,235,0.65); box-shadow: 0 0 0 3px rgba(37,99,235,0.11); }
        .text-input:disabled { opacity: 0.45; cursor: not-allowed; }

        /* Glow card (top-line shimmer) */
        .glow-card {
          background: linear-gradient(160deg,rgba(15,23,41,0.92) 0%,rgba(9,13,26,0.96) 100%);
          border: 1px solid rgba(255,255,255,0.07); border-radius: 22px;
          backdrop-filter: blur(18px); position: relative; overflow: hidden;
        }
        .glow-card::before {
          content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
          background: linear-gradient(90deg,transparent 0%,rgba(37,99,235,0.55) 40%,rgba(96,165,250,0.3) 60%,transparent 100%);
        }

        /* Gradient text */
        .gradient-text {
          background: linear-gradient(135deg,#E2E8F0 0%,#94A3B8 60%,#60A5FA 100%);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
        }

        /* Buttons */
        .primary-btn {
          background: linear-gradient(135deg,#2563EB 0%,#1e40af 100%); border: none;
          border-radius: 13px; padding: 13px 26px; color: white;
          font-size: 14px; font-weight: 700; cursor: pointer;
          transition: all 0.2s; font-family: inherit;
          box-shadow: 0 4px 18px rgba(37,99,235,0.28);
        }
        .primary-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(37,99,235,0.42); }
        .primary-btn:disabled { opacity: 0.48; cursor: not-allowed; transform: none; }

        .secondary-btn {
          background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
          border-radius: 12px; padding: 9px 20px; color: #94A3B8;
          font-size: 13px; font-weight: 600; cursor: pointer;
          transition: all 0.2s; font-family: inherit;
        }
        .secondary-btn:hover { background: rgba(255,255,255,0.09); color: #E2E8F0; border-color: rgba(255,255,255,0.18); }

        /* Video card action buttons */
        .card-action-btn {
          flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
          border-radius: 9px; padding: 9px 0; color: #94A3B8;
          font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-family: inherit;
        }
        .card-action-btn:hover { background: rgba(255,255,255,0.1); color: #F1F5F9; border-color: rgba(255,255,255,0.15); }
        .card-action-btn.primary {
          background: linear-gradient(135deg,#2563EB,#1e40af); border: none; color: white;
        }
        .card-action-btn.primary:hover { opacity: 0.86; }

        /* Modal close */
        .modal-close-btn {
          background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
          border-radius: 9px; width: 34px; height: 34px;
          display: flex; align-items: center; justify-content: center;
          cursor: pointer; color: #64748B; transition: all 0.2s;
        }
        .modal-close-btn:hover { background: rgba(220,38,38,0.12); color: #DC2626; border-color: rgba(220,38,38,0.28); }

        /* Chip */
        .prompt-chip {
          background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
          border-radius: 40px; padding: 7px 16px; font-size: 12px;
          color: #94A3B8; cursor: pointer; transition: all 0.2s; font-family: inherit; font-weight: 600;
        }
        .prompt-chip:hover { background: rgba(37,99,235,0.12); border-color: rgba(37,99,235,0.4); color: #93C5FD; }

        /* Assistant response */
        .assistant-message {
          display: grid;
          grid-template-columns: 36px minmax(0, 1fr);
          gap: 13px;
          margin-bottom: 22px;
          align-items: start;
        }
        .assistant-avatar {
          width: 36px;
          height: 36px;
          border-radius: 12px;
          background: linear-gradient(135deg,#2563EB,#1e40af);
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 8px 24px rgba(37,99,235,0.28);
        }
        .assistant-bubble {
          min-width: 0;
          max-width: 920px;
          background: linear-gradient(160deg,rgba(15,23,42,0.82),rgba(8,13,27,0.92));
          border: 1px solid rgba(148,163,184,0.12);
          border-radius: 18px;
          border-top-left-radius: 8px;
          padding: 18px 20px 20px;
          box-shadow: 0 18px 44px rgba(0,0,0,0.24);
        }
        .assistant-label {
          display: inline-flex;
          align-items: center;
          margin-bottom: 9px;
          padding: 4px 9px;
          border-radius: 999px;
          background: rgba(37,99,235,0.12);
          border: 1px solid rgba(96,165,250,0.16);
          color: #93C5FD;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.12em;
          text-transform: uppercase;
        }
        .assistant-bubble h2,
        .assistant-bubble h3,
        .assistant-bubble h4,
        .assistant-bubble p {
          overflow-wrap: anywhere;
        }
        .assistant-bubble h2 {
          margin: 6px 0 12px;
          color: #F8FAFC;
          font-size: 19px;
          line-height: 1.28;
          font-weight: 800;
        }
        .assistant-bubble h3 {
          margin: 18px 0 8px;
          color: #BFDBFE;
          font-size: 15px;
          line-height: 1.35;
          font-weight: 800;
        }
        .assistant-bubble h4 {
          margin: 16px 0 7px;
          color: #E2E8F0;
          font-size: 13px;
          line-height: 1.35;
          font-weight: 800;
        }
        .assistant-bubble p {
          margin: 8px 0;
          color: #CBD5E1;
          font-size: 14px;
          line-height: 1.74;
        }
        .assistant-bubble strong { color: #F8FAFC; font-weight: 800; }
        .assistant-bubble em { color: #BAE6FD; font-style: normal; }
        .assistant-bubble code {
          background: rgba(37,99,235,0.15);
          border: 1px solid rgba(96,165,250,0.12);
          border-radius: 6px;
          padding: 2px 6px;
          font-family: 'DM Mono','Fira Code',monospace;
          font-size: 0.88em;
          color: #93C5FD;
        }
        .assistant-bubble ul,
        .assistant-bubble ol {
          margin: 10px 0 12px;
          padding: 0;
          display: grid;
          gap: 8px;
          list-style: none;
        }
        .assistant-bubble li {
          position: relative;
          padding: 10px 12px 10px 34px;
          border-radius: 12px;
          background: rgba(255,255,255,0.035);
          border: 1px solid rgba(255,255,255,0.055);
          color: #D7DEE9;
          font-size: 14px;
          line-height: 1.6;
        }
        .assistant-bubble ul li::before {
          content: '';
          position: absolute;
          left: 14px;
          top: 18px;
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #60A5FA;
          box-shadow: 0 0 0 4px rgba(96,165,250,0.12);
        }
        .assistant-bubble ol { counter-reset: response-step; }
        .assistant-bubble ol li { counter-increment: response-step; }
        .assistant-bubble ol li::before {
          content: counter(response-step);
          position: absolute;
          left: 10px;
          top: 10px;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: rgba(37,99,235,0.18);
          color: #93C5FD;
          font-size: 11px;
          font-weight: 800;
          display: grid;
          place-items: center;
        }
        .assistant-table-wrap {
          overflow-x: auto;
          margin: 13px 0;
          border: 1px solid rgba(148,163,184,0.12);
          border-radius: 14px;
        }
        .assistant-table-wrap table {
          width: 100%;
          border-collapse: collapse;
          min-width: 520px;
          font-size: 13px;
        }
        .assistant-table-wrap th {
          text-align: left;
          background: rgba(37,99,235,0.14);
          color: #BFDBFE;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          padding: 11px 13px;
        }
        .assistant-table-wrap td {
          color: #CBD5E1;
          padding: 12px 13px;
          border-top: 1px solid rgba(148,163,184,0.09);
          line-height: 1.5;
        }
        .assistant-citations {
          margin-top: 16px;
          padding-top: 14px;
          border-top: 1px solid rgba(148,163,184,0.12);
          display: grid;
          gap: 8px;
        }
        .assistant-citations-title {
          color: #64748B;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.12em;
          text-transform: uppercase;
        }
        .assistant-citation-card {
          background: rgba(15,23,42,0.68);
          border: 1px solid rgba(96,165,250,0.12);
          border-radius: 12px;
          padding: 11px 13px;
        }
        .assistant-citation-meta {
          color: #93C5FD;
          font-size: 11px;
          font-weight: 800;
          margin-bottom: 5px;
        }
        .assistant-citation-excerpt {
          color: #94A3B8;
          font-size: 12px;
          line-height: 1.58;
        }
        .assistant-streaming { color: #64748B; }

        /* Ambient */
        .orb { position: fixed; border-radius: 50%; pointer-events: none; filter: blur(90px); z-index: 0; }
        .noise { position: fixed; inset: 0; pointer-events: none; z-index: 0; opacity: 0.025;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
        }

        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>

      {/* Ambient depth layer */}
      <div className="noise"/>
      <div className="orb" style={{ width: "580px", height: "580px", top: "-180px", left: "-120px", background: "radial-gradient(circle,rgba(37,99,235,0.13) 0%,transparent 70%)" }}/>
      <div className="orb" style={{ width: "460px", height: "460px", bottom: "0", right: "-80px", background: "radial-gradient(circle,rgba(124,58,237,0.09) 0%,transparent 70%)" }}/>

      <div style={{ position: "relative", zIndex: 1, maxWidth: "1300px", margin: "0 auto", padding: "38px 26px 80px" }}>

        {/* â”€â”€ HERO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        <motion.header variants={stagger} initial="initial" animate="animate" style={{ textAlign: "center", marginBottom: "60px" }}>
          {/* Nav */}
          <motion.div variants={fadeUp} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "52px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "9px" }}>
              <div style={{ width: "30px", height: "30px", borderRadius: "9px", background: "linear-gradient(135deg,#2563EB,#7C3AED)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <SparkleIcon/>
              </div>
              <span style={{ fontSize: "17px", fontWeight: 800, letterSpacing: "-0.02em", color: "#F1F5F9" }}>Auralytix</span>
            </div>
            <div style={{
              display: "flex", alignItems: "center", gap: "7px",
              background: sessionId ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.04)",
              border: `1px solid ${sessionId ? "rgba(16,185,129,0.24)" : "rgba(255,255,255,0.08)"}`,
              borderRadius: "40px", padding: "5px 13px",
              fontSize: "11px", fontWeight: 600,
              color: sessionId ? "#34D399" : "#64748B",
            }}>
              <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: sessionId ? "#34D399" : "#64748B", display: "inline-block" }}/>
              {sessionId ? "Session Active" : "Ready"}
            </div>
          </motion.div>

          <motion.div variants={fadeUp} style={{ fontSize: "11px", letterSpacing: "0.2em", color: "#2563EB", fontWeight: 700, textTransform: "uppercase", marginBottom: "16px" }}>
            AI Social Media Intelligence
          </motion.div>
          <motion.h1 variants={fadeUp} className="gradient-text" style={{ fontSize: "clamp(34px,5.2vw,58px)", fontWeight: 800, lineHeight: 1.07, letterSpacing: "-0.03em", marginBottom: "20px" }}>
            Compare, Analyze &<br/>Understand Any Social Video
          </motion.h1>
          <motion.p
  variants={fadeUp}
  style={{
    fontSize: "15px",
    color: "#64748B",
    maxWidth: "500px",
    margin: "0 auto",
    lineHeight: 1.68,
    fontFamily: "Aptos, sans-serif"
  }}
>
  Extract insights, compare performance, and get AI-powered recommendations for YouTube and Instagram content.
</motion.p>
        </motion.header>

        {/* â”€â”€ ERROR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        <AnimatePresence>
          {error && (
            <motion.div variants={fadeUp} initial="initial" animate="animate" exit="exit"
              style={{ background: "rgba(220,38,38,0.1)", border: "1px solid rgba(220,38,38,0.3)", borderRadius: "14px", padding: "14px 18px", marginBottom: "28px", color: "#FCA5A5", fontSize: "13px" }}>
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* â”€â”€ INPUT / ANALYSIS TOGGLE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        <AnimatePresence mode="wait">
          {!analysisResult ? (
            /* â”€â”€ INPUT CARD â”€â”€ */
            <motion.div key="input" variants={fadeUp} initial="initial" animate="animate" exit="exit" style={{ marginBottom: "44px" }}>
              <div className="glow-card" style={{ padding: "32px" }}>
                <div style={{ fontSize: "11px", fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.11em", marginBottom: "24px" }}>
                  Enter Video URLs to Begin
                </div>
                <form onSubmit={handleAnalyze}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "18px", marginBottom: "20px" }}>
                    {[
                      { label: "A", val: videoAUrl, set: setVideoAUrl },
                      { label: "B", val: videoBUrl, set: setVideoBUrl },
                    ].map(({ label, val, set }) => (
                      <div key={label}>
                        <div style={{ fontSize: "11px", fontWeight: 700, color: "#475569", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "9px", display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ background: "linear-gradient(135deg,#2563EB,#1e40af)", color: "white", borderRadius: "5px", padding: "1px 8px", fontSize: "11px" }}>Video {label}</span> URL
                        </div>
                        <input type="url" className="text-input" value={val} onChange={e => set(e.target.value)} placeholder="YouTube or Instagram URL" disabled={isExtracting} required/>
                      </div>
                    ))}
                  </div>
                  <button type="submit" disabled={!canAnalyze} className="primary-btn" style={{ width: "100%", fontSize: "14px" }}>
                    {isExtracting ? (
                      <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "10px" }}>
                        <span style={{ width: "15px", height: "15px", border: "2px solid rgba(255,255,255,0.28)", borderTopColor: "white", borderRadius: "50%", display: "inline-block", animation: "spin 0.9s linear infinite" }}/>
                        Analyzing Videos...
                      </span>
                    ) : "Analyze Videos"}
                  </button>
                </form>
              </div>
            </motion.div>
          ) : (
            /* â”€â”€ ANALYSIS VIEW â”€â”€ */
            <motion.div key="analysis" variants={stagger} initial="initial" animate="animate" exit="exit" style={{ marginBottom: "28px" }}>
              {/* Row 1: 2 video cards â€” full width, equal columns */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "18px", marginBottom: "14px" }}>
                <VideoCard
                  label="A"
                  platform={analysisResult?.video_a_platform || platformFromUrl(videoAUrl)}
                  title={analysisResult?.video_a_title}
                  channel={videoAData.metrics?.channel}
                  metrics={videoAData.metrics}
                  thumbnail={videoAData.metadata?.thumbnail}
                  onViewTranscript={() => openTranscript("A")}
                  onViewMetrics={() => openMetrics("A")}
                />
                <VideoCard
                  label="B"
                  platform={analysisResult?.video_b_platform || platformFromUrl(videoBUrl)}
                  title={analysisResult?.video_b_title}
                  channel={videoBData.metrics?.channel}
                  metrics={videoBData.metrics}
                  thumbnail={videoBData.metadata?.thumbnail}
                  onViewTranscript={() => openTranscript("B")}
                  onViewMetrics={() => openMetrics("B")}
                />
              </div>

              {/* Row 2: 6 metric tiles in a single horizontal row */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(6,minmax(0,1fr))", gap: "14px", marginBottom: "14px" }}>
                <MetricTile emoji="V" label="Video A - Views" value={videoAData.metrics?.views}  accent="#2563EB"/>
                <MetricTile emoji="L" label="Video A - Likes" value={videoAData.metrics?.likes}  accent="#DC2626"/>
                <MetricTile emoji="%" label="Video A - Engagement" value={formatEngagementRate(videoAData.metrics?.engagement_rate)} accent="#0891B2"/>
                <MetricTile emoji="V" label="Video B - Views" value={videoBData.metrics?.views}  accent="#7C3AED"/>
                <MetricTile emoji="L" label="Video B - Likes" value={videoBData.metrics?.likes}  accent="#059669"/>
                <MetricTile emoji="%" label="Video B - Engagement" value={formatEngagementRate(videoBData.metrics?.engagement_rate)} accent="#CA8A04"/>
              </div>

              {/* Analysis deck */}
              <motion.div variants={fadeUp} className="glow-card" style={{ padding: "24px" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "14px", marginBottom: "20px" }}>
                  {[
                    { label: "Status",  value: "Extraction Complete", sub: "Both sources are loaded into the active session", color: "#34D399" },
                    { label: "Memory",  value: "Chat Grounded",        sub: "Follow-up replies can reference both videos",    color: "#60A5FA" },
                    { label: "Session", value: sessionId ? "Active" : "-", sub: sessionId ? `ID: ${sessionId.slice(0,14)}...` : "Start analysis to begin", color: "#A78BFA" },
                  ].map((c, i) => (
                    <div key={i} style={{ background: "rgba(255,255,255,0.025)", borderRadius: "16px", padding: "18px", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <div style={{ fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#475569", marginBottom: "7px" }}>{c.label}</div>
                      <div style={{ fontSize: "15px", fontWeight: 700, color: c.color, marginBottom: "5px" }}>{c.value}</div>
                      <div style={{ fontSize: "11px", color: "#475569", lineHeight: 1.5 }}>{c.sub}</div>
                    </div>
                  ))}
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                  <button className="secondary-btn" onClick={handleResetAnalysis}>New Analysis</button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* â”€â”€ CHAT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        <motion.div variants={fadeUp} initial="initial" animate="animate">
          <div className="glow-card chatbot-panel" style={{ overflow: "hidden" }}>
            {/* Header */}
            <div style={{ padding: "18px 22px", borderBottom: "1px solid rgba(255,255,255,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 700, color: "#E2E8F0" }}>Analysis Assistant</div>
                <div style={{ fontSize: "11px", color: "#475569", marginTop: "2px" }}>
                  {sessionId ? "Ask anything about Video A and Video B" : "Analyze videos above to start the conversation"}
                </div>
              </div>
              {sessionId && (
                <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "#34D399", background: "rgba(16,185,129,0.07)", border: "1px solid rgba(16,185,129,0.18)", borderRadius: "40px", padding: "4px 11px" }}>
                  <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#34D399", display: "inline-block" }}/>Live
                </div>
              )}
            </div>

            {/* Messages */}
            <div style={{ height: "420px", overflowY: "auto", padding: "22px" }}>
              {messages.length === 0 ? (
                <div style={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "10px" }}>
                  <div style={{ fontSize: "36px", opacity: 0.18 }}>*</div>
                  <div style={{ fontSize: "13px", color: "#374151" }}>The assistant will appear here after analysis</div>
                </div>
              ) : (
                messages.map((msg, i) =>
                  msg.role === "assistant"
                    ? <AssistantMessageContent key={i} content={msg.content} citations={msg.citations}/>
                    : (
                      <motion.div key={i} variants={fadeUp} initial="initial" animate="animate"
                        style={{ display: "flex", justifyContent: "flex-end", marginBottom: "20px" }}>
                        <div style={{ background: "linear-gradient(135deg,#2563EB,#1e40af)", borderRadius: "18px 18px 4px 18px", padding: "11px 17px", maxWidth: "68%", fontSize: "14px", lineHeight: 1.62, color: "white", boxShadow: "0 4px 14px rgba(37,99,235,0.28)" }}>
                          {msg.content}
                        </div>
                      </motion.div>
                    )
                )
              )}
              {isSending && <TypingDots/>}
              <div ref={messagesEndRef}/>
            </div>

            {/* Input row */}
            <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", padding: "14px 18px", display: "flex", gap: "10px", background: "rgba(0,0,0,0.14)" }}>
              <input
                ref={chatInputRef}
                className="text-input"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={handleChatKeyDown}
                disabled={!sessionId || isSending}
                placeholder={sessionId ? "Ask about performance, engagement, improvements..." : "Analyze videos first to chat"}
                style={{ flex: 1, borderRadius: "11px" }}
              />
              <button onClick={handleSend} disabled={!canSend} className="primary-btn"
                style={{ padding: "0 18px", borderRadius: "11px", display: "flex", alignItems: "center", gap: "7px", whiteSpace: "nowrap", fontSize: "13px" }}>
                <SendIcon/> Send
              </button>
            </div>
          </div>

          {/* Prompt chips */}
          <AnimatePresence>
            {sessionId && (
              <motion.div variants={fadeUp} initial="initial" animate="animate" exit="exit"
                style={{ display: "flex", gap: "9px", justifyContent: "center", marginTop: "18px", flexWrap: "wrap" }}>
                {["Compare the hooks", "Find audience differences", "Suggest improvements", "Which video performs better?"].map(p => (
                  <button key={p} type="button" className="prompt-chip" disabled={isSending} onClick={() => handlePrompt(p)}>{p}</button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* â”€â”€ MODALS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <Modal
        isOpen={modalState.isOpen}
        onClose={closeModal}
        title={`Video ${modalState.video} - ${modalState.type === "transcript" ? "Transcript" : "Full Metrics"}`}
        platform={modalState.video === "A" ? analysisResult?.video_a_platform : analysisResult?.video_b_platform}
      >
        {modalState.type === "transcript" && <TranscriptModal transcript={activeVideo?.transcript} source={activeVideo?.transcript_source}/>}
        {modalState.type === "metrics" && <MetricsModal metrics={activeVideo?.metrics} metadata={activeVideo?.metadata}/>}
      </Modal>
    </>
  );
}

