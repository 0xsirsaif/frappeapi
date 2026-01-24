# FrappeAPI

Better APIs for Frappe.

FrappeAPI brings FastAPI-style routing and validation to the Frappe Framework. Define endpoints with type hints, get automatic validation and documentation.

## Installation

```bash
pip install frappeapi
```

## Quick Start

```python
from frappeapi import FrappeAPI

app = FrappeAPI()

@app.get()
def hello(name: str = "World"):
    return {"message": f"Hello, {name}!"}
```

## Examples

### Path Parameters

Enable FastAPI-style paths for cleaner URLs:

```python
from frappeapi import FrappeAPI

app = FrappeAPI(fastapi_path_format=True)

@app.get("/items/{item_id}")
def get_item(item_id: str):
    return {"id": item_id}

# GET /api/items/abc123
# Response: {"id": "abc123"}
```

Multiple path parameters:

```python
@app.get("/users/{user_id}/orders/{order_id}")
def get_user_order(user_id: str, order_id: int):
    return {"user_id": user_id, "order_id": order_id}

# GET /api/users/john/orders/42
# Response: {"user_id": "john", "order_id": 42}
```

Combine path and query parameters:

```python
@app.get("/products/{category}")
def list_products(
    category: str,           # Path parameter
    sort_by: str = "name",   # Query parameter
    limit: int = 10          # Query parameter
):
    return {"category": category, "sort_by": sort_by, "limit": limit}

# GET /api/products/electronics?sort_by=price&limit=20
```

### Query Parameters

Automatic type parsing:

```python
@app.get()
def get_product_details(
    product_id: int,
    unit_price: float,
    in_stock: bool
):
    return {
        "product_id": product_id,  # "123" -> 123
        "unit_price": unit_price,  # "9.99" -> 9.99
        "in_stock": in_stock       # "true" -> True
    }
```

Optional parameters with defaults:

```python
@app.get()
def list_products(
    category: str = "all",
    page: int = 1,
    search: str | None = None
):
    return {"category": category, "page": page, "search": search}
```

Enum parameters:

```python
from enum import Enum

class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"

@app.get()
def list_orders(status: OrderStatus = OrderStatus.pending):
    return {"status": status}
```

List parameters:

```python
from frappeapi import Query

@app.get()
def search_products(
    tags: List[str] = Query(default=[]),
    categories: List[int] = Query(default=[])
):
    return {"tags": tags, "categories": categories}

# GET ?tags=electronics&tags=sale&categories=1&categories=2
# Response: {"tags": ["electronics", "sale"], "categories": [1, 2]}
```

Aliased parameters:

```python
from typing import Annotated
from frappeapi import Query

@app.get()
def search_items(
    search_text: Annotated[str, Query(alias="q")] = "",
    page_number: Annotated[int, Query(alias="p")] = 1
):
    return {"search": search_text, "page": page_number}

# GET ?q=laptop&p=2
```

Query parameter models:

```python
from pydantic import BaseModel, Field

class ProductFilter(BaseModel):
    search: str | None = None
    category: str = "all"
    min_price: float = Field(0, ge=0)
    in_stock: bool = True

@app.get()
def filter_products(filters: Annotated[ProductFilter, Query()]):
    return filters
```

### Request Body

Single model:

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    price: float = Field(..., gt=0)

@app.post()
def create_item(item: Item):
    return item
```

Multiple body parameters:

```python
class User(BaseModel):
    username: str
    email: str

class Item(BaseModel):
    name: str
    price: float

@app.post()
def create_user_item(user: User, item: Item):
    return {"user": user, "item": item}

# Request body:
# {
#     "user": {"username": "john", "email": "john@example.com"},
#     "item": {"name": "Laptop", "price": 999.99}
# }
```

Nested models:

```python
from pydantic import HttpUrl

class Image(BaseModel):
    url: HttpUrl
    name: str

class Product(BaseModel):
    name: str
    price: float
    images: List[Image]

@app.post()
def create_product(product: Product):
    return product
```

### Form Data

```python
from typing import Annotated
from frappeapi import Form

@app.post()
def create_user_profile(
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    bio: Annotated[str | None, Form()] = None
):
    return {"username": username, "email": email, "bio": bio}
```

### File Uploads

Small files (in-memory):

```python
from typing import Annotated
from frappeapi import File, Form

@app.post()
def upload_document(
    file: Annotated[bytes, File()],
    description: Annotated[str | None, Form()] = None
):
    return {"file_size": len(file), "description": description}
```

Large files (streamed):

```python
from frappeapi import UploadFile

@app.post()
def upload_large_file(file: UploadFile):
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }
```

### Response Models

Filter response data:

```python
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@app.get(response_model=UserResponse)
def get_user(user_id: int):
    return {
        "id": user_id,
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secret"  # Filtered out
    }
```

List responses:

```python
class Product(BaseModel):
    id: int
    name: str
    price: float

@app.get(response_model=List[Product])
def list_products():
    return [
        {"id": 1, "name": "Laptop", "price": 999.99},
        {"id": 2, "name": "Mouse", "price": 24.99}
    ]
```

### Error Handling

Raise HTTP exceptions:

```python
from frappeapi.exceptions import HTTPException

@app.get()
def get_item(item_id: int):
    if item_id < 0:
        raise HTTPException(status_code=400, detail="Item ID must be positive")
    return {"id": item_id}
```

Custom exception handlers:

```python
from frappeapi import JSONResponse, Request

class ItemNotFound(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id

@app.exception_handler(ItemNotFound)
def item_not_found_handler(request: Request, exc: ItemNotFound):
    return JSONResponse(
        status_code=404,
        content={"error": "ITEM_NOT_FOUND", "detail": f"Item {exc.item_id} not found"}
    )
```

Override validation error handler:

```python
from frappeapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "details": [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()]
        }
    )
```

### Header Parameters

```python
from typing import Annotated
from frappeapi import Header

@app.get()
def get_user_info(
    user_agent: Annotated[str, Header()],
    x_custom_header: Annotated[str, Header()]
):
    return {"user_agent": user_agent, "custom_header": x_custom_header}

# Headers: User-Agent, X-Custom-Header (hyphen converted to underscore)
```

### Field Validation

String validation:

```python
class Product(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    sku: str = Field(pattern="^[A-Z]{2}-[0-9]{4}$")  # Format: XX-0000
```

Numeric validation:

```python
class Order(BaseModel):
    quantity: int = Field(gt=0, le=100)
    unit_price: float = Field(gt=0)
    discount_percent: float = Field(ge=0, le=100)
```

## Version Compatibility

FrappeAPI automatically detects your Frappe version:

| Frappe Version | Support |
|---------------|---------|
| v14.x | Stable |
| v15.x | Stable |
| v16.x | Beta |

Check detected version:

```python
import frappeapi
print(frappeapi.get_detected_frappe_version())  # Returns: 14, 15, or 16
```

## Documentation

FrappeAPI follows FastAPI's interface. For detailed information, see [FastAPI's documentation](https://fastapi.tiangolo.com/).

## Roadmap

### Frappe Versions

- [x] Frappe V14 support
- [x] Frappe V15 support
- [x] Frappe V16 support (develop branch)

### Methods

- [x] `app.get(...)`
- [x] `app.post(...)`
- [x] `app.put(...)`
- [x] `app.patch(...)`
- [x] `app.delete(...)`

### Query Parameters

- [x] Automatic type parsing based on type hints
- [x] Required parameters (`needy: str`, `needy: str = ...`)
- [x] Optional parameters with defaults (`skip: int = 0`)
- [x] Optional parameters without defaults (`limit: int | None = None`)
- [x] Enum support
- [x] Boolean parameters
- [x] List parameters (`?q=foo&q=bar`)
- [x] Aliased parameters (`Query(alias="query")`)
- [x] Query parameter models
- [x] Automatic documentation generation

### Body Parameters

- [x] Pydantic model body (`item: Item`)
- [x] Multiple body parameters
- [x] Singular values with `Body()`
- [x] Embed body parameter
- [x] Nested models
- [x] Automatic type parsing

### Header Parameters

- [x] Basic header support
- [ ] Header parameter models
- [ ] Duplicate headers
- [ ] Forbid extra headers

### Cookie Parameters

- [ ] Cookie parameter support

### Form Data

- [x] Form fields with `Form()`
- [x] Multiple form fields
- [x] Form data as Pydantic model
- [ ] Forbid extra form fields

### File Uploads

- [x] Small files with `File()`
- [x] Large files with `UploadFile`
- [ ] Optional file uploads
- [ ] Multiple file uploads

### Error Handling

- [x] HTTPException
- [x] RequestValidationError
- [x] ResponseValidationError
- [x] Custom exception handlers
- [x] Override default handlers
- [ ] Frappe transaction management

### Response Models

- [x] `response_model` parameter
- [x] Return type annotations
- [x] Output filtering
- [x] `response_model` takes precedence over return type

### Validation

- [x] String validations (`min_length`, `max_length`, `pattern`)
- [x] Numeric validations (`gt`, `ge`, `lt`, `le`)
- [x] Metadata (`title`, `description`, `deprecated`)
- [x] `include_in_schema`

### Planned

- [ ] Rate limiting
- [ ] Dependencies
- [ ] Middleware
- [ ] Debugging capabilities
- [ ] Dotted path parameters

## Related

- [PR #23135](https://github.com/frappe/frappe/pull/23135): Type hints for API functions
- [PR #22300](https://github.com/frappe/frappe/pull/22300): Enhanced `frappe.whitelist()`
- [PR #19029](https://github.com/frappe/frappe/pull/19029): Type safety improvements
- [Issue #14905](https://github.com/frappe/frappe/issues/14905): API documentation discussion
