class ReportsService:
    def __init__(self):
        # Puedes inicializar la conexión a la DB aquí si lo necesitas
        print("Servicio de Reportes inicializado")

    async def get_reports(self):
        return [
            {
                "title": "Reporte de Prueba 1",
                "type": "incident",
                "filters_applied": {
                    "additionalProp1": {
                        "date_range": "2024-05-01 to 2024-05-31",
                        "plant": "planta_norte",
                    }
                },
                "id": "rep_123",
                "generated_by": "usr_abc123",
                "generated_at": "2024-06-01T12:00:00Z",
                "file_url": "https://storage.googleapis.com/bucket_name/reports/rep_123.pdf",
            }
        ]
