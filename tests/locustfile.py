"""Free load test: infrastructure endpoints only by default."""
import os

from locust import HttpUser, between, task


class NerfSQLUser(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(5)
    def health(self):
        self.client.get("/health", name="GET /health")

    @task(2)
    def connections(self):
        self.client.get("/connections", name="GET /connections")

    @task(2)
    def schema(self):
        connection_id = os.getenv("BENCHMARK_CONNECTION_ID")
        path = f"/schema?connection_id={connection_id}" if connection_id else "/schema"
        self.client.get(path, name="GET /schema")

    @task(1)
    def providers(self):
        self.client.get("/providers", name="GET /providers")


