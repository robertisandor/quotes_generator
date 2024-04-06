FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates=20230311ubuntu0.22.04.1 \
    build-essential=12.9ubuntu3 \
    curl=7.81.0-1ubuntu1.16 \
    pkg-config=0.29.2-1ubuntu3 \
    libssl-dev=3.0.2-0ubuntu1.15 \
    postgresql-14 \
    libpq-dev=14.11-0ubuntu0.22.04.1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* 

RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN rustup default stable
RUN cargo install diesel_cli@2.1.1 --no-default-features --features postgres
RUN USER=root cargo new --bin quotes-generator
RUN curl --proto '=https' --tlsv1.2 -sSfL https://sh.vector.dev | bash -s -- -y
WORKDIR /quotes_generator
COPY Cargo* .
COPY diesel.toml .
COPY ./src ./src
CMD ["bash"]