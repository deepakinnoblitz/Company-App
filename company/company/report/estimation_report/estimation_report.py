import frappe
import json
from frappe import _

def execute(filters=None):
    if isinstance(filters, str):
        filters = json.loads(filters)
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)
    summary = get_summary(filters)

    return columns, data, None, None, summary

def get_columns():
    return [
        {"label": _("Ref No"), "fieldname": "name", "fieldtype": "Link", "options": "Estimation", "width": 120},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Estimate Date"), "fieldname": "estimate_date", "fieldtype": "Date", "width": 110},
        {"label": _("Item"), "fieldname": "service", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Qty"), "fieldname": "quantity", "fieldtype": "Float", "width": 80},
        {"label": _("Price"), "fieldname": "price", "fieldtype": "Currency", "width": 100},
        {"label": _("Tax Type"), "fieldname": "tax_type", "fieldtype": "Data", "width": 120},
        {"label": _("Tax Amount"), "fieldname": "tax_amount", "fieldtype": "Currency", "width": 110},
        {"label": _("Subtotal"), "fieldname": "sub_total", "fieldtype": "Currency", "width": 120},
        {"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 130},
    ]

def get_data(filters):
    conditions = []
    query_filters = {}

    if filters.get("client_name"):
        conditions.append("e.client_name = %(client_name)s")
        query_filters["client_name"] = filters["client_name"]
    if filters.get("from_date"):
        conditions.append("e.estimate_date >= %(from_date)s")
        query_filters["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("e.estimate_date <= %(to_date)s")
        query_filters["to_date"] = filters["to_date"]

    where = " AND ".join(conditions)
    if where:
        where = "WHERE " + where

    query = f"""
        SELECT
            e.name,
            e.customer_name,
            e.estimate_date,
            e.grand_total,
            i.service,
            i.quantity,
            i.price,
            i.tax_type,
            i.tax_amount,
            i.sub_total
        FROM `tabEstimation` e
        LEFT JOIN `tabEstimation Items` i ON i.parent = e.name
        {where}
        ORDER BY e.estimate_date DESC
    """
    return frappe.db.sql(query, query_filters, as_dict=True)

def get_summary(filters):
    conditions = []
    query_filters = {}

    if filters.get("client_name"):
        conditions.append("client_name = %(client_name)s")
        query_filters["client_name"] = filters["client_name"]
    if filters.get("from_date"):
        conditions.append("estimate_date >= %(from_date)s")
        query_filters["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("estimate_date <= %(to_date)s")
        query_filters["to_date"] = filters["to_date"]

    where = " AND ".join(conditions)
    if where:
        where = "WHERE " + where

    totals = frappe.db.sql(f"""
        SELECT
            SUM(grand_total) AS total_amount,
            SUM(total_qty) AS total_qty
        FROM `tabEstimation`
        {where}
    """, query_filters, as_dict=True)[0]

    count_filters = []
    if filters.get("client_name"):
        count_filters.append(["client_name", "=", filters["client_name"]])
    if filters.get("from_date"):
        count_filters.append(["estimate_date", ">=", filters["from_date"]])
    if filters.get("to_date"):
        count_filters.append(["estimate_date", "<=", filters["to_date"]])

    estimation_count = frappe.db.count("Estimation", filters=count_filters)

    return [
        {
            "label": "Total Amount",
            "value": totals.total_amount or 0,
            "indicator": "blue",
            "datatype": "Currency"
        },
        {
            "label": "Total Quantity",
            "value": totals.total_qty or 0,
            "indicator": "green",
            "datatype": "Float"
        },
        {
            "label": "Estimation Records",
            "value": estimation_count,
            "indicator": "orange"
        }
    ]
