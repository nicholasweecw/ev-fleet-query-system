import sqlite3

def setup_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("ev_fleet.db")
    cursor = conn.cursor()

    # Create 'vehicles' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            ID TEXT PRIMARY KEY,
            model TEXT,
            state_of_charge REAL,
            health_status TEXT,
            mileage INTEGER,
            last_service_date TEXT
        )
    ''')

    # Create 'alerts' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            vehicle_id TEXT,
            alert_type TEXT,
            alert_date TEXT,
            severity TEXT,
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(ID)
        )
    ''')

    # Create 'maintenance_predictions' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_predictions (
            vehicle_id TEXT,
            predicted_issue TEXT,
            prediction_date TEXT,
            confidence_level REAL,
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(ID)
        )
    ''')

    # Insert sample data into 'vehicles'
    vehicles_data = [
        ("EV001", "Model A", 10.0, "Poor", 35000, "2024-05-01"),  # Low charge
        ("EV002", "Model B", 15.0, "Fair", 22000, "2024-03-10"),  # Low charge
        ("EV003", "Model C", 20.0, "Good", 18000, "2024-02-20"),  # Medium charge
        ("EV004", "Model D", 25.0, "Good", 25000, "2024-04-15"),  # Medium charge
        ("EV005", "Model E", 18.0, "Poor", 30000, "2024-01-05"),  # Low charge
        ("EV006", "Model F", 12.0, "Fair", 40000, "2024-06-01"),  # Low charge
        ("EV007", "Model G", 8.0, "Poor", 45000, "2024-05-20"),   # Low charge
        ("EV008", "Model H", 22.0, "Good", 15000, "2024-03-25"),  # Medium charge
        ("EV009", "Model I", 30.0, "Fair", 12000, "2024-02-01"),  # Medium charge
        ("EV010", "Model J", 28.0, "Excellent", 5000, "2024-03-15"),  # Medium charge
        ("EV011", "Model K", 85.0, "Good", 6000, "2024-02-25"),   # High charge
        ("EV012", "Model L", 95.0, "Excellent", 2000, "2024-01-30"),  # High charge
        ("EV013", "Model M", 82.0, "Fair", 8000, "2024-04-10"),   # High charge
        ("EV014", "Model N", 50.0, "Good", 12000, "2024-03-20"),  # Medium charge
        ("EV015", "Model O", 75.0, "Excellent", 10000, "2024-02-10"),  # Medium charge
        ("EV016", "Model P", 5.0, "Poor", 47000, "2024-06-05"),   # Very low charge
        ("EV017", "Model Q", 40.0, "Good", 20000, "2024-03-18"),  # Medium charge
        ("EV018", "Model R", 90.0, "Excellent", 3000, "2024-01-05"),  # High charge
        ("EV019", "Model S", 78.0, "Fair", 11000, "2024-02-28"),  # Medium charge
        ("EV020", "Model T", 15.0, "Poor", 35000, "2024-04-01")   # Low charge
    ]
    cursor.executemany('INSERT OR IGNORE INTO vehicles VALUES (?, ?, ?, ?, ?, ?)', vehicles_data)

    # Insert sample data into 'alerts'
    alerts_data = [
        ("EV001", "Brake Failure", "2024-12-25", "High"),
        ("EV002", "Engine Warning", "2024-12-18", "Medium"),
        ("EV003", "Low Coolant", "2024-12-28", "Low"),
        ("EV004", "Battery Issue", "2024-11-25", "High"),
        ("EV005", "Flat Tire", "2024-12-10", "Medium"),
        ("EV006", "Brake Pads Worn", "2024-12-15", "High"),
        ("EV007", "Transmission Issue", "2024-12-20", "High"),
        ("EV008", "Oil Change Needed", "2024-12-05", "Low"),
        ("EV009", "Steering Issue", "2024-11-30", "Medium"),
        ("EV010", "Suspension Problem", "2024-12-18", "High"),
        ("EV011", "Suspension Failure", "2024-12-22", "High"),
        ("EV012", "Engine Overheating", "2024-12-21", "High"),
        ("EV013", "Battery Replacement", "2024-11-27", "Critical"),
        ("EV014", "Wheel Alignment Needed", "2024-12-14", "Medium"),
        ("EV015", "Airbag Fault", "2024-11-29", "High"),
        ("EV016", "Fuel Pump Failure", "2024-12-25", "High"),
        ("EV017", "Exhaust System Warning", "2024-12-11", "Low"),
        ("EV018", "Catalytic Converter Issue", "2024-12-17", "Medium"),
        ("EV019", "Alternator Failure", "2024-12-23", "High"),
        ("EV020", "Suspension Noise", "2024-12-20", "Low"),
        ("EV021", "Engine Misfire", "2024-12-15", "High"),
        ("EV022", "Radiator Leak", "2024-12-10", "Critical"),
        ("EV023", "Turbocharger Issue", "2024-12-05", "Medium"),
        ("EV024", "Timing Belt Worn", "2024-12-12", "High"),
        ("EV025", "Brake Fluid Low", "2024-12-18", "Medium"),
        ("EV026", "Power Steering Issue", "2024-12-09", "High"),
        ("EV027", "Shock Absorber Fault", "2024-12-13", "Medium"),
        ("EV028", "Engine Knocking", "2024-12-24", "Critical"),
        ("EV029", "Suspension Damage", "2024-12-26", "Critical"),
        ("EV030", "Clutch Problem", "2024-12-30", "High")
    ]
    cursor.executemany('INSERT OR IGNORE INTO alerts VALUES (?, ?, ?, ?)', alerts_data)

    # Insert sample data into 'maintenance_predictions'
    maintenance_data = [
        ("EV001", "Brake Replacement", "2024-12-29", 0.75),
        ("EV002", "Engine Overhaul", "2024-12-27", 0.80),
        ("EV003", "Coolant Leak", "2024-12-30", 0.70),
        ("EV004", "Battery Replacement", "2025-01-15", 0.85),
        ("EV005", "Tire Change", "2025-01-20", 0.65),
        ("EV006", "Brake Fluid Replacement", "2025-02-18", 0.90),
        ("EV007", "Transmission Overhaul", "2025-04-25", 0.88),
        ("EV008", "Oil Filter Replacement", "2025-05-05", 0.72),
        ("EV009", "Steering Adjustment", "2025-10-10", 0.68),
        ("EV010", "Suspension Check", "2025-12-15", 0.80)
    ]
    cursor.executemany('INSERT OR IGNORE INTO maintenance_predictions VALUES (?, ?, ?, ?)', maintenance_data)

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print("Database setup complete and sample data inserted.")

# Run the setup function
setup_database()
