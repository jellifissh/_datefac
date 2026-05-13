import os
import sys

import requests


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_kv(key: str, value) -> None:
    print(f"{key}: {value}")


def test_url(url: str, headers: dict | None = None, use_stream: bool = False, timeout: int = 20) -> None:
    print(f"- GET {url}")
    response = None
    try:
        response = requests.get(
            url,
            headers=headers or {},
            allow_redirects=True,
            timeout=timeout,
            stream=use_stream,
        )
        print(f"  status_code={response.status_code}")
        print(f"  content-length={response.headers.get('content-length', '')}")
        print(f"  content-range={response.headers.get('content-range', '')}")
        print(f"  final_url={response.url}")
    except Exception as exc:
        print(f"  exception_type={type(exc).__name__}")
        print(f"  exception_message={exc}")
    finally:
        if response is not None:
            response.close()


def main() -> int:
    print_section("Runtime")
    print_kv("sys.executable", sys.executable)

    print_section("Proxy & Requests")
    print_kv("HTTP_PROXY", os.environ.get("HTTP_PROXY", ""))
    print_kv("HTTPS_PROXY", os.environ.get("HTTPS_PROXY", ""))
    print_kv("http_proxy", os.environ.get("http_proxy", ""))
    print_kv("https_proxy", os.environ.get("https_proxy", ""))
    with requests.Session() as session:
        print_kv("requests.Session().trust_env", session.trust_env)

    print_section("Network Checks")
    test_url("https://models.datalab.to")
    test_url("https://models.datalab.to/layout/2025_09_23/manifest.json")
    test_url(
        "https://models.datalab.to/layout/2025_09_23/model.safetensors",
        headers={"Range": "bytes=0-1023"},
        use_stream=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
