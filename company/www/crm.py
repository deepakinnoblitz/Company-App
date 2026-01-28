import frappe

def get_context(context):
    """
    Serve the React SPA for all /crm/* routes.
    This allows client-side routing to work properly.
    """
    csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()
    
    context.no_cache = 1
    context.show_sidebar = False
    
    # Pass CSRF token to the frontend
    context.csrf_token = csrf_token
    
    return context
