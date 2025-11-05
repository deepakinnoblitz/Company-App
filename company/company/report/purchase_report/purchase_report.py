import frappe

def execute(filters=None):
    columns = [
        {"label": "Purchase ID", "fieldname": "bill_no", "fieldtype": "Data", "width": 150},
        {"label": "Vendor Name", "fieldname": "vendor_name", "fieldtype": "Data", "width": 200},
        {"label": "Bill Date", "fieldname": "bill_date", "fieldtype": "Date", "width": 120},
        {"label": "Amount", "fieldname": "grand_total", "fieldtype": "Currency", "width": 150},
        {"label": "Description", "fieldname": "description", "fieldtype": "Data", "width": 250},
    ]

    data = frappe.db.sql("""
        SELECT bill_no, vendor_name, bill_date, grand_total, description
        FROM `tabPurchase`
        ORDER BY bill_date ASC
    """, as_dict=True)

    total = sum([row.grand_total for row in data])
    data.append({
        "bill_no": "TOTAL",
        "grand_total": total
    })

    return columns, data
