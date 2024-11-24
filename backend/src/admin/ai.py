from sqladmin import ModelView
from src.models import AIModels, GPTPrompt
from src.schemas.common_schema import (get_consumer_choices,
                                       get_provider_choices)
from wtforms import DecimalField, SelectField


class AIModelsAdmin(ModelView, model=AIModels):
    name = "Модель ИИ"
    name_plural = "Модели ИИ"
    column_list = [
        AIModels.id,
        AIModels.provider,
        AIModels.title_public,
        AIModels.title_model,
        AIModels.api_key,
        AIModels.is_default,
        AIModels.is_free,
        AIModels.incoming_price,
        AIModels.outgoing_price,
        AIModels.context_window,
        AIModels.max_request_token,
        AIModels.time_window,
        AIModels.consumer,
    ]
    column_labels = {
        AIModels.id: "ID",
        AIModels.provider: "Провайдер",
        AIModels.title_public: "Публичное название",
        AIModels.title_model: "Название модели",
        AIModels.api_key: "API ключ",
        AIModels.is_default: "По умолчанию",
        AIModels.is_free: "Бесплатная",
        AIModels.incoming_price: "Стоимость входящих токенов",
        AIModels.outgoing_price: "Стоимость исходящих токенов",
        AIModels.context_window: "Контекстное окно",
        AIModels.max_request_token: "Максимум токенов",
        AIModels.time_window: "Окно времени",
        AIModels.consumer: "Потребитель",
    }

    column_searchable_list = [AIModels.title_public, AIModels.title_model, AIModels.api_key]

    column_sortable_list = [
        AIModels.provider,
        AIModels.title_public,
        AIModels.incoming_price,
        AIModels.outgoing_price,
        AIModels.context_window,
        AIModels.time_window,
    ]

    column_default_sort = [(AIModels.title_public, True)]

    form_columns = [
        'provider',
        'title_public',
        'title_model',
        'api_key',
        'is_default',
        'is_free',
        'incoming_price',
        'outgoing_price',
        'context_window',
        'max_request_token',
        'time_window',
        'consumer',
    ]
    form_overrides = {
        'incoming_price': DecimalField,
        'outgoing_price': DecimalField,
        'provider': SelectField,
        'consumer': SelectField,
    }
    form_args = {
        'provider': {
            'choices': get_provider_choices(),
            'label': 'Провайдер',
        },
        'consumer': {
            'choices': get_consumer_choices(),
            'label': 'Потребитель',
        },
    }


class GPTPromptAdmin(ModelView, model=GPTPrompt):
    name = "Промпт ИИ"
    name_plural = "Промпты ИИ"
    column_list = [
        GPTPrompt.id,
        GPTPrompt.title,
        GPTPrompt.en_prompt_text,
        GPTPrompt.ru_prompt_text,
        GPTPrompt.is_default,
        GPTPrompt.consumer,
    ]
    column_labels = {
        GPTPrompt.id: "ID",
        GPTPrompt.title: "Название",
        GPTPrompt.en_prompt_text: "Текст подсказки (EN)",
        GPTPrompt.ru_prompt_text: "Текст подсказки (RU)",
        GPTPrompt.is_default: "По умолчанию",
        GPTPrompt.consumer: "Потребитель",
    }
    column_searchable_list = [GPTPrompt.title, GPTPrompt.en_prompt_text, GPTPrompt.ru_prompt_text]

    column_sortable_list = [
        GPTPrompt.title,
        GPTPrompt.is_default,
        GPTPrompt.consumer,
    ]

    column_default_sort = [(GPTPrompt.title, True)]

    form_columns = [
        'title',
        'en_prompt_text',
        'ru_prompt_text',
        'is_default',
        'consumer',
    ]
    form_overrides = {
        'consumer': SelectField,
    }
    form_args = {
        'consumer': {
            'choices': get_consumer_choices(),
            'label': 'Потребитель',
        },
    }
