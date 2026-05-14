"""9R-2.1 Unified Exception Hierarchy."""


class KL9Error(Exception):
    def __init__(self, message: str = "", *, code: str = "KL9-000", details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class LLMError(KL9Error):
    def __init__(self, message: str = "", *, code: str = "LLM-000", provider: str | None = None, details: dict | None = None):
        super().__init__(message, code=code, details=details)
        self.provider = provider


class ProviderError(LLMError):
    pass


class ProviderAuthError(ProviderError):
    pass


class ProviderRateLimitError(ProviderError):
    pass


class ProviderTimeoutError(ProviderError):
    pass


class ProviderBadRequestError(ProviderError):
    pass


class ProviderServerError(ProviderError):
    pass


class RoutingError(KL9Error):
    pass


class FoldError(KL9Error):
    pass


class QualityValidationError(KL9Error):
    pass


class ConfigurationError(KL9Error):
    pass


class MigrationError(KL9Error):
    pass
