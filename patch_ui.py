import os

# 1. Update backend/routers/farmers.py
router_path = "backend/routers/farmers.py"
with open(router_path, "r") as f:
    router_code = f.read()

if "@router.put(\"/{farmer_id}/activate\")" not in router_code:
    router_code += """
# Activate a farmer (START)
@router.put("/{farmer_id}/activate")
def activate_farmer(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    farmer.is_active = True
    db.commit()
    return {"message": "Farmer activated"}

# Delete a farmer
@router.delete("/{farmer_id}")
def delete_farmer(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    db.delete(farmer)
    db.commit()
    return {"message": "Farmer deleted successfully"}
"""
    with open(router_path, "w") as f:
        f.write(router_code)


# 2. Update admin-panel/src/App.jsx
app_path = "admin-panel/src/App.jsx"
with open(app_path, "r") as f:
    app_code = f.read()

if "toggleFarmerStatus" not in app_code:
    insert_idx = app_code.find("const handleRegisterFarmer")
    
    functions = """
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

"""
    app_code = app_code[:insert_idx] + functions + app_code[insert_idx:]

if "Action</th>" not in app_code:
    app_code = app_code.replace("<th>Status</th>", "<th>Status</th>\n                    <th>Action</th>")
    
    old_td = "</td>\n                    </tr>\n                  ))}"
    new_td = """</td>
                      <td>
                        <button onClick={() => toggleFarmerStatus(f.id, f.is_active)} style={{ padding: "4px 8px", marginRight: "5px", background: f.is_active ? "#ffa502" : "#2ed573", color: "white", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.75rem" }}>
                          {f.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button onClick={() => deleteFarmer(f.id)} style={{ padding: "4px 8px", background: "#ff4d4d", color: "white", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "0.75rem" }}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}"""
    
    app_code = app_code.replace(old_td, new_td)

    with open(app_path, "w") as f:
        f.write(app_code)

print("SUCCESS")
