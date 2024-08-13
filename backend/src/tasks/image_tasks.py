from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from src.conf import taskiq_broker
from src.crud import image_dao
from src.db.deps import get_async_session
from taskiq import TaskiqDepends
from pathlib import Path


@taskiq_broker.task
async def process_image_task(image_id: UUID4, db_session: AsyncSession = TaskiqDepends(get_async_session)):
    image, url = await image_dao.get(id=image_id, scheme=False, db_session=db_session)
    path = Path(image.file)
    file = await image.storage.download_file_by_url(str(url))
    image.file = await image.storage.update_object(file, image.file, str(path.parent))
    await db_session.commit()

    return f"Successfully update image {image_id}"
