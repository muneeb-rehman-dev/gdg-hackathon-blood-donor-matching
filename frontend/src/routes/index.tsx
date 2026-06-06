import { createFileRoute, Link } from "@tanstack/react-router";
import { Droplet, MessageCircleHeart, HeartHandshake } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "LifeDrop — Find blood donors in minutes" },
      { name: "description", content: "Chat with LifeDrop to request blood. We match and notify the 5 nearest compatible donors instantly." },
      { property: "og:title", content: "LifeDrop — Find blood donors in minutes" },
      { property: "og:description", content: "Chat-based blood seeker that notifies the 5 nearest compatible donors instantly." },
    ],
  }),
  component: Home,
});

function Home() {
  return (
    <main className="min-h-screen px-6 py-10 md:py-20 max-w-6xl mx-auto">
      <header className="flex items-center justify-between mb-16">
        <div className="flex items-center gap-2">
          <span className="w-9 h-9 rounded-full blood-drop grid place-items-center shadow-lg shadow-primary/30">
            <Droplet className="w-4 h-4 text-primary-foreground" fill="currentColor" />
          </span>
          <span className="font-display text-2xl">LifeDrop</span>
        </div>
        <Link to="/donor" className="text-sm text-muted-foreground hover:text-foreground transition">
          Donor portal →
        </Link>
      </header>

      <section className="text-center max-w-3xl mx-auto">
        <p className="inline-block text-xs uppercase tracking-[0.2em] text-primary/80 mb-6 px-3 py-1 rounded-full border border-primary/20 bg-primary/5">
          Every minute matters
        </p>
        <h1 className="font-display text-5xl md:text-7xl leading-[1.05] mb-6">
          A drop of urgency,<br/>
          <span className="italic text-primary">a chat away</span> from help.
        </h1>
        <p className="text-lg text-muted-foreground mb-10 max-w-xl mx-auto">
          Tell us what you need. We'll quietly ping the five nearest compatible donors and surface who's coming.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/chat"
            className="group inline-flex items-center gap-2 px-7 py-4 rounded-full bg-primary text-primary-foreground shadow-xl shadow-primary/30 hover:shadow-primary/50 hover:-translate-y-0.5 transition"
          >
            <MessageCircleHeart className="w-5 h-5" />
            <span className="font-medium">Request blood now</span>
          </Link>
          <Link
            to="/donor"
            className="inline-flex items-center gap-2 px-7 py-4 rounded-full border border-border bg-card/80 hover:bg-accent transition"
          >
            <HeartHandshake className="w-5 h-5 text-primary" />
            <span className="font-medium">I want to donate</span>
          </Link>
        </div>
      </section>

      <section className="mt-28 grid md:grid-cols-3 gap-6">
        {[
          { n: "01", t: "Chat your need", d: "Bottles, blood group, hospital, when. No forms. Just chat." },
          { n: "02", t: "We match the 5 nearest", d: "Compatible blood group, sorted by distance to your hospital." },
          { n: "03", t: "Live responses", d: "Donor confirmations appear right inside the chat as they happen." },
        ].map((s) => (
          <div key={s.n} className="glass-card rounded-2xl p-7">
            <div className="font-display text-3xl text-primary mb-2">{s.n}</div>
            <div className="font-medium text-lg mb-1">{s.t}</div>
            <p className="text-sm text-muted-foreground">{s.d}</p>
          </div>
        ))}
      </section>

      <footer className="text-center text-xs text-muted-foreground mt-24">
        Demo app · Sample donor directory · Not a medical service
      </footer>
    </main>
  );
}
