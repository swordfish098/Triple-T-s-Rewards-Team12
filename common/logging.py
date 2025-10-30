from extensions import db
from models import AuditLog
import logging
from datetime import datetime

#Event Type Conventions
SALES_BY_SPONSOR = "SALES_BY_SPONSOR"
SALES_BY_DRIVER  = "SALES_BY_DRIVER"
INVOICE_EVENT    = "INVOICE_EVENT"
DRIVER_POINTS    = "DRIVER_POINTS"
LOGIN_EVENT    = "LOGIN_EVENT"

logging.basicConfig(level=logging.INFO)

def log_audit_event(event_type: str, details: str = ""):
    log_entry = AuditLog(
        EVENT_TYPE=event_type,
        DETAILS=details or None,
        CREATED_AT=datetime.utcnow()
    )
    db.session.add(log_entry)
    db.session.commit()
    logging.info("AUDIT: %s - %s", event_type, details)
    return log_entry