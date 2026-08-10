import re
from pydantic import BaseModel, field_validator, model_validator

def success_response(data=None, message=""):
    return {
        "success": True,
        "message": message,
        "data":    data,
    }


def error_response(message="", data=None):
    return {
        "success": False,
        "message": message,
        "data":    data,
    }

