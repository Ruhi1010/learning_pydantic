# Pydantic Model Documentation

This document explains the Pydantic v2 concepts used in the `Model` / `Category`
example below, based on a restaurant menu item validator.

```python
from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_validator,
    model_validator,
    ConfigDict
)
from typing import Optional, Literal


class Category(BaseModel):
    name: Literal['starter', 'main course', 'desert', 'drinks']


class Model(BaseModel):

    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
        validate_assignment=True,
        validate_by_name=True,
        validate_by_alias=True
    )

    id: int

    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="The name of the item",
        alias="item_name"
    )

    price: float = Field(
        ...,
        gt=0,
        description="The price of the item"
    )

    category: Category = Field(
        ...,
        description="The category of the item"
    )

    is_available: bool = Field(default=True)

    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def title_name(cls, value):
        return value.title()

    @model_validator(mode='after')
    def check_available(self):
        if self.is_available and self.price <= 0:
            raise ValueError(
                'Available items must have a price greater than 0.'
            )
        return self

    @computed_field
    @property
    def price_with_tax(self) -> float:
        return round(self.price * 1.05, 2)
```

---

## 1. What Pydantic Is

Pydantic is a data-validation library. A `BaseModel` subclass declares the
**shape** of your data using ordinary Python type hints, and Pydantic then:

- Parses raw input (dicts, JSON, keyword args) into typed Python objects
- Validates every field against its declared type and constraints
- Raises a `ValidationError` listing every problem at once if anything is invalid
- Can serialize the validated object back out to a `dict` or JSON string

---

## 2. `Category` — a Nested Model with `Literal`

```python
class Category(BaseModel):
    name: Literal['starter', 'main course', 'desert', 'drinks']
```

- `Category` is itself a `BaseModel`, so it can be nested inside another model
  (see `category: Category` on `Model`).
- `Literal[...]` restricts `name` to one of the exact listed strings. Anything
  else (e.g. `"soup"`) fails validation. This is how you model an enum-like
  field without a full `Enum` class.
- Because `Model` is `strict=True` (see below), `category` must be passed as
  an actual `Category` instance (or a dict, depending on strictness rules for
  nested models) — a bare string like `"main course"` will **not** be
  auto-wrapped into `{"name": "main course"}` unless you add a
  `field_validator(mode="before")` to do that conversion yourself.

---

## 3. `model_config` — Model-Wide Behavior

```python
model_config = ConfigDict(
    extra='forbid',
    frozen=True,
    strict=True,
    validate_assignment=True,
    validate_by_name=True,
    validate_by_alias=True
)
```

| Option | Effect |
|---|---|
| `extra='forbid'` | Any field in the input that isn't declared on the model raises a `ValidationError`. (Alternatives: `'ignore'` drops unknown fields silently, `'allow'` keeps them.) |
| `frozen=True` | Once created, the instance is immutable — attempting `item.price = 999` raises an error. This also makes the model hashable. |
| `strict=True` | Disables Pydantic's usual "lax" type coercion. For example `id="1"` (a string) will **not** be coerced into `int`; it must already be an `int`. This applies model-wide unless a field overrides it. |
| `validate_assignment=True` | If the model *weren't* frozen, this would re-run validation every time an attribute is reassigned. Combined with `frozen=True` here, it's effectively redundant (there can be no assignment to validate), but it's good practice to keep in case `frozen` is ever removed. |
| `validate_by_name=True` | Allows the model to be constructed using the field's **Python name** (`name=`) in addition to its alias. |
| `validate_by_alias=True` | Allows the model to be constructed using the field's **alias** (`item_name=`) in addition to its Python name. Together with `validate_by_name`, both `name=` and `item_name=` are accepted as constructor kwargs. |

> **Note:** In Pydantic v1 / early v2, the equivalent of `validate_by_name`
> was `populate_by_name`. If you're on an older Pydantic version, use
> `populate_by_name=True` instead.

---

## 4. Fields and `Field(...)`

```python
id: int

name: str = Field(
    ...,
    min_length=3,
    max_length=50,
    description="The name of the item",
    alias="item_name"
)

price: float = Field(..., gt=0, description="The price of the item")

category: Category = Field(..., description="The category of the item")

is_available: bool = Field(default=True)

description: Optional[str] = None
```

- **`id: int`** — a plain required field, no extra constraints. Because of
  `strict=True`, it must be passed as an actual `int`.
- **`Field(...)`** — the `...` (Ellipsis) marks the field as **required**
  (no default value).
- **`min_length` / `max_length`** — string-length constraints on `name`.
- **`alias="item_name"`** — the field is exposed externally (constructor
  input and, optionally, output) as `item_name`, while internally it's
  accessed as `model.name`. This is common when your API's JSON schema uses
  different casing/naming than your Python code.
- **`gt=0`** — numeric constraint: `price` must be strictly greater than 0.
- **`category: Category`** — a required nested model; Pydantic validates the
  nested object recursively.
- **`is_available: bool = Field(default=True)`** — optional field with a
  default value.
- **`description: Optional[str] = None`** — optional field; `None` is a valid
  value and also the default when omitted.

---

## 5. `field_validator` — Per-Field Validation

```python
@field_validator('name')
@classmethod
def title_name(cls, value):
    return value.title()
```

- Runs after the field's own type/constraint checks pass (default
  `mode='after'`).
- Takes the already-validated value and can transform it before it's stored
  on the model — here, `"Kacchi BIRYANI"` becomes `"Kacchi Biryani"`.
- Must be a `@classmethod` decorated *below* `@field_validator`.
- A validator can also raise `ValueError` (or `TypeError`, `AssertionError`)
  to reject a value; Pydantic converts that into a `ValidationError` entry.
- `mode='before'` (not used here) would let you intercept and transform the
  **raw** input before Pydantic's own type coercion/validation runs — this is
  how you'd unwrap a plain string into `{"name": ...}` for the `Category`
  field mentioned in Section 2.

---

## 6. `model_validator` — Cross-Field Validation

```python
@model_validator(mode='after')
def check_available(self):
    if self.is_available and self.price <= 0:
        raise ValueError(
            'Available items must have a price greater than 0.'
        )
    return self
```

- `mode='after'` runs once **all** individual fields have already passed
  their own validation, and gives you `self` — the fully-built model — so you
  can check relationships *between* fields (something a single
  `field_validator` can't do).
- Must `return self` (or a modified copy, if the model isn't frozen) so the
  final validated instance is produced.
- Raising `ValueError` here fails the whole model's construction, not just
  one field.
- **Important:** raise `ValueError(...)`, not a bare `raise('...')` — the
  latter is invalid Python (`raise` needs an exception instance, not a
  string) and throws a `TypeError` instead of a clean validation error.

---

## 7. `computed_field` — Derived, Serialized Properties

```python
@computed_field
@property
def price_with_tax(self) -> float:
    return round(self.price * 1.05, 2)
```

- Combines Python's `@property` with Pydantic's `@computed_field`.
- Unlike a plain `@property`, a `computed_field` **is included** in
  `model_dump()` and `model_dump_json()` output automatically, even though it
  isn't a real stored/input field.
- It's read-only and recalculated every time it's accessed — nothing is
  cached or persisted.
- A return type annotation (`-> float`) is required so Pydantic knows how to
  serialize it.

---

## 8. Aliases in Practice

```python
item = Model(
    id=1,
    item_name="Kacchi BIRYANI",   # using the alias
    price=390.00,
    category=Category(name="main course"),
    is_available=True,
    description="A flavorful rice dish with tender chicken and aromatic spices."
)
```

- The constructor call uses `item_name=` (the alias) rather than `name=`,
  which works because `validate_by_alias=True`. Thanks to
  `validate_by_name=True`, `name="Kacchi BIRYANI"` would also have worked.
- `category=Category(name="main course")` passes an **already-constructed**
  `Category` instance, which satisfies `strict=True` (a raw dict or string
  would be rejected under strict mode without a `mode='before'` validator).
- `id=1` is a genuine `int`; passing `id="1"` would raise a `ValidationError`
  because of `strict=True`.

---

## 9. Serialization: `model_dump()` vs `model_dump_json()`

```python
item.model_dump()          # -> Python dict
item.model_dump_json()     # -> JSON string
item.model_dump(by_alias=True)   # -> dict keyed by alias ("item_name" instead of "name")
```

| Method | Output | Typical use |
|---|---|---|
| `model_dump()` | A Python `dict` (nested models become nested dicts) | In-process use, passing to other Python code |
| `model_dump_json()` | A JSON-formatted `str` | Sending over HTTP, writing to a file, logging |
| `model_dump(by_alias=True)` | Dict keyed by each field's `alias` where defined | Matching an external API's expected JSON shape |

Both include `price_with_tax`, since it's a `computed_field`.

---

## 10. `frozen=True` and Immutability

Because the model is frozen:

```python
item.price = 999   # raises a pydantic.ValidationError / TypeError-like error
```

Any attempt to reassign an attribute after construction fails. This is useful
for representing values that should never change once validated — e.g. an
immutable record read from a database or API response.

---

## 11. `strict=True` — What It Changes

With `strict=True` at the model level:

- `id="1"` → **rejected** (string is not coerced to `int`)
- `price="390.00"` → **rejected** (string is not coerced to `float`)
- `is_available="true"` → **rejected** (string is not coerced to `bool`)

Without `strict=True` (Pydantic's default "lax" mode), all of the above would
be silently coerced into the correct type. Strict mode trades convenience for
predictability — useful when you want to guarantee the caller sent exactly
the right type, e.g. validating data that's already supposed to be
well-formed (from your own database or internal service) rather than loosely
typed user input.

> If you need strict mode overall but want one specific field to allow
> coercion (e.g. parsing an ISO date string into a `date` object), override it
> per-field with `Field(..., strict=False)`.

---

## 12. `extra='forbid'` — Rejecting Unknown Fields

```python
Model(id=1, item_name="Chai", price=50, category=..., unexpected_field="x")
# -> ValidationError: Extra inputs are not permitted
```

`extra='forbid'` makes the model strict about its schema: any key in the
input that isn't `id`, `item_name`/`name`, `price`, `category`,
`is_available`, or `description` causes validation to fail. This is good for
catching typos or unexpected payload shapes early. The alternatives are:

- `extra='ignore'` — silently drop unknown fields (default in Pydantic v2)
- `extra='allow'` — keep unknown fields and expose them as extra attributes

---

## 13. Quick Reference: Concepts Used

| Concept | Import | Purpose |
|---|---|---|
| `BaseModel` | `pydantic` | Base class for all validated models |
| `Field` | `pydantic` | Declare constraints, defaults, aliases, docs per field |
| `ConfigDict` | `pydantic` | Configure model-wide behavior (`model_config`) |
| `field_validator` | `pydantic` | Custom validation/transformation for a single field |
| `model_validator` | `pydantic` | Custom validation across multiple fields |
| `computed_field` | `pydantic` | Derived, serialized read-only property |
| `Literal` | `typing` | Restrict a field to an exact set of values |
| `Optional` | `typing` | Field may be `None` / is not required |

---

## 14. Common Pitfalls Seen in Similar Code

- **`raise('some string')`** is invalid — always raise an actual exception:
  `raise ValueError('some string')`.
- Typos in `Literal` values (e.g. `'desert'` instead of `'dessert'`) will
  silently make valid data fail category validation — the `Literal` list
  must exactly match the real-world values you expect.
- Passing a plain string for a nested model field (e.g.
  `category="main course"`) fails under `strict=True` unless you add a
  `field_validator(mode='before')` to wrap it into the expected shape.
- Forgetting `by_alias=True` when your consumer expects alias-cased JSON
  (`item_name`) will produce output keyed by the Python field name (`name`)
  instead.