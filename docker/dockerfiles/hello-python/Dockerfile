# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /app
COPY hello.py .
# Numeric user: this script needs no home directory or writable files.
USER 10001:10001
CMD ["python", "hello.py"]
