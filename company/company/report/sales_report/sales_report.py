import frappe
import json

@frappe.whitelist()
def execute(filters=None):

    # Ensure filters is a dict
    if isinstance(filters, str):
        filters = json.loads(filters)

    if not filters:
        filters = {}

    # --- Table Columns ---
    columns = [
        {"fieldname": "client_name", "label": "Client Name", "fieldtype": "Data", "width": 250},
        {"fieldname": "invoice_no", "label": "Invoice No", "fieldtype": "Data", "width": 200},
        {"fieldname": "invoice_date", "label": "Invoice Date", "fieldtype": "Date", "width": 150},
        {"fieldname": "grand_total", "label": "Total Sales Amount", "fieldtype": "Currency", "width": 200},
        {"fieldname": "received_amount", "label": "Received Sales Amount", "fieldtype": "Currency", "width": 200},
        {"fieldname": "balance_amount", "label": "Pending Sales Amount", "fieldtype": "Currency", "width": 200},
    ]

    # --- Build SQL Filters ---
    conditions = []
    if filters.get("from_date"):
        conditions.append(f"invoice_date >= '{filters['from_date']}'")
    if filters.get("to_date"):
        conditions.append(f"invoice_date <= '{filters['to_date']}'")
    if filters.get("client_name"):
        conditions.append(f"client_name = '{filters['client_name']}'")

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    # --- Fetch All Invoices ---
    invoices = frappe.db.sql(f"""
        SELECT
            client_name,
            name AS invoice_no,
            invoice_date,
            grand_total,
            received_amount,
            balance_amount
        FROM `tabInvoice`
        {where_clause}
        ORDER BY invoice_date DESC
    """, as_dict=True)

    # --- Get Totals ---
    totals = frappe.db.sql(f"""
        SELECT
            SUM(grand_total) AS total_sales,
            SUM(received_amount) AS total_received,
            SUM(balance_amount) AS total_pending
        FROM `tabInvoice`
        {where_clause}
    """, as_dict=True)[0]

    total_sales = totals["total_sales"] or 0
    total_received = totals["total_received"] or 0
    total_pending = totals["total_pending"] or 0

    # --- Calculate Ratios ---
    received_percent = (total_received / total_sales * 100) if total_sales else 0
    pending_percent = (total_pending / total_sales * 100) if total_sales else 0

    # --- Attractive Summary Cards ---
    report_summary = [
        {"label": "Total Sales Amount", "value": total_sales, "indicator": "blue", "datatype": "Currency"},
        {"label": f"Received Amount ({received_percent:.1f}%)", "value": total_received,
         "indicator": "green" if received_percent >= 50 else "orange", "datatype": "Currency"},
        {"label": f"Pending Amount ({pending_percent:.1f}%)", "value": total_pending,
         "indicator": "red" if total_pending > 0 else "green", "datatype": "Currency"}
    ]

    # --- Add Chart (Pie) ---
    chart = {
        "data": {
            "labels": ["Received", "Pending"],
            "datasets": [
                {"values": [total_received, total_pending]}
            ]
        },
        "type": "pie",   # change to "bar" or "line" if you like
        "colors": ["#28a745", "#dc3545"]  # green for received, red for pending
    }

    summary_data = {
        "total_sales": total_sales,
        "received_sales": total_received,
        "pending_sales": total_pending,
        "invoice_count": len(invoices)
    }

    # --- Return table + summary + chart ---
    return columns, invoices, summary_data, chart, report_summary
