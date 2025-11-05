import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import getdate

class Estimation(Document):
    def autoname(self):
        # Set name = ref_no
        if self.ref_no:
            self.name = self.ref_no

    def before_insert(self):
        today = getdate()
        year = today.year

        # Financial Year (April → March)
        if today.month < 4:
            start_year = year - 1
            end_year = year
        else:
            start_year = year
            end_year = year + 1

        fy = f"{str(start_year)[-2:]}-{str(end_year)[-2:]}"

        # ✅ Use correct make_autoname format with dot
        seq = make_autoname(".###", doc=self)  # IB-E/.001, .002, etc.

        # Assign to ref_no (which will also become name)
        self.ref_no = f"IB-E/{fy}/{seq.split('.')[-1]}"
