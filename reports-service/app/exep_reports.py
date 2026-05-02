from fastapi import HTTPException, status


# Creamos errores personalizados para luego solo importarlos y usarlos en el service,
# así mantenemos el código limpio y organizado.
class AreaNotFoundError(HTTPException):
    def __init__(self, area_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El área con ID {area_id} no fue encontrada.",
        )


# Luego en tu service simplemente harías:
# raise AreaNotFoundError(report_data.area_id)
