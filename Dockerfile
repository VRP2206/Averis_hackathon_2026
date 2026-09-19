# SDOC API: the pipeline behind FastAPI.
#   docker build -t sdoc-api .
#   docker run -p 8000:8000 --env-file .env sdoc-api
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY sdoc ./sdoc
RUN pip install --no-cache-dir .

# The participant dataset ships with the image; the answer key is mounted at run time (see docker-compose.yml).
COPY ["Provided Information/Participant Info", "Provided Information/Participant Info"]

EXPOSE 8000
CMD ["uvicorn", "sdoc.api:app", "--host", "0.0.0.0", "--port", "8000"]
