---
title: "FrappeAPI — FastAPI-Style REST APIs for Frappe Framework"
description: "FrappeAPI brings FastAPI-style routing, validation, and automatic OpenAPI documentation to the Frappe Framework. Build modern REST APIs for Frappe with type hints, Pydantic models, and path parameters."
---

# FrappeAPI: FastAPI-Style REST APIs for Frappe Framework

FrappeAPI is a Python library that brings FastAPI-style API development to the [Frappe Framework](https://frappeframework.com/). It lets you define REST API endpoints with type hints, Pydantic models, and modern path routing — all within your existing Frappe applications.

If you have ever wished you could write Frappe APIs the way you write FastAPI endpoints, FrappeAPI is for you.

## What is FrappeAPI?

FrappeAPI is a wrapper around the Frappe Framework's API layer that replaces the default whitelisted-function approach with a structured, FastAPI-inspired interface. Instead of using `frappe.whitelist()` and manually parsing arguments, you declare typed parameters and let FrappeAPI handle validation, parsing, and OpenAPI schema generation automatically.

FrappeAPI follows FastAPI's interface and semantics. For in-depth information about specific features, refer to [FastAPI's documentation](https://fastapi.tiangolo.com/).

## Key Features

- **FastAPI-style path routing** — define endpoints like `/items/{item_id}` instead of dotted paths
- **Automatic request validation** — query parameters, request bodies, and path parameters are validated using Python type hints and Pydantic models
- **OpenAPI documentation** — auto-generated Swagger UI for every endpoint you define
- **File uploads** — handle small and large file uploads with `File()` and `UploadFile`
- **Response models** — filter and validate API responses using Pydantic models
- **Error handling** — built-in exception handlers with support for custom handlers
- **Header parameters** — read and validate HTTP headers declaratively

## Quick Start

Install FrappeAPI from PyPI:

```bash
pip install frappeapi
```

Define your first API endpoint:

```python
from frappeapi import FrappeAPI

app = FrappeAPI()

@app.get()
def hello(name: str = "World"):
    return {"message": f"Hello, {name}!"}
```

Or use FastAPI-style path parameters:

```python
app = FrappeAPI(fastapi_path_format=True)

@app.get("/items/{item_id}")
def get_item(item_id: str):
    return {"item_id": item_id}
```

## Frappe Version Compatibility

| FrappeAPI | Frappe Framework |
|-----------|-----------------|
| v0.1.x    | v14             |
| v0.2.x    | v14             |

## Next Steps

- [Usage Examples](usage_examples.md) — query parameters, request bodies, file uploads, response models, and more
- [OpenAPI Documentation](openapi_docs.md) — set up Swagger UI for your Frappe APIs
- [Roadmap](roadmap.md) — planned features and Frappe version support
