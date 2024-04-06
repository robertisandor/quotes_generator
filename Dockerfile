FROM ubuntu:22.04 as build_1
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
WORKDIR /quotes_generator
COPY Cargo* .
COPY diesel.toml .
COPY ./src ./src
RUN cargo build --release
RUN rm src/*.rs

FROM ubuntu:22.04 as build_2
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev=14.11-0ubuntu0.22.04.1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV ROCKET_ADDRESS=0.0.0.0
EXPOSE 8000
COPY --from=build_1 /quotes_generator/target/release/quotes_generator /usr/local/bin/quotes-generator
WORKDIR /usr/local/bin
CMD ["quotes-generator"]