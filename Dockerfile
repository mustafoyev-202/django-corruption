FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /corruption

# Copy and install dependencies
COPY requirements.txt /corruption/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt --timeout 100 --retries 5

# Copy project files
COPY . /corruption/

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
