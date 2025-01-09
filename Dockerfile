# Usa una imagen oficial de Python como base
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo .env y el archivo de requerimientos (si tienes uno) al contenedor
COPY .env /app/.env
COPY requirements.txt /app/requirements.txt
COPY . /app/

# Instala las dependencias necesarias desde el archivo requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expon la porta que la app FastAPI usará
EXPOSE 3000

# Comando para correr la app FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]