from src.conf import static_storage


async def static_collection():
    await static_storage.collect_and_upload_static(static_dir="src/static")
