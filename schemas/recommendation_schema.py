"""Schemas for recommendation and list responses."""

from pydantic import BaseModel
from typing import List


class AllUsersResponse(BaseModel):
    """Response wrapper for returning a list of users and total count."""

    total_users: int
    users: List[dict]
