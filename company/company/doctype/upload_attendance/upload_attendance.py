import frappe
import pandas as pd
from frappe.model.document import Document
from datetime import datetime
import os

class UploadAttendance(Document):
    pass


@frappe.whitelist()
def import_attendance(docname):
    """
    Import attendance from uploaded CSV, or XLSX file in Upload Attendance DocType.
    Maps Person ID -> employee_id, finds the Employee record, and links employee accordingly.
    """
    try:
        doc = frappe.get_doc("Upload Attendance", docname)
        file_doc = frappe.get_doc("File", {"file_url": doc.attendance_file})
        file_url = file_doc.file_url

        # --- Determine file path ---
        if file_url.startswith("/private/"):
            file_path = frappe.get_site_path(file_url.lstrip("/"))
        elif file_url.startswith("/files/"):
            file_path = frappe.get_site_path("public", file_url.lstrip("/files/"))
        else:
            frappe.throw(f"Unsupported file path: {file_url}")

        if not os.path.exists(file_path):
            frappe.throw(f"File not found: {file_url}")

        # --- Read File ---
        file_name = file_doc.file_name.lower()
        if file_name.endswith(".csv"):
            df = pd.read_csv(file_path, header=4)
        elif file_name.endswith(".xlsx"):
            df = pd.read_excel(file_path, engine='openpyxl', header=4)
        else:
            frappe.msgprint("Unsupported file format! Please upload CSV or XLSX.")
            return

        if df.empty:
            frappe.throw("File has no data!")

        df.columns = [c.strip().lower() for c in df.columns]

        # --- Map CSV columns to Attendance fields ---
        column_map = {
            "person id": "employee_id",
            "name": "employee_name",
            "date": "attendance_date",
            "check-in": "in_time",
            "check-out": "out_time"
        }
        df.rename(columns=lambda x: column_map.get(x, x), inplace=True)

        attendance_fields = ["employee_id", "employee", "employee_name", "attendance_date", "in_time", "out_time", "status"]

        # --- Validate ---
        if "employee_id" not in df.columns:
            frappe.throw("CSV must contain 'Person ID' column!")

        inserted_count = 0
        skipped_count = 0
        error_rows = []

        # --- Process Each Row ---
        for index, row in df.iterrows():
            try:
                row_dict = {k: (None if pd.isna(v) or str(v).strip().lower() in ["", "nan"] else v)
                            for k, v in row.items()}

                person_id = row_dict.get("employee_id")

                if not person_id:
                    error_rows.append(f"Row {index+1}: Missing Person ID")
                    skipped_count += 1
                    continue

                # Normalize Person ID (handle Excel numeric)
                try:
                    person_id = str(int(float(person_id)))
                except Exception:
                    person_id = str(person_id).strip()

                # Normalize Person ID (handle Excel numeric + zero padding)
                try:
                    person_id_raw = str(int(float(person_id)))
                except Exception:
                    person_id_raw = str(person_id).strip()

                # Try match with or without padding (up to 5 digits)
                possible_ids = [person_id_raw.zfill(i) for i in range(1, 6)]
                employee_name = None

                for pid in possible_ids:
                    employee_name = frappe.db.get_value("Employee", {"employee_id": pid}, "name")
                    if employee_name:
                        break

                # If still not found, try match against Employee.name (ERP ID)
                if not employee_name:
                    employee_name = frappe.db.get_value("Employee", {"name": person_id_raw}, "name")

                if not employee_name:
                    error_rows.append(f"Row {index+1}: No Employee found for Person ID '{person_id_raw}'")
                    skipped_count += 1
                    continue

                # Add employee link to row
                row_dict["employee"] = employee_name
                row_dict["employee_id"] = person_id_raw


                # Add employee link to the row
                row_dict["employee"] = employee_name
                row_dict["employee_id"] = person_id  # keep original ID from CSV

                # --- Mark Status ---
                if row_dict.get("in_time") in [None, "-", "–"] or row_dict.get("out_time") in [None, "-", "–"]:
                    row_dict["status"] = "Absent"
                    row_dict["in_time"] = None
                    row_dict["out_time"] = None
                else:
                    row_dict["status"] = "Present"
                    row_dict["in_time"] = normalize_time(row_dict["in_time"])
                    row_dict["out_time"] = normalize_time(row_dict["out_time"])

                # --- Avoid duplicates ---
                existing = frappe.db.exists({
                    "doctype": "Attendance",
                    "employee": row_dict["employee"],
                    "attendance_date": row_dict["attendance_date"]
                })
                if existing:
                    skipped_count += 1
                    error_rows.append(
                        f"Row {index+1}: Attendance already exists for {row_dict['employee']} on {row_dict['attendance_date']}"
                    )
                    continue

                # --- Create Attendance ---
                attendance_doc = frappe.get_doc({
                    "doctype": "Attendance",
                    "employee": row_dict["employee"],
                    "employee_id": row_dict["employee_id"],
                    "employee_name": row_dict.get("employee_name"),
                    "attendance_date": row_dict.get("attendance_date"),
                    "in_time": row_dict.get("in_time"),
                    "out_time": row_dict.get("out_time"),
                    "status": row_dict.get("status")
                })
                attendance_doc.insert(ignore_permissions=True)
                inserted_count += 1

            except Exception as e:
                error_rows.append(f"Row {index+1}: {str(e)}")

        frappe.db.commit()

        msg = f"{inserted_count} Attendance records imported successfully."
        if skipped_count:
            msg += f"<br>{skipped_count} records skipped."
        if error_rows:
            msg += "<br><br>Errors:<br>" + "<br>".join(error_rows)

        return msg

    except Exception as e:
        frappe.throw(f"Error importing attendance: {e}")


def normalize_time(value):
    """Normalize time from string or Excel float to HH:MM format."""
    if value in [None, "-", "–", "nan"]:
        return None

    try:
        if isinstance(value, (int, float)):
            time_obj = pd.to_datetime(value, unit='d', origin='1899-12-30').time()
            return time_obj.strftime("%H:%M")
    except Exception:
        pass

    value = str(value).strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt).strftime("%H:%M")
        except ValueError:
            continue

    raise ValueError(f"Invalid time format: {value}")
