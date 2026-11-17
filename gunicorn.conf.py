import os


def post_worker_init(worker):
    if os.environ.get("START_CLOUD_COLLECTOR", "").lower() == "true":
        from cloud_collector import start_collector

        started = start_collector()
        worker.log.warning(
            "COLLECTOR START: pid=%s started=%s",
            os.getpid(),
            started,
        )
