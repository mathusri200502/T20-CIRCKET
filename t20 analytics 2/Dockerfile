FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose a default port; hosting platform should provide $PORT at runtime
EXPOSE 8000

# Use sh -c so $PORT env var is expanded
CMD ["sh","-c","gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} app:app"]
