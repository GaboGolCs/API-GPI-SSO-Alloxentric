from app.services.incident_service import IncidentService


def get_current_user():
    return {"user_id": "usr_abc123", "role": "sso_manager", "tenant": "planta_norte"}


def get_incident_service():
    return IncidentService()
