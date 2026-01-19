# Copyright (c) 2025, deepak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Purchase(Document):
	pass


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_purchase_contacts(doctype, txt, searchfield, start, page_len, filters):
	"""Return only contacts where customer_type = 'Purchase'"""
	return frappe.db.sql("""
		SELECT name, first_name, company_name
		FROM `tabContacts`
		WHERE customer_type = 'Purchase'
			AND (name LIKE %(txt)s 
				OR first_name LIKE %(txt)s 
				OR company_name LIKE %(txt)s)
		ORDER BY
			CASE WHEN name LIKE %(txt)s THEN 0 ELSE 1 END,
			CASE WHEN first_name LIKE %(txt)s THEN 0 ELSE 1 END,
			name
		LIMIT %(page_len)s OFFSET %(start)s
	""", {
		'txt': f"%{txt}%",
		'start': start,
		'page_len': page_len
	})
