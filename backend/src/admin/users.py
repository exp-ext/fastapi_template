from sqladmin import ModelView
from src.models import User


class UserAdmin(ModelView, model=User):
    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    column_list = [User.id, User.email, User.is_active, User.is_superuser]

    column_searchable_list = [User.email, User.id]

    column_filters = [User.is_active, User.is_superuser]

    column_labels = {
        User.id: "ID",
        User.email: "Email",
        User.is_active: "Активный",
        User.is_superuser: "Суперпользователь"
    }
