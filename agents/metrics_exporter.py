
from prometheus_client import Gauge, start_http_server


agent_status = Gauge(
    "iclim_agent_status",
    "Whether the ICLIM agent is running"
)


def main():
    agent_status.set(1)

    start_http_server(8000)

    print("ICLIM metrics exporter started on port 8000")

    while True:
        pass


if __name__ == "__main__":
    main()
