"""Serves the built dashboard (`frontend/dist`) from the API server.

The dashboard is a single-page app: the browser handles paths like
`/runs/<id>` itself. So a path with no file behind it gets `index.html`,
and a page refresh still works. Paths under `/api` are left alone, so a
wrong API path still answers 404.
"""

from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


class SinglePageApp(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as error:
            # `scope["path"]` is the URL path; `path` uses the OS separator (`\` on Windows).
            if error.status_code != 404 or scope["path"].startswith("/api/"):
                raise
            return await super().get_response("index.html", scope)
