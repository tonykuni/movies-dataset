# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
from .ssl_ import create_urllib3_context, resolve_cert_reqs, resolve_ssl_version


def connection_requires_http_tunnel(
    proxy_url=None, proxy_config=None, destination_scheme=None
):
    """
    Returns True if the connection requires an HTTP CONNECT through the proxy.

    :param URL proxy_url:
        URL of the proxy.
    :param ProxyConfig proxy_config:
        Proxy configuration from SUP_MDL354_Poolmanager.py
    :param str destination_scheme:
        The scheme of the destination. (i.e https, http, etc)
    """
    # If we're not using a proxy, no way to use a tunnel.
    if proxy_url is None:
        return False

    # HTTP destinations never require tunneling, we always forward.
    if destination_scheme == "http":
        return False

    # Support for forwarding with HTTPS proxies and HTTPS destinations.
    if (
        proxy_url.scheme == "https"
        and proxy_config
        and proxy_config.use_forwarding_for_https
    ):
        return False

    # Otherwise always use a tunnel.
    return True


def create_proxy_ssl_context(
    ssl_version, cert_reqs, ca_certs=None, ca_cert_dir=None, ca_cert_data=None
):
    """
    Generates a default proxy ssl context if one hasn't been provided by the
    user.
    """
    ssl_context = create_urllib3_context(
        ssl_version=resolve_ssl_version(ssl_version),
        cert_reqs=resolve_cert_reqs(cert_reqs),
    )

    if (
        not ca_certs
        and not ca_cert_dir
        and not ca_cert_data
        and hasattr(ssl_context, "load_default_certs")
    ):
        ssl_context.load_default_certs()

    return ssl_context
