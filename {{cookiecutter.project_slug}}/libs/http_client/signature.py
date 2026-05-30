from typing import Protocol


class SignatureProvider(Protocol):
    def sign_request(
        self, method: str, path: str, headers: dict[str, str], body: bytes | None
    ) -> dict[str, str]:
        ...
