FROM python:3.12-slim

WORKDIR /app

# Instalar uv
RUN pip install uv

# Copiar archivos de dependencias
COPY pyproject.toml .

# Instalar dependencias
RUN uv sync

# Copiar código fuente
COPY . .

# Puerto por defecto
EXPOSE 8080

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
