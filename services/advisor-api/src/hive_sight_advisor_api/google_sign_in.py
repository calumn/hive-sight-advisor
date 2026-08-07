from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


class InvalidGoogleIdToken(Exception):
    pass


@dataclass(frozen=True)
class GoogleIdentity:
    sub: str
    email: str | None
    name: str | None


class _Transport(Protocol):
    def __call__(self, url: str, method: str = "GET"): ...


class GoogleIdTokenVerifier:
    def __init__(
        self,
        client_id: str,
        transport: _Transport | None = None,
        certs_url: str = GOOGLE_CERTS_URL,
    ) -> None:
        self._client_id = client_id
        self._transport = transport if transport is not None else GoogleAuthRequest()
        self._certs_url = certs_url

    def verify(self, token: str) -> GoogleIdentity:
        try:
            claims = google_id_token.verify_token(
                token,
                self._transport,
                audience=self._client_id,
                certs_url=self._certs_url,
            )
        except Exception as exc:
            raise InvalidGoogleIdToken(str(exc)) from exc

        if claims.get("iss") not in GOOGLE_ISSUERS:
            raise InvalidGoogleIdToken(f"Unexpected issuer: {claims.get('iss')!r}")

        return GoogleIdentity(
            sub=claims["sub"],
            email=claims.get("email"),
            name=claims.get("name"),
        )
