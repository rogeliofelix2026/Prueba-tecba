"""Servicio de aplicación para resolver los procedimientos asociados a una actividad."""

from app.repositories.procedures import ProcedureRepository


class ProcedureService:
    def __init__(self) -> None:
        self.repo = ProcedureRepository()

    async def resolve(self, activity_id: int):
        return await self.repo.for_activity(activity_id)
