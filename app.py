from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime, timedelta
import re
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.WARNING)

def parse_query(query):
    """
    Parses the user query to extract intent and required SQL condition.

    Args:
        query (str): The natural language query entered by the user.

    Returns:
        dict: A dictionary containing the parsed intent and SQL condition,
              or {'intent': 'unknown'} if the query does not match any patterns.
    """
    query_lower = query.lower()

    # Identify queries requesting the status of a specific vehicle.
    # Example: "What is the status of EV001?" or "Status for EV123."
    vehicle_match = re.search(r"status (?:of|for) (ev\d+)", query_lower)
    if vehicle_match:
        vehicle_id = vehicle_match.group(1).upper()
        return {"intent": "vehicle_status_query", "condition": f"ID = '{vehicle_id}'"}

    # Identify queries asking if a specific vehicle is at risk for a certain condition.
    # Example: "Is EV002 at risk of brake failure?"
    risk_match = re.search(r"is (ev\d+) at risk of (.+)\??", query_lower)
    if risk_match:
        vehicle_id, risk_type = risk_match.groups()
        vehicle_id = vehicle_id.upper()
        risk_type = risk_type.strip().rstrip("?")
        return {
            "intent": "specific_vehicle_risk_query",
            "condition": f"vehicle_id = '{vehicle_id}' AND LOWER(alert_type) = '{risk_type.lower()}'",
        }

    if "low charge" in query_lower:
        return {"intent": "charge_query", "condition": "state_of_charge < 20"}
    elif "medium charge" in query_lower:
        return {"intent": "charge_query", "condition": "state_of_charge BETWEEN 20 AND 80"}
    elif "high charge" in query_lower:
        return {"intent": "charge_query", "condition": "state_of_charge > 80"}

    # Identify queries asking which vehicles are at risk of a general condition.
    # Example: "Which vehicles are at risk of low charge?"
    match = re.search(r"at risk of (.+)\??", query_lower)
    if match:
        risk_type = match.group(1).strip().rstrip("?")
        return {"intent": "risk_query", "condition": f"LOWER(alert_type) = '{risk_type.lower()}'"}

    if "malfunction" in query_lower:
        if "next month" in query_lower:
            today = datetime.now()
            start_date = today.replace(day=1) + timedelta(days=32)
            start_date = start_date.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            return {
                "intent": "malfunction_query",
                "condition": f"DATE(prediction_date) BETWEEN '{start_date.date()}' AND '{end_date.date()}'"
            }
        
        if "next year" in query_lower:
            today = datetime.now()
            start_date = today
            end_date = today + timedelta(days=365)
            return {
                "intent": "malfunction_query",
                "condition": f"DATE(prediction_date) BETWEEN '{start_date.date()}' AND '{end_date.date()}'"
            }

        # Identify queries specifying a timeframe for the next N years, months, or days.
        # Example: "Which vehicles will malfunction in the next 6 months?"
        next_match = re.search(r"next\s(\d+)\s(years|months|days)", query_lower)
        if next_match:
            num, period = next_match.groups()
            days = int(num) * (365 if "year" in period else 30 if "month" in period else 1)
            return {
                "intent": "malfunction_query",
                "condition": f"DATE(prediction_date) BETWEEN DATE('now') AND DATE('now', '+{days} days')"
            }

        # Identify queries specifying a specific month and year.
        # Example: "Which vehicles are expected to malfunction in January 2025?"
        specific_match = re.search(r'(\w+)\s(\d{4})', query_lower)
        if specific_match:
            month_or_keyword, year = specific_match.groups()
            if month_or_keyword.lower() == "in":
                return {"intent": "malfunction_query", "condition": f"strftime('%Y', prediction_date) = '{year}'"}
            else:
                try:
                    month_number = datetime.strptime(month_or_keyword, '%B').month
                    return {
                        "intent": "malfunction_query",
                        "condition": f"strftime('%Y-%m', prediction_date) = '{year}-{month_number:02}'"
                    }
                except ValueError:
                    return {"intent": "unknown"}

        # Default to the next 6 months
        return {
            "intent": "malfunction_query",
            "condition": "DATE(prediction_date) BETWEEN DATE('now') AND DATE('now', '+180 days')"
        }

    if "average state of charge" in query_lower:
        return {"intent": "summary_query", "operation": "average_charge"}
    elif "fleet health" in query_lower:
        return {"intent": "summary_query", "operation": "fleet_health"}

    return {"intent": "unknown"}

def generate_sql(parsed_query):
    """
    Generates an SQL query based on the parsed user intent.

    Args:
        parsed_query (dict): The parsed query containing intent and condition.

    Returns:
        str: The SQL query string to fetch the required data, or None if intent is unknown.
    """
    intent = parsed_query["intent"]

    if intent == "vehicle_status_query":
        condition = parsed_query["condition"]
        return f"SELECT * FROM vehicles WHERE {condition}"

    if intent == "specific_vehicle_risk_query":
        condition = parsed_query["condition"]
        return f"""
            SELECT vehicle_id, alert_type, alert_date, severity 
            FROM alerts 
            WHERE {condition}
        """

    if intent == "risk_query":
        condition = parsed_query["condition"]
        return f"""
            SELECT DISTINCT vehicle_id, alert_type, alert_date, severity 
            FROM alerts 
            WHERE {condition}
        """
    elif intent == "charge_query":
        condition = parsed_query["condition"]
        return f"SELECT ID, model, state_of_charge FROM vehicles WHERE {condition}"
    elif intent == "malfunction_query":
        condition = parsed_query["condition"]
        return f"""
            SELECT DISTINCT vehicle_id, predicted_issue, prediction_date, confidence_level 
            FROM maintenance_predictions 
            WHERE {condition}
        """
    elif intent == "summary_query":
        operation = parsed_query["operation"]
        if operation == "average_charge":
            return "SELECT AVG(state_of_charge) as avg_charge, COUNT(*) as total_vehicles FROM vehicles"
        elif operation == "fleet_health":
            return "SELECT health_status, COUNT(*) as count FROM vehicles GROUP BY health_status"
    return None

def execute_query(sql):
    """
    Executes the SQL query on the EV fleet database.

    Args:
        sql (str): The SQL query to be executed.

    Returns:
        list: A list of tuples containing the query results.
    """
    try:
        conn = sqlite3.connect("ev_fleet.db")
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
    except sqlite3.Error as e:
        logging.warning(f"Database query failed: {e}")
        return []
    finally:
        conn.close()
    return results

def format_risk_query_response(results):
    if not results:
        return "No matching vehicles found for the specified condition in the database."
    formatted_results = []
    for row in results:
        vehicle_id, alert_type, alert_date, severity = row
        formatted_results.append(
            f"Vehicle {vehicle_id}: {alert_type} reported on {alert_date} with severity {severity}"
        )
    return "Vehicles at risk: " + "; ".join(formatted_results)

def process_query(query):
    parsed_query = parse_query(query)

    if parsed_query["intent"] == "unknown":
        return (
            "I'm sorry, I couldn't understand your query. "
            "Please try rephrasing or asking about specific conditions, such as "
            "'Which EVs are at risk of brake failure?' or 'Which EVs are expected to malfunction in 2025?'."
        )

    sql = generate_sql(parsed_query)
    if not sql:
        return "No valid SQL query generated for the intent. Please refine your query."

    results = execute_query(sql)

    if parsed_query["intent"] == "vehicle_status_query":
        if not results:
            return "No data available for the specified vehicle ID."
        return f"Vehicle Status: {results[0]}"
    elif parsed_query["intent"] == "specific_vehicle_risk_query":
        return format_risk_query_response(results)
    elif parsed_query["intent"] == "risk_query":
        return format_risk_query_response(results)
    elif parsed_query["intent"] == "charge_query":
        if not results:
            return "No vehicles match the specified charge condition."
        return "Vehicles matching the charge condition: " + ", ".join(
            [f"{row[1]} (ID: {row[0]}, SoC: {row[2]}%)" for row in results]
        )
    elif parsed_query["intent"] == "malfunction_query":
        if not results:
            return "No vehicles are expected to malfunction in the specified time period."
        return "Predicted malfunctions: " + ", ".join(
            [f"Vehicle {row[0]} ({row[1]}) on {row[2]} with confidence {row[3]:.2f}" for row in results]
        )
    elif parsed_query["intent"] == "summary_query":
        if parsed_query["operation"] == "average_charge":
            if not results or results[0][0] is None:
                return "No fleet data available."
            avg_charge, total_vehicles = results[0]
            return f"Fleet Summary: Average State of Charge = {avg_charge:.2f}%, Total Vehicles = {total_vehicles}"
        elif parsed_query["operation"] == "fleet_health":
            if not results:
                return "No fleet health data available."
            return "Fleet Health Summary: " + ", ".join(
                [f"{row[0]}: {row[1]} vehicles" for row in results]
            )
    return "Unhandled query. Please try a different question or refer to the query examples."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    user_query = request.form['query']
    response = process_query(user_query)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=False)
