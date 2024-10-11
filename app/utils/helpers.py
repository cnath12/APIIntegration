from flask import request, url_for

def ensure_https(url):
    """Ensure that the given URL uses HTTPS."""
    if url.startswith('http:'):
        return url.replace('http:', 'https:', 1)
    return url

def https_url_for(endpoint, **values):
    """Like url_for, but ensures the URL uses HTTPS."""
    url = url_for(endpoint, **values, _external=True)
    return ensure_https(url)