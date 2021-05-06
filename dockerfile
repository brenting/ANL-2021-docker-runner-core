FROM openjdk:8-jdk-alpine AS java

FROM python:3.6-alpine
COPY --from=java / /
WORKDIR /app/
COPY run.py run.py
ADD scripts scripts
RUN ["pip3", "install", "pyyaml"]
CMD ["python3", "run.py"]