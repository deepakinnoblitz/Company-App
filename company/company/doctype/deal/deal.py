import frappe
from frappe.model.document import Document
import json
 
class Deal(Document):
    pass
 
@frappe.whitelist()
def get_deals_list(start=0, page_length=20, search=None, stage=None, sort_by=None, filterValues=None):
    start = int(start)
    page_length = int(page_length)
   
    filters = []
    if filterValues:
        if isinstance(filterValues, str):
            filterValues = json.loads(filterValues)
           
        for key, value in filterValues.items():
            if value and value != 'all':
                filters.append(f"d.{key} = {frappe.db.escape(value)}")
 
    if stage and stage != 'all' and (not filterValues or not filterValues.get('stage')):
        filters.append(f"d.stage = {frappe.db.escape(stage)}")
 
    search_condition = ""
    if search:
        search_term = f"%{search}%"
        search_condition = f"AND (d.deal_title LIKE {frappe.db.escape(search_term)} OR d.account LIKE {frappe.db.escape(search_term)})"
 
    filter_condition = " AND ".join(filters)
    if filter_condition:
        filter_condition = "AND " + filter_condition
 
    order_by = "d.creation DESC"
    if sort_by:
        if sort_by == 'contact_name_asc':
            order_by = "c.first_name ASC"
        elif sort_by == 'contact_name_desc':
            order_by = "c.first_name DESC"
        else:
            # Convert standard frappe sort format e.g. "creation_desc" -> "d.creation DESC"
            parts = sort_by.rsplit('_', 1)
            if len(parts) == 2 and parts[1] in ['asc', 'desc']:
                field, direction = parts
                # Map common fields if necessary or use directly
                order_by = f"d.{field} {direction.upper()}"
 
    sql = f"""
        SELECT
            d.name, d.deal_title, d.account, d.contact, d.value,
            d.expected_close_date, d.stage, d.probability, d.type,
            d.source_lead, d.next_step, d.notes, d.deal_owner, d.owner, d.creation,
            c.first_name as contact_name
        FROM
            `tabDeal` d
        LEFT JOIN
            `tabContacts` c ON d.contact = c.name
        WHERE
            1=1
            {filter_condition}
            {search_condition}
        ORDER BY
            {order_by}
        LIMIT
            {page_length} OFFSET {start}
    """
 
    data = frappe.db.sql(sql, as_dict=True)
   
    # Get total count for pagination
    count_sql = f"""
        SELECT COUNT(*) as total
        FROM `tabDeal` d
        LEFT JOIN `tabContacts` c ON d.contact = c.name
        WHERE
            1=1
            {filter_condition}
            {search_condition}
    """
    count = frappe.db.sql(count_sql, as_dict=True)[0].total
 
    return {
        "data": data,
        "total": count
    }
 
@frappe.whitelist()
def get_deal_details(name):
    sql = f"""
        SELECT
            d.name, d.deal_title, d.account, d.contact, d.value,
            d.expected_close_date, d.stage, d.probability, d.type,
            d.source_lead, d.next_step, d.notes, d.deal_owner, d.owner, d.creation,
            c.first_name as contact_name
        FROM
            `tabDeal` d
        LEFT JOIN
            `tabContacts` c ON d.contact = c.name
        WHERE
            d.name = {frappe.db.escape(name)}
    """
   
    data = frappe.db.sql(sql, as_dict=True)
   
    if not data:
        return None
       
    return data[0]
 