# syntax=docker/dockerfile:1
# Stage 1 contains the compiler; it is not shipped in the final image.
FROM debian:bookworm-slim AS builder
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY hello.c .
RUN gcc -Wall -Wextra -Werror -O2 hello.c -o /hello

# Matching Debian releases supply compatible runtime libraries.
FROM debian:bookworm-slim AS runtime
WORKDIR /app
COPY --from=builder /hello /app/hello
USER 10001:10001
CMD ["/app/hello"]
