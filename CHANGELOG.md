# Changelog

All notable changes to FrappeAPI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-12-19

### Added

- **Automatic Frappe version detection** - FrappeAPI now automatically detects which version of Frappe you're using (v14, v15, or v16) and applies the appropriate compatibility patch.
- **Frappe v15 support** - Full compatibility with Frappe v15's new API architecture.
- **Frappe v16 support** - Beta support for Frappe v16 (develop branch).
- **`get_detected_frappe_version()` function** - New API to check which Frappe version was detected.
- **Enhanced logging** - Added detailed logging for patch installation and version detection to aid in debugging.
- **Graceful error handling** - If patch installation fails, FrappeAPI now logs the error and fails gracefully instead of crashing.

### Changed

- **Version-aware patching** - The monkey-patch for `frappe.api.handle` now adapts to the Frappe version:
  - v14: Uses parameterless `handle()` signature
  - v15+: Uses `handle(request)` signature with Request parameter
- **Skip native API routes in v15+** - FrappeAPI now skips Frappe's native `/api/v1/` and `/api/v2/` routes to avoid conflicts.
- **Improved fallback logic** - Multiple fallback methods for version detection (version string parsing, module structure inspection, and default to v14).

### Fixed

- **Critical: Compatibility with Frappe v15+** - Fixed `TypeError: patched_handle() takes 0 positional arguments but 1 was given` that prevented FrappeAPI from working on Frappe v15 and v16.
- **Path parameter storage** - Path parameters are now stored in both `frappe.local.request.path_params` and `request.path_params` for better compatibility.

### Documentation

- Added **Version Compatibility** section to README with support matrix.
- Created **FRAPPE_COMPATIBILITY_PLAN.md** with detailed analysis of Frappe API changes across versions.
- Created **PROJECT_REVIEW.md** with comprehensive code review and recommendations.

### Breaking Changes

None. This release is fully backward compatible with existing FrappeAPI code. If you're using FrappeAPI with Frappe v14, your code will continue to work without any changes.

### Migration Guide

No migration required! Simply update FrappeAPI:

```bash
pip install --upgrade frappeapi
```

Your existing code will work automatically:

```python
from frappeapi import FrappeAPI

app = FrappeAPI(fastapi_path_format=True)

@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"id": item_id}
```

### Technical Details

For developers interested in the implementation:

1. **Version Detection**:
   - Primary: Parse `frappe.__version__` string
   - Fallback 1: Check for `frappe.api.API_URL_MAP` (v15+ indicator)
   - Fallback 2: Default to v14 compatibility mode

2. **Patch Strategy**:
   - v14: Wrap original `handle()` with parameterless function
   - v15+: Wrap original `handle(request)` with function that accepts request parameter

3. **Route Matching**:
   - v14: All `/api/` routes (except `/api/method/` and `/api/resource/`)
   - v15+: Skip `/api/v1/` and `/api/v2/` in addition to above

See **FRAPPE_COMPATIBILITY_PLAN.md** for complete technical details.

---

## [0.2.1] - 2024-XX-XX

### Changed

- Skip resource calls in path matching.

---

## [0.2.0] - 2024-XX-XX

### Added

- Initial release with FastAPI-style decorators for Frappe.
- Support for query parameters, body parameters, path parameters.
- File upload support.
- OpenAPI documentation generation.
- Exception handling.
- Response model validation.

### Supported Frappe Versions

- Frappe v14 (full support)

---

[0.3.0]: https://github.com/0xsirsaif/frappeapi/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/0xsirsaif/frappeapi/releases/tag/v0.2.1
[0.2.0]: https://github.com/0xsirsaif/frappeapi/releases/tag/v0.2.0
