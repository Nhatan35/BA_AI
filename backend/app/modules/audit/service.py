from app.modules.audit.models import AuditLog, SecurityEvent


def audit(db, actor, project_id, action, entity_type, entity_id, metadata=None):
    # Callers supply only allowlisted lifecycle/role/revision metadata, never document/user payloads.
    db.add(
        AuditLog(
            project_id=project_id,
            actor_user_id=actor.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            safe_metadata=metadata or {},
        )
    )
    db.flush()


def security_event(db, action, user_id=None):
    db.add(SecurityEvent(action=action, actor_user_id=user_id))
