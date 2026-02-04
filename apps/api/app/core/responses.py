"""HTTP response utilities for common status codes."""

from fastapi import Response, status


def empty_response(status_code: int) -> Response:
    """Return an empty response with the given status code.

    Use this for status codes that are self-explanatory and don't need a body.
    Examples: 204 No Content, 404 Not Found, 401 Unauthorized

    Args:
        status_code: The HTTP status code to return.

    Returns:
        A Response object with the given status code and no body.
    """
    return Response(status_code=status_code)


def no_content() -> Response:
    """Return 204 No Content response."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def not_found() -> Response:
    """Return 404 Not Found response."""
    return Response(status_code=status.HTTP_404_NOT_FOUND)


def unauthorized() -> Response:
    """Return 401 Unauthorized response."""
    return Response(status_code=status.HTTP_401_UNAUTHORIZED)


def forbidden() -> Response:
    """Return 403 Forbidden response."""
    return Response(status_code=status.HTTP_403_FORBIDDEN)


def bad_request() -> Response:
    """Return 400 Bad Request response."""
    return Response(status_code=status.HTTP_400_BAD_REQUEST)
