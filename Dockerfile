# Use a base Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

COPY source/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY source/ /app/

# Expose Streamlit port
EXPOSE 9000

# Run the app
CMD ["python", "start.py"]