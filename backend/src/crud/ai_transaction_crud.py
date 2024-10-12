import uuid
from sqlalchemy import and_, between, select
from src.crud.base_crud import GenericCRUD
from src.models import AITransactions
from src.schemas.ai_transaction_schema import AITransactionCreate
from sqlalchemy.ext.asyncio.session import AsyncSession


class AITransactionsDAO(GenericCRUD[AITransactions, AITransactionCreate, AITransactionCreate]):

    async def get_history(self, user_ai_model_id: uuid.UUID, time_start, current_time, db_session: AsyncSession):
        query = select(
            AITransactions.question,
            AITransactions.question_tokens,
            AITransactions.answer,
            AITransactions.answer_tokens
        ).where(
            and_(
                AITransactions.user_ai_model_id == user_ai_model_id,
                between(AITransactions.created_at, time_start, current_time),
                AITransactions.answer.isnot(None)
            )
        )

        result = await db_session.execute(query)
        history = result.mappings().all()
        pass
        return [dict(row) for row in history]


ai_transaction_dao = AITransactionsDAO(AITransactions)