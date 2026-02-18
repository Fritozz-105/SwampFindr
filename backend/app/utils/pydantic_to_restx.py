"""Helper to convert Pydantic models to Flask-RESTX models."""
from flask_restx import fields
from pydantic import BaseModel
from typing import get_origin, get_args


def pydantic_to_restx_model(api, pydantic_model: BaseModel, name: str = None):
    """
    Convert a Pydantic model to a Flask-RESTX model for Swagger documentation.
    
    Args:
        api: Flask-RESTX Namespace or Api instance
        pydantic_model: Pydantic BaseModel class
        name: Optional name for the model (defaults to Pydantic model name)
    
    Returns:
        Flask-RESTX model
    """
    if name is None:
        name = pydantic_model.__name__
    
    restx_fields = {}
    
    for field_name, field_info in pydantic_model.model_fields.items():
        field_type = field_info.annotation
        required = field_info.is_required()
        description = field_info.description or ""
        
        # Get the actual type if it's Optional
        origin = get_origin(field_type)
        if origin is type(None) or str(origin) == 'typing.Union':
            args = get_args(field_type)
            if args and type(None) in args:
                # It's Optional, get the actual type
                field_type = next(arg for arg in args if arg is not type(None))
                required = False
        
        # Handle List types
        if get_origin(field_type) is list:
            inner_type = get_args(field_type)[0]
            if inner_type == str:
                restx_fields[field_name] = fields.List(fields.String, required=required, description=description)
            elif inner_type == int:
                restx_fields[field_name] = fields.List(fields.Integer, required=required, description=description)
            elif inner_type == float:
                restx_fields[field_name] = fields.List(fields.Float, required=required, description=description)
            else:
                restx_fields[field_name] = fields.List(fields.Raw, required=required, description=description)
        # Map Python types to Flask-RESTX fields
        elif field_type == str:
            restx_fields[field_name] = fields.String(required=required, description=description)
        elif field_type == int:
            restx_fields[field_name] = fields.Integer(required=required, description=description)
        elif field_type == float:
            restx_fields[field_name] = fields.Float(required=required, description=description)
        elif field_type == bool:
            restx_fields[field_name] = fields.Boolean(required=required, description=description)
        else:
            # Default to Raw for complex types
            restx_fields[field_name] = fields.Raw(required=required, description=description)
    
    return api.model(name, restx_fields)
