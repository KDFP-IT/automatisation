import re


PRICE_LIST = r"Прайс[-–‑ ]листы\s+к\s+разделу\s+КАЦ\s*№\s*"
SECTION_NAME = re.compile(rf"(?:Раздел\s+|{PRICE_LIST})(\d+)\s*[-–—]\s*(\S.*)", re.I)
OFFER_NAME = re.compile(r"^КП\s*(\d+(?:\s*\.\s*\d+)+)(?![\d.])", re.I)
INFO_LETTER = re.compile(r"^Информационное\s+письмо(?:\s|[.\-–—]|$)", re.I)
