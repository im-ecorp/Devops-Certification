# syntax=docker/dockerfile:1
FROM alpine:3.22
WORKDIR /app
COPY greet.sh .
USER 10001:10001
# Calling sh explicitly means the script does not require executable permissions.
ENTRYPOINT ["sh", "/app/greet.sh"]
CMD ["Docker learner"]
