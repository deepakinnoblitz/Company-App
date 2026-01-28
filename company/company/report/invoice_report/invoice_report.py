import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    if isinstance(filters, str):
        import json
        filters = json.loads(filters)
    
    filters = filters or {}
    
    columns = get_columns()
    data = get_data(filters)
    summary = get_summary(filters)
    
    return columns, data, None, None, summary

def get_columns():
    return [
        {"label": _("Ref No"), "fieldname": "name", "fieldtype": "Link", "options": "Invoice", "width": 120},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Invoice Date"), "fieldname": "invoice_date", "fieldtype": "Date", "width": 110},
        {"label": _("Item"), "fieldname": "service", "fieldtype": "Data", "width": 150},
        {"label": _("Qty"), "fieldname": "quantity", "fieldtype": "Float", "width": 80},
        {"label": _("Price"), "fieldname": "price", "fieldtype": "Currency", "width": 100},
        {"label": _("Tax Type"), "fieldname": "tax_type", "fieldtype": "Data", "width": 120},
        {"label": _("Tax Amount"), "fieldname": "tax_amount", "fieldtype": "Currency", "width": 100},
        {"label": _("Subtotal"), "fieldname": "sub_total", "fieldtype": "Currency", "width": 120},
        {"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
    ]

def get_data(filters):
    conditions = []
    params = {}

    if filters.get("client_name"):
        conditions.append("i.client_name = %(client_name)s")
        params["client_name"] = filters["client_name"]
    if filters.get("from_date"):
        conditions.append("i.invoice_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("i.invoice_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]

    where = " AND ".join(conditions)
    if where:
        where = "WHERE " + where

    query = f"""
        SELECT
            i.name,
            i.customer_name,
            i.invoice_date,
            i.grand_total,
            it.service,
            it.quantity,
            it.price,
            it.tax_type,
            it.tax_amount,
            it.sub_total
        FROM `tabInvoice` i
        LEFT JOIN `tabInvoice Items` it ON it.parent = i.name
        {where}
        ORDER BY i.invoice_date DESC
    """
    return frappe.db.sql(query, params, as_dict=True)

def get_summary(filters):
    # Build raw SQL WHERE clause and parameters
    conditions = []
    params = {}

    # Build Frappe-standard filters for frappe.db.count
    count_filters = []

    if filters.get("client_name"):
        conditions.append("client_name = %(client_name)s")
        params["client_name"] = filters["client_name"]
        count_filters.append(["client_name", "=", filters["client_name"]])
        
    if filters.get("from_date"):
        conditions.append("invoice_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]
        count_filters.append(["invoice_date", ">=", filters["from_date"]])
        
    if filters.get("to_date"):
        conditions.append("invoice_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]
        count_filters.append(["invoice_date", "<=", filters["to_date"]])

    where = " AND ".join(conditions)
    if where:
        where = "WHERE " + where

    totals = frappe.db.sql(f"""
        SELECT
            SUM(grand_total) AS total_amount,
            SUM(total_qty) AS total_qty
        FROM `tabInvoice`
        {where}
    """, params, as_dict=True)[0]

    invoice_count = frappe.db.count("Invoice", filters=count_filters)

    return [
        {"label": _("Total Amount"), "value": flt(totals.total_amount), "indicator": "blue", "datatype": "Currency"},
        {"label": _("Total Quantity"), "value": flt(totals.total_qty), "indicator": "green", "datatype": "Float"},
        {"label": _("Invoice Records"), "value": invoice_count, "indicator": "orange"},
    ]
