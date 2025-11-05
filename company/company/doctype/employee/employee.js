// Copyright (c) 2025, deepak and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Employee", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Employee', {
    onload(frm) {
        const restricted_fields = [
            "basic_pay",
            "hra",
            "conveyance_allowances",
            "medical_allowances",
            "other_allowances",
            "pf",
            "health_insurance",
            "professional_tax",
            "loan_recovery",
            "employee_id",
            "date_of_joining",
            "pf_number",
            "esi_no",
            "status",
            "user",
            "bank_account",
            "bank_name",
            "office_phone_number",
            "department",
            "designation"
        ];

        // Check if current user has the HR role
        const is_hr = frappe.user.has_role('HR');

        // Loop through all restricted fields
        restricted_fields.forEach(field => {
            frm.set_df_property(field, 'read_only', is_hr ? 0 : 1);
        });
    }
});

