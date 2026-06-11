from pydantic import (
    BaseModel,
    EmailStr,
    field_validator
)


class UserCreate(BaseModel):

    name: str

    email: EmailStr

    password: str


    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):

        return value.lower().strip()


    @field_validator("password")
    @classmethod
    def validate_password(cls, value):

        if len(value) < 6:

            raise ValueError(
                "Password must be at least 6 characters"
            )

        return value


class UserLogin(BaseModel):

    email: EmailStr

    password: str


    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):

        return value.lower().strip()