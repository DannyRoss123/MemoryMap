import { useEffect, useMemo, useState } from "react";

const API_BASE = "";
const TABS = ["dashboard", "clients", "updates", "calendar", "family"];

const defaultState = {
  profile: null,
  clients: [],
  updates: [],
  tasks: [],
  alerts: [],
  checkins: [],
};

function fetchJSON(path, caregiverId) {
  const headers = caregiverId
    ? {
        "X-Person-Id": String(caregiverId),
      }
    : {};
  return fetch(`${API_BASE}${path}`, { headers }).then((res) => {
    if (!res.ok) {
      return res.text().then((txt) => {
        throw new Error(txt || res.statusText);
      });
    }
    return res.json();
  });
}

const fmtDate = (value, opts = { month: "short", day: "numeric" }) => {
  if (!value) return "";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "";
  return dt.toLocaleDateString(undefined, opts);
};

const fmtDateTime = (value) => {
  if (!value) return "";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "";
  return dt.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

const initials = (name = "") =>
  name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("") || "?";

const formatRole = (value) =>
  value ? String(value).replace(/_/g, " ") : "caregiver";

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [caregiverId, setCaregiverId] = useState(() => {
    const stored = window.localStorage.getItem("caregiver_id");
    return stored || "1";
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(defaultState);

  useEffect(() => {
    window.localStorage.setItem("caregiver_id", caregiverId);
  }, [caregiverId]);

  useEffect(() => {
    let cancelled = false;
    async function loadAll() {
      setLoading(true);
      setError(null);
      try {
        const [profile, clients, updates, alerts] = await Promise.all([
          fetchJSON(`/caregivers/${caregiverId}/profile`, caregiverId),
          fetchJSON(`/caregivers/${caregiverId}/clients`, caregiverId),
          fetchJSON(`/caregivers/${caregiverId}/updates?limit=100`, caregiverId),
          fetchJSON(`/caregivers/${caregiverId}/alerts?limit=100`, caregiverId),
        ]);

        const clientIds = (clients || []).map(({ client }) => client.id);
        const taskPromises = clientIds.map((id) =>
          fetchJSON(`/users/${id}/tasks?status=open&limit=50`, caregiverId)
            .then((rows) => rows.map((row) => ({ ...row, user_id: id })))
            .catch(() => [])
        );
        const tasksResults = await Promise.all(taskPromises);
        const allTasks = tasksResults.flat();

        const checkins = (updates || [])
          .filter((item) => item.kind === "checkin")
          .map((item) => ({
            ...item,
            timestamp: item.timestamp || item.data?.created_at,
          }));

        if (!cancelled) {
          setData({
            profile,
            clients,
            updates: (updates || []).map((item) => ({
              ...item,
              timestamp: item.timestamp || item.data?.created_at || item.data?.occurred_at,
            })),
            tasks: allTasks,
            alerts: alerts || [],
            checkins,
          });
        }
      } catch (err) {
        if (!cancelled) {
          console.error(err);
          setError(err.message || "Failed to fetch caregiver data.");
          setData(defaultState);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadAll();
    return () => {
      cancelled = true;
    };
  }, [caregiverId]);

  const familyContacts = useMemo(() => {
    return data.clients.flatMap((entry) =>
      (entry.family || []).map((contact) => ({
        ...contact,
        client: entry.client,
      }))
    );
  }, [data.clients]);

  const handleChangeCaregiver = () => {
    const next = window.prompt("Enter caregiver ID", caregiverId);
    if (!next) return;
    const parsed = Number(next);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      alert("Invalid caregiver id");
      return;
    }
    setCaregiverId(String(parsed));
  };

  const resolveClientName = (userId) => {
    const match = data.clients.find((entry) => entry.client?.id === userId);
    return match?.client?.name || "";
  };

  return (
    <div className="layout">
      <aside>
        <div className="brand">Memory Map</div>
        <nav>
          {TABS.map((tab) => (
            <button
              key={tab}
              className="nav-btn"
              data-active={activeTab === tab}
              onClick={() => setActiveTab(tab)}
            >
              {tab === "dashboard"
                ? "Dashboard"
                : tab === "clients"
                ? "Clients"
                : tab === "updates"
                ? "Updates"
                : tab === "calendar"
                ? "Calendar"
                : "Family & Friends"}
            </button>
          ))}
        </nav>
        <div className="muted">
          Active caregiver ID: <strong>{caregiverId}</strong>
        </div>
        <button className="nav-btn" onClick={handleChangeCaregiver}>
          Switch Caregiver
        </button>
      </aside>
      <main>
        <Header profile={data.profile} loading={loading} />
        {error && <div className="card" style={{ color: "crimson" }}>{error}</div>}
        {activeTab === "dashboard" && (
          <DashboardSection
            updates={data.updates}
            alerts={data.alerts}
            tasks={data.tasks}
            checkins={data.checkins}
            resolveClientName={resolveClientName}
            familyContacts={familyContacts}
            onNavigate={setActiveTab}
          />
        )}
        {activeTab === "clients" && (
          <ClientsSection clients={data.clients} checkins={data.checkins} tasks={data.tasks} />
        )}
        {activeTab === "updates" && (
          <UpdatesSection updates={data.updates} resolveClientName={resolveClientName} />
        )}
        {activeTab === "calendar" && (
          <CalendarSection
            tasks={data.tasks}
            checkins={data.checkins}
            resolveClientName={resolveClientName}
          />
        )}
        {activeTab === "family" && (
          <FamilySection clients={data.clients} />
        )}
      </main>
    </div>
  );
}

const Header = ({ profile, loading }) => {
  const today = fmtDate(new Date(), {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  return (
    <section className="section" data-active="true" style={{ display: "flex" }}>
      <div className="topbar">
        <div className="info">
          <div className="title">Caregiver Dashboard</div>
          <div className="muted">{today}</div>
        </div>
        <div>
          <div className="badge">
            {loading ? "Loading caregiver..." : profile?.name || "Caregiver"}
          </div>
        </div>
      </div>
    </section>
  );
};

const DashboardSection = ({
  updates,
  tasks,
  alerts,
  checkins,
  resolveClientName,
  familyContacts,
  onNavigate,
}) => {
  const openTasks = tasks.length;
  const recentCheckins = useMemo(() => {
    const windowMs = 7 * 24 * 3600 * 1000;
    const now = Date.now();
    return checkins.filter((item) => {
      const ts = new Date(item.timestamp || item.data?.created_at || 0).getTime();
      return !Number.isNaN(ts) && now - ts <= windowMs;
    }).length;
  }, [checkins]);
  const unreadAlerts = alerts.filter((alert) => !alert.is_read).length;

  const topUpdate = updates[0];
  const prioritizedContacts = useMemo(() => {
    const prioritized = [
      ...familyContacts.filter((entry) => entry.notify),
      ...familyContacts.filter((entry) => !entry.notify),
    ];
    return prioritized.slice(0, 3);
  }, [familyContacts]);

  const handleViewUpdates = () => onNavigate("updates");
  const handleViewFamily = () => onNavigate("family");

  return (
    <>
      <div className="card-grid">
        <MetricCard title="Open Tasks" number={openTasks} sub="Tasks needing attention" />
        <MetricCard title="Recent Check-ins" number={recentCheckins} sub="Within the last 7 days" />
        <MetricCard title="Unread Alerts" number={unreadAlerts} sub="Awaiting review" />
      </div>
      <div className="split">
        <div className="card">
          <h3>Recent Update</h3>
          {!topUpdate ? (
            <div className="muted">No updates yet.</div>
          ) : (
            <>
              <div className="muted">
                {fmtDateTime(topUpdate.timestamp)} – {resolveClientName(topUpdate.user_id)}
              </div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>
                {topUpdate.title || topUpdate.kind}
              </div>
              <div style={{ fontSize: 14, color: "#111827" }}>
                {topUpdate.summary || ""}
              </div>
              <div className="actions">
                <button className="filter" data-active="true" onClick={handleViewUpdates}>
                  Open feed
                </button>
              </div>
            </>
          )}
        </div>
        <div className="card">
          <h3>Upcoming Tasks</h3>
          <div className="list">
            {tasks.length === 0 ? (
              <div className="empty">No open tasks.</div>
            ) : (
              tasks
                .slice()
                .sort(
                  (a, b) =>
                    (new Date(a.due_at || Infinity).getTime() || Infinity) -
                    (new Date(b.due_at || Infinity).getTime() || Infinity)
                )
                .slice(0, 4)
                .map((task) => (
                  <div className="item" key={task.id}>
                    <div className="line">
                      <span>{task.title}</span>
                      <StatusPill task={task} />
                    </div>
                    <div className="line muted">
                      <span>{resolveClientName(task.user_id) || "Client"}</span>
                      <span>{fmtDate(task.due_at, { month: "short", day: "numeric" }) || "No due date"}</span>
                    </div>
                  </div>
                ))
            )}
          </div>
        </div>
      </div>
      <div className="split">
        <div className="card">
          <h3>Recent Memories</h3>
          <div className="list">
            {updates.filter((item) => item.kind === "memory" && item.data?.image_url).slice(0, 3)
              .map((mem) => (
                <div className="item" key={mem.source_id}>
                  <div className="line">
                    <span>{mem.title || "Memory"}</span>
                    <span className="muted">{fmtDate(mem.timestamp)}</span>
                  </div>
                  <img src={mem.data.image_url} alt={mem.title || "Memory"} />
                  <div className="muted">{mem.summary || ""}</div>
                </div>
              ))}
            {updates.filter((item) => item.kind === "memory" && item.data?.image_url).length === 0 && (
              <div className="empty">Add memories to see them here.</div>
            )}
          </div>
        </div>
        <div className="card">
          <h3>Family Contacts</h3>
          <div className="list">
            {prioritizedContacts.length === 0 ? (
              <div className="empty">Add family notifications on the Clients tab.</div>
            ) : (
              prioritizedContacts.map((entry) => (
                <div className="item" key={`${entry.person?.id}-${entry.client?.id}`}>
                  <div className="line">
                    <span>{entry.person?.name || "Name"}</span>
                    <span className="pill">
                      {entry.client?.name || "Client"} – {entry.relationship || formatRole(entry.role)}
                    </span>
                  </div>
                  <div className="muted">
                    {entry.person?.phone || "No phone"} - {entry.person?.email || "No email"}
                  </div>
                </div>
              ))
            )}
          </div>
          <button className="card cta" style={{ marginTop: 12 }} onClick={handleViewFamily}>
            View all contacts
          </button>
        </div>
      </div>
    </>
  );
};

const MetricCard = ({ title, number, sub }) => (
  <div className="card">
    <h3>{title}</h3>
    <div className="metric">{number}</div>
    <div className="sub">{sub}</div>
  </div>
);

const StatusPill = ({ task }) => {
  const due = task.due_at ? new Date(task.due_at) : null;
  const isOverdue = due && due < new Date() && task.status === "open";
  const status = isOverdue ? "Overdue" : (task.status || "open");
  const className = ["pill", isOverdue ? "danger" : ""].join(" ").trim();
  return <span className={className}>{status}</span>;
};

const ClientsSection = ({ clients, checkins, tasks }) => {
  if (!clients.length) {
    return <div className="empty">No clients yet. Add a client link to populate this view.</div>;
  }
  return (
    <section className="section" data-active="true">
      <div className="topbar">
        <div className="info">
          <div className="title">Clients</div>
          <div className="muted">People you support day to day</div>
        </div>
      </div>
      <div className="people-grid">
        {clients.map((entry) => {
          const client = entry.client || {};
          const clientTasks = tasks.filter((task) => task.user_id === client.id);
          const clientCheckins = checkins.filter((item) => item.user_id === client.id);
          const latestMood = clientCheckins.length
            ? clientCheckins[0].data?.mood || "-"
            : "-";
          const location = client.location || "Location unknown";
          const roleLabel = entry.relationship || formatRole(entry.caregiver_role);
          const familyCount = (entry.family || []).length;
          return (
            <div className="person-card" key={client.id}>
              <div className="top">
                <div className="avatar">{initials(client.name)}</div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 16 }}>{client.name}</div>
                  <div className="muted">{location}</div>
                  <div className="muted">Your role: {roleLabel}</div>
                </div>
              </div>
              <div className="quick-stats">
                <span>Open tasks: {clientTasks.length}</span>
                <span>Recent mood: {latestMood}</span>
                <span>Family contacts: {familyCount}</span>
              </div>
              <div className="muted">
                {client.email || "No email"} - {client.phone || "No phone"}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

const UpdatesSection = ({ updates, resolveClientName }) => {
  const [filter, setFilter] = useState("all");

  const filtered = useMemo(() => {
    if (filter === "all") return updates;
    return updates.filter((item) => item.kind === filter);
  }, [updates, filter]);

  return (
    <section className="section" data-active="true">
      <div className="topbar">
        <div className="info">
          <div className="title">Updates Feed</div>
          <div className="muted">Latest activity across your circle</div>
        </div>
        <div className="filters">
          {["all", "task", "checkin", "alert", "memory"].map((kind) => (
            <button
              key={kind}
              className="filter"
              data-active={filter === kind}
              onClick={() => setFilter(kind)}
            >
              {kind === "all" ? "All" : kind.charAt(0).toUpperCase() + kind.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <div className="updates">
        <div className="feed">
          {!filtered.length ? (
            <div className="empty">No {filter === "all" ? "" : "matching "}updates yet.</div>
          ) : (
            filtered.map((item) => (
              <article className="feed-card" key={`${item.kind}-${item.source_id}`}>
                <div className="muted">
                  <span className="pill" style={{ marginRight: 8 }}>
                    {item.kind}
                  </span>
                  <span>{fmtDateTime(item.timestamp)}</span>{" "}
                  <span>{resolveClientName(item.user_id)}</span>
                </div>
                <div style={{ fontWeight: 700, fontSize: 16 }}>
                  {item.title || item.kind}
                </div>
                <div style={{ fontSize: 14, color: "#111827" }}>
                  {item.summary || item.data?.notes || ""}
                </div>
                {item.kind === "task" && item.data?.description && (
                  <div style={{ fontSize: 14, color: "#111827" }}>{item.data.description}</div>
                )}
                {item.kind === "checkin" && (
                  <div style={{ fontSize: 14, color: "#111827" }}>
                    Mood: {item.data?.mood || "-"} | Hydration: {item.data?.hydration || "-"} | Sleep:{" "}
                    {item.data?.sleep_hours ?? "-"}h
                  </div>
                )}
                {item.kind === "memory" && item.data?.image_url && (
                  <img src={item.data.image_url} alt={item.title || "Memory"} />
                )}
              </article>
            ))
          )}
        </div>
      </div>
    </section>
  );
};

const CalendarSection = ({ tasks, checkins, resolveClientName }) => {
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth());
  const [year, setYear] = useState(today.getFullYear());
  const [selectedDate, setSelectedDate] = useState(today);

  const eventsByDate = useMemo(() => {
    const events = new Map();
    const add = (dateKey, type, payload) => {
      if (!events.has(dateKey)) events.set(dateKey, []);
      events.get(dateKey).push({ type, payload });
    };
    tasks.forEach((task) => {
      if (!task.due_at) return;
      const date = new Date(task.due_at);
      add(date.toISOString().slice(0, 10), "task", task);
    });
    checkins.forEach((check) => {
      const ts = new Date(check.timestamp || check.data?.created_at || 0);
      if (Number.isNaN(ts.getTime())) return;
      add(ts.toISOString().slice(0, 10), "checkin", check);
    });
    return events;
  }, [tasks, checkins]);

  const daysMatrix = useMemo(() => {
    const first = new Date(year, month, 1);
    const startDay = first.getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const matrix = [];
    let dayCounter = 1 - startDay;
    for (let week = 0; week < 6; week++) {
      const row = [];
      for (let col = 0; col < 7; col++, dayCounter++) {
        const current = new Date(year, month, dayCounter);
        const key = current.toISOString().slice(0, 10);
        row.push({
          date: current,
          day: current.getDate(),
          inMonth: current.getMonth() === month,
          hasTask: (eventsByDate.get(key) || []).some((ev) => ev.type === "task"),
          hasCheckin: (eventsByDate.get(key) || []).some((ev) => ev.type === "checkin"),
        });
      }
      matrix.push(row);
      if (dayCounter >= daysInMonth && matrix.length > 4) break;
    }
    return matrix;
  }, [month, year, eventsByDate]);

  const agendaItems = useMemo(() => {
    const key = selectedDate.toISOString().slice(0, 10);
    return eventsByDate.get(key) || [];
  }, [selectedDate, eventsByDate]);

  const handlePrev = () => {
    setMonth((prev) => {
      if (prev === 0) {
        setYear((y) => y - 1);
        return 11;
      }
      return prev - 1;
    });
  };
  const handleNext = () => {
    setMonth((prev) => {
      if (prev === 11) {
        setYear((y) => y + 1);
        return 0;
      }
      return prev + 1;
    });
  };

  return (
    <section className="section" data-active="true">
      <div className="topbar">
        <div className="info">
          <div className="title">Calendar</div>
          <div className="muted">Due dates and wellness check-ins</div>
        </div>
      </div>
      <div className="calendar-wrap">
        <div className="calendar">
          <header>
            <button className="filter" onClick={handlePrev}>
              Prev
            </button>
            <div style={{ fontWeight: 700 }}>
              {new Date(year, month).toLocaleDateString(undefined, {
                month: "long",
                year: "numeric",
              })}
            </div>
            <button className="filter" onClick={handleNext}>
              Next
            </button>
          </header>
          <table>
            <thead>
              <tr>
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                  <th key={day}>{day}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {daysMatrix.map((week, idx) => (
                <tr key={idx}>
                  {week.map((cell) => {
                    const key = cell.date.toISOString().slice(0, 10);
                    const events = eventsByDate.get(key) || [];
                    return (
                      <td
                        key={key}
                        data-out={cell.inMonth ? undefined : "1"}
                        data-active={
                          key === selectedDate.toISOString().slice(0, 10) ? "true" : undefined
                        }
                        onClick={() => {
                          setSelectedDate(cell.date);
                        }}
                      >
                        {cell.day}
                        {cell.hasTask && <div className="dot task" />}
                        {cell.hasCheckin && <div className="dot checkin" />}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="agenda">
          <h3>Day Details</h3>
          <div className="muted">
            {selectedDate.toLocaleDateString(undefined, {
              weekday: "long",
              month: "long",
              day: "numeric",
            })}
          </div>
          <div className="list">
            {!agendaItems.length ? (
              <div className="empty">No events for this day.</div>
            ) : (
              agendaItems
                .slice()
                .sort((a, b) => {
                  const ta = new Date(a.payload.due_at || a.payload.timestamp || 0).getTime();
                  const tb = new Date(b.payload.due_at || b.payload.timestamp || 0).getTime();
                  return ta - tb;
                })
                .map((evt, idx) => (
                  <div className="agenda item" key={idx}>
                    <div style={{ fontWeight: 700 }}>
                      {evt.type === "task" ? "Task" : "Check-in"} – {evt.payload.title || ""}
                    </div>
                    <div className="muted">{resolveClientName(evt.payload.user_id)}</div>
                    {evt.type === "task" ? (
                      <div>{evt.payload.description || ""}</div>
                    ) : (
                      <div>
                        Mood: {evt.payload.data?.mood || "-"} | Notes: {evt.payload.data?.notes || ""}
                      </div>
                    )}
                  </div>
                ))
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

const FamilySection = ({ clients }) => {
  if (!clients.length) {
    return <div className="empty">Link clients to start tracking their family and friends.</div>;
  }
  return (
    <section className="section" data-active="true">
      <div className="topbar">
        <div className="info">
          <div className="title">Family & Friends</div>
          <div className="muted">Contact list grouped by client</div>
        </div>
      </div>
      <div className="contacts" id="family-grid">
        {clients.map((entry) => {
          const client = entry.client || {};
          const contacts = entry.family || [];
          const caregiverRole = entry.relationship || formatRole(entry.caregiver_role);
          return (
            <div className="contact-card" key={client.id}>
              <div className="name">{client.name}</div>
              <div className="labels">
                <span className="chip">{caregiverRole}</span>
                <span className="chip">Family contacts: {contacts.length}</span>
              </div>
              {contacts.length === 0 ? (
                <div className="empty">No family contacts yet for this client.</div>
              ) : (
                contacts.map((contact) => {
                  const person = contact.person || {};
                  const phone = person.phone || "";
                  const email = person.email || "";
                  const label = contact.relationship || formatRole(contact.role);
                  return (
                    <div className="item" key={person.id}>
                      <div className="line">
                        <span>{person.name || "Name"}</span>
                        <span className="pill">{label}</span>
                      </div>
                      <div className="muted">
                        {phone || "No phone listed"} - {email || "No email listed"}
                      </div>
                      <div className="contact-actions">
                        <button data-copy={phone} onClick={() => copyToClipboard(phone, "phone")}>
                          Copy Phone
                        </button>
                        <button data-copy={email} onClick={() => copyToClipboard(email, "email")}>
                          Copy Email
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
};

const copyToClipboard = (value, label) => {
  if (!value) {
    window.alert(`No ${label} available`);
    return;
  }
  navigator.clipboard
    .writeText(value)
    .then(() => {
      window.alert(`${label} copied to clipboard`);
    })
    .catch(() => window.alert("Copy failed"));
};

export default App;
