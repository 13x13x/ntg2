# Use the official Python image from Docker Hub
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose a port if required (if the bot interacts via a web service)
# EXPOSE 5000

# Set the default command to run the bot
CMD ["python", "bot.py"]
