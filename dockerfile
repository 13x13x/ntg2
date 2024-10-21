# Use the official Python image from Docker Hub
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code and new.py into the container
COPY bot.py /app/
COPY new.py /app/

# Command to run the bot
CMD ["python3", "bot.py"]
