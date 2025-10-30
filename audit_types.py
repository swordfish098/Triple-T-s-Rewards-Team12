# audit_types.py

# Canonical names you prefer to use going forward
LOGIN_EVENT = "LOGIN_EVENT"
LOGOUT_EVENT = "LOGOUT_EVENT"
DRIVER_POINTS = "DRIVER_POINTS"
SALES_BY_SPONSOR = "SALES_BY_SPONSOR"
SALES_BY_DRIVER = "SALES_BY_DRIVER"
INVOICE_EVENT = "INVOICE_EVENT"

# === Seen-in-DB variants (from your shell output) ===
LOGIN_VARIANTS = {
    LOGIN_EVENT, LOGOUT_EVENT,            # canonical
    "LOGIN SUCCESS", "LOGOUT"             # legacy/variant strings
}

# If you want password resets to appear with "Login Activity",
# add these here; otherwise move them to a different category.
PASSWORD_VARIANTS = {"RESET REQUEST", "RESET SUCCESS", "RESET"}

BULK_VARIANTS = {
    # plain/prefix forms
    "bulk_load", "bulk_load_processed", "bulk_load_completed",
    "bulk_load_success", "bulk_load_failed",

    # prefixed by the entity
    "sponsor_bulk_load_processed",
    "driver_created_via_bulk_load",
    "organization_created_via_bulk_load",
    "organization_reserved_via_bulk_load",
    "sponsor_created_via_bulk_load",
}

AUDIT_CATEGORIES = {
    # Login/Logout (and optionally password reset)
    "login": LOGIN_VARIANTS | PASSWORD_VARIANTS,

    # Driver point tracking
    "driver_points": {DRIVER_POINTS},

    # Sales tracking (placeholders until you log with these)
    "sales_by_sponsor": {SALES_BY_SPONSOR},
    "sales_by_driver": {SALES_BY_DRIVER},

    # Invoices (placeholder)
    "invoices": {INVOICE_EVENT},

    # Bulk loading
    "bulk_load": BULK_VARIANTS,
}
