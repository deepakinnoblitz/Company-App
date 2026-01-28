import frappe
from frappe.utils import flt
import json


def execute(filters=None):

    # Convert JSON to dict (Frappe sends filters as string)
    if isinstance(filters, str):
        filters = json.loads(filters)

    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)
    summary = get_summary(data)

    # Return 5 values → (columns, rows, message, chart, summary)
    return columns, data, None, None, summary


# ---------------------------------------------------
#  COLUMNS
# ---------------------------------------------------
def get_columns():
    return [
        {"label": "Invoice", "fieldname": "invoice", "fieldtype": "Link", "options": "Invoice", "width": 150},
        {"label": "Invoice Date", "fieldname": "invoice_date", "fieldtype": "Date", "width": 110},

        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Contacts", "width": 150},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 150},

        {"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
        {"label": "Collected Amount", "fieldname": "amount_collected", "fieldtype": "Currency", "width": 130},
        {"label": "Pending Amount", "fieldname": "amount_pending", "fieldtype": "Currency", "width": 120},

        {"label": "Last Collection Date", "fieldname": "last_collection_date", "fieldtype": "Date", "width": 130},
        {"label": "Payment Mode", "fieldname": "payment_mode", "fieldtype": "Data", "width": 120},
    ]


# ---------------------------------------------------
#  MAIN DATA
# ---------------------------------------------------
def get_data(filters):

    conditions = "1=1"

    if filters.get("from_date"):
        conditions += f" AND inv.invoice_date >= '{filters['from_date']}'"

    if filters.get("to_date"):
        conditions += f" AND inv.invoice_date <= '{filters['to_date']}'"

    if filters.get("customer"):
        conditions += f" AND (inv.client_name LIKE '%%{filters['customer']}%%' OR inv.billing_name LIKE '%%{filters['customer']}%%')"

    if filters.get("invoice"):
        conditions += f" AND inv.name = '{filters['invoice']}'"

    invoices = frappe.db.sql(f"""
        SELECT
            inv.name,
            inv.invoice_date,
            inv.client_name AS customer,
            inv.billing_name AS customer_name,
            inv.grand_total
        FROM `tabInvoice` inv
        WHERE {conditions}
        ORDER BY inv.invoice_date DESC
    """, as_dict=True)

    if not invoices:
        return []

    invoice_list = [i.name for i in invoices]

    # Collections
    collections = frappe.db.sql("""
        SELECT
            ic.invoice,
            SUM(ic.amount_collected) AS collected,
            MAX(ic.collection_date) AS last_date,
            MAX(ic.mode_of_payment) AS payment_mode
        FROM `tabInvoice Collection` ic
        WHERE ic.invoice IN %(inv)s
        GROUP BY ic.invoice
    """, {"inv": invoice_list}, as_dict=True)

    collect_map = {c.invoice: c for c in collections}

    final_data = []

    for inv in invoices:

        c = collect_map.get(inv.name, {})

        collected = flt(c.get("collected", 0))
        pending = flt(inv.grand_total) - collected

        final_data.append({
            "invoice": inv.name,
            "invoice_date": inv.invoice_date,
            "customer": inv.customer,
            "customer_name": inv.customer_name,

            "grand_total": inv.grand_total,
            "amount_collected": collected,
            "amount_pending": pending,

            "last_collection_date": c.get("last_date"),
            "payment_mode": c.get("payment_mode"),
        })

    return final_data


# ---------------------------------------------------
#  SUMMARY CARDS
# ---------------------------------------------------
def get_summary(data):

    total_inv = sum(flt(d.get("grand_total")) for d in data)
    total_collected = sum(flt(d.get("amount_collected")) for d in data)
    total_pending = sum(flt(d.get("amount_pending")) for d in data)

    return [
        {
            "label": "Total Invoice Amount",
            "value": total_inv,
            "indicator": "blue",
            "datatype": "Currency",
        },
        {
            "label": "Total Collected",
            "value": total_collected,
            "indicator": "green",
            "datatype": "Currency",
        },
        {
            "label": "Total Pending",
            "value": total_pending,
            "indicator": "red",
            "datatype": "Currency",
        }
    ]


