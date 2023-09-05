FROM ubuntu:latest
ARG DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt install -y build-essential \
curl \
pkg-config \
libssl-dev \
postgresql \
libpq-dev

RUN apt update
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN rustup default nightly
RUN cargo install diesel_cli --no-default-features --features postgres
RUN USER=root cargo new --bin quotes-generator
WORKDIR "/quotes_generator"
COPY . .
RUN cargo build --release
RUN rm src/*.rs

FROM ubuntu:latest
ARG DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt install -y libpq-dev
ENV ROCKET_ADDRESS=0.0.0.0
EXPOSE 8000
COPY --from=0 /quotes_generator/target/release/quotes-generator /usr/local/bin/quotes-generator
WORKDIR /usr/local/bin
CMD ["quotes-generator"]