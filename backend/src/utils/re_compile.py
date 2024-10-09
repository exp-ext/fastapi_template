import re

from src.cities.city_extractor import CityExtractor

DATE_PATTERN = re.compile(r'(\d+)[\.](\d+)[\.]?')
COMMAND_PATTERN = re.compile(r'^/.*')
WORD_PATTERN = re.compile(r'\b\w+\b')
NUMBER_BYTE_OFFSET = re.compile(r'byte offset (\d+)')
DIGIT_REGEX = re.compile(r'\d+')
AD_BLOCK_ID_REGEX = re.compile(r'^[A-Z]-[A-Z]-\d+-\d+$')
MARKDOWN_CODE_BLOCK = re.compile(r'```[\s\S]*?```')
CITY_EXTRACTOR = CityExtractor()
CHAPTER_RE = re.compile(r'^(\d+)\.?\s+([^\.].+)$', re.M)
SUBCHAPTER_RE = re.compile(r'^(\d+\.\d+)\.?\s+(.+)$', re.M)
DESCRIPTION_RE = re.compile(r'^\s*([^\d].+)$', re.M)
NUMBER_RE = re.compile(r'^\d')
PUNCTUATION_RE = re.compile(r'[^\w\s]')
