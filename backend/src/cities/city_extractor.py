import pickle
import re

from src.conf import settings
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
from pyrsistent import plist


class CityExtractor:
    def __init__(self):
        with open(f'{settings.project_root}/cities/city_regex', encoding='utf8') as f:
            regstr = f.read()

        with open(f'{settings.project_root}/cities/citi_dct.pkl', 'rb') as f:
            self.dct = pickle.load(f)

        self.ex = re.compile(regstr)

        self.tokenizer = RegexpTokenizer(r"[А-Яа-я\-]{3,}")
        self.stemmer = SnowballStemmer('russian')

    def tokenize(self, text):
        """Токенизация текста."""
        return self.tokenizer.tokenize(text)

    def stem_tokens(self, tokens):
        """Применение стемминга к токенам."""
        return [self.stemmer.stem(token) for token in tokens]

    def _extract(self, text):
        """Основной метод для извлечения городов."""
        matches = self.ex.findall(text.lower())
        return [
            self.dct.get(plist(self.stem_tokens(self.tokenize(match))))
            for match in matches
        ]

    def extract(self, text):
        """Извлечение городов из текста."""
        return self._extract(text)
