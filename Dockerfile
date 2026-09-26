FROM python:3.11-slim

WORKDIR /app

# curl is needed for the HEALTHCHECK below; not present in python:slim by default
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first so this layer is cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the app
COPY . .

EXPOSE 8501

# Streamlit-specific flags: bind to all interfaces, disable telemetry prompt,
# and turn off CORS/XSRF checks that otherwise break when running behind
# Streamlit Community Cloud's proxy or a local port-forward
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "code_files/app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]