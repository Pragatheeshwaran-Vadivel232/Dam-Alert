import os

app_path = "admin-panel/src/App.jsx"
with open(app_path, "r") as f:
    app_code = f.read()

func_insert = """
  const triggerCombinedBroadcast = async () => {
    try {
      const response = await fetch(`http://localhost:8000/alerts/broadcast/combined`, { method: 'POST' });
      const data = await response.json();
      alert(`Sent combined SMS to ${data.total_farmers || 0} farmers!`);
      // fetchLogs(); // just in case fetchLogs doesn't exist either
    } catch (error) {
      console.error("Error triggering combined broadcast:", error);
    }
  };
"""

if "const triggerCombinedBroadcast =" not in app_code:
    app_code = app_code.replace("const fetchDams = async () => {", func_insert + "\n  const fetchDams = async () => {")
    with open(app_path, "w") as f:
        f.write(app_code)
    print("FIXED")
else:
    print("FUNCTION ALREADY THERE")
