"""Модуль, необходимый для запросов к БД"""

from sqlalchemy import between
from sqlalchemy import func

from app import db
from model import CurriculumUnit
from model import LessonsBeginning
from model import StudGroup


def get_all_groups_by_semester(semester: int) -> list:
    """Запрос для нахождения всех групп по семестру"""
    groups = db.session.query(StudGroup). \
        filter(StudGroup.active). \
        filter(StudGroup.semester == semester). \
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num,
                 StudGroup.subnum). \
        all()
    return groups


def get_group_by_semester_and_group_number(semester: int, group_num: int, group_subnum: int) -> StudGroup:
    """Запрос для нахождения конкретной группы по семестру, номеру группы и подгруппы"""
    group = db.session.query(StudGroup). \
        filter(StudGroup.active). \
        filter(StudGroup.semester == semester). \
        filter(StudGroup.num == group_num). \
        filter(StudGroup.subnum == group_subnum). \
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num,
                 StudGroup.subnum). \
        first()
    return group


def get_curriculum_units_by_group_id_and_lesson_type(group_id: int, lesson_type: str) -> list:
    """Запрос для нахождения единиц учебного плана по id группы"""
    curriculum_units = db.session.query(CurriculumUnit). \
        filter(CurriculumUnit.stud_group_id == group_id). \
        all()
    curriculum_units_with_checked_teaching_lessons = []
    for unit in curriculum_units:
        for teaching_lesson in unit.teaching_lessons:
            if teaching_lesson.lesson_type.value == lesson_type:
                curriculum_units_with_checked_teaching_lessons.append(unit)
    return curriculum_units_with_checked_teaching_lessons


def get_current_half_year(year_of_study: int) -> int:
    """Запрос для нахождения текущего номера полугодия"""
    # month_number = datetime.now().month
    month_number = 10
    lessons_beginning = db.session.query(LessonsBeginning). \
        filter(LessonsBeginning.year == year_of_study). \
        filter(
        between(month_number, func.month(LessonsBeginning.beginning_date), func.month(LessonsBeginning.end_date))). \
        first()
    return lessons_beginning.half_year


def get_group_of_current_user_by_id(stud_group_id: int) -> StudGroup:
    """Запрос для нахождения группы по id"""
    current_user_group = db.session.query(StudGroup). \
        filter(StudGroup.id == stud_group_id). \
        first()
    return current_user_group
