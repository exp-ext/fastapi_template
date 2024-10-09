from sqlalchemy import select
from src.crud.base_crud import GenericCRUD, ModelType
from src.models import AIModels, GPTPrompt
from src.schemas.ai_schema import (AIModelCreate, AIModelUpdate,
                                   GPTPromptCreate, GPTPromptUpdate)
from sqlalchemy.ext.asyncio.session import AsyncSession


class AIModelsDAO(GenericCRUD[AIModels, AIModelCreate, AIModelUpdate]):

    async def get_default(self, db_session: AsyncSession | None = None) -> ModelType:
        result = await db_session.execute(
            select(self.model).where(self.model.is_default.is_(True))
        )
        return result.scalars().one_or_none()


class GPTPromptDAO(GenericCRUD[GPTPrompt, GPTPromptCreate, GPTPromptUpdate]):
    async def get_default(self, db_session: AsyncSession | None = None) -> ModelType:
        result = await db_session.execute(
            select(self.model).where(self.model.is_default.is_(True))
        )
        return result.scalars().one_or_none()


ai_model_dao = AIModelsDAO(AIModels)
gpt_prompt_dao = GPTPromptDAO(GPTPrompt)
