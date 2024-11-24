import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.crud.ai_crud import ai_model_dao, gpt_prompt_dao
from src.crud.base_crud import GenericCRUD, ModelType
from src.models import User, UserAIModel
from src.schemas.ai_user_models_schema import (UserAIModelCreate,
                                               UserAIModelUpdate)


class UserAIModelDAO(GenericCRUD[UserAIModel, UserAIModelCreate, UserAIModelUpdate]):

    async def create_default(self, user: User, db_session: AsyncSession) -> ModelType:
        default_model, default_prompt = await asyncio.gather(
            ai_model_dao.get_default(db_session=db_session),
            gpt_prompt_dao.get_default(db_session=db_session)
        )
        obj_in = UserAIModelCreate(
            user_id=user.id,
            model_id=default_model.id if default_model else None,
            prompt_id=default_prompt.id if default_prompt else None
        )
        user_ai_model = await self.create(obj_in=obj_in, db_session=db_session)
        await db_session.refresh(user_ai_model, ["model", "prompt"])
        return user_ai_model

    async def get_active_model(self, user: User, db_session: AsyncSession) -> UserAIModel | None:
        query = select(self.model).where(self.model.user_id == user.id)

        result = await db_session.execute(query)
        user_ai_model = result.scalars().one_or_none()

        if user_ai_model:
            await db_session.refresh(user_ai_model, ["model", "prompt"])

        return user_ai_model


user_ai_model_dao = UserAIModelDAO(UserAIModel)
