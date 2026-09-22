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
        validate_by_name = True,
        validate_by_alias = True
    )

    # Fields
    id: int

    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="The name of the item",
        alias="item_name"  # Alias for the field
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

    # Field Validator
    @field_validator('name')
    @classmethod
    def title_name(cls, value):
        return value.title()

    # Model Validator
    @model_validator(mode='after')
    def check_available(self):
        if self.is_available and self.price <= 0:
            raise ValueError(
                'Available items must have a price greater than 0.'
            )
        return self

    # Computed Field
    @computed_field
    @property
    def price_with_tax(self) -> float:
        return round(self.price * 1.05, 2)


item = Model(
    id=1,  # Changed from '1' to 1 because strict=True
    item_name="Kacchi BIRYANI",
    price=390.00,
    category=Category(name="main course"),
    is_available=True,
    description="A flavorful rice dish with tender chicken and aromatic spices."
)


# Dictionary
print(f'Dictionary model_dump():\n{item.model_dump()}')


# JSON
print(f'\nJSON model_dump_json():\n{item.model_dump_json()}')


# Access fields
print(f'\nName: {item.name}')
print(f'Price with tax: {item.price_with_tax}')


# Dump using alias
print(f'\nNormal dump:\n{item.model_dump()}')
print(f'\nAlias dump:\n{item.model_dump(by_alias=True)}')