from __future__ import annotations

from typing import Dict, Any, Optional

from mnemos.generator import AbsGenerator
from mnemos.profile.profile_store import UserProfileStore
from mnemos.prompts import PROFILE_UPDATE_PROMPT


class UserProfileAgent:
    def __init__(self, generator: AbsGenerator, profile_store: Optional[UserProfileStore] = None) -> None:
        self.generator = generator
        self.profile_store = profile_store or UserProfileStore()

    def update_profile(self, user_id: str, message: str) -> Dict[str, Any]:
        prompt = PROFILE_UPDATE_PROMPT.format(message=message)
        try:
            response = self.generator.generate_single(prompt=prompt)
            text = response.get("text", "")
            from mnemos.utils.json_utils import extract_json_object
            data = extract_json_object(text) or {}
        except Exception:
            data = {}

        static_updates = data.get("static_updates") or {}
        dynamic_updates = data.get("dynamic_updates") or {}
        traits_updates = data.get("traits_updates") or {}
        profile = self.profile_store.update(
            user_id=user_id,
            static_updates=static_updates,
            dynamic_updates=dynamic_updates,
            traits_updates=traits_updates,
        )
        return {
            "profile": profile,
            "updates": data,
        }
