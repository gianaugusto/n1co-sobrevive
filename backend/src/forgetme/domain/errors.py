"""Domain errors. They carry no HTTP or infrastructure concerns."""


class DomainError(Exception):
    """Base class for every error raised by the domain and application layers."""


class ProcessNotFoundError(DomainError):
    def __init__(self, process_id: object) -> None:
        super().__init__(f"Process {process_id} not found")


class SubscriberNotFoundError(DomainError):
    def __init__(self, process_id: object, subscriber: str) -> None:
        super().__init__(f"Subscriber '{subscriber}' not found in process {process_id}")


class RetryNotAllowedError(DomainError):
    def __init__(self, subscriber: str, status: str) -> None:
        super().__init__(f"Only failed subscribers can be retried; '{subscriber}' is {status}")


class PublishError(DomainError):
    """The message broker did not accept a message."""
