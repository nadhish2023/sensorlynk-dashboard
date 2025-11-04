# Use the official Python base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./requirements.txt

# Install the Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code (dashboard.py)
COPY . .

# Expose the port that Streamlit runs on
EXPOSE 8501

# The command to run when the container starts
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]