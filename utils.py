from enum import Enum


class LessonType(str, Enum):
    """Перечисление для типа занятий"""
    lection = 'Лекция'
    practice = 'Практика'
    seminar = 'Семинар'


class HalfYearEnum(int, Enum):
    """Перечисление для полугодия"""
    first_half_year = 1
    second_half_year = 2
