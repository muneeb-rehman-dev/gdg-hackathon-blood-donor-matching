import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Droplet, Send, ArrowLeft, Loader2 } from "lucide-react";
import { postChat, WS_URL, getOrCreateSessionId, type WSEvent } from "@/lib/api";

export const Route = createFileRoute("/chat")({
  head: () => ({
    meta: [
      { title: "Request blood — LifeDrop" },
      { name: "description", content: "Chat with LifeDrop AI to request blood and reach the nearest compatible donors." },
    ],
  }),
  component: ChatPage,
  errorComponent: ({ error }) => <div className="p-8">Something went wrong: {error.message}</div>,
});

type Msg =
  | { from: "bot" | "user"; text: string }
  | { from: "event"; event: WSEvent };

const HINT = `Try: "Emergency! Need 2 units of O+ at Aga Khan Hospital in Saddar"`;

const INTENT_STYLE: Record<string, { label: string; cls: string }> = {
  accepted:    { label: "Accepted ✓",   cls: "bg-green-500/15 text-green-400 border-green-500/30" },
  rejected:    { label: "Declined",      cls: "bg-muted text-muted-foreground border-border" },
  unavailable: { label: "Unavailable",   cls: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30" },
  no_response: { label: "No response",   cls: "bg-muted text-muted-foreground border-border" },
};

function ChatPage() {
  const router = useRouter();
  const sessionId = useRef(getOrCreateSessionId());
  const [messages, setMessages] = useState<Msg[]>([
    { from: "bot", text: "Hi! I'm LifeDrop AI. Describe the blood request and I'll find donors immediately.\n\n" + HINT },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [wsEvents, setWsEvents] = useState<WSEvent[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, wsEvents]);

  // Connect WebSocket once we have a requestId
  useEffect(() => {
    if (!requestId) return;
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try {
        const ev: WSEvent = JSON.parse(e.data);
        if (ev.request_id !== requestId) return;
        setWsEvents((prev) => [...prev, ev]);
        setMessages((prev) => [...prev, { from: "event", event: ev }]);
      } catch {}
    };

    ws.onerror = () => {
      setMessages((prev) => [
        ...prev,
        { from: "bot", text: "Live updates unavailable — make sure the backend server is running." },
      ]);
    };

    // Keep connection alive with periodic pings
    const ping = setInterval(() => { if (ws.readyState === WebSocket.OPEN) ws.send("ping"); }, 20000);

    return () => { clearInterval(ping); ws.close(); };
  }, [requestId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { from: "user", text }]);
    setLoading(true);

    try {
      const res = await postChat(sessionId.current, text);
      setMessages((prev) => [...prev, { from: "bot", text: res.bot_reply }]);

      if (res.status === "outreach_started" && res.request_id) {
        setRequestId(res.request_id);
        setMessages((prev) => [
          ...prev,
          { from: "bot", text: "Donor outreach started! Responses will appear below as they come in 👇" },
        ]);
      }

      if (res.needs_clarification && res.clarification_questions.length > 0) {
        const qs = res.clarification_questions.map((q, i) => `${i + 1}. ${q}`).join("\n");
        setMessages((prev) => [...prev, { from: "bot", text: qs }]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { from: "bot", text: "Sorry, couldn't reach the server. Make sure the backend is running on port 8000." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function startNew() {
    wsRef.current?.close();
    setMessages([{ from: "bot", text: "Hi! I'm LifeDrop AI. Describe the blood request and I'll find donors immediately.\n\n" + HINT }]);
    setInput("");
    setRequestId(null);
    setWsEvents([]);
    sessionId.current = crypto.randomUUID();
    router.invalidate();
  }

  return (
    <main className="min-h-screen px-4 py-6 max-w-2xl mx-auto flex flex-col">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      <div className="glass-card rounded-3xl flex-1 flex flex-col overflow-hidden shadow-xl">
        {/* Header */}
        <div className="flex items-center gap-3 p-5 border-b border-border">
          <span className="w-10 h-10 rounded-full blood-drop grid place-items-center">
            <Droplet className="w-4 h-4 text-primary-foreground" fill="currentColor" />
          </span>
          <div>
            <div className="font-display text-xl leading-none">LifeDrop AI</div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className={`w-1.5 h-1.5 rounded-full ${requestId ? "bg-green-400 animate-pulse" : "bg-muted-foreground"}`} />
              <span className="text-xs text-muted-foreground">
                {requestId ? "Live · outreach in progress" : "Ready"}
              </span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 space-y-3 min-h-[420px] max-h-[60vh]">
          {messages.map((m, i) => {
            if (m.from === "event") return <EventCard key={i} event={m.event} />;
            return (
              <div key={i} className={`flex ${m.from === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[82%] px-4 py-2.5 rounded-2xl text-[15px] leading-snug whitespace-pre-wrap ${
                  m.from === "user"
                    ? "bg-primary text-primary-foreground rounded-br-sm"
                    : "bg-accent text-accent-foreground rounded-bl-sm"
                }`}>
                  {m.text}
                </div>
              </div>
            );
          })}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-accent text-accent-foreground px-4 py-2.5 rounded-2xl rounded-bl-sm flex items-center gap-2 text-sm">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Thinking…
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-border flex gap-2 bg-card/60">
          <input
            autoFocus
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={requestId ? "Ask a follow-up or start a new request…" : "Describe the blood request…"}
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-full bg-background border border-input focus:outline-none focus:ring-2 focus:ring-ring text-[15px] disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="w-12 h-12 rounded-full bg-primary text-primary-foreground grid place-items-center disabled:opacity-40 hover:shadow-lg hover:shadow-primary/30 transition"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </form>

        {requestId && (
          <div className="px-4 pb-3 text-center text-xs text-muted-foreground">
            Live · Donor updates appear automatically. Keep this window open.
          </div>
        )}
      </div>

      <button
        onClick={startNew}
        className="text-xs text-muted-foreground hover:text-foreground mt-4 self-center"
      >
        Start a new request
      </button>
    </main>
  );
}

function EventCard({ event }: { event: WSEvent }) {
  const { event: type, wave_number, data } = event;

  if (type === "wave_started") {
    return (
      <div className="mx-auto text-center py-1">
        <span className="text-xs px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20">
          Wave {wave_number} started · contacting {data.donor_count as number} donors
        </span>
      </div>
    );
  }

  if (type === "donor_response") {
    const donor = data.donor as { name: string; blood_group: string; area: string; distance_km: number };
    const intent = data.intent as string;
    const style = INTENT_STYLE[intent] ?? INTENT_STYLE.no_response;
    return (
      <div className="bg-card border border-border rounded-2xl p-4 flex items-center justify-between gap-3 animate-in slide-in-from-bottom-2 duration-300">
        <div>
          <div className="font-medium text-sm">
            {donor.name} <span className="text-primary">· {donor.blood_group}</span>
          </div>
          <div className="text-xs text-muted-foreground mt-0.5">
            {donor.area} · {donor.distance_km.toFixed(1)} km away
          </div>
          <div className="text-xs text-muted-foreground mt-1 italic">"{data.response_text as string}"</div>
        </div>
        <span className={`shrink-0 text-xs px-3 py-1 rounded-full border ${style.cls}`}>{style.label}</span>
      </div>
    );
  }

  if (type === "wave_completed") {
    const d = data as { accepted: number; rejected: number; unavailable: number };
    return (
      <div className="mx-auto text-center py-1">
        <span className="text-xs px-3 py-1 rounded-full bg-accent text-accent-foreground border border-border">
          Wave {wave_number} done · ✓ {d.accepted} accepted · ✗ {d.rejected} declined · ○ {d.unavailable} unavailable
        </span>
      </div>
    );
  }

  if (type === "request_fulfilled") {
    return (
      <div className="bg-green-500/10 border border-green-500/30 rounded-2xl p-4 text-center">
        <div className="text-green-400 font-medium">Request fulfilled!</div>
        <div className="text-xs text-muted-foreground mt-1">
          {data.confirmed_donors as number} donor{(data.confirmed_donors as number) > 1 ? "s" : ""} confirmed · {data.total_waves as number} wave{(data.total_waves as number) > 1 ? "s" : ""}
        </div>
      </div>
    );
  }

  if (type === "request_failed") {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 text-center">
        <div className="text-red-400 font-medium">Could not fulfil request</div>
        <div className="text-xs text-muted-foreground mt-1">
          Only {data.confirmed_donors as number} donor{(data.confirmed_donors as number) !== 1 ? "s" : ""} confirmed after {data.total_waves as number} waves. Please try again or contact a blood bank.
        </div>
      </div>
    );
  }

  if (type === "status_update") {
    return (
      <div className="mx-auto text-center py-1">
        <span className="text-xs text-muted-foreground italic">{data.message as string}</span>
      </div>
    );
  }

  return null;
}
