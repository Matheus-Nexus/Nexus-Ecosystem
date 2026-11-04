# Dockerfile para NEXUS Ecosystem
FROM python:3.11-slim

# Configura o working directory
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requirements
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do NEXUS
COPY . .

# Cria o diretório de backups
RUN mkdir -p /app/backups

# Define a variável de ambiente para o SQLite
ENV NEXUS_DB_PATH=/app/nexus_state.db

# Expõe a porta da API (FastAPI)
EXPOSE 8000

# Comando de entrada
CMD ["python", "main.py"]
