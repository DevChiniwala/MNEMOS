# -*- coding: utf-8 -*-
"""Mnemos profiles — identity and context for actors."""

from __future__ import annotations

import json
from typing import Dict

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """Profile data for an entity interacting with memory."""

    user_id: str
    attributes: Dict[str, str] = Field(default_factory=dict)
    preferences: Dict[str, str] = Field(default_factory=dict)


class InMemoryProfileStore:
    """Store for user profiles."""

    def __init__(self) -> None:
        self._profiles: Dict[str, UserProfile] = {}

    def get_profile(self, user_id: str) -> UserProfile:
        return self._profiles.get(user_id, UserProfile(user_id=user_id))

    def update_profile(self, profile: UserProfile) -> None:
        self._profiles[profile.user_id] = profile
