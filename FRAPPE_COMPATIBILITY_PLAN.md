# FrappeAPI - Frappe Version Compatibility Plan

**Analysis Date:** 2025-12-19
**Target Versions:** Frappe 14, 15, 16 (develop)
**Current FrappeAPI Version:** 0.2.1

---

## Executive Summary

FrappeAPI's monkey-patching approach in `fast_routes.py` **will fail on Frappe v15+** due to fundamental architectural changes in how Frappe handles API routing. This document provides a comprehensive analysis and migration plan.

---

## 1. Version Comparison Analysis

### 1.1 Frappe v14 Architecture

**File Structure:**
- Single file: `frappe/api.py`

**`handle()` Function Signature:**
```python
def handle():
    """
    Handler for `/api` methods.

    Routes:
    - /api/method/{methodname} - Call whitelisted method
    - /api/resource/{doctype} - Query documents
    - /api/resource/{doctype}/{name} - CRUD operations
    """
    # Direct path parsing from frappe.request.path
    parts = frappe.request.path[1:].split("/")
    call = doctype = name = None

    if len(parts) > 1:
        call = parts[1]
    if len(parts) > 2:
        doctype = parts[2]
    if len(parts) > 3:
        name = parts[3]

    # Direct routing logic
    if call == "method":
        frappe.local.form_dict.cmd = doctype
        return frappe.handler.handle()
    elif call == "resource":
        # Handle resource operations
        # ... CRUD logic ...

    return build_response("json")
```

**Key Characteristics:**
- ✅ Direct function signature: `def handle()`
- ✅ No parameters
- ✅ Simple path parsing with string manipulation
- ✅ Direct routing in single function
- ✅ Can be monkey-patched easily

**FrappeAPI Patch Works:** ✅ YES

---

### 1.2 Frappe v15 Architecture

**File Structure:**
- Module: `frappe/api/__init__.py`
- Supporting files: `frappe/api/v1.py`, `frappe/api/v2.py`

**`handle()` Function Signature:**
```python
def handle(request: Request):
    """
    Entry point for `/api` methods.

    APIs are versioned using second part of path.
    v1 -> `/api/v1/*`
    v2 -> `/api/v2/*`
    """

    try:
        endpoint, arguments = API_URL_MAP.bind_to_environ(request.environ).match()
    except NotFound:
        raise frappe.DoesNotExistError

    data = endpoint(**arguments)
    if isinstance(data, Response):
        return data

    if data is not None:
        frappe.response["data"] = data
    data = build_response("json")

    # Monitoring code...
    return data
```

**Key Characteristics:**
- ❌ **Takes `request: Request` parameter** (breaking change!)
- ❌ Uses Werkzeug URL routing (`API_URL_MAP`)
- ❌ Endpoint delegation pattern
- ✅ Versioned API support (v1/v2)
- ❌ Cannot be directly replaced with parameterless function

**FrappeAPI Patch Works:** ❌ **NO** - Signature mismatch

---

### 1.3 Frappe v16 (develop) Architecture

**File Structure:**
- Module: `frappe/api/__init__.py`
- Supporting files: `frappe/api/v1.py`, `frappe/api/v2.py`

**`handle()` Function Signature:**
```python
def handle(request: Request):
    """
    Entry point for `/api` methods.

    [Same structure as v15 with additions:]
    """

    # Optional API request logging
    if frappe.get_system_settings("log_api_requests"):
        doc = frappe.get_doc({
            "doctype": "API Request Log",
            "path": request.path,
            "user": frappe.session.user,
            "method": request.method,
        })
        doc.deferred_insert()

    try:
        endpoint, arguments = API_URL_MAP.bind_to_environ(request.environ).match()
    except NotFound:
        raise frappe.DoesNotExistError

    # ... rest same as v15 ...
```

**Key Characteristics:**
- ❌ **Takes `request: Request` parameter** (same as v15)
- ❌ Uses Werkzeug URL routing
- ❌ Endpoint delegation pattern
- ✅ Enhanced logging capabilities
- ✅ Same structure as v15 (incremental changes)
- ❌ Cannot be directly replaced with parameterless function

**FrappeAPI Patch Works:** ❌ **NO** - Signature mismatch

---

## 2. Current Patch Analysis

### 2.1 Current Implementation

**Location:** `frappeapi/fast_routes.py:93-161`

```python
def _install_patch() -> None:
    """Install the patch to frappe.api.handle once per process."""
    if hasattr(frappe, "flags") and getattr(frappe.flags, "in_migrate", False):
        return

    if getattr(frappe, "_fastapi_path_patch_done", False):
        return

    if not hasattr(frappe, "api"):
        return

    orig_handle = frappe.api.handle  # ❌ Gets the function reference

    def patched_handle() -> types.ModuleType | dict:  # ❌ No parameters!
        request_path = frappe.local.request.path

        # ... FrappeAPI routing logic ...

        # Fall back to original
        return orig_handle()  # ❌ Calls without parameters

    frappe.api.handle = patched_handle  # ❌ Replaces with incompatible signature
    frappe._fastapi_path_patch_done = True
```

### 2.2 Why It Fails

| Version | Issue | Error |
|---------|-------|-------|
| **v14** | ✅ Works | None - signatures match |
| **v15** | ❌ Fails | `TypeError: patched_handle() takes 0 positional arguments but 1 was given` |
| **v16** | ❌ Fails | `TypeError: patched_handle() takes 0 positional arguments but 1 was given` |

**Root Cause:**
Frappe v15+ calls `handle(request)` with a Request object, but FrappeAPI's patch defines `patched_handle()` with no parameters.

---

## 3. Impact Assessment

### 3.1 Breaking Changes in Frappe v15+

1. **Function Signature Change:**
   ```python
   # v14
   def handle():

   # v15+
   def handle(request: Request):
   ```

2. **Routing Mechanism:**
   ```python
   # v14: Manual path parsing
   parts = frappe.request.path[1:].split("/")

   # v15+: Werkzeug URL routing
   endpoint, arguments = API_URL_MAP.bind_to_environ(request.environ).match()
   ```

3. **API Versioning:**
   - v14: No versioning, all routes under `/api/`
   - v15+: Versioned routes `/api/v1/` and `/api/v2/`

4. **Request Access:**
   ```python
   # v14: Global access
   frappe.request
   frappe.local.request

   # v15+: Parameter-based
   request  # passed as parameter
   ```

### 3.2 Compatibility Matrix

| Feature | v14 | v15 | v16 | Notes |
|---------|-----|-----|-----|-------|
| Current patch works | ✅ | ❌ | ❌ | Signature incompatible |
| `handle()` signature | No params | `(request)` | `(request)` | Breaking change |
| Path parsing | Manual | Werkzeug | Werkzeug | - |
| API versioning | No | Yes | Yes | v1/v2 support |
| Request logging | No | No | Yes | Optional feature |
| URL map routing | No | Yes | Yes | Endpoint delegation |

---

## 4. Solution Strategies

### Strategy A: Version Detection with Compatible Wrapper ⭐ **RECOMMENDED**

**Approach:** Detect Frappe version and apply appropriate patch.

**Implementation:**

```python
def _get_frappe_version():
    """Detect Frappe major version."""
    try:
        import frappe
        version = frappe.__version__
        major = int(version.split('.')[0]) if version else 14
        return major
    except:
        return 14  # Default to v14

def _install_patch() -> None:
    """Install version-appropriate patch."""
    if not hasattr(frappe, "api"):
        return

    if getattr(frappe, "_fastapi_path_patch_done", False):
        return

    frappe_version = _get_frappe_version()
    orig_handle = frappe.api.handle

    if frappe_version >= 15:
        # v15+ patch with request parameter
        def patched_handle(request) -> types.ModuleType | dict:
            request_path = request.path

            for app_instance in _FRAPPEAPI_INSTANCES:
                if not app_instance.fastapi_path_format:
                    continue

                if not (
                    request_path.startswith("/api/")
                    and not request_path.startswith("/api/method/")
                    and not request_path.startswith("/api/resource/")
                    and not request_path.startswith("/api/v1/")  # New: Skip v1
                    and not request_path.startswith("/api/v2/")  # New: Skip v2
                ):
                    continue

                # Extract path segment (handle both /api/... and /api/vX/...)
                path_segment_to_match = request_path[4:]  # Remove /api

                for api_route in app_instance.router.routes:
                    if not (api_route.fastapi_path_format_flag and api_route.path_for_starlette_matching):
                        continue

                    scope = {
                        "type": "http",
                        "path": path_segment_to_match,
                        "root_path": "",
                        "method": request.method.upper(),
                    }

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

            # Fall back to original with request parameter
            return orig_handle(request)

    else:
        # v14 patch without request parameter
        def patched_handle() -> types.ModuleType | dict:
            request_path = frappe.local.request.path

            # ... existing v14 logic ...

            return orig_handle()

    frappe.api.handle = patched_handle
    frappe._fastapi_path_patch_done = True
```

**Pros:**
- ✅ Maintains backward compatibility
- ✅ Minimal code changes
- ✅ Works across all versions
- ✅ Automatic version detection

**Cons:**
- ⚠️ Still relies on monkey-patching
- ⚠️ Requires version detection logic
- ⚠️ Two code paths to maintain

---

### Strategy B: Hook into Werkzeug URL Map (v15+ only)

**Approach:** Register routes directly in Frappe's `API_URL_MAP` instead of patching.

**Implementation:**

```python
def register_frappeapi_routes():
    """Register FrappeAPI routes in Frappe's URL map."""
    from werkzeug.routing import Rule

    for app_instance in _FRAPPEAPI_INSTANCES:
        if not app_instance.fastapi_path_format:
            continue

        for api_route in app_instance.router.routes:
            if not api_route.fastapi_path_format_flag:
                continue

            # Create Werkzeug rule
            rule = Rule(
                api_route.path_for_starlette_matching,
                methods=list(api_route.methods),
                endpoint=f"frappeapi_{id(api_route)}",
            )

            # Add to Frappe's URL map
            frappe.api.API_URL_MAP.add(rule)

            # Register handler
            frappe.api._endpoints[f"frappeapi_{id(api_route)}"] = api_route.handle_request
```

**Pros:**
- ✅ No monkey-patching of `handle()`
- ✅ Uses native Frappe routing
- ✅ Cleaner integration
- ✅ Better performance (native routing)

**Cons:**
- ❌ Only works for v15+
- ❌ Requires understanding Werkzeug URL map
- ❌ May conflict with Frappe's internal routing
- ⚠️ Still needs v14 fallback

---

### Strategy C: Frappe Hook System

**Approach:** Use Frappe's official hook system for extending API.

**Implementation:**

In `hooks.py` of consuming app:

```python
# hooks.py
app_name = "myapp"

# Register custom request handler
override_whitelisted_methods = {
    "frappeapi.handle_fastapi_request": "myapp.api.handle_fastapi_request"
}

# Or use after_request hook
after_request = [
    "myapp.api.intercept_fastapi_routes"
]
```

In `myapp/api.py`:

```python
def intercept_fastapi_routes():
    """Intercept and handle FrappeAPI routes."""
    request_path = frappe.local.request.path

    # Check if this is a FrappeAPI route
    for app_instance in _FRAPPEAPI_INSTANCES:
        # ... routing logic ...
        pass
```

**Pros:**
- ✅ Official Frappe extension mechanism
- ✅ No monkey-patching
- ✅ More maintainable
- ✅ Version independent

**Cons:**
- ❌ Requires app installation (not just library)
- ❌ More complex setup
- ❌ Less portable
- ⚠️ Performance overhead (runs after normal routing)

---

### Strategy D: Middleware Approach

**Approach:** Implement WSGI middleware to intercept requests before they reach Frappe.

**Implementation:**

```python
class FrappeAPIMiddleware:
    """WSGI middleware for FrappeAPI routing."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request_path = environ.get('PATH_INFO', '')

        # Check for FrappeAPI routes
        if self._is_frappeapi_route(request_path):
            response = self._handle_frappeapi_route(environ)
            return response(environ, start_response)

        # Pass through to Frappe
        return self.app(environ, start_response)

    def _is_frappeapi_route(self, path):
        # Check if path matches any FrappeAPI route
        pass

    def _handle_frappeapi_route(self, environ):
        # Handle FrappeAPI route
        pass
```

**Pros:**
- ✅ Completely independent of Frappe internals
- ✅ Works across all versions
- ✅ Clean separation of concerns
- ✅ Can intercept before Frappe

**Cons:**
- ❌ Requires WSGI middleware setup
- ❌ Complex configuration
- ❌ Bypasses Frappe's auth/session
- ⚠️ Need to replicate Frappe's request handling

---

## 5. Recommended Implementation Plan

### Phase 1: Version Detection (Week 1)

**Goal:** Add version detection and maintain v14 compatibility.

**Tasks:**
1. ✅ Add `_get_frappe_version()` function
2. ✅ Create version-specific patch branches
3. ✅ Add unit tests for version detection
4. ✅ Update documentation

**Files to Modify:**
- `frappeapi/fast_routes.py`
- `frappeapi/__init__.py` (add version constant)

**Deliverable:** FrappeAPI detects version and patches appropriately.

---

### Phase 2: v15+ Compatible Patch (Week 2)

**Goal:** Make patch work with v15+ request parameter.

**Tasks:**
1. ✅ Implement `patched_handle(request)` for v15+
2. ✅ Update path matching to skip `/api/v1/` and `/api/v2/`
3. ✅ Test with Frappe v15 installation
4. ✅ Ensure fallback to `orig_handle(request)` works

**Code Changes:**

```python
# frappeapi/fast_routes.py

def _create_v15_plus_patch(orig_handle):
    """Create patch compatible with Frappe v15+."""
    def patched_handle(request):
        request_path = request.path

        for app_instance in _FRAPPEAPI_INSTANCES:
            if not app_instance.fastapi_path_format:
                continue

            # Skip Frappe's native API versioning routes
            if request_path.startswith(("/api/v1/", "/api/v2/")):
                continue

            if not (
                request_path.startswith("/api/")
                and not request_path.startswith("/api/method/")
                and not request_path.startswith("/api/resource/")
            ):
                continue

            # FrappeAPI uses /api/... (without v1/v2)
            path_segment = request_path[4:]  # Remove "/api"

            for api_route in app_instance.router.routes:
                if not (api_route.fastapi_path_format_flag and api_route.path_for_starlette_matching):
                    continue

                scope = {
                    "type": "http",
                    "path": path_segment,
                    "root_path": "",
                    "method": request.method.upper(),
                }

                starlette_route = Route(
                    api_route.path_for_starlette_matching,
                    endpoint=api_route.endpoint,
                    methods=list(api_route.methods) if api_route.methods else None,
                )

                match, child_scope = starlette_route.matches(scope)
                if match == Match.FULL:
                    path_params = child_scope.get("path_params", {})
                    # Store in both places for compatibility
                    frappe.local.request.path_params = path_params
                    if hasattr(request, "path_params"):
                        request.path_params = path_params
                    response = api_route.handle_request()
                    return response

        return orig_handle(request)

    return patched_handle


def _create_v14_patch(orig_handle):
    """Create patch compatible with Frappe v14."""
    def patched_handle():
        # ... existing v14 logic ...
        return orig_handle()

    return patched_handle


def _install_patch() -> None:
    """Install version-appropriate patch."""
    if hasattr(frappe, "flags") and getattr(frappe.flags, "in_migrate", False):
        return

    if getattr(frappe, "_fastapi_path_patch_done", False):
        return

    if not hasattr(frappe, "api"):
        return

    orig_handle = frappe.api.handle
    frappe_version = _get_frappe_version()

    if frappe_version >= 15:
        patched_handle = _create_v15_plus_patch(orig_handle)
    else:
        patched_handle = _create_v14_patch(orig_handle)

    frappe.api.handle = patched_handle
    frappe._fastapi_path_patch_done = True
```

**Deliverable:** FrappeAPI works with v15 and v16.

---

### Phase 3: Testing & Validation (Week 3)

**Goal:** Comprehensive testing across versions.

**Tasks:**
1. ✅ Set up test environments for v14, v15, v16
2. ✅ Create integration tests
3. ✅ Test path parameter extraction
4. ✅ Test response handling
5. ✅ Benchmark performance impact

**Test Matrix:**

| Test Case | v14 | v15 | v16 |
|-----------|-----|-----|-----|
| Simple GET /api/items | ⬜ | ⬜ | ⬜ |
| Path param /api/items/{id} | ⬜ | ⬜ | ⬜ |
| POST with body | ⬜ | ⬜ | ⬜ |
| Query parameters | ⬜ | ⬜ | ⬜ |
| File upload | ⬜ | ⬜ | ⬜ |
| Error handling | ⬜ | ⬜ | ⬜ |
| OpenAPI generation | ⬜ | ⬜ | ⬜ |
| Dotted path fallback | ⬜ | ⬜ | ⬜ |
| Native /api/v1/ routes | N/A | ⬜ | ⬜ |
| Native /api/v2/ routes | N/A | ⬜ | ⬜ |

**Deliverable:** All tests passing across versions.

---

### Phase 4: Documentation & Migration Guide (Week 4)

**Goal:** Help users migrate and understand version differences.

**Tasks:**
1. ✅ Update README with version compatibility
2. ✅ Create migration guide
3. ✅ Document version-specific behavior
4. ✅ Add troubleshooting section
5. ✅ Update examples

**Documentation Structure:**

```markdown
# Version Compatibility

## Supported Versions
- ✅ Frappe v14.x
- ✅ Frappe v15.x
- ✅ Frappe v16.x (develop)

## Version-Specific Notes

### Frappe v14
- Uses dotted path routing by default
- FastAPI-style paths require `fastapi_path_format=True`

### Frappe v15+
- Native API versioning available
- FrappeAPI routes use `/api/...` (not `/api/v1/...`)
- Both dotted and FastAPI paths supported

## Troubleshooting

### TypeError: patched_handle() takes 0 positional arguments
**Solution:** Update FrappeAPI to v0.3.0+ which includes version detection.

### Routes not matching
**Solution:** Ensure `fastapi_path_format=True` when creating FrappeAPI instance.
```

**Deliverable:** Complete documentation for all versions.

---

## 6. Testing Strategy

### 6.1 Unit Tests

```python
# tests/test_version_detection.py

def test_get_frappe_version_v14():
    """Test version detection for v14."""
    with mock.patch('frappe.__version__', '14.23.0'):
        assert _get_frappe_version() == 14


def test_get_frappe_version_v15():
    """Test version detection for v15."""
    with mock.patch('frappe.__version__', '15.5.0'):
        assert _get_frappe_version() == 15


def test_patch_installation_v14():
    """Test patch installs correctly for v14."""
    # Mock Frappe v14
    with mock.patch('frappe.__version__', '14.0.0'):
        _install_patch()
        # Verify no parameters
        assert frappe.api.handle.__code__.co_argcount == 0


def test_patch_installation_v15():
    """Test patch installs correctly for v15."""
    # Mock Frappe v15
    with mock.patch('frappe.__version__', '15.0.0'):
        _install_patch()
        # Verify one parameter
        assert frappe.api.handle.__code__.co_argcount == 1
```

### 6.2 Integration Tests

```python
# tests/integration/test_v14_routing.py

@pytest.mark.frappe_v14
def test_fastapi_path_routing_v14():
    """Test FastAPI-style paths work in v14."""
    app = FrappeAPI(fastapi_path_format=True)

    @app.get("/items/{item_id}")
    def get_item(item_id: int):
        return {"id": item_id, "name": "Test"}

    response = frappe.local.request.get("/api/items/123")
    assert response.status_code == 200
    assert response.json()["id"] == 123


# tests/integration/test_v15_routing.py

@pytest.mark.frappe_v15
def test_fastapi_path_routing_v15():
    """Test FastAPI-style paths work in v15."""
    # Same test as v14, should work identically
    app = FrappeAPI(fastapi_path_format=True)

    @app.get("/items/{item_id}")
    def get_item(item_id: int):
        return {"id": item_id, "name": "Test"}

    response = frappe.local.request.get("/api/items/123")
    assert response.status_code == 200
    assert response.json()["id"] == 123


@pytest.mark.frappe_v15
def test_native_v1_routing_not_intercepted():
    """Test that native /api/v1/ routes are not intercepted."""
    # FrappeAPI should not interfere with Frappe's native v1 routes
    response = frappe.local.request.get("/api/v1/resource/User")
    # Should be handled by Frappe, not FrappeAPI
    assert "handled_by_frappeapi" not in response.headers
```

### 6.3 Performance Tests

```python
# tests/performance/test_routing_overhead.py

def test_routing_overhead_v14():
    """Measure routing overhead in v14."""
    import timeit

    # Without patch
    time_without = timeit.timeit(
        lambda: frappe.api.handle(),
        number=1000
    )

    # With patch
    _install_patch()
    time_with = timeit.timeit(
        lambda: frappe.api.handle(),
        number=1000
    )

    overhead = (time_with - time_without) / time_without * 100
    assert overhead < 5  # Less than 5% overhead
```

---

## 7. Migration Guide for Users

### 7.1 Upgrading from FrappeAPI 0.2.x to 0.3.x

**Step 1:** Update FrappeAPI

```bash
# Update FrappeAPI
pip install --upgrade frappeapi
```

**Step 2:** No Code Changes Required

The version detection is automatic. Your existing code will work:

```python
from frappeapi import FrappeAPI

app = FrappeAPI(fastapi_path_format=True)

@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"id": item_id}
```

**Step 3:** Test Your Endpoints

```bash
# Test dotted path (works in all versions)
curl http://localhost:8000/api/method/myapp.api.get_item?item_id=123

# Test FastAPI path (works in all versions with updated FrappeAPI)
curl http://localhost:8000/api/items/123
```

### 7.2 Version-Specific Behavior

**Frappe v14:**
- FrappeAPI routes: `/api/items/123`
- Dotted paths: `/api/method/myapp.api.get_item`

**Frappe v15+:**
- FrappeAPI routes: `/api/items/123`
- Frappe v1 routes: `/api/v1/resource/DocType`
- Frappe v2 routes: `/api/v2/resource/DocType`
- Dotted paths: `/api/method/myapp.api.get_item`

**Important:** FrappeAPI routes do NOT use `/api/v1/` or `/api/v2/` prefixes.

---

## 8. Risks & Mitigation

### 8.1 Risks

| Risk | Severity | Probability | Impact |
|------|----------|-------------|---------|
| Future Frappe API changes | High | High | Breaking changes |
| Performance regression | Medium | Low | Slower routing |
| Monkey-patch conflicts | Medium | Medium | Runtime errors |
| Version detection failure | Low | Low | Wrong patch applied |

### 8.2 Mitigation Strategies

1. **Version Detection:**
   - Multiple fallback methods
   - Log detected version
   - Warn on unknown versions

2. **Graceful Degradation:**
   - If patch fails, log warning
   - Fall back to dotted paths only
   - Don't break existing functionality

3. **Testing:**
   - CI/CD for all versions
   - Integration tests with real Frappe
   - Performance benchmarks

4. **Documentation:**
   - Clear version compatibility matrix
   - Migration guides
   - Troubleshooting section

---

## 9. Future Considerations

### 9.1 Long-Term Solutions

1. **Official Frappe Integration:**
   - Propose FrappeAPI features upstream
   - Collaborate with Frappe core team
   - Become official plugin

2. **Alternative Architecture:**
   - Move away from monkey-patching
   - Use official Frappe hooks
   - Implement as Frappe app (not library)

3. **API Gateway Approach:**
   - Deploy separate API gateway
   - Proxy to Frappe backend
   - Handle routing externally

### 9.2 Deprecation Path

If monkey-patching becomes unmaintainable:

1. **Phase 1:** Deprecation warning (v0.4.0)
2. **Phase 2:** Frappe app version (v1.0.0)
3. **Phase 3:** Remove monkey-patch (v2.0.0)

---

## 10. Implementation Checklist

### Development Tasks

- [ ] Implement `_get_frappe_version()` function
- [ ] Create `_create_v14_patch()` function
- [ ] Create `_create_v15_plus_patch()` function
- [ ] Update `_install_patch()` with version detection
- [ ] Add version skipping for `/api/v1/` and `/api/v2/`
- [ ] Handle `request.path_params` for v15+

### Testing Tasks

- [ ] Write unit tests for version detection
- [ ] Write unit tests for patch creation
- [ ] Set up v14 test environment
- [ ] Set up v15 test environment
- [ ] Set up v16 test environment
- [ ] Integration tests for all versions
- [ ] Performance benchmarks
- [ ] Edge case testing

### Documentation Tasks

- [ ] Update README with version compatibility
- [ ] Create MIGRATION_GUIDE.md
- [ ] Document version-specific behavior
- [ ] Add troubleshooting section
- [ ] Update API reference
- [ ] Create examples for each version

### Release Tasks

- [ ] Version bump to 0.3.0
- [ ] Update CHANGELOG.md
- [ ] Tag release
- [ ] Publish to PyPI
- [ ] Announce on forums/Discord

---

## 11. Timeline

### Sprint 1 (Week 1-2): Core Implementation
- Version detection
- v15+ compatible patch
- Basic testing

### Sprint 2 (Week 3): Testing & Validation
- Integration tests
- Performance testing
- Bug fixes

### Sprint 3 (Week 4): Documentation & Release
- Documentation updates
- Migration guides
- Release preparation

**Total Estimated Time: 3-4 weeks**

---

## 12. Success Criteria

✅ **Must Have:**
- Works on Frappe v14, v15, v16
- Automatic version detection
- No breaking changes for existing users
- Tests passing on all versions

✅ **Should Have:**
- Less than 5% performance overhead
- Comprehensive documentation
- Migration guide
- CI/CD for all versions

✅ **Nice to Have:**
- Benchmark comparison
- Video tutorials
- Community examples

---

## 13. Conclusion

The current FrappeAPI implementation **will not work** on Frappe v15+ without modifications. The recommended approach is **Strategy A: Version Detection with Compatible Wrapper**, which provides:

1. ✅ Backward compatibility with v14
2. ✅ Forward compatibility with v15+
3. ✅ Minimal code changes
4. ✅ Automatic version detection

This plan provides a clear path forward to support all Frappe versions while maintaining the excellent developer experience FrappeAPI provides.

---

**Next Steps:**
1. Review and approve this plan
2. Create GitHub issues for each phase
3. Set up CI/CD for multi-version testing
4. Begin Phase 1 implementation

**Questions?** Open an issue or discussion on the FrappeAPI repository.

---

## References

- [Frappe v15 Migration Guide](https://github.com/frappe/frappe/wiki/Migrating-to-Version-15)
- [Frappe API PR #22300](https://github.com/frappe/frappe/pull/22300) - API versioning
- [Frappe v16 Develop Branch](https://github.com/frappe/frappe/tree/develop)
