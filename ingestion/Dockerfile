FROM debian:12-slim
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update && apt upgrade -y && apt install python3.11 python3.11-venv python3-pip nano -y 
COPY src/ /src/
RUN python3.11 -m venv env 
# && source env/bin/activate
# RUN pip3 install requests datetime boto3 random_header_generator
# python3.11 src/target_store_location_webscraper.py




