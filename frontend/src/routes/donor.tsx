import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowLeft, Droplet, Users, Activity } from "lucide-react";
import { getDonors, getRequests, getDashboardStats, type Donor, type BloodRequest, type DashboardStats } from "@/lib/api";

export const Route = createFileRoute("/donor")({
  head: () => ({
    meta: [
      { title: "Donor directory — LifeDrop" },
      { name: "description", content: "Browse registered blood donors in Karachi." },
    ],
  }),
  component: DonorPortal,
  errorComponent: ({ error }) => <div className="p-8">Error: {error.message}</div>,
});

const AREAS = ["Clifton","DHA","Gulshan-e-Iqbal","Nazimabad","North Karachi","Saddar","Korangi","Malir","Lyari"];
const BLOOD_GROUPS = ["A+","A-","B+","B-","AB+","AB-","O+","O-"];

const INTENT_CLS: Record<string, string> = {
  accepted:    "text-green-400",
  rejected:    "text-muted-foreground",
  unavailable: "text-yellow-400",
};

function DonorPortal() {
  const [donors, setDonors] = useState<Donor[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [requests, setRequests] = useState<BloodRequest[]>([]);
  const [filterBg, setFilterBg] = useState("");
  const [filterArea, setFilterArea] = useState("");
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState<Donor | null>(null);

  useEffect(() => {
    Promise.all([
      getDonors({ limit: 200 }),
      getDashboardStats(),
      getRequests(),
    ]).then(([d, s, r]) => {
      setDonors(d);
      setStats(s);
      setRequests(r);
    }).finally(() => setLoading(false));
  }, []);

  const filtered = donors.filter((d) => {
    if (filterBg && d.blood_group !== filterBg) return false;
    if (filterArea && d.area !== filterArea) return false;
    return true;
  });

  return (
    <main className="min-h-screen px-4 py-6 max-w-4xl mx-auto">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      <header className="flex items-center gap-3 mb-6">
        <span className="w-10 h-10 rounded-full blood-drop grid place-items-center">
          <Droplet className="w-4 h-4 text-primary-foreground" fill="currentColor" />
        </span>
        <div>
          <h1 className="font-display text-3xl">Donor directory</h1>
          <p className="text-sm text-muted-foreground">Registered Karachi donors · AI-matched for each emergency</p>
        </div>
      </header>

      {/* Stats strip */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: "Total donors",    value: stats.total_donors },
            { label: "Eligible now",    value: stats.eligible_donors },
            { label: "Requests sent",   value: stats.total_requests },
            { label: "Fulfilled",       value: `${Math.round(stats.fulfillment_rate * 100)}%` },
          ].map((s) => (
            <div key={s.label} className="glass-card rounded-2xl p-4 text-center">
              <div className="font-display text-3xl text-primary">{s.value}</div>
              <div className="text-xs text-muted-foreground mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {active ? (
        <DonorDetail
          donor={active}
          requests={requests}
          onBack={() => setActive(null)}
        />
      ) : (
        <>
          {/* Filters */}
          <div className="flex flex-wrap gap-2 mb-4">
            <select
              value={filterBg}
              onChange={(e) => setFilterBg(e.target.value)}
              className="text-sm px-3 py-1.5 rounded-full border border-border bg-card focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="">All blood groups</option>
              {BLOOD_GROUPS.map((bg) => <option key={bg}>{bg}</option>)}
            </select>
            <select
              value={filterArea}
              onChange={(e) => setFilterArea(e.target.value)}
              className="text-sm px-3 py-1.5 rounded-full border border-border bg-card focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="">All areas</option>
              {AREAS.map((a) => <option key={a}>{a}</option>)}
            </select>
            <span className="text-xs text-muted-foreground self-center ml-1">
              {loading ? "Loading…" : `${filtered.length} donors`}
            </span>
          </div>

          {/* Donor grid */}
          <div className="grid sm:grid-cols-2 gap-3">
            {filtered.map((d) => (
              <button
                key={d.id}
                onClick={() => setActive(d)}
                className="text-left glass-card rounded-2xl p-4 hover:border-primary/40 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="font-medium">{d.name}</div>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                    {d.blood_group}
                  </span>
                </div>
                <div className="text-sm text-muted-foreground mt-1">{d.area}</div>
                <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                  <span className={d.health_status === "available" ? "text-green-400" : "text-red-400"}>
                    ● {d.health_status}
                  </span>
                  <span><Activity className="inline w-3 h-3 mr-0.5" />{Math.round(d.response_rate * 100)}% response</span>
                  <span><Users className="inline w-3 h-3 mr-0.5" />{d.total_donations} donations</span>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </main>
  );
}

function DonorDetail({ donor, requests, onBack }: { donor: Donor; requests: BloodRequest[]; onBack: () => void }) {
  // Find waves this donor was part of
  const involved = requests.filter((r) =>
    r.waves?.some((w) => w.donor_ids?.includes(donor.id))
  );

  return (
    <div>
      <button onClick={onBack} className="text-sm text-muted-foreground hover:text-foreground mb-4 flex items-center gap-1">
        <ArrowLeft className="w-3.5 h-3.5" /> All donors
      </button>

      {/* Donor card */}
      <div className="glass-card rounded-2xl p-5 mb-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-display text-2xl">{donor.name}</h2>
            <div className="text-sm text-muted-foreground mt-1">{donor.area} · {donor.phone}</div>
          </div>
          <span className="text-lg font-bold text-primary">{donor.blood_group}</span>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="text-center">
            <div className="font-display text-2xl text-primary">{donor.total_donations}</div>
            <div className="text-xs text-muted-foreground">Donations</div>
          </div>
          <div className="text-center">
            <div className="font-display text-2xl text-primary">{Math.round(donor.response_rate * 100)}%</div>
            <div className="text-xs text-muted-foreground">Response rate</div>
          </div>
          <div className="text-center">
            <div className={`font-display text-xl ${donor.health_status === "available" ? "text-green-400" : "text-red-400"}`}>
              {donor.health_status === "available" ? "Ready" : "Unavailable"}
            </div>
            <div className="text-xs text-muted-foreground">Status</div>
          </div>
        </div>
        {donor.last_donation_date && (
          <div className="text-xs text-muted-foreground mt-3">
            Last donation: {new Date(donor.last_donation_date).toLocaleDateString()}
          </div>
        )}
      </div>

      {/* Recent request involvement */}
      <div className="text-xs uppercase tracking-wider text-muted-foreground mb-3">Recent requests</div>
      {involved.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">Not yet contacted for any requests.</p>
      ) : (
        <div className="space-y-3">
          {involved.map((req) => {
            // Find this donor's response in the request's waves
            const response = req.waves
              ?.flatMap((w) => w.responses ?? [])
              .find((r) => r.donor_id === donor.id);

            return (
              <div key={req.id} className="glass-card rounded-2xl p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-xs text-primary uppercase tracking-wider">
                      {req.blood_group} · {req.units_needed} unit{req.units_needed > 1 ? "s" : ""}
                    </div>
                    <div className="font-medium mt-0.5">{req.hospital_name}</div>
                    <div className="text-xs text-muted-foreground">{req.hospital_area} · {req.urgency_level} urgency</div>
                  </div>
                  {response && (
                    <span className={`shrink-0 text-xs font-medium ${INTENT_CLS[response.intent] ?? "text-muted-foreground"}`}>
                      {response.intent}
                    </span>
                  )}
                </div>
                {response && (
                  <div className="text-xs text-muted-foreground mt-2 italic">"{response.response_text}"</div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
