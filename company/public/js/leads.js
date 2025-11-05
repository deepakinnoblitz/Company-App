frappe.ui.form.on("Leads", {
    after_save: function(frm) {
        if (frm.doc.move_to_party === "Moved") {
            // 🔍 Check if a Customer linked with this Lead already exists
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Customer",
                    filters: { lead: frm.doc.name }, // check by Lead ID
                    fields: ["name"]
                },
                callback: function(r) {
                    if (!r.message || r.message.length === 0) {
                        // 🚀 No customer exists, create a new one
                        frappe.call({
                            method: "frappe.client.insert",
                            args: {
                                doc: {
                                    doctype: "Customer",
                                    customer_name: frm.doc.lead_name,   // Lead Name → Customer Name
                                    company_name: frm.doc.company_name,
                                    gstin: frm.doc.gstin,
                                    phone_number: frm.doc.phone_number,
                                    email: frm.doc.email,
                                    country: frm.doc.country,
                                    state: frm.doc.state,
                                    billing_address: frm.doc.billing_address,
                                    remarks: frm.doc.remarks,
                                    assigned_to: frm.doc.assigned_to,
                                    lead: frm.doc.name   // ✅ correctly link Lead to Customer
                                }
                            },
                            callback: function(res) {
                                if (!res.exc) {
                                    // ✅ Update Lead's customer_created flag in DB
                                    frappe.call({
                                        method: "frappe.client.set_value",
                                        args: {
                                            doctype: "Leads",
                                            name: frm.doc.name,
                                            fieldname: {
                                                customer_created: 1
                                            }
                                        },
                                        callback: function() {
                                            frm.reload_doc(); // refresh UI after updating
                                            frappe.msgprint("✅ Customer created and Lead updated successfully!");
                                        }
                                    });
                                }
                            }
                        });
                    }
                }
            });
        }
    }
});
