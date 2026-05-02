from app.services.srv_incidents import IncidentService


def get_current_user():
    return {"user_id": "usr_abc123", "role": "sso_manager", "tenant": "planta_norte"}


# Crea una instancia de IncidentService para ser usada como dependencia en los endpoints.
def get_incident_service():
    return IncidentService()
