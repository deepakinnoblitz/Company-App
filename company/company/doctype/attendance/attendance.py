from datetime import datetime, timedelta
import frappe
from frappe.model.document import Document

class Attendance(Document):
    def validate(self):
        # Always recalc before save
        self.calculate_working_hours()

    def calculate_working_hours(self):
        # If leave_type is set, mark as On Leave
        if self.leave_type:
            self.status = "On Leave"
            self.working_hours_display = "0:00"
            self.working_hours_decimal = 0
            self.overtime_display = "0:00"
            self.overtime_decimal = 0
            return

        # Normalize in_time and out_time
        in_time = self.in_time if self.in_time not in ["00:00", "00:00:00", None] else None
        out_time = self.out_time if self.out_time not in ["00:00", "00:00:00", None] else None

        # Both times missing → Absent
        if not in_time and not out_time:
            self.status = "Absent"
            self.working_hours_display = "0:00"
            self.working_hours_decimal = 0
            self.overtime_display = "0:00"
            self.overtime_decimal = 0
            return

        # Only one time filled → Missing
        if (in_time and not out_time) or (not in_time and out_time):
            self.status = "Missing"
            self.working_hours_display = "0:00"
            self.working_hours_decimal = 0
            self.overtime_display = "0:00"
            self.overtime_decimal = 0
            return

        # Both times exist → calculate working hours
        fmt = "%H:%M:%S"
        start = datetime.strptime(in_time, fmt)
        end = datetime.strptime(out_time, fmt)

        # Handle overnight shifts (e.g., 22:00 → 06:00)
        if end < start:
            end += timedelta(days=1)

        total_minutes = int((end - start).total_seconds() / 60)

        if total_minutes <= 0:
            self.status = "Missing"
            self.working_hours_display = "0:00"
            self.working_hours_decimal = 0
            self.overtime_display = "0:00"
            self.overtime_decimal = 0
            return

        # ✅ Show actual total working time (not capped to 9 hours)
        reg_hours = total_minutes // 60
        reg_minutes = total_minutes % 60
        self.working_hours_display = f"{reg_hours}:{reg_minutes:02d}"
        self.working_hours_decimal = round(total_minutes / 60, 2)

        # Status based on total hours
        if total_minutes < 4 * 60:
            self.status = "Half Day"
        else:
            self.status = "Present"

        # ✅ Calculate overtime beyond 9 hours
        overtime_minutes = max(0, total_minutes - 9 * 60)
        ot_hours = overtime_minutes // 60
        ot_minutes = overtime_minutes % 60
        self.overtime_display = f"{ot_hours}:{ot_minutes:02d}"
        self.overtime_decimal = round(overtime_minutes / 60, 2)
