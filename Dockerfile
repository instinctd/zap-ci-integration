FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt


RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000
ENV FLASK_APP=app.py

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
