import React, { useState, useEffect } from 'react';

const API_BASE = "http://localhost:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [damsData, setDamsData] = useState({});
  const [farmers, setFarmers] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  // Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [newFarmer, setNewFarmer] = useState({
    name: "", phone: "+91", village: "", farm_size_acres: "", dam_preference: "BOTH", language: "TAMIL"
  });

  // Broadcast Custom State
  const [broadcastDam, setBroadcastDam] = useState("AMARAVATHI");
  const [customMsg, setCustomMsg] = useState("");

  const showNotification = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  
  const triggerCombinedBroadcast = async () => {
    try {
      const response = await fetch(`http://localhost:8000/alerts/broadcast/combined`, { method: 'POST' });
      const data = await response.json();
      alert(`Sent combined SMS to ${data.total_farmers || 0} farmers!`);
      fetchLogs(); // just in case fetchLogs doesn't exist either
    } catch (error) {
      console.error("Error triggering combined broadcast:", error);
    }
  };

  const fetchDams = async () => {
    try {
      const res = await fetch(`${API_BASE}/dams/latest`);
      const data = await res.json();
      setDamsData(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchFarmers = async () => {
    try {
      const res = await fetch(`${API_BASE}/farmers`);
      const data = await res.json();
      setFarmers(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/alerts/logs`);
      const data = await res.json();
      setLogs(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchDams();
    fetchFarmers();
    fetchLogs();
  }, []);

  const handleSyncData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/dams/sync`, { method: "POST" });
      const data = await res.json();
      await fetchDams();
      showNotification(`✓ ${data.message} (${data.records_updated} dams updated)`);
    } catch (e) {
      showNotification("Failed to sync live data from portal", "error");
    }
    setLoading(false);
  };

  
  const toggleFarmerStatus = async (id, currentStatus) => {
    const action = currentStatus ? 'deactivate' : 'activate';
    try {
      await fetch(`http://localhost:8000/farmers/${id}/${action}`, { method: 'PUT' });
      fetchFarmers();
    } catch (error) {
      console.error(`Error ${action} farmer:`, error);
    }
  };

  const deleteFarmer = async (id) => {
    if (!window.confirm("Are you sure you want to delete this farmer?")) return;
    try {
      await fetch(`http://localhost:8000/farmers/${id}`, { method: 'DELETE' });
      fetchFarmers();
    } catch (error) {
      console.error("Error deleting farmer:", error);
    }
  };

const handleRegisterFarmer = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/farmers/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...newFarmer,
          farm_size_acres: newFarmer.farm_size_acres ? parseFloat(newFarmer.farm_size_acres) : null
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");
      
      showNotification(`✓ ${data.message}`);
      setShowAddModal(false);
      setNewFarmer({ name: "", phone: "+91", village: "", farm_size_acres: "", dam_preference: "BOTH", language: "TAMIL" });
      fetchFarmers();
    } catch (e) {
      showNotification(e.message, "error");
    }
  };

  const handleTriggerBroadcast = async (damName) => {
    if (!confirm(`Broadcast official morning SMS for ${damName} to all subscribed farmers?`)) return;
    try {
      const res = await fetch(`${API_BASE}/alerts/broadcast/dam/${damName}`, { method: "POST" });
      const data = await res.json();
      showNotification(`✓ SMS Broadcast sent to ${data.total_farmers} farmer(s)!`);
      fetchLogs();
    } catch (e) {
      showNotification("Failed to trigger broadcast", "error");
    }
  };

  const handleSendCustomSMS = async (e) => {
    e.preventDefault();
    if (!customMsg.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/alerts/broadcast/custom`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dam_name: broadcastDam, message_text: customMsg })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Broadcast failed");
      showNotification(`✓ Custom SMS sent to ${data.total_sent} farmer(s)!`);
      setCustomMsg("");
      fetchLogs();
    } catch (e) {
      showNotification(e.message, "error");
    }
  };

  const getMeterColor = (pct) => {
    if (pct >= 95) return "#ef4444";
    if (pct >= 85) return "#f97316";
    if (pct >= 70) return "#eab308";
    return "#10b981";
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="brand-title">
          <span style={{ fontSize: "1.8rem" }}>🌊</span>
          <div>
            <h1>KaLai Vivasayam Dam Alert</h1>
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.2rem" }}>
              <span className="brand-badge">Village Panchayat Admin</span>
              <span className="brand-badge" style={{ background: "rgba(16,185,129,0.3)" }}>Amaravathi & Thirumoorthi</span>
            </div>
          </div>
        </div>

        <nav className="nav-tabs">
          <button className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            📊 Dashboard
          </button>
          <button className={`nav-tab ${activeTab === 'farmers' ? 'active' : ''}`} onClick={() => setActiveTab('farmers')}>
            🚜 Farmers ({farmers.length})
          </button>
          <button className={`nav-tab ${activeTab === 'broadcast' ? 'active' : ''}`} onClick={() => setActiveTab('broadcast')}>
            📢 Send Alerts
          </button>
          <button className={`nav-tab ${activeTab === 'logs' ? 'active' : ''}`} onClick={() => setActiveTab('logs')}>
            📜 SMS Logs ({logs.length})
          </button>
        </nav>
      </header>

      {/* Main Area */}
      <main className="main-content">
        {toast && (
          <div className={`toast ${toast.type}`}>
            <span>{toast.msg}</span>
            <button onClick={() => setToast(null)} style={{ background: "transparent", border: "none", cursor: "pointer", fontWeight: "bold" }}>✕</button>
          </div>
        )}

        {/* Tab 1: Dashboard */}
        {activeTab === "dashboard" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
              <div>
                <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>Live Dam Gauges & Status</h2>
                <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
                  Source: Tamil Nadu Agriculture Reservoir Portal (9:00 AM Sync)
                </p>
              </div>
              <button className="btn btn-primary" onClick={handleSyncData} disabled={loading}>
                {loading ? "🔄 Syncing..." : "🔄 Sync Live Data Now"}
              </button>
            </div>

            
            <button onClick={triggerCombinedBroadcast} className="btn btn-primary" style={{ marginBottom: "1.5rem", width: "100%", padding: "1rem", fontSize: "1.1rem", background: "linear-gradient(135deg, #0984e3, #6c5ce7)", color: "white", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: "bold" }}>
              📢 Send Combined Daily SMS (Both Dams in One Message)
            </button>
            
            <div className="dams-grid">

              {["AMARAVATHI", "THIRUMURTHY"].map((name) => {
                const d = damsData[name] || {};
                const fillPct = d.fill_percent || 0;
                return (
                  <div className="dam-card" key={name}>
                    <div className="dam-header">
                      <div>
                        <div className="dam-name">{name} DAM</div>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                          Capacity: {d.full_depth_ft || "--"} ft | {d.full_cap_mcft || "--"} M.Cft
                        </span>
                      </div>
                      <span className={`badge badge-${d.alert_level || 'NORMAL'}`}>
                        {d.alert_level || 'NORMAL'}
                      </span>
                    </div>

                    <div className="dam-body">
                      <div className="meter-container">
                        <div className="meter-labels">
                          <span>Current Storage Level</span>
                          <span style={{ fontWeight: 800, color: getMeterColor(fillPct) }}>{fillPct}% Full</span>
                        </div>
                        <div className="meter-bar-bg">
                          <div className="meter-bar-fill" style={{ width: `${Math.min(fillPct, 100)}%`, backgroundColor: getMeterColor(fillPct) }} />
                        </div>
                      </div>

                      <div className="metrics-grid">
                        <div className="metric-tile">
                          <div className="metric-tile-title">Water Level</div>
                          <div className="metric-tile-value">{d.level_ft ? `${d.level_ft} ft` : '--'}</div>
                        </div>
                        <div className="metric-tile">
                          <div className="metric-tile-title">Live Storage</div>
                          <div className="metric-tile-value">{d.storage_mcft ? `${d.storage_mcft} M.Cft` : '--'}</div>
                        </div>
                        <div className="metric-tile">
                          <div className="metric-tile-title">Inflow Rate</div>
                          <div className="metric-tile-value" style={{ color: '#0284c7' }}>
                            {d.inflow_cusecs !== null ? `${d.inflow_cusecs} CuSecs` : '--'}
                          </div>
                        </div>
                        <div className="metric-tile">
                          <div className="metric-tile-title">Outflow Rate</div>
                          <div className="metric-tile-value" style={{ color: '#ea580c' }}>
                            {d.outflow_cusecs !== null ? `${d.outflow_cusecs} CuSecs` : '--'}
                          </div>
                        </div>
                      </div>

                      <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '0.6rem', border: '1px solid var(--border)', fontSize: '0.825rem' }}>
                        ⏱️ <strong>Est. Time to Full (TTF):</strong> {d.ttf_hours ? `~${d.ttf_hours} Hours` : "Not Filling (Steady / Emptying)"}
                      </div>

                      <button className="btn btn-outline" style={{ marginTop: 'auto' }} onClick={() => handleTriggerBroadcast(name)}>
                        📢 Trigger {name} Morning SMS Digest
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab 2: Farmers */}
        {activeTab === "farmers" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
              <div>
                <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>Registered Village Farmers</h2>
                <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
                  All farmers receiving automatic dam alerts in your village
                </p>
              </div>
              <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
                ➕ Register New Farmer
              </button>
            </div>

            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Farmer Name</th>
                    <th>Mobile (SMS)</th>
                    <th>Village</th>
                    <th>Farm Size</th>
                    <th>Dam Subscribed</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {farmers.map((f) => (
                    <tr key={f.id}>
                      <td style={{ fontWeight: 700 }}>#{f.id}</td>
                      <td style={{ fontWeight: 600 }}>{f.name}</td>
                      <td><code>{f.phone}</code></td>
                      <td>{f.village || "--"}</td>
                      <td>{f.farm_size_acres ? `${f.farm_size_acres} Acres` : "--"}</td>
                      <td>
                        <span className="badge badge-RELEASE" style={{ fontSize: "0.7rem" }}>
                          {f.dam_preference}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${f.is_active ? 'badge-NORMAL' : 'badge-CRITICAL'}`}>
                          {f.is_active ? 'ACTIVE' : 'INACTIVE'}
                        </span>
                      </td>
                      <td>
                        <button onClick={() => toggleFarmerStatus(f.id, f.is_active)} style={{ padding: "4px 8px", marginRight: "5px", background: f.is_active ? "#ffa502" : "#2ed573", color: "white", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.75rem" }}>
                          {f.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button onClick={() => deleteFarmer(f.id)} style={{ padding: "4px 8px", background: "#ff4d4d", color: "white", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.75rem" }}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                  {farmers.length === 0 && (
                    <tr><td colSpan="7" style={{ textAlign: "center", color: "var(--text-muted)", padding: "2rem" }}>No farmers registered yet. Click "Register New Farmer" above!</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Broadcast */}
        {activeTab === "broadcast" && (
          <div style={{ maxWidth: "680px", margin: "0 auto" }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>📢 Send Instant / Custom SMS Broadcast</h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
              Push an instant emergency message, water release notification, or canal schedule to farmers.
            </p>

            <form onSubmit={handleSendCustomSMS} style={{ background: "white", padding: "1.75rem", borderRadius: "1rem", border: "1px solid var(--border)", boxShadow: "var(--shadow)", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <div className="form-group">
                <label>Target Audience (Farmers by Dam):</label>
                <select className="form-control" value={broadcastDam} onChange={(e) => setBroadcastDam(e.target.value)}>
                  <option value="AMARAVATHI">Amaravathi Dam Farmers Only</option>
                  <option value="THIRUMURTHY">Thirumoorthi Dam Farmers Only</option>
                  <option value="BOTH">All Registered Village Farmers</option>
                </select>
              </div>

              <div className="form-group">
                <label>Message Content (Tamil / English):</label>
                <textarea 
                  className="form-control" 
                  rows="5" 
                  placeholder="Type alert message here..."
                  value={customMsg}
                  onChange={(e) => setCustomMsg(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                <button type="button" className="btn btn-outline" style={{ fontSize: "0.75rem" }} onClick={() => setCustomMsg("💧 [WATER RELEASE] Canal water release is scheduled for tomorrow at 6:00 AM. Please prepare your fields! - KaLai Dam Alert")}>
                  + Fill Water Release Template
                </button>
                <button type="button" className="btn btn-outline" style={{ fontSize: "0.75rem" }} onClick={() => setCustomMsg("🚨 [FLOOD WARNING] Amaravathi Dam is at 96% capacity! High canal flow expected. Protect low-lying fields. - KaLai Dam Alert")}>
                  + Fill Flood Alert Template
                </button>
              </div>

              <button type="submit" className="btn btn-primary" style={{ padding: "0.85rem", fontSize: "1rem", marginTop: "0.5rem" }}>
                🚀 Send SMS Broadcast Now
              </button>
            </form>
          </div>
        )}

        {/* Tab 4: Logs */}
        {activeTab === "logs" && (
          <div>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>📜 SMS Delivery & Alert Logs</h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
              History of all automated digests and manual SMS alerts dispatched
            </p>

            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Recipient</th>
                    <th>Dam</th>
                    <th>Alert Type</th>
                    <th>SMS Preview</th>
                    <th>Delivery Status</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((l) => (
                    <tr key={l.id}>
                      <td style={{ fontSize: "0.8rem", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                        {l.sent_at ? new Date(l.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "--"}
                      </td>
                      <td>
                        <strong>{l.farmer_name}</strong><br />
                        <small style={{ color: "var(--text-muted)" }}>{l.farmer_phone}</small>
                      </td>
                      <td><span className="badge badge-RELEASE">{l.dam_name}</span></td>
                      <td><span className={`badge badge-${l.alert_level || 'NORMAL'}`}>{l.alert_level}</span></td>
                      <td style={{ maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: "0.8rem" }}>
                        {l.message_text}
                      </td>
                      <td>
                        <span className={`badge ${l.sms_status === 'SENT' ? 'badge-NORMAL' : 'badge-CRITICAL'}`}>
                          {l.sms_status}
                        </span>
                      </td>
                      <td>
                        <button onClick={() => toggleFarmerStatus(f.id, f.is_active)} style={{ padding: "4px 8px", marginRight: "5px", background: f.is_active ? "#ffa502" : "#2ed573", color: "white", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.75rem" }}>
                          {f.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button onClick={() => deleteFarmer(f.id)} style={{ padding: "4px 8px", background: "#ff4d4d", color: "white", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.75rem" }}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                  {logs.length === 0 && (
                    <tr><td colSpan="6" style={{ textAlign: "center", color: "var(--text-muted)", padding: "2rem" }}>No alerts sent yet.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Add Farmer Modal */}
      {showAddModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3 style={{ fontWeight: 800 }}>➕ Register Farmer</h3>
              <button onClick={() => setShowAddModal(false)} style={{ border: "none", background: "transparent", cursor: "pointer", fontSize: "1.2rem" }}>✕</button>
            </div>
            <form onSubmit={handleRegisterFarmer}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Full Name:</label>
                  <input className="form-control" required placeholder="e.g. S. Murugesan" value={newFarmer.name} onChange={e => setNewFarmer({...newFarmer, name: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Mobile Number (with +91):</label>
                  <input className="form-control" required placeholder="+919488888888" value={newFarmer.phone} onChange={e => setNewFarmer({...newFarmer, phone: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Village / Hamlet:</label>
                  <input className="form-control" placeholder="e.g. Alangiyam" value={newFarmer.village} onChange={e => setNewFarmer({...newFarmer, village: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Farm Size (Acres):</label>
                  <input className="form-control" type="number" step="0.1" placeholder="e.g. 3.5" value={newFarmer.farm_size_acres} onChange={e => setNewFarmer({...newFarmer, farm_size_acres: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Dam Subscription:</label>
                  <select className="form-control" value={newFarmer.dam_preference} onChange={e => setNewFarmer({...newFarmer, dam_preference: e.target.value})}>
                    <option value="BOTH">Both Amaravathi & Thirumoorthi</option>
                    <option value="AMARAVATHI">Amaravathi Dam Only</option>
                    <option value="THIRUMURTHY">Thirumoorthi Dam Only</option>
                  </select>
                </div>
                <button type="submit" className="btn btn-primary" style={{ marginTop: "0.5rem", padding: "0.75rem" }}>
                  Save & Register Farmer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
