from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from src.conf import taskiq_broker
from src.crud import image_dao
from src.db.deps import get_async_session
from src.models import Image
from src.utils.s3_utils import S3Manager
from taskiq import TaskiqDepends


@taskiq_broker.task
async def process_image_task(image_id: UUID4, db_session: AsyncSession = TaskiqDepends(get_async_session)):
    image, url = await image_dao.get(id=image_id, scheme=False, db_session=db_session)
    path = image.file.split('/')[0]
    file_url = str(url) if not isinstance(url, str) else url

    s3_manager = S3Manager(storage=Image.storage())
    file = await s3_manager.download_file_by_url(file_url)
    new_key = await s3_manager.update_object(file, image.file, path)

    image.file = new_key
    await db_session.commit()

    return f"Successfully update image {image_id}"
