"""Модуль, необходимый для запросов к БД"""

from datetime import datetime

from sqlalchemy import between
from sqlalchemy import func
from sqlalchemy import tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect

from app import db
from model import Attendance
from model import CurriculumUnit
from model import LessonsBeginning
from model import StudGroup
from model import Student
from model import Subject
from model import TEACHING_LESSON_AND_CURRICULUM_UNIT
from model import TeachingLessons
from model import TeachingPairs

RECORDS_PER_PAGE = 10


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
        filter(TeachingLessons.lesson_type == lesson_type). \
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
    current_user_group = db.session.query(StudGroup).get(stud_group_id)
    return current_user_group


def get_teaching_lesson_id_by_subject_name(subject_name: str) -> int:
    """Запрос для получения teaching_lesson_id по названию предмета"""
    curriculum_unit = db.session.query(CurriculumUnit). \
        join(CurriculumUnit.subject). \
        filter(Subject.name == subject_name). \
        first()
    teaching_lesson = db.session.query(TEACHING_LESSON_AND_CURRICULUM_UNIT). \
        filter(TEACHING_LESSON_AND_CURRICULUM_UNIT.c.curriculum_unit_id == curriculum_unit.id). \
        first()
    return teaching_lesson.teaching_lesson_id


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


def insert_or_update_attendance(student_id: int, teaching_pair_id: int, lesson_date, lesson_attendance: bool):
    """Апдейт или вставка новой ячейки посещаемости по определенной дате для студента с конкретным предметом"""
    # ToDo - db.session.merge здесь попробовать как-нибудь аккуратно
    try:
        attendance = db.session.query(Attendance). \
            filter(Attendance.student_id == student_id). \
            filter(Attendance.teaching_pair_id == teaching_pair_id). \
            filter(Attendance.lesson_date == lesson_date). \
            first()
        if not attendance:
            attendance = Attendance(lesson_attendance, lesson_date, student_id, teaching_pair_id)
            db.session.add(attendance)
        else:
            db.session.query(Attendance). \
                filter(Attendance.student_id == student_id). \
                filter(Attendance.teaching_pair_id == teaching_pair_id). \
                filter(Attendance.lesson_date == lesson_date). \
                update({'lesson_attendance': lesson_attendance})
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def update_can_expose_group_leader_attr_by_teaching_lesson_id(teaching_lesson_id: int,
                                                              can_expose_group_leader_value: bool):
    """Апдейт атрибута can_expose_group_leader для учебного занятия по его id"""
    try:
        db.session.query(TeachingLessons). \
            filter(TeachingLessons.teaching_lesson_id == teaching_lesson_id). \
            update({'can_expose_group_leader': can_expose_group_leader_value})
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def get_attr_can_expose_group_leader_by_teaching_lesson_id(teaching_lesson_id: int) -> bool:
    """Получение атрибута can_expose_group_leader учебного занятия по его id"""
    teaching_lesson = db.session.query(TeachingLessons).get(teaching_lesson_id)
    return teaching_lesson.can_expose_group_leader


def get_student_by_card_number(card_number: int) -> Student:
    """Получение студента по номеру его карты"""
    student = db.session.query(Student). \
        filter(Student.card_number == card_number). \
        first()
    return student


def get_lesson_dates_for_subject(subject_name: str, year: int, half_year: int) -> list:
    """Запрос для получения дат занятия по парам по названию предмета"""
    curriculum_unit = db.session.query(CurriculumUnit). \
        join(CurriculumUnit.subject). \
        filter(Subject.name == subject_name). \
        first()
    teaching_lessons = db.session.query(TeachingLessons). \
        join(TeachingLessons.curriculum_units). \
        filter(CurriculumUnit.id == curriculum_unit.id). \
        all()
    lessons_beginning = db.session.query(LessonsBeginning).get((year, half_year))
    datetime_now = datetime.now()
    current_week_number = datetime_now.isocalendar()[1]
    beginning_week_number = lessons_beginning.beginning_date.isocalendar()[1]
    diff_between_week_numbers = current_week_number - beginning_week_number
    lesson_dates = []
    if diff_between_week_numbers & 1:
        for teaching_lesson in teaching_lessons:
            lesson_date = datetime.fromisocalendar(datetime_now.year, current_week_number,
                                                   teaching_lesson.day_number_numerator).strftime('%d.%m.%Y')
            for teaching_pair in teaching_lesson.teaching_pairs:
                lesson_dates.append(
                    f"{lesson_date} {teaching_pair.time_of_beginning.strftime('%H:%M')} - {teaching_pair.time_of_ending.strftime('%H:%M')}")
    else:
        for teaching_lesson in teaching_lessons:
            lesson_date = datetime.fromisocalendar(datetime_now.year, current_week_number,
                                                   teaching_lesson.day_number_denominator).strftime('%d.%m.%Y')
            for teaching_pair in teaching_lesson.teaching_pairs:
                lesson_dates.append(
                    f"{lesson_date} {teaching_pair.time_of_beginning.strftime('%H:%M')} - {teaching_pair.time_of_ending.strftime('%H:%M')}")
    return lesson_dates


def filter_students_attendance(students: list, subject_name: str) -> list:
    """Фильтрация посещаемости студентов для более удобного вывода на страницу"""
    curriculum_unit = db.session.query(CurriculumUnit). \
        join(CurriculumUnit.subject). \
        filter(Subject.name == subject_name). \
        first()
    teaching_lessons = db.session.query(TeachingLessons). \
        join(TeachingLessons.curriculum_units). \
        filter(CurriculumUnit.id == curriculum_unit.id). \
        all()
    for student in students:
        student_attendance_list = []
        for teaching_lesson in teaching_lessons:
            for teaching_pair in teaching_lesson.teaching_pairs:
                student_attendance = db.session.query(Attendance). \
                    filter(Attendance.student_id == student.id). \
                    filter(Attendance.teaching_pair_id == teaching_pair.pair_id). \
                    first()
                student_attendance_list.append(student_attendance)
        student.attendance = student_attendance_list
    return students


def get_teaching_pair_ids(subject_name: str) -> list:
    """Получение списка id учебных пар по названию предмета"""
    curriculum_unit = db.session.query(CurriculumUnit). \
        join(CurriculumUnit.subject). \
        filter(Subject.name == subject_name). \
        first()
    teaching_lessons = db.session.query(TeachingLessons). \
        join(TeachingLessons.curriculum_units). \
        filter(CurriculumUnit.id == curriculum_unit.id). \
        all()
    teaching_pair_ids = []
    for teaching_lesson in teaching_lessons:
        for teaching_pair in teaching_lesson.teaching_pairs:
            teaching_pair_ids.append(teaching_pair.pair_id)
    return teaching_pair_ids


def delete_record_from_table(table_name: str, all_ids: list):
    """Удаление из таблицы одной или нескольких записей"""
    try:
        table_names_dict = {'lessons_beginning': LessonsBeginning,
                            'teaching_pairs': TeachingPairs,
                            'teaching_lessons': TeachingLessons}
        class_table = table_names_dict.get(table_name)
        all_ids = tuple(tuple(map(int, item)) for item in all_ids)
        db.session.query(class_table).filter(tuple_(*inspect(class_table).primary_key).in_(all_ids)).delete()
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
    db.session.flush()


def get_object_for_form_filling(table_name: str, all_ids: list) -> [LessonsBeginning, TeachingLessons, TeachingPairs]:
    """Получение обьекта для заполнения полей формы для multiple редаткирования"""
    table_names_dict = {'lessons_beginning': LessonsBeginning,
                        'teaching_pairs': TeachingPairs,
                        'teaching_lessons': TeachingLessons}
    class_table = table_names_dict.get(table_name)
    record_for_multiple_edit = class_table()
    all_ids = tuple(tuple(map(int, item)) for item in all_ids)
    records_from_db = db.session.query(class_table).filter(tuple_(*inspect(class_table).primary_key).in_(all_ids)).all()
    if len(records_from_db):
        return records_from_db[0]
    for column in class_table.__table__.columns:
        records_from_db_set = set(getattr(record, column.name) for record in records_from_db)
        if len(records_from_db_set):
            setattr(record_for_multiple_edit, column.name, records_from_db_set.pop())
    return record_for_multiple_edit


def multiple_edit_records(object_from_form_data: [LessonsBeginning, TeachingLessons, TeachingPairs], ids_to_edit: list):
    """Редактирование нескольких записей в таблице"""
    try:
        record_class = type(object_from_form_data)
        ids_to_edit = tuple(tuple(map(int, item)) for item in ids_to_edit)
        edit_query = db.session.query(record_class).filter(tuple_(*inspect(record_class).primary_key).in_(ids_to_edit))
        attrs_and_values_for_update = object_from_form_data.get_attrs_and_values_for_update()
        edit_query.update(attrs_and_values_for_update)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def get_all_teaching_lessons() -> list:
    """Запрос для получения всех учебных занятий"""
    teaching_lessons = db.session.query(TeachingLessons).all()
    return teaching_lessons


def get_all_lessons_beginning() -> list:
    """Запрос для получения всех начал занятий"""
    lessons_beginning = db.session.query(LessonsBeginning).all()
    return lessons_beginning


def get_all_teaching_pairs() -> list:
    """Запрос для получения всех учебных пар"""
    teaching_pairs = db.session.query(TeachingPairs).all()
    return teaching_pairs


def get_teaching_lessons_on_page(page: int):
    """Запрос для получения учебных занятий на конкретной странице"""
    teaching_lessons = db.session.query(TeachingLessons).paginate(page, RECORDS_PER_PAGE, False)
    return teaching_lessons


def get_lessons_beginning_on_page(page: int):
    """Запрос для получения начал занятий на конкретной странице"""
    lessons_beginning = db.session.query(LessonsBeginning).paginate(page, RECORDS_PER_PAGE, False)
    return lessons_beginning


def get_teaching_pairs_on_page(page: int):
    """Запрос для получения учебных пар на конкретной странице"""
    teaching_pairs = db.session.query(TeachingPairs).paginate(page, RECORDS_PER_PAGE, False)
    return teaching_pairs


def get_lesson_beginning_by_year_and_half_year(year: int, half_year: int) -> LessonsBeginning:
    """Запрос для получения начала учебных занятий в конкретном году и полугодии"""
    lesson_beginning = db.session.query(LessonsBeginning).get((year, half_year))
    return lesson_beginning


def get_teaching_pair_by_id(teaching_pair_id: int) -> TeachingPairs:
    """Запрос для получения пары по id"""
    teaching_pair = db.session.query(TeachingPairs).get(teaching_pair_id)
    return teaching_pair


def get_teaching_lesson_by_id(teaching_lesson_id: int) -> TeachingLessons:
    """Запрос для получения учебного занятия по id"""
    teaching_lesson = db.session.query(TeachingLessons).get(teaching_lesson_id)
    return teaching_lesson
