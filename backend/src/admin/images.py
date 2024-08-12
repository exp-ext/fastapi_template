from sqladmin import ModelView
from src.models import Image


class ImageAdmin(ModelView, model=Image):
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True

    column_list = [Image.id, Image.file, Image.is_main, Image.created_at, Image.updated_at]
    column_searchable_list = [Image.file]
    column_sortable_list = [Image.is_main, Image.created_at]

    column_labels = {
        Image.id: "ID",
        Image.file: "Файл",
        Image.is_main: "Главное изображение",
        Image.created_at: "Дата создания",
        Image.updated_at: "Дата обновления"
    }

    column_details_list = [Image.id, Image.file, Image.is_main, Image.created_at, Image.updated_at]

    can_export = True
    export_types = ["csv", "json"]
