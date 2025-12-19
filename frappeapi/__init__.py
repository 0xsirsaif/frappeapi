# --- 1. Install the patch _before_ anything else touches FastAPI ---
from fastapi._compat import lenient_issubclass as _orig
from starlette.responses import JSONResponse as _StarletteJSONResponse


def _patched_lenient(cls, parent):
	from frappeapi.responses import JSONResponse as _FrappeJSONResponse

	if cls is _FrappeJSONResponse and parent is _StarletteJSONResponse:
		return True
	return _orig(cls, parent)


import fastapi._compat as _compat

_compat.lenient_issubclass = _patched_lenient

# Also update the copies already made inside FastAPI sub‑modules
import fastapi.openapi.utils as _utils

_utils.lenient_issubclass = _patched_lenient

# --- 2. Now FastAPI can use the patched version ---
__version__ = "0.3.0"

from fastapi.datastructures import UploadFile  # noqa: F401
from fastapi.params import (
	Body,  # noqa: F401
	Depends,  # noqa: F401
	File,  # noqa: F401
	Form,  # noqa: F401
	Header,  # noqa: F401
	Query,  # noqa: F401
)

from frappeapi.applications import FrappeAPI  # noqa: F401

# quick re‑export for power users
from frappeapi.fast_routes import DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT  # noqa: F401


def get_detected_frappe_version():
	"""
	Get the Frappe version detected by FrappeAPI.

	Returns:
		int or None: Major version number (14, 15, 16, etc.) if detected, None if not yet detected

	Example:
		>>> import frappeapi
		>>> frappeapi.get_detected_frappe_version()
		15
	"""
	try:
		import frappe

		return getattr(frappe, "_frappeapi_detected_version", None)
	except ImportError:
		return None
