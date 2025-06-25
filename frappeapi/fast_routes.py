"""
FastAPI-style path routing for **FrappeAPI**
==============================================

Purpose
----------
- Enable decorators like `@app.get("/items/{code}")` next to the existing
  dotted-path system.
- Use routes registered in the FrappeAPI app instance without duplication.
- Leave every Frappe lifecycle guarantee intact (DB, auth, error handling).

How it works
--------------
1. Each FrappeAPI instance registers routes in its self.router.routes collection.
2. At import time we monkey-patch **`frappe.api.handle`**:
   - For every `/api/**` request we check against the registered routes.
   - On a match, we extract path parameters and call the corresponding handler.
   - If nothing matches we fall back to the original `frappe.api.handle`.
"""

from __future__ import annotations

import types
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Type, Union

if TYPE_CHECKING:
	from unittest.mock import Mock

	frappe = Mock()
else:
	import frappe

from fastapi.datastructures import Default
from starlette.routing import Match, Route
from werkzeug.wrappers import Response as WerkzeugResponse

from frappeapi.responses import JSONResponse

__all__ = [
	"GET",
	"POST",
	"PUT",
	"DELETE",
	"PATCH",
	"OPTIONS",
	"HEAD",
	"register_app",
]

_FRAPPEAPI_INSTANCES = []


def register_app(app):
	"""Register a FrappeAPI instance to be considered for routing."""
	if app not in _FRAPPEAPI_INSTANCES:
		_FRAPPEAPI_INSTANCES.append(app)


def _factory(methods: List[str]) -> Callable:
	def decorator(
		path: str,
		*,
		response_model: Any = Default(None),
		status_code: Optional[int] = None,
		description: Optional[str] = None,
		tags: Optional[List[Union[str, Enum]]] = None,
		summary: Optional[str] = None,
		include_in_schema: bool = True,
		response_class: Type[WerkzeugResponse] = Default(JSONResponse),
		allow_guest: bool = False,
		xss_safe: bool = False,
		fastapi_path_format: bool = False,
	) -> Callable[[Callable], Callable]:
		def register(func: Callable) -> Callable:
			# This is just a pass-through - the actual registration happens in applications.py via the FrappeAPI._dual method
			return func

		return register

	return decorator


GET = _factory(["GET"])
POST = _factory(["POST"])
PUT = _factory(["PUT"])
DELETE = _factory(["DELETE"])
PATCH = _factory(["PATCH"])
OPTIONS = _factory(["OPTIONS"])
HEAD = _factory(["HEAD"])


def _install_patch() -> None:
	"""Install the patch to frappe.api.handle once per process."""
	if hasattr(frappe, "flags") and getattr(frappe.flags, "in_migrate", False):
		return

	if getattr(frappe, "_fastapi_path_patch_done", False):
		return

	if not hasattr(frappe, "api"):
		return

	orig_handle = frappe.api.handle

	def patched_handle(request=None) -> types.ModuleType | dict:
		request_path = frappe.local.request.path

		for app_instance in _FRAPPEAPI_INSTANCES:
			if not app_instance.fastapi_path_format:
				continue

			if not (
				request_path.startswith("/api/")
				and not request_path.startswith("/api/method/")
				and not request_path.startswith("/api/resource/")
			):
				continue

			path_segment_to_match = request_path[4:]

			if not hasattr(app_instance, "router") or not hasattr(app_instance.router, "routes"):
				continue

			for api_route in app_instance.router.routes:
				# api_route.fastapi_path_format_flag is the mode of the APIRoute instance itself.
				# api_route.path_for_starlette_matching is the relative path like "/items/{item_id}".
				if not (api_route.fastapi_path_format_flag and api_route.path_for_starlette_matching):
					continue

				scope = {
					"type": "http",
					"path": path_segment_to_match,
					"root_path": "",
					"method": frappe.local.request.method.upper(),
				}

				# Create a temporary Starlette route for matching.
				starlette_route = Route(
					api_route.path_for_starlette_matching,
					endpoint=api_route.endpoint,
					methods=[m for m in api_route.methods] if api_route.methods else None,
				)

				match, child_scope = starlette_route.matches(scope)
				if match == Match.FULL:
					path_params = child_scope.get("path_params", {})
					frappe.local.request.path_params = path_params
					response = api_route.handle_request()
					return response

		# No FastAPI-style route matched for any app instance in FastAPI mode,
		# or the path was not a FastAPI-style candidate.
		# Fall back to the original Frappe handler for dotted paths or other unhandled /api/ calls.
		if request:
			return orig_handle(request)
		return orig_handle()

	frappe.api.handle = patched_handle
	frappe._fastapi_path_patch_done = True


_install_patch()
