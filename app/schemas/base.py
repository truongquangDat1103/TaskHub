from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PasswordBaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
