# Build stage
FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y \
    make \
    unzip \
    sqlite3 \
    libsqlite3-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY autograding_src/ ./autograding_src/
COPY data/ ./data/

WORKDIR /build/autograding_src
RUN make clean && make

# Runtime stage
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    make \
    unzip \
    sqlite3 \
    libsqlite3-0 \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -s /bin/bash grader
USER grader
WORKDIR /home/grader

# Copy only the built binaries and data
COPY --from=builder --chown=grader:grader /build/autograding_src/autograder ./autograding_src/
COPY --from=builder --chown=grader:grader /build/data/ ./data/

WORKDIR /home/grader