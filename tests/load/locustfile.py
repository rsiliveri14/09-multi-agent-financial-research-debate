"""Locust user mix for the debate API.

Host CPU monitoring is disabled: Locust's psutil `cpu_count()` probe crashes in
some sandboxes and would abort a healthy run.
"""

from __future__ import annotations

import gevent
from locust import HttpUser, between, task
from locust.runners import Runner


def _skip_host_cpu_monitor(_self) -> None:
    while True:
        gevent.sleep(60)


Runner.monitor_cpu_and_memory = _skip_host_cpu_monitor  # type: ignore[method-assign]


class DebateUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self) -> None:
        self.headers = {"Authorization": "Bearer dev-analyst-token"}

    @task(3)
    def health(self) -> None:
        self.client.get("/health")

    @task(1)
    def debate(self) -> None:
        self.client.post(
            "/v1/debate",
            json={"question": "What were Amazon net sales and AWS net sales in 2024?"},
            headers=self.headers,
        )
