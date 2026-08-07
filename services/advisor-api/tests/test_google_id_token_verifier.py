import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from hive_sight_advisor_api.google_sign_in import GoogleIdTokenVerifier, InvalidGoogleIdToken

CLIENT_ID = "my-client-id.apps.googleusercontent.com"
CERTS_URL = "https://fake.example/certs"


class _FakeResponse:
    def __init__(self, data: dict) -> None:
        self.status = 200
        self.data = json.dumps(data).encode("utf-8")


class _FakeTransport:
    def __init__(self, certs: dict) -> None:
        self._certs = certs

    def __call__(self, url, method="GET"):
        return _FakeResponse(self._certs)


def _make_signed_token(claims: dict, key, kid: str = "test-kid") -> str:
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid})


def _make_keypair_and_certs(kid: str = "test-kid"):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    public_jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return key, {"keys": [public_jwk]}


def _default_claims(**overrides) -> dict:
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": "1234567890",
        "email": "beekeeper@example.com",
        "name": "Bea Keeper",
        "iat": now,
        "exp": now + 3600,
    }
    claims.update(overrides)
    return claims


def test_verify_accepts_a_validly_signed_token_and_extracts_claims() -> None:
    key, certs = _make_keypair_and_certs()
    token = _make_signed_token(_default_claims(), key)
    verifier = GoogleIdTokenVerifier(
        client_id=CLIENT_ID, transport=_FakeTransport(certs), certs_url=CERTS_URL
    )

    identity = verifier.verify(token)

    assert identity.sub == "1234567890"
    assert identity.email == "beekeeper@example.com"
    assert identity.name == "Bea Keeper"


def test_verify_rejects_a_token_with_the_wrong_audience() -> None:
    key, certs = _make_keypair_and_certs()
    token = _make_signed_token(_default_claims(aud="someone-elses-client-id"), key)
    verifier = GoogleIdTokenVerifier(
        client_id=CLIENT_ID, transport=_FakeTransport(certs), certs_url=CERTS_URL
    )

    with pytest.raises(InvalidGoogleIdToken):
        verifier.verify(token)


def test_verify_rejects_a_token_with_the_wrong_issuer() -> None:
    key, certs = _make_keypair_and_certs()
    token = _make_signed_token(_default_claims(iss="https://not-google.example"), key)
    verifier = GoogleIdTokenVerifier(
        client_id=CLIENT_ID, transport=_FakeTransport(certs), certs_url=CERTS_URL
    )

    with pytest.raises(InvalidGoogleIdToken):
        verifier.verify(token)


def test_verify_rejects_an_expired_token() -> None:
    key, certs = _make_keypair_and_certs()
    now = int(time.time())
    token = _make_signed_token(_default_claims(iat=now - 7200, exp=now - 3600), key)
    verifier = GoogleIdTokenVerifier(
        client_id=CLIENT_ID, transport=_FakeTransport(certs), certs_url=CERTS_URL
    )

    with pytest.raises(InvalidGoogleIdToken):
        verifier.verify(token)


def test_verify_rejects_a_token_whose_signing_key_isnt_in_the_certs() -> None:
    signing_key, _unused_certs = _make_keypair_and_certs()
    token = _make_signed_token(_default_claims(), signing_key)
    # No matching kid in the served certs, as if the real key had been rotated out.
    verifier = GoogleIdTokenVerifier(
        client_id=CLIENT_ID,
        transport=_FakeTransport({"keys": []}),
        certs_url=CERTS_URL,
    )

    with pytest.raises(InvalidGoogleIdToken):
        verifier.verify(token)
