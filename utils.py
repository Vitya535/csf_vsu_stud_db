from enum import Enum
from enum import auto


class LessonType(str, Enum):
    """Перечисление для типа занятий"""
    lection = 'Лекция'
    practice = 'Практика'
    seminar = 'Семинар'


class HalfYearEnum(int, Enum):
    """Перечисление для полугодия"""
    first_half_year = auto()
    second_half_year = auto()


def get_field(field_id: str, fields: tuple):
    return next((fld for fld in fields if fld.id == field_id))
