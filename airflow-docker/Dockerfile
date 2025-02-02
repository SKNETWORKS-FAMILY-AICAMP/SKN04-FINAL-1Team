FROM apache/airflow:2.7.1

USER root

# Install basic utilities
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow 