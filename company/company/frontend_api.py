import frappe
from frappe.auth import LoginManager
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_csrf_token():
    return frappe.sessions.get_csrf_token()

@frappe.whitelist()
def get_invoice_count():
    return frappe.db.count("Invoice")

@frappe.whitelist()
def get_doctype_list(doctype, txt=None, fields=None, filters=None):
    """
    Fetch a list of documents for a given DocType.
    Useful for populating dropdowns on the frontend.
    """
    if not frappe.has_permission(doctype, "read"):
        frappe.throw("Not permitted")

    query_filters = {}
    if txt:
        query_filters["name"] = ["like", f"%{txt}%"]
    
    if filters:
        import json
        extra_filters = json.loads(filters)
        query_filters.update(extra_filters)

    if fields:
        import json
        field_list = json.loads(fields)
        return frappe.get_list(doctype, filters=query_filters, fields=field_list, limit=1000)

    return frappe.get_list(doctype, filters=query_filters, pluck="name", limit=1000)


@frappe.whitelist(allow_guest=True)
def mobile_login(username, password):
    """
    Login API for Mobile / App
    Returns API Key + Secret per user
    """

    if not username or not password:
        frappe.throw(_("Username and password required"))

    # Authenticate user
    login_manager = LoginManager()
    login_manager.authenticate(username, password)
    login_manager.post_login()

    user = frappe.get_doc("User", username)

    # Generate API Key if missing
    if not user.api_key:
        frappe.throw(_("API Key not found for user {}".format(username)))

    # Generate API Secret if missing
    if not user.api_secret:
        frappe.throw(_("API Secret not found for user {}".format(username)))

    user.save(ignore_permissions=True)

    return {
        "user": user.name,
        "api_key": user.api_key,
        "api_secret": user.get_password("api_secret")
    }


@frappe.whitelist()
def get_lead_permissions():
    """
    Check if the current user has read, write, and delete permissions for the Lead DocType.
    """
    return get_doc_permissions("Lead")


@frappe.whitelist()
def get_deal_permissions():
    """
    Check if the current user has read, write, and delete permissions for the Deal DocType.
    """
    return get_doc_permissions("Deal")


@frappe.whitelist()
def get_doc_permissions(doctype):
    """
    Check if the current user has read, write, and delete permissions for a given DocType.
    """
    return {
        "read": bool(frappe.has_permission(doctype, "read")),
        "write": bool(frappe.has_permission(doctype, "write")),
        "delete": bool(frappe.has_permission(doctype, "delete")),
    }


@frappe.whitelist()
def get_current_user_info():
    """
    Fetch the full details of the currently logged-in user.
    """
    user = frappe.get_doc("User", frappe.session.user)
    
    # Calculate allowed modules (All - Blocked)
    all_modules = frappe.get_all("Module Def", pluck="name")
    blocked_modules = [d.module for d in user.block_modules]
    allowed_modules = [m for m in all_modules if m not in blocked_modules]

    return {
        "name": user.name,
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "username": user.username,
        "email": user.email,
        "time_zone": user.time_zone,
        "user_image": user.user_image,
        "roles": [role.role for role in user.roles],
        "role_profile_name": user.role_profile_name,
        "allowed_modules": allowed_modules
    }


@frappe.whitelist()
def get_dashboard_stats():
    """
    Fetch CRM dashboard statistics including counts for Leads, Contacts, Deals, Events, Todo, Calls, and Meetings.
    """
    stats = {}
    
    # Get counts for each DocType
    doctypes = {
        "leads": "Lead",
        "contacts": "Contacts",
        "deals": "Deal",
        "accounts": "Accounts",
    }
    
    for key, doctype in doctypes.items():
        try:
            if frappe.has_permission(doctype, "read"):
                stats[key] = frappe.db.count(doctype)
            else:
                stats[key] = 0
        except Exception:
            stats[key] = 0
    
    # Get recent leads (last 7 days)
    try:
        if frappe.has_permission("Lead", "read"):
            stats["recent_leads"] = frappe.db.count("Lead", {
                "creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -7)]
            })
        else:
            stats["recent_leads"] = 0
    except Exception:
        stats["recent_leads"] = 0
    
    # Get leads by status (workflow_state)
    try:
        if frappe.has_permission("Lead", "read"):
            stats["leads_by_status"] = frappe.db.sql("""
                SELECT workflow_state as status, COUNT(*) as count
                FROM `tabLead`
                GROUP BY workflow_state
            """, as_dict=True)
        else:
            stats["leads_by_status"] = []
    except Exception:
        stats["leads_by_status"] = []
    
    # Get deals by stage
    try:
        if frappe.has_permission("Deal", "read"):
            stats["deals_by_stage"] = frappe.db.sql("""
                SELECT stage, COUNT(*) as count
                FROM `tabDeal`
                GROUP BY stage
            """, as_dict=True)
        else:
            stats["deals_by_stage"] = []
    except Exception:
        stats["deals_by_stage"] = []
    
    # Get total deal value
    try:
        if frappe.has_permission("Deal", "read"):
            total_value = frappe.db.sql("""
                SELECT SUM(value) as total
                FROM `tabDeal`
                WHERE stage NOT IN ('Closed Lost')
            """, as_dict=True)
            stats["total_deal_value"] = total_value[0].get("total") or 0 if total_value else 0
        else:
            stats["total_deal_value"] = 0
    except Exception:
        stats["total_deal_value"] = 0

    # Get historical data for the last 7 days
    try:
        days = []
        lead_series = []
        contact_series = []
        deal_series = []
        account_series = []
        
        for i in range(6, -1, -1):
            date = frappe.utils.add_days(frappe.utils.nowdate(), -i)
            day_name = frappe.utils.get_datetime(date).strftime('%a')
            days.append(day_name)
            
            lead_series.append(frappe.db.count("Lead", {"creation": ["like", f"{date}%"]}))
            contact_series.append(frappe.db.count("Contacts", {"creation": ["like", f"{date}%"]}))
            deal_series.append(frappe.db.count("Deal", {"creation": ["like", f"{date}%"]}))
            account_series.append(frappe.db.count("Accounts", {"creation": ["like", f"{date}%"]}))
            
        stats["charts"] = {
            "categories": days,
            "leads": lead_series,
            "contacts": contact_series,
            "deals": deal_series,
            "accounts": account_series
        }
    except Exception as e:
        frappe.log_error(f"Error calculating dashboard chart data: {str(e)}")
        stats["charts"] = {
            "categories": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            "leads": [0]*7,
            "contacts": [0]*7,
            "deals": [0]*7,
            "accounts": [0]*7
        }
    
    return stats


@frappe.whitelist()
def get_today_activities():
    """
    Fetch today's calls and meetings.
    """
    from datetime import datetime
    
    activities = {
        "calls": [],
        "meetings": []
    }
    
    # Get today's date
    today_date = frappe.utils.today()
    
    # Fetch and filter calls
    try:
        if frappe.has_permission("Calls", "read"):
            # Use SQL for calls too for consistency and to avoid field issues
            activities["calls"] = frappe.db.sql("""
                SELECT name, title, call_for, lead_name, call_start_time, call_end_time, outgoing_call_status, call_purpose
                FROM `tabCalls`
                WHERE DATE(call_start_time) = %s
                ORDER BY call_start_time ASC
                LIMIT 10
            """, (today_date,), as_dict=True)
    except Exception as e:
        frappe.log_error(f"Error fetching calls for dashboard: {str(e)}")
    
    # Fetch and filter meetings (strictly from Meeting DocType)
    try:
        if frappe.has_permission("Meeting", "read"):
            # Using direct SQL because 'from' is a reserved keyword in SQL
            activities["meetings"] = frappe.db.sql("""
                SELECT name, title, meet_for, lead_name, `from`, `to`, outgoing_call_status, meeting_venue, location
                FROM `tabMeeting`
                WHERE DATE(`from`) = %s
                ORDER BY `from` ASC
                LIMIT 10
            """, (today_date,), as_dict=True)
    except Exception as e:
        frappe.log_error(f"Error fetching meetings for dashboard: {str(e)}")
    
    return activities


@frappe.whitelist()
def update_event(name, data):
    """
    Update event data (subject, starts_on, ends_on, etc.)
    """
    if isinstance(data, str):
        import json
        data = json.loads(data)
        
    try:
        if frappe.has_permission("Event", "write", doc=name):
            doc = frappe.get_doc("Event", name)
            doc.update(data)
            doc.save()
            return {"status": "success", "message": "Event updated successfully"}
        else:
            frappe.throw("No permission to update this event", frappe.PermissionError)
    except Exception as e:
        frappe.log_error(f"Error updating event {name}: {str(e)}")
        return {"status": "error", "message": str(e)}

        
@frappe.whitelist()
def delete_event(name):
    """
    Delete an event
    """
    try:
        if frappe.has_permission("Event", "delete", doc=name):
            frappe.delete_doc("Event", name)
            return {"status": "success", "message": "Event deleted successfully"}
        else:
            frappe.throw("No permission to delete this event", frappe.PermissionError)
    except Exception as e:
        frappe.log_error(f"Error deleting event {name}: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def create_event(data):
    """
    Create a new event
    """
    if isinstance(data, str):
        import json
        data = json.loads(data)
        
    try:
        if frappe.has_permission("Event", "create"):
            doc = frappe.get_doc({
                "doctype": "Event",
                **data
            })
            doc.insert()
            return {"status": "success", "message": "Event created successfully", "name": doc.name}
        else:
            frappe.throw("No permission to create events", frappe.PermissionError)
    except Exception as e:
        frappe.log_error(f"Error creating event: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_events(start=None, end=None):
    """
    Fetch events for calendar view.
    """
    filters = {}
    
    if start and end:
        filters["starts_on"] = ["between", [start, end]]
    
    try:
        if frappe.has_permission("Event", "read"):
            events = frappe.get_all(
                "Event",
                filters=filters,
                fields=["name", "subject", "starts_on", "ends_on", "event_category", "event_type", "status", "description", "color", "all_day"],
                order_by="starts_on asc",
                limit=500
            )
            return events
        else:
            return []
    except Exception as e:
        frappe.log_error(f"Error fetching events: {str(e)}")
        return []

@frappe.whitelist()
def get_workflow_states(doctype="Lead", current_state=None):
    """Get workflow states and allowed transitions for a doctype and current state"""
    try:
        # Get workflow for the doctype
        workflow = frappe.get_all(
            "Workflow",
            filters={"document_type": doctype, "is_active": 1},
            fields=["name"],
            limit=1
        )
        
        if not workflow:
            return {"states": [], "transitions": [], "actions": []}
        
        workflow_name = workflow[0].name
        
        # Get all workflow states
        states = frappe.get_all(
            "Workflow Document State",
            filters={"parent": workflow_name},
            fields=["state", "doc_status", "is_optional_state"],
            order_by="idx"
        )
        
        # Get all workflow transitions
        transitions = frappe.get_all(
            "Workflow Transition",
            filters={"parent": workflow_name},
            fields=["state", "action", "next_state", "allowed"],
            order_by="idx"
        )
        
        # If current_state is provided, filter transitions for that state
        allowed_actions = []
        if current_state:
            user_roles = frappe.get_roles()
            for transition in transitions:
                if transition.state == current_state:
                    # Check if user has the required role
                    if not transition.allowed or transition.allowed in user_roles:
                        allowed_actions.append({
                            "action": transition.action,
                            "next_state": transition.next_state
                        })
        
        return {
            "states": [s.state for s in states],
            "transitions": transitions,
            "actions": allowed_actions
        }
    except Exception as e:
        frappe.log_error(f"Error fetching workflow states: {str(e)}")
        return {"states": [], "transitions": [], "actions": []}
@frappe.whitelist()
def get_doc_fields(doctype):
    """
    Fetch relevant fields for a given DocType for mapping/import purposes.
    """
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    meta = frappe.get_meta(doctype)
    fields = []

    # Add Name/ID field
    fields.append({
        "fieldname": "name",
        "label": _("ID"),
        "fieldtype": "Data",
        "reqd": 0
    })

    # Add Owner field
    fields.append({
        "fieldname": "owner",
        "label": _("Owner"),
        "fieldtype": "Link",
        "options": "User"
    })

    for df in meta.fields:
        if df.fieldtype not in ("Section Break", "Column Break", "Tab Break", "HTML", "Button"):
            fields.append({
                "fieldname": df.fieldname,
                "label": _(df.label),
                "fieldtype": df.fieldtype,
                "options": df.options,
                "reqd": df.reqd
            })
    
    return fields


@frappe.whitelist()
def download_import_template(doctype):
    """
    Generate and download a blank import template for a given DocType.
    """
    import json
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    from frappe.core.doctype.data_import.data_import import download_template
    
    meta = frappe.get_meta(doctype)
    # Get relevant fields for the template (mandatory + common)
    fields = [df.fieldname for df in meta.fields if (df.reqd or df.in_list_view) and df.fieldtype not in ("Section Break", "Column Break", "Tab Break", "HTML", "Button") and not df.hidden]
    
    if "name" not in fields:
        fields.insert(0, "name")

    export_fields = {doctype: fields}
    
    return download_template(doctype, export_fields=json.dumps(export_fields), export_records="blank_template", file_type="Excel")


@frappe.whitelist()
def update_import_file(data_import_name, data):
    """
    Save edited preview data back to a CSV file and update the Data Import record.
    """
    import json
    import csv
    import io
    from frappe.utils.file_manager import save_file

    data_import = frappe.get_doc("Data Import", data_import_name)
    data_import.check_permission("write")

    rows = json.loads(data)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    for row in rows:
        writer.writerow(row)
    
    content = output.getvalue()
    
    # Save as a new file
    filename = f"edited_{data_import_name}.csv"
    file_doc = save_file(
        filename,
        content.encode("utf-8"),
        "Data Import",
        data_import_name,
        is_private=1,
        df="import_file"
    )

    # Update Data Import record
    data_import.import_file = file_doc.file_url
    data_import.save()
    
    return {"status": "success", "file_url": file_doc.file_url}

@frappe.whitelist()
def get_doctype_fields(doctype):
    meta = frappe.get_meta(doctype)
    fields = []
    
    for d in meta.fields:
        if d.fieldtype not in ['Section Break', 'Column Break', 'Tab Break', 'HTML', 'Button', 'Table'] and not d.hidden and not d.read_only:
             fields.append({
                "fieldname": d.fieldname,
                "label": d.label,
                "fieldtype": d.fieldtype,
                "options": d.options,
                "hidden": d.hidden
            })
            
    return {"name": doctype, "fields": fields}

@frappe.whitelist()
def get_hr_dashboard_data():
    """
    Fetch HR dashboard statistics and data.
    """
    data = {}
    today = frappe.utils.today()
    
    # 1. Announcements
    try:
        data["announcements"] = frappe.get_all(
            "Announcement",
            fields=["title", "message", "posting_date"],
            order_by="posting_date desc",
            limit=5
        )
    except Exception:
        data["announcements"] = []

    # 2. Employee Stats
    try:
        data["total_employees"] = frappe.db.count("Employee", {"status": "Active"})
    except Exception:
        data["total_employees"] = 0

    # 3. Pending Leaves (Workflow based)
    try:
        # Assuming workflow states 'Pending' or 'Draft' are pending
        data["pending_leaves"] = frappe.db.count("Leave Application", {
            "workflow_state": ["in", ["Pending", "Draft", "Open"]]
        })
    except Exception:
        data["pending_leaves"] = 0

    # 4. Attendance Stats (Today)
    try:
        data["present_today"] = frappe.db.count("Attendance", {
            "attendance_date": today,
            "status": "Present"
        })
        
        total_active = data.get("total_employees", 0)
        marked_attendance = frappe.db.count("Attendance", {"attendance_date": today})
        data["missing_attendance"] = max(0, total_active - marked_attendance)
    except Exception:
        data["present_today"] = 0
        data["missing_attendance"] = 0

    # 5. Today's Leaves
    try:
        # Check Attendance for "On Leave" status or Leave Application for approved leaves today
        data["todays_leaves"] = frappe.db.sql("""
            SELECT e.employee_name, e.name as employee
            FROM `tabLeave Application` la
            JOIN `tabEmployee` e ON la.employee = e.name
            WHERE la.workflow_state = 'Approved'
            AND %s BETWEEN la.from_date AND la.to_date
        """, (today,), as_dict=True)
    except Exception:
        data["todays_leaves"] = []

    # 6. Today's Birthdays
    try:
        # Match day and month
        data["todays_birthdays"] = frappe.db.sql("""
            SELECT employee_name, name as employee
            FROM `tabEmployee`
            WHERE status = 'Active'
            AND DAY(date_of_birth) = DAY(%s)
            AND MONTH(date_of_birth) = MONTH(%s)
        """, (today, today), as_dict=True)
    except Exception:
        data["todays_birthdays"] = []

    # 7. Holidays (Current Month)
    try:
        first_day = frappe.utils.get_first_day(today)
        last_day = frappe.utils.get_last_day(today)
        
        holiday_list = frappe.db.get_value("Holiday List", {"is_default": 1}, "name")
            
        if holiday_list:
            data["holidays"] = frappe.db.sql("""
                SELECT holiday_date as date, description
                FROM `tabHoliday`
                WHERE parent = %s
                AND holiday_date BETWEEN %s AND %s
            """, (holiday_list, first_day, last_day), as_dict=True)
        else:
            data["holidays"] = []
    except Exception:
        data["holidays"] = []

    return data


@frappe.whitelist()
def convert_estimation_to_invoice(estimation):
    if not estimation:
        frappe.throw("Estimation ID required")

    # Load estimation document
    est = frappe.get_doc("Estimation", estimation)

    # Prevent duplicate conversion
    existing_invoice = frappe.db.get_value(
        "Invoice",
        {"converted_estimation_id": est.name},
        "name"
    )
    if existing_invoice:
        frappe.msgprint(f"Invoice <b>{existing_invoice}</b> already created for this estimation.")
        return existing_invoice

    # Create new invoice
    inv = frappe.new_doc("Invoice")
    inv.flags.ignore_mandatory = True

    # Copy main fields
    fields_to_copy = [
        "customer_name",
        "billing_name",
        "billing_address",
        "phone_number",
        "total_qty",
        "total_amount",
        "overall_discount_type",
        "overall_discount",
        "grand_total",
        "description",
        "terms_and_conditions",
        "bank_account"
    ]

    for f in fields_to_copy:
        inv.set(f, est.get(f))
        
    # Set customer_id from client_name
    inv.customer_id = est.client_name

    # Invoice date
    inv.invoice_date = frappe.utils.nowdate()

    # Conversion flags
    inv.converted_from_estimation = 1
    inv.converted_estimation_id = est.name

    # Copy items
    for item in est.get("table_qecz"):
        inv.append("table_qecz", {
            "service": item.service,
            "hsn_code": item.hsn_code,
            "description": item.description,
            "quantity": item.quantity,
            "price": item.price,
            "discount_type": item.discount_type,
            "discount": item.discount,
            "tax_type": item.tax_type,
            "tax_category": item.tax_category,
            "tax_percent": item.tax_percent,
            "tax_amount": item.tax_amount,
            "cgst": item.cgst,
            "sgst": item.sgst,
            "igst": item.igst,
            "sub_total": item.sub_total
        })

    # Save invoice
    inv.insert(ignore_permissions=True, ignore_mandatory=True)

    # SUCCESS MESSAGE
    frappe.msgprint(
        msg=f"Estimation <b>{est.name}</b> successfully converted to Invoice <b>{inv.name}</b>!",
        title="Conversion Complete",
        indicator="green"
    )

    return inv.name


@frappe.whitelist()
def get_sales_dashboard_data():
    """
    Fetch Sales dashboard statistics and data.
    """
    data = {}
    today = frappe.utils.today()
    first_day_month = frappe.utils.get_first_day(today)
    first_day_year = f"{today[:4]}-01-01"
    
    try:
        # 1. Summary Metrics from Invoices
        invoices = frappe.get_all("Invoice", fields=[
            "grand_total", "total_amount", "overall_discount", 
            "total_qty", "invoice_date", "balance_amount", "due_date",
            "client_name", "billing_name"
        ])
        
        data["total_sales"] = sum(frappe.utils.flt(inv.grand_total) for inv in invoices)
        data["total_qty_sold"] = sum(frappe.utils.flt(inv.total_qty) for inv in invoices)
        data["total_orders"] = len(invoices)
        data["aov"] = data["total_sales"] / data["total_orders"] if data["total_orders"] > 0 else 0
        
        # Gross vs Net
        data["gross_sales"] = sum(frappe.utils.flt(inv.total_amount) for inv in invoices)
        data["net_sales"] = data["total_sales"] # Using grand_total as net sales for now
        data["total_discounts"] = sum(frappe.utils.flt(inv.overall_discount) for inv in invoices)
        
        # MTD / YTD
        data["mtd_sales"] = sum(frappe.utils.flt(inv.grand_total) for inv in invoices if inv.invoice_date >= frappe.utils.getdate(first_day_month))
        data["ytd_sales"] = sum(frappe.utils.flt(inv.grand_total) for inv in invoices if inv.invoice_date >= frappe.utils.getdate(first_day_year))
        
        # 2. Pipeline from Deals
        deals = frappe.get_all("Deal", fields=["value", "stage"])
        data["pipeline_value"] = sum(frappe.utils.flt(d.value) for d in deals if d.stage not in ["Closed Won", "Closed Lost"])
        
        # 3. Top Customers
        data["top_customers_by_revenue"] = frappe.db.sql("""
            SELECT client_name, billing_name, SUM(grand_total) as revenue, COUNT(name) as order_count
            FROM `tabInvoice`
            GROUP BY client_name
            ORDER BY revenue DESC
            LIMIT 5
        """, as_dict=True)
        
        data["most_repeated_customers"] = frappe.db.sql("""
            SELECT client_name, billing_name, COUNT(name) as order_count, SUM(grand_total) as total_spent
            FROM `tabInvoice`
            GROUP BY client_name
            ORDER BY order_count DESC
            LIMIT 5
        """, as_dict=True)
        
        # 4. Overdue / Pending Orders
        data["overdue_orders"] = frappe.get_all("Invoice", 
            filters={
                "balance_amount": [">", 0],
                "due_date": ["<", today]
            },
            fields=["name", "billing_name", "due_date", "balance_amount", "grand_total"],
            order_by="due_date asc",
            limit=5
        )
        data["pending_orders_count"] = frappe.db.count("Invoice", {"balance_amount": [">", 0]})
        
        # 5. Trends (Last 12 months)
        trends = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(invoice_date, '%%Y-%%m') as month,
                SUM(grand_total) as total_sales,
                SUM(overall_discount) as total_discount
            FROM `tabInvoice`
            WHERE invoice_date >= DATE_SUB(%s, INTERVAL 12 MONTH)
            GROUP BY month
            ORDER BY month ASC
        """, (today,), as_dict=True)
        
        data["sales_trend"] = {
            "categories": [t.month for t in trends],
            "series": [frappe.utils.flt(t.total_sales) for t in trends]
        }
        data["discount_trend"] = {
            "categories": [t.month for t in trends],
            "series": [frappe.utils.flt(t.total_discount) for t in trends]
        }
        
        # 6. Conversion Rate (Estimations to Invoices)
        total_estimations = frappe.db.count("Estimation")
        converted_estimations = frappe.db.count("Invoice", {"converted_from_estimation": 1})
        data["conversion_rate"] = (converted_estimations / total_estimations * 100) if total_estimations > 0 else 0
        
    except Exception as e:
        frappe.log_error(f"Sales Dashboard Error: {str(e)}")
        # Return empty data structure to avoid frontend crashes
        return {
            "total_sales": 0, "total_qty_sold": 0, "total_orders": 0, "aov": 0,
            "gross_sales": 0, "net_sales": 0, "total_discounts": 0,
            "mtd_sales": 0, "ytd_sales": 0, "pipeline_value": 0,
            "top_customers_by_revenue": [], "most_repeated_customers": [],
            "overdue_orders": [], "pending_orders_count": 0,
            "sales_trend": {"categories": [], "series": []},
            "discount_trend": {"categories": [], "series": []},
            "conversion_rate": 0
        }

    return data

@frappe.whitelist(allow_guest=True)
def update_my_password(old_password, new_password):
    """
    Update the current user's password.
    """
    user = frappe.session.user
    
    if user == "Guest": 
        frappe.throw(_("Please login to change password"))  
        
    # Verify old password
    try:
        frappe.utils.password.check_password(user, old_password)
    except frappe.AuthenticationError:
        return {"status": "failed", "message": "Incorrect old password"}

    # Update password
    frappe.utils.password.update_password(user, new_password)
    
    return {"status": "success", "message": "Password updated successfully"}


@frappe.whitelist(allow_guest=True)
def update_profile_info(first_name, middle_name=None, last_name=None):
    """
    Update the current user's profile information (names).
    """
    user = frappe.session.user
    
    if user == "Guest":
        return {"status": "failed", "message": "Please login to update profile"}
        
    try:
        user_doc = frappe.get_doc("User", user)
        user_doc.first_name = first_name
        user_doc.middle_name = middle_name
        user_doc.last_name = last_name
        user_doc.save(ignore_permissions=True)
        
        return {
            "status": "success", 
            "message": "Profile updated successfully",
            "data": {
                "first_name": user_doc.first_name,
                "middle_name": user_doc.middle_name,
                "last_name": user_doc.last_name,
                "full_name": user_doc.full_name
            }
        }
    except Exception as e:
        frappe.log_error(f"Error updating profile: {str(e)}")
        return {"status": "failed", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def upload_profile_image():
    """
    Upload and update profile image for the current user.
    """
    user_email = frappe.session.user
   
    if user_email == "Guest":
        return {"status": "failed", "message": "Please login to upload profile image"}
 
    try:
        user_doc = frappe.get_doc("User", user_email)
       
        # 'file' is the key in FormData
        file = frappe.request.files.get("file")
        if not file:
             return {"status": "failed", "message": "No file uploaded"}
       
        from frappe.utils.file_manager import save_file
       
        # Save the file
        fname = file.filename
        content = file.stream.read()
       
        # Save file and attach to User document
        saved_file = save_file(
            fname,
            content,
            "User",
            user_email,
            decode=False,
            is_private=0,
            df="user_image"
        )
       
        # Explicitly update user_image just in case save_file df param didn't trigger it (though it should)
        user_doc.user_image = saved_file.file_url
        user_doc.save(ignore_permissions=True)
 
        return {
            "status": "success",
            "message": "Profile image updated",
            "file_url": saved_file.file_url
        }
 
    except Exception as e:
        frappe.log_error(f"Error uploading profile image: {str(e)}")
        return {"status": "failed", "message": str(e)}
 
 