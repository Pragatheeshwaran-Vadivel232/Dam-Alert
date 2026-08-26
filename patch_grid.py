import os
app_path = "admin-panel/src/App.jsx"
with open(app_path, "r") as f:
    app_code = f.read()

btn_insert = """
            <button onClick={triggerCombinedBroadcast} className="btn btn-primary" style={{ marginBottom: "1.5rem", width: "100%", padding: "1rem", fontSize: "1.1rem", background: "linear-gradient(135deg, #0984e3, #6c5ce7)", color: "white", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: "bold" }}>
              📢 Send Combined Daily SMS (Both Dams in One Message)
            </button>
            
            <div className="dams-grid">
"""

if "📢 Send Combined Daily SMS" not in app_code:
    app_code = app_code.replace('<div className="dams-grid">', btn_insert)
    with open(app_path, "w") as f:
        f.write(app_code)
    print("SUCCESS")
else:
    print("ALREADY EXISTS")
