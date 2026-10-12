# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /app
# Build-time default, deliberately persisted as a runtime environment variable.
ARG APP_NAME="Docker learner"
ENV APP_NAME=${APP_NAME}
COPY app.py .
USER 10001:10001
CMD ["python", "app.py"]
