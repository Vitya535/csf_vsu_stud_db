"""Модуль, необходимый для запросов к БД"""

from datetime import datetime
from datetime import date
from datetime import timedelta

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


def get_attend_lessons(subject_name: str, stud_group_id: int, student_id: int, dstart: date, dend: date) -> list:
    """Запрос для нахождения всех пар с посещаемостью для студента,
    которые должны быть в течении семестра по предметам"""
    curriculum_unit_ids = db.session.query(CurriculumUnit.id).\
        join(CurriculumUnit.subject).\
        filter(Subject.name == subject_name,
               CurriculumUnit.stud_group_id == stud_group_id).\
        all()
    teaching_lesson_ids = db.session.query(TEACHING_LESSON_AND_CURRICULUM_UNIT.c.teaching_lesson_id).\
        filter(TEACHING_LESSON_AND_CURRICULUM_UNIT.c.curriculum_unit_id.in_(
            tuple(curriculum_unit_id[0] for curriculum_unit_id in curriculum_unit_ids))).\
        all()
    teaching_pairs = db.session.query(TeachingPairs).\
        filter(TeachingPairs.teaching_lesson_id.in_(
            tuple(teaching_lesson_id[0] for teaching_lesson_id in teaching_lesson_ids))).\
        all()
    teaching_lessons = db.session.query(TeachingLessons).\
        filter(TeachingLessons.teaching_lesson_id.in_(
            tuple(teaching_pair.teaching_lesson_id for teaching_pair in teaching_pairs))).\
        all()
    list_for_output = []
    for teaching_lesson in teaching_lessons:
        days_numerator = [dstart + timedelta(days=x * 2) for x in range((dend - dstart).days + 1) if
                          (dstart + timedelta(days=x * 2)).weekday() == teaching_lesson.day_number_numerator - 1]
        days_denominator = [dstart + timedelta(days=x * 2 + 1) for x in range((dend - dstart).days + 1) if
                            (dstart + timedelta(days=x * 2 + 1)).weekday() == teaching_lesson.day_number_denominator - 1]
        all_days = []
        for i in range(min(len(days_numerator), len(days_denominator))):
            all_days.append(days_denominator[i])
            all_days.append(days_numerator[i])
        days_with_short_names_dict = {0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт', 5: 'Сб', 6: 'Вс'}
        teaching_pairs = db.session.query(TeachingPairs).\
            filter(TeachingPairs.teaching_lesson_id == teaching_lesson.teaching_lesson_id).\
            all()
        for teaching_pair in teaching_pairs:
            attendance = db.session.query(Attendance). \
                filter(Attendance.teaching_pair_id == teaching_pair.pair_id,
                       Attendance.student_id == student_id). \
                first()
            l_type = teaching_lesson.lesson_type
            for item in all_days:
                date_string = f'{item} ({days_with_short_names_dict.get(item.weekday())}) '\
                              f'{teaching_pair.time_of_beginning} - {teaching_pair.time_of_ending}'
                if attendance is not None and attendance.lesson_date == item:
                    attendance_status = attendance.lesson_attendance
                else:
                    attendance_status = None
                t = (date_string, l_type, attendance_status)
                list_for_output.append(t)
    return list_for_output


def get_count_of_all_pairs_for_lessons(subjects: list, stud_group_id: int) -> list:
    """Запрос для нахождения всех пар, которые должны быть в течении семестра по предметам"""
    counts_of_all_pairs_for_lessons = []
    current_year = 2018
    month_number = 10
    lessons_beginning = db.session.query(LessonsBeginning). \
        filter(LessonsBeginning.year == current_year,
               between(month_number, func.month(LessonsBeginning.beginning_date),
                       func.month(LessonsBeginning.end_date))
               ).first()
    count_of_weeks_in_semester = abs(lessons_beginning.end_date - lessons_beginning.beginning_date).days // 7
    for subject in subjects:
        curriculum_unit_ids = db.session.query(CurriculumUnit.id).\
            join(CurriculumUnit.subject).\
            filter(Subject.name == subject.name,
                   CurriculumUnit.stud_group_id == stud_group_id).\
            all()
        teaching_lesson_ids = db.session.query(TEACHING_LESSON_AND_CURRICULUM_UNIT.c.teaching_lesson_id).\
            filter(TEACHING_LESSON_AND_CURRICULUM_UNIT.c.curriculum_unit_id.in_(
                tuple(curriculum_unit_id[0] for curriculum_unit_id in curriculum_unit_ids))).\
            all()
        count_of_teaching_lessons_with_pairs = db.session.query(TeachingLessons, TeachingPairs).\
            join(TeachingPairs).\
            filter(TeachingLessons.teaching_lesson_id.in_(
                tuple(teaching_lesson_id[0] for teaching_lesson_id in teaching_lesson_ids))).\
            count()
        counts_of_all_pairs_for_lessons.append(count_of_teaching_lessons_with_pairs * count_of_weeks_in_semester)
    return counts_of_all_pairs_for_lessons


def get_count_of_attend_lessons(subjects: list, stud_group_id: int, student_id: int) -> list:
    """Запрос для нахождения всех посещенных занятий по предметам для группы студента"""
    counts_of_attend_pairs_count = []
    for subject in subjects:
        curriculum_unit_ids = db.session.query(CurriculumUnit.id).\
            join(CurriculumUnit.subject).\
            filter(Subject.name == subject.name,
                   CurriculumUnit.stud_group_id == stud_group_id).\
            all()
        teaching_lesson_ids = db.session.query(TEACHING_LESSON_AND_CURRICULUM_UNIT.c.teaching_lesson_id).\
            filter(TEACHING_LESSON_AND_CURRICULUM_UNIT.c.curriculum_unit_id.in_(
                tuple(curriculum_unit_id[0] for curriculum_unit_id in curriculum_unit_ids))).\
            all()
        teaching_pair_ids = db.session.query(TeachingPairs.pair_id).\
            filter(TeachingPairs.teaching_lesson_id.in_(
                tuple(teaching_lesson_id[0] for teaching_lesson_id in teaching_lesson_ids))).\
            all()
        attend_pairs_count = db.session.query(Attendance).\
            filter(Attendance.teaching_pair_id.in_(
                        tuple(teaching_pair_id[0] for teaching_pair_id in teaching_pair_ids)
                   ),
                   Attendance.student_id == student_id,
                   Attendance.lesson_attendance).\
            count()
        counts_of_attend_pairs_count.append(attend_pairs_count)
    return counts_of_attend_pairs_count


def get_subjects_for_group_student(group_id: int) -> list:
    """Запрос для нахождения всех предметов, которые есть у студента"""
    subjects = db.session.query(Subject).\
        join(CurriculumUnit.subject).\
        filter(CurriculumUnit.stud_group_id == group_id).\
        all()
    return subjects


def get_all_groups_by_semester(semester: int) -> list:
    """Запрос для нахождения всех групп по семестру"""
    groups = db.session.query(StudGroup).\
        filter(StudGroup.active, StudGroup.semester == semester).\
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum).\
        all()
    return groups


def get_group_by_semester_and_group_number(semester: int, group_num: int, group_subnum: int) -> StudGroup:
    """Запрос для нахождения конкретной группы по семестру, номеру группы и подгруппы"""
    group = db.session.query(StudGroup).\
        filter(StudGroup.active, StudGroup.semester == semester,
               StudGroup.num == group_num, StudGroup.subnum == group_subnum).\
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum).\
        first()
    return group


def get_curriculum_units_by_group_id_and_lesson_type(group_id: int, lesson_type: str) -> list:
    """Запрос для нахождения единиц учебного плана по id группы"""
    curriculum_units = db.session.query(CurriculumUnit).\
        join(CurriculumUnit.teaching_lessons).\
        filter(CurriculumUnit.stud_group_id == group_id,
               TeachingLessons.lesson_type == lesson_type).\
        all()
    return curriculum_units


def get_current_half_year(year_of_study: int) -> int:
    """Запрос для нахождения текущего номера полугодия"""
    # month_number = datetime.now().month
    month_number = 10
    lessons_beginning = db.session.query(LessonsBeginning).\
        filter(LessonsBeginning.year == year_of_study,
               between(month_number, func.month(LessonsBeginning.beginning_date), func.month(LessonsBeginning.end_date))
               ).first()
    return lessons_beginning.half_year


def get_group_of_current_user_by_id(stud_group_id: int) -> StudGroup:
    """Запрос для нахождения группы по id"""
    current_user_group = db.session.query(StudGroup).get(stud_group_id)
    return current_user_group


def get_teaching_lesson_id_by_subject_name(subject_name: str) -> int:
    """Запрос для получения teaching_lesson_id по названию предмета"""
    curriculum_unit = db.session.query(CurriculumUnit).\
        join(CurriculumUnit.subject).\
        filter(Subject.name == subject_name).\
        first()
    teaching_lesson = db.session.query(TEACHING_LESSON_AND_CURRICULUM_UNIT).\
        filter(TEACHING_LESSON_AND_CURRICULUM_UNIT.c.curriculum_unit_id == curriculum_unit.id).\
        first()
    return teaching_lesson.teaching_lesson_id


def get_student_by_id_and_fio(semester: int, group_id: int, student_name: str, student_surname: str,
                              student_middlename: str) -> Student:
    """Запрос для получения студента по семестру, id его группы и ФИО"""
    student = db.session.query(Student).\
        filter(Student.semester == semester,
               Student.stud_group_id == group_id,
               Student.firstname == student_name,
               Student.surname == student_surname,
               Student.middlename == student_middlename).\
        first()
    return student


def insert_or_update_attendance(student_id: int, teaching_pair_id: int,
                                lesson_date: str, lesson_attendance: bool) -> None:
    """Апдейт или вставка новой ячейки посещаемости по определенной дате для студента с конкретным предметом"""
    try:
        attendance_query = db.session.query(Attendance).\
            filter(Attendance.student_id == student_id,
                   Attendance.teaching_pair_id == teaching_pair_id,
                   Attendance.lesson_date == lesson_date)
        if not attendance_query.first():
            attendance = Attendance(lesson_attendance, lesson_date, student_id, teaching_pair_id)
            db.session.add(attendance)
        else:
            attendance_query.update({'lesson_attendance': lesson_attendance})
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def update_can_expose_group_leader_attr_by_teaching_lesson_id(teaching_lesson_id: int,
                                                              can_expose_group_leader_value: bool) -> None:
    """Апдейт атрибута can_expose_group_leader для учебного занятия по его id"""
    try:
        db.session.query(TeachingLessons).\
            filter(TeachingLessons.teaching_lesson_id == teaching_lesson_id).\
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
    student = db.session.query(Student).\
        filter(Student.card_number == card_number).\
        first()
    return student


def get_lesson_dates_for_subject(subject_name: str, year: int, half_year: int) -> list:
    """Запрос для получения дат занятия по парам по названию предмета"""
    curriculum_unit = db.session.query(CurriculumUnit).\
        join(CurriculumUnit.subject).\
        filter(Subject.name == subject_name).\
        first()
    teaching_lessons = db.session.query(TeachingLessons).\
        join(TeachingLessons.curriculum_units).\
        filter(CurriculumUnit.id == curriculum_unit.id).\
        all()
    lessons_beginning = db.session.query(LessonsBeginning).get((year, str(half_year)))
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
                    f"{lesson_date} {teaching_pair.time_of_beginning.strftime('%H:%M')} - "
                    f"{teaching_pair.time_of_ending.strftime('%H:%M')}")
    else:
        for teaching_lesson in teaching_lessons:
            lesson_date = datetime.fromisocalendar(datetime_now.year, current_week_number,
                                                   teaching_lesson.day_number_denominator).strftime('%d.%m.%Y')
            for teaching_pair in teaching_lesson.teaching_pairs:
                lesson_dates.append(
                    f"{lesson_date} {teaching_pair.time_of_beginning.strftime('%H:%M')} - "
                    f"{teaching_pair.time_of_ending.strftime('%H:%M')}")
    return lesson_dates


def filter_students_attendance(students: list, subject_name: str, set_text_dates: set) -> list:
    """Фильтрация посещаемости студентов для более удобного вывода на страницу"""
    curriculum_unit = db.session.query(CurriculumUnit).\
        join(CurriculumUnit.subject).\
        filter(Subject.name == subject_name).\
        first()
    teaching_lessons = db.session.query(TeachingLessons).\
        join(TeachingLessons.curriculum_units).\
        filter(CurriculumUnit.id == curriculum_unit.id).\
        all()
    for student in students:
        student_attendance_list = []
        for teaching_lesson in teaching_lessons:
            for teaching_pair in teaching_lesson.teaching_pairs:
                student_attendance = db.session.query(Attendance).\
                    filter(Attendance.student_id == student.id,
                           Attendance.teaching_pair_id == teaching_pair.pair_id,
                           Attendance.lesson_date.in_(set_text_dates)).\
                    first()
                student_attendance_list.append(student_attendance)
        student.attendance = student_attendance_list
    return students


def get_teaching_pair_ids(subject_name: str) -> list:
    """Получение списка id учебных пар по названию предмета"""
    curriculum_unit = db.session.query(CurriculumUnit).\
        join(CurriculumUnit.subject).\
        filter(Subject.name == subject_name).\
        first()
    teaching_lessons = db.session.query(TeachingLessons).\
        join(TeachingLessons.curriculum_units).\
        filter(CurriculumUnit.id == curriculum_unit.id).\
        all()
    teaching_pair_ids = []
    for teaching_lesson in teaching_lessons:
        for teaching_pair in teaching_lesson.teaching_pairs:
            teaching_pair_ids.append(teaching_pair.pair_id)
    return teaching_pair_ids


def get_pk_and_all_ids(table_name: str, all_ids: list) -> tuple:
    """Получение первичного ключа и кортеж из всех id"""
    table_names_dict = {'lessons_beginning': LessonsBeginning,
                        'teaching_pairs': TeachingPairs,
                        'teaching_lessons': TeachingLessons}
    class_table = table_names_dict.get(table_name)
    pk = inspect(class_table).primary_key
    tuple_of_all_ids = tuple(tuple(pk[i].type.python_type(ids[i]) for i in range(len(ids))) for ids in all_ids)
    return pk, tuple_of_all_ids


def delete_record_from_table(table_name: str, all_ids: list) -> None:
    """Удаление из таблицы одной или нескольких записей"""
    try:
        pk, all_ids = get_pk_and_all_ids(table_name, all_ids)
        table_names_dict = {'lessons_beginning': LessonsBeginning,
                            'teaching_pairs': TeachingPairs,
                            'teaching_lessons': TeachingLessons}
        class_table = table_names_dict.get(table_name)
        db.session.query(class_table).filter(tuple_(*pk).in_(all_ids)).delete()
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
    db.session.flush()


def get_object_for_form_filling(table_name: str, all_ids: list) -> [LessonsBeginning, TeachingLessons, TeachingPairs]:
    """Получение обьекта для заполнения полей формы для multiple редактирования"""
    pk, all_ids = get_pk_and_all_ids(table_name, all_ids)
    table_names_dict = {'lessons_beginning': LessonsBeginning,
                        'teaching_pairs': TeachingPairs,
                        'teaching_lessons': TeachingLessons}
    class_table = table_names_dict.get(table_name)
    records_from_db = db.session.query(class_table).filter(tuple_(*pk).in_(all_ids)).all()
    if len(records_from_db) == 1:
        return records_from_db[0]
    record_for_multiple_edit = class_table()
    for column in class_table.__table__.columns:
        records_from_db_set = set(getattr(record, column.name) for record in records_from_db)
        if len(records_from_db_set) == 1:
            setattr(record_for_multiple_edit, column.name, records_from_db_set.pop())
    return record_for_multiple_edit


def multiple_edit_records(object_from_form_data: [LessonsBeginning, TeachingLessons, TeachingPairs],
                          ids_to_edit: list) -> None:
    """Редактирование нескольких записей в таблице"""
    try:
        record_class = type(object_from_form_data)
        pk = inspect(record_class).primary_key
        tuple_of_ids_to_edit = tuple(tuple(pk[i].type.python_type(item[i]) for i in range(len(item)))
                                     for item in ids_to_edit)
        edit_query = db.session.query(record_class).filter(tuple_(*pk).in_(tuple_of_ids_to_edit))
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
