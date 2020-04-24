"""Модуль, необходимый для запросов к БД"""

from sqlalchemy import between
from sqlalchemy import func

from app import db
from model import Attendance
from model import CurriculumUnit
from model import LessonsBeginning
from model import StudGroup
from model import Student
from model import Subject
from model import TEACHING_LESSON_AND_CURRICULUM_UNIT
from model import TeachingLesson


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
        join(CurriculumUnit.teaching_lessons). \
        filter(CurriculumUnit.stud_group_id == group_id). \
        filter(TeachingLesson.lesson_type == lesson_type). \
        all()
    return curriculum_units


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


def get_teaching_lesson_id_by_subject_name(subject_name: str) -> int:
    """Запрос для получения teaching_lesson_id, необходимого для посещаемости"""
    curriculum_unit_id = db.session.query(CurriculumUnit). \
        join(CurriculumUnit.subject). \
        filter(Subject.name == subject_name). \
        first().id
    teaching_lesson_id = db.session.query(TEACHING_LESSON_AND_CURRICULUM_UNIT). \
        filter(TEACHING_LESSON_AND_CURRICULUM_UNIT.c.curriculum_unit_id == curriculum_unit_id). \
        first().teaching_lesson_id
    return teaching_lesson_id


def get_student_by_id_and_fio(semester: int, group_id: int, student_name: str, student_surname: str,
                              student_middlename: str) -> Student:
    """Запрос для получения студента по семестру, id его группы и ФИО"""
    student = db.session.query(Student). \
        filter(Student.semester == semester). \
        filter(Student.stud_group_id == group_id). \
        filter(Student.firstname == student_name). \
        filter(Student.surname == student_surname). \
        filter(Student.middlename == student_middlename). \
        first()
    return student


def update_attendance(student_id: int, teaching_lesson_id: int, lesson_date, lesson_attendance: bool):
    """Апдейт ячейки посещаемости по определенной дате для студента с конкретным предметом"""
    db.session.query(Attendance). \
        filter(Attendance.student_id == student_id). \
        filter(Attendance.teaching_lesson_id == teaching_lesson_id). \
        filter(Attendance.lesson_date == lesson_date). \
        update({'lesson_attendance': lesson_attendance})
    db.session.commit()


def update_can_expose_group_leader_attr_by_teaching_lesson_id(teaching_lesson_id: int,
                                                              can_expose_group_leader_value: bool):
    """Апдейт атрибута can_expose_group_leader для учебного занятия по его id"""
    db.session.query(TeachingLesson). \
        filter(TeachingLesson.teaching_lesson_id == teaching_lesson_id). \
        update({'can_expose_group_leader': can_expose_group_leader_value})
    db.session.commit()


def get_attr_can_expose_group_leader_by_teaching_lesson_id(teaching_lesson_id: int) -> bool:
    """Получение атрибута can_expose_group_leader учебного занятия по его id"""
    can_expose_group_leader_value = db.session.query(TeachingLesson). \
        filter(TeachingLesson.teaching_lesson_id == teaching_lesson_id). \
        first().can_expose_group_leader
    return can_expose_group_leader_value
