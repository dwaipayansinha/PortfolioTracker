FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create cache directories with appropriate permissions
RUN mkdir -p api_cache && chmod 777 api_cache

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.current", "--port", "8000"]
