FROM python:3.9-slim-buster

# Install C++ build tools
RUN apt-get update && apt-get install -y build-essential

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD ["python3", "main.py"]