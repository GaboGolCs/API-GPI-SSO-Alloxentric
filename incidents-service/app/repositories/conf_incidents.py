from google.cloud import firestore

# Según tu especificación 6.1: "El cliente Python soporta async/await"
# Instanciamos el cliente asíncrono.
# Nota: En Cloud Run, esto tomará las credenciales automáticamente (Workload Identity).
db = firestore.AsyncClient()


def get_db():
    return db
