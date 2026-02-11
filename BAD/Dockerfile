# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Define environment variable fallback (optional, can be overridden)
# ENV NAME World

# Run tickets_assistant.py when the container launches
# We use -u for unbuffered output to see logs in real-time
CMD ["python", "-u", "src/bridge/tickets_assistant.py"]
