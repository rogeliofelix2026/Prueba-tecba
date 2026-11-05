"""Caso de uso: evaluación preliminar de actividad + territorio."""

from __future__ import annotations

from app.repositories.activity import ActivityRepository
from app.repositories.urban_uses import UrbanUseRuleRepository
from app.services.urban_uses import evaluate_activity


class UrbanEvaluationService:
    def __init__(
        self,
        activities: ActivityRepository,
        rules: UrbanUseRuleRepository,
    ) -> None:
        self.activities = activities
        self.rules = rules

    async def evaluate(
        self,
        activity_input: str | dict,
        urban_rule: dict | None,
        *,
        surface_m2: float | None = None,
        street_width_m: float | None = None,
        frontage_m: float | None = None,
    ) -> dict:
        if isinstance(activity_input, dict) and activity_input.get("id") is not None:
            # Reutiliza la actividad ya confirmada en el flujo principal; evita
            # resolver otra vez por nombre y crear una ambigüedad artificial.
            activity = activity_input
        else:
            activity = await self.activities.resolve(str(activity_input))
        if activity is None:
            raise ValueError("Actividad no encontrada en el catálogo.")

        rules = await self.rules.for_activity(int(activity["id"]))
        if urban_rule is not None:
            urban_rule = dict(urban_rule)
            urban_rule["activity_rules"] = {
                str(key): value for key, value in rules.items()
            }

        return evaluate_activity(
            activity,
            urban_rule,
            surface_m2=surface_m2,
            street_width_m=street_width_m,
            frontage_m=frontage_m,
        )
