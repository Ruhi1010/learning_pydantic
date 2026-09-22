

import json
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError, computed_field, field_validator, model_validator


class Category(BaseModel):  # Pydantic model
    # Fixed a typo from the original ('desert' -> 'dessert') and added
    # 'snacks', since item #9 (Samosa) in the sample data uses that category.
    name: Literal["starter", "main course", "dessert", "beverage", "snacks"]


class Model(BaseModel):
    model_config = ConfigDict(
        extra="allow",                # Extra fields (e.g. 'spicy') are kept, not rejected
        frozen=True,                  # Immutable once created — no attribute can be reassigned
        strict=True,                  # No implicit type coercion (e.g. "10" will NOT become 10)
        validate_assignment=True,     # Re-validate on edit (moot here since frozen blocks edits)
    )

    id: int
    name: str = Field(..., min_length=3, max_length=50, description="Item name")
    price: float = Field(..., gt=0, description="Item price, must be greater than 0")
    category: Category = Field(..., description="Item category")
    is_available: bool = Field(default=True)
    description: Optional[str] = None
    added_by_email: EmailStr = Field(..., description="Email of the person who added this item")
    # strict=False override: JSON has no native date type, only ISO strings like
    # "2025-01-12" — with the model strict, a plain str would otherwise be
    # rejected outright instead of being parsed into a real date.
    date_added: date = Field(..., strict=False, description="Date the item was added (ISO format)")

    # --- Field validator ---
    @field_validator("category", mode="before")
    @classmethod
    def wrap_category_string(cls, value):
        """Sample JSON stores category as a plain string ('starter'), not a
        nested object — wrap it so it can build the Category submodel."""
        if isinstance(value, str):
            return {"name": value}
        return value

    @field_validator("name")
    @classmethod
    def title_name(cls, value):
        return value.title()

    # --- Model validator ---
    @model_validator(mode="after")
    def check_available(self):
        if self.is_available and self.price <= 0:
            # Original had `raise('...')`, which raises a TypeError since you
            # can't raise a bare string — fixed to a proper ValueError.
            raise ValueError("Available item must have a price greater than 0")
        return self

    # --- Computed field ---
    @computed_field
    @property
    def price_with_tax(self) -> float:
        return round(self.price * 1.05, 2)


if __name__ == "__main__":
    # --- Quick manual example, same spirit as the original snippet ---
    item = Model(
        id=2,
        name="Chole Kulche",
        price=180,
        category="main course",
        added_by_email="chef.manual@spicehouse.com",
        date_added="2025-04-01",
        spicy="Bohot tezz",  # extra field, kept because extra='allow'
    )

    print("Dictionary model_dump()")
    print(item.model_dump())

    print("\nJSON model_dump_json()")
    print(item.model_dump_json())

    try:
        item.price = 999  # should fail — model is frozen
    except Exception as e:
        print(f"\nFrozen check -> can't mutate: {type(e).__name__}")

    # --- Batch-validate every item in the sample JSON file ---
    print("\n" + "=" * 60)
    print("Validating sample-menu-items.json")
    print("=" * 60)

    with open("practice_menu.json") as f:
        raw_items = json.load(f)

    valid_count = 0
    invalid_count = 0

    for raw in raw_items:
        try:
            validated = Model(**raw)
            valid_count += 1
            print(f"[OK]   id={validated.id:<3} {validated.name}  (price incl. tax: {validated.price_with_tax})")
        except ValidationError as e:
            invalid_count += 1
            print(f"[FAIL] id={raw.get('id')} {raw.get('name')}")
            for err in e.errors():
                loc = ".".join(str(p) for p in err["loc"])
                print(f"       - {loc}: {err['msg']}")

    print("-" * 60)
    print(f"Valid: {valid_count}  |  Invalid: {invalid_count}  |  Total: {len(raw_items)}")