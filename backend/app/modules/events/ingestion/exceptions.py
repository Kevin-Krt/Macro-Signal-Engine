class ConnectorError(Exception):
    """
    Base class for every connector failure.
    """


class ConnectorFetchError(ConnectorError):
    def __init__(self, source: str, status: int | None = None) -> None:
        self.source = source
        self.status = status
        super().__init__(
            f"{source}: fetch failed" + (f" (HTTP {status})" if status else "")
        )


class ConnectorParseError(ConnectorError):
    def __init__(self, source: str, external_id: str | None = None) -> None:
        self.source = source
        self.external_id = external_id
        super().__init__(f"{source}: failed to parse event {external_id or '?'}")
