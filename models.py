from pydantic import BaseModel, Field, AnyUrl, EmailStr, computed_field, field_validator, model_validator, ConfigDict
from typing import Optional, Literal
from datetime import date


class Category(BaseModel): # Pydantic model
    name: Literal['starter', 'main course', 'desert', 'drinks'] # exact fields which fields are required in category



class Model(BaseModel): # BaseModel is for checking if the incoming data is valid or not.
    model_config = ConfigDict(
        extra = 'forbid', # This is used to allow extra fields in the model. If set to 'forbid', it will raise an error if any extra fields are present in the input data. If set to 'ignore', it will ignore any extra fields and not include them in the model.
        frozen = True, # This is used to make the model immutable. If set to True, it will prevent any modifications to the model's fields after it has been created. If set to False, it will allow modifications to the model's fields.
        strict = True, # This is used to enforce strict type checking. If set to True, it will raise an error if the input data does not match the expected types of the model's fields. If set to False, it will allow type coercion and attempt to convert the input data to the expected types.
        validate_assignment = True # This is used to validate the assignment of values to the model's fields. If set to True, it will validate the assigned value against the field's type and constraints. If set to False, it will allow any value to be assigned to the field without validation.
    )
    
    
    
    # Field : Value Type
    id           : int 
    name         : str = Field(..., min_length=3, max_length=50, description="The name of the item") # required field
    price        : float = Field(..., gt=0, description="The price of the item") # required field
    category     : Category = Field(..., description="The category of the item") # required field
    is_available : bool = Field(default=True) # default value is True
    description  : Optional[str] = None # optional field
    # email        : EmailStr -> valid email address is required field
    # url          : AnyUrl -> valid url is required field
    # date         : date -> valid date is required field
    
    

    # Field Validator -> This is work for just one field.
    @field_validator('name')
    @classmethod
    def title_name(cls, value): # value = "Chicken BIRIYANI" -> Chicken Biryani
        return value.title() # title() method capitalizes the first letter of each word in a string
        


    # Model Validator -> This is work for multiple fields.
    @model_validator(mode='after')
    def check_available(self):
        if self.is_available and self.price <= 0:
            raise ('Available items must have a price greater than 0.')
        return self


    # Computed field -> Used to create a field whose value is calculated from other fields in the Pydantic model. It can be accessed like a normal field and included in serialization, but it is not a database-stored field by Pydantic itself.
    @computed_field
    @property
    def price_with_tax(self) -> float:
        return round(self.price * 1.05, 2)



    
    
item = Model(
    id=1,
    item_name="Kacchi BIRYANI",
    price=390.00,
    category=Category(name="main course"),
    is_available=True,
    description="A flavorful rice dish with tender chicken and aromatic spices."
)


# 1. model_dumb() -> This method is used to convert the Pydantic model into a dictionary. It returns a dictionary representation of the model, including all its fields and their values.
# This will only work inside python

print(f'Dictionary model_dumb() :\n{item.model_dump()}') # {'id': 1, 'name': 'Kacchi Biryani', 'price': 390.0, 'category': {'name': 'main course'}, 'is_available': True, 'description': 'A flavorful rice dish with tender chicken and aromatic spices.'}



# 2. model_dump_json() -> This method is used to convert the Pydantic model into a JSON string. It returns a JSON representation of the model, including all its fields and their values.
# Object over the internet or website, out of python, we need to use this method to convert the Pydantic model into a JSON string.

print(f'JSON model_dump_json() :\n{item.model_dump_json()}') # {"id": 1, "name": "Kacchi Biryani", "price": 390.0, "category": {"name": "main course"}, "is_available": true, "description": "A flavorful rice dish with tender chicken and aromatic spices."}



print(item.name)
print(item.price_with_tax)

print(item.model_dump())
print(item.model_dump(by_alias=True))