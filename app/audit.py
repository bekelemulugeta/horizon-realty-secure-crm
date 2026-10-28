
import json
from flask import session, request
from app.models import db, AuditLog


def log_action(action, target_type=None, target_id=None, before=None, after=None):
    entry = AuditLog(
        actor_user_id=session.get("user_id"),
        actor_username=session.get("username"),
        action=action,
        target_type=target_type,
        target_id=target_id,
        before_state=json.dumps(before) if before is not None else None,
        after_state=json.dumps(after) if after is not None else None,
        ip_address=request.remote_addr,
    )
    db.session.add(entry)
    # Deliberately NOT committing here 

