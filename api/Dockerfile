# Lab 10 — backend Dockerfile. Author this file.
#
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first so pip install layer is cached separately
# from the source code — a code change won't re-install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Now copy the rest of the source tree.
COPY . .

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
