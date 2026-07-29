from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SetupRequest(BaseModel):
    family_name: str = Field(min_length=2, max_length=160)
    family_slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$")
    profile: str = Field(default="small_family", pattern=r"^(small_family|extended_family)$")
    household_name: str = Field(min_length=2, max_length=160)
    admin_name: str = Field(min_length=2, max_length=160)
    admin_email: EmailStr
    admin_password: str = Field(min_length=10, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserCreate(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=10, max_length=200)
    household_id: UUID | None = None
    role_names: list[str] = []


class HouseholdCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class UserView(BaseModel):
    id: UUID
    email: str
    display_name: str
    status: str
    is_superadmin: bool
    roles: list[str]
