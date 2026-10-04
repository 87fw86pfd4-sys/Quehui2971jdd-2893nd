import hashlib
import hmac
import os
import sys
import time
from urllib.parse import urlencode

import requests


BASE_URL = "https://api.bybit.eu"
RECV_WINDOW = "5000"
HTTP_TIMEOUT = 15

API_KEY = os.getenv("BYBIT_API_KEY", "").strip()
API_SECRET = os.getenv("BYBIT_API_SECRET", "").strip()


def stop(message: str) -> None:
    print(f"ERROR: {message}", flush=True)
    sys.exit(1)


def check_secrets() -> None:
    if not API_KEY:
        stop("BYBIT_API_KEY ontbreekt in GitHub Secrets.")

    if not API_SECRET:
        stop("BYBIT_API_SECRET ontbreekt in GitHub Secrets.")

    print("OK - GitHub Secrets gevonden.", flush=True)


def check_public_api() -> None:
    url = f"{BASE_URL}/v5/market/time"

    try:
        response = requests.get(
            url,
            timeout=HTTP_TIMEOUT,
        )
    except requests.RequestException as exc:
        stop(
            "Kan Bybit EU niet bereiken: "
            f"{type(exc).__name__}"
        )

    if response.status_code != 200:
        stop(
            "Bybit EU public API gaf HTTP "
            f"{response.status_code}"
        )

    try:
        data = response.json()
    except ValueError:
        stop("Bybit gaf geen geldige JSON terug.")

    if data.get("retCode") != 0:
        stop(
            "Bybit public API fout: "
            f"{data.get('retCode')} - "
            f"{data.get('retMsg')}"
        )

    print("OK - Bybit EU API bereikbaar.", flush=True)


def signed_get(path: str, params: dict | None = None) -> dict:
    params = params or {}

    query_string = urlencode(
        sorted(params.items())
    )

    timestamp = str(
        int(time.time() * 1000)
    )

    string_to_sign = (
        timestamp
        + API_KEY
        + RECV_WINDOW
        + query_string
    )

    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-SIGN": signature,
        "X-BAPI-RECV-WINDOW": RECV_WINDOW,
    }

    url = f"{BASE_URL}{path}"

    if query_string:
        url = f"{url}?{query_string}"

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=HTTP_TIMEOUT,
        )
    except requests.RequestException as exc:
        stop(
            "Private Bybit request mislukt: "
            f"{type(exc).__name__}"
        )

    try:
        data = response.json()
    except ValueError:
        stop(
            "Private Bybit API gaf geen geldige JSON terug. "
            f"HTTP status: {response.status_code}"
        )

    if response.status_code != 200:
        stop(
            "Private Bybit API gaf HTTP "
            f"{response.status_code}: "
            f"{data.get('retMsg', 'onbekende fout')}"
        )

    if data.get("retCode") != 0:
        stop(
            "Bybit API fout: "
            f"{data.get('retCode')} - "
            f"{data.get('retMsg')}"
        )

    return data


def check_api_key() -> None:
    data = signed_get(
        "/v5/user/query-api"
    )

    result = data.get("result", {})

    read_only = result.get("readOnly")
    permissions = result.get("permissions", {})
    note = result.get("note", "")
    deadline_days = result.get("deadlineDay")

    print("OK - API key + API secret werken.", flush=True)

    if note:
        print(
            f"API naam: {note}",
            flush=True,
        )

    if read_only == 1:
        print(
            "OK - API key is READ-ONLY.",
            flush=True,
        )
    elif read_only == 0:
        print(
            "WAARSCHUWING - API key heeft READ + WRITE rechten.",
            flush=True,
        )
    else:
        print(
            f"WAARSCHUWING - Onbekende readOnly waarde: {read_only}",
            flush=True,
        )

    if deadline_days is not None:
        print(
            f"Resterende geldigheid: {deadline_days} dagen",
            flush=True,
        )

    if isinstance(permissions, dict):
        spot_permissions = permissions.get(
            "Spot",
            []
        )

        wallet_permissions = permissions.get(
            "Wallet",
            []
        )

        print(
            f"Spot permissions: {spot_permissions}",
            flush=True,
        )

        print(
            f"Wallet permissions: {wallet_permissions}",
            flush=True,
        )

    if read_only != 1:
        stop(
            "Voor deze eerste test verwacht BOT FIN "
            "een read-only API key."
        )


def main() -> None:
    print(
        "==============================================",
        flush=True,
    )
    print(
        "BOT FIN - BYBIT EU CONNECTION TEST",
        flush=True,
    )
    print(
        "==============================================",
        flush=True,
    )

    check_secrets()
    check_public_api()
    check_api_key()

    print(
        "==============================================",
        flush=True,
    )
    print(
        "SUCCESS - GITHUB IS VERBONDEN MET BYBIT",
        flush=True,
    )
    print(
        "READ-ONLY - ER KAN NIET WORDEN GEKOCHT OF VERKOCHT",
        flush=True,
    )
    print(
        "==============================================",
        flush=True,
    )


if __name__ == "__main__":
    main()
