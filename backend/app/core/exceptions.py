class HealthCheckError(Exception):
    def __init__(self, checks: dict[str, bool]) -> None:
        self.checks = checks
        super().__init__("health check failed")
