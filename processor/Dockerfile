FROM flink:1.18-java11

# Install Python and pip
USER root
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-dev curl && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set Python environment
ENV PYFLINK_PYTHON=/usr/bin/python3

# Install PyFlink and dependencies
COPY requirements.txt /opt/flink/
RUN pip3 install --no-cache-dir -r /opt/flink/requirements.txt

# Create lib directory
RUN mkdir -p /opt/flink/lib

# Download Kafka connector JAR
RUN curl -L -o /opt/flink/lib/flink-sql-connector-kafka-1.18.0.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/1.18.0/flink-sql-connector-kafka-1.18.0.jar

# Download PostgreSQL JDBC driver
RUN curl -L -o /opt/flink/lib/postgresql-42.7.1.jar \
    https://jdbc.postgresql.org/download/postgresql-42.7.1.jar

# Download Flink JDBC connector
RUN curl -L -o /opt/flink/lib/flink-connector-jdbc-3.1.2-1.18.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.1.2-1.18/flink-connector-jdbc-3.1.2-1.18.jar

# Copy the Flink job
COPY fraud_detector.py /opt/flink/

WORKDIR /opt/flink

# Default command
CMD ["python", "fraud_detector.py"]
