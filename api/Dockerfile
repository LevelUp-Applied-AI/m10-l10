# Lab 10 — backend Dockerfile.
#
# Build context is the repo root (parent of api/) — see docker-compose.yml
# (`context: .`, `dockerfile: api/Dockerfile`) and the CI docker job
# (`docker build -f api/Dockerfile .`). Running `uvicorn api.main:app`
# from /app preserves the starter's package-relative imports
# (`from .deps import ...`); `cd api && uvicorn main:app` would break them.
FROM python:3.11-slim

WORKDIR /app

# Cache-friendly layer order: install requirements before copying the
# rest of the source so a code change does not bust the pip layer.
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install the spaCy English model needed by /extract.
RUN python -m spacy download en_core_web_sm

# Copy the rest of the build context (the api/ package lands at /app/api/).
COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
