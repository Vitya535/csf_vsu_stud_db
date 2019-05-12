from datetime import datetime

from app_config import db
from model import StudGroup, Subject, Teacher, Student, CurriculumUnit, AttMark, MarkType, AdminUser
from wtforms import validators, Form, SubmitField, IntegerField, StringField, HiddenField, FormField
from wtforms_alchemy import ModelForm, ModelFieldList
from wtforms_alchemy.fields import QuerySelectField
from wtforms_alchemy.validators import Unique


class _PersonForm:
    surname = StringField('Фамилия', [validators.DataRequired()])
    firstname = StringField('Имя', [validators.DataRequired()])
    middlename = StringField('Отчество')
    login = StringField('Login', [
        validators.Optional(),
        validators.Regexp("^[a-z0-9_]+$", message="Учётное имя может содержать только латинкие символы, цифры и знак подчёркивания"),
        Unique(Student.login, get_session=lambda: db.session, message='Логин занят'),
        Unique(Teacher.login, get_session=lambda: db.session, message='Логин занят'),
        Unique(AdminUser.login, get_session=lambda: db.session, message='Логин занят')
    ])


class StudGroupForm(ModelForm):
    class Meta:
        model = StudGroup
        exclude = ['active']

    year = IntegerField('Учебный год с 1 сентября',
                        [validators.DataRequired(), validators.NumberRange(min=2000, max=datetime.now().year + 1)])
    semester = IntegerField('Семестр', [validators.DataRequired(), validators.NumberRange(min=1, max=10)])
    num = IntegerField('Группа', [validators.DataRequired(), validators.NumberRange(min=1, max=255)])
    subnum = IntegerField('Подгруппа', [validators.NumberRange(min=0, max=3)])
    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class StudentForm(_PersonForm, ModelForm):
    class Meta:
        model = Student
        include_primary_keys = True

    id = IntegerField('Номер студенческого билета', [validators.DataRequired(), validators.NumberRange(min=1), Unique(Student.id, get_session=lambda: db.session, message='Номер студенческого билета занят')])
    semester = IntegerField('Семестр', [validators.NumberRange(min=1, max=10), validators.Optional()])
    stud_group = QuerySelectField('Группа',
                                  query_factory=lambda: db.session.query(StudGroup).filter(StudGroup.active).order_by(
                                      StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс группа %s" % (g.course, g.num_print),
                                  blank_text='Не указана', allow_blank=True)
    alumnus_year = IntegerField('Учебный год выпуск', [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])
    expelled_year = IntegerField('Учебный год отчисления', [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class StudentSearchForm(Form):
    id = IntegerField('Номер студенческого билета', [validators.NumberRange(min=1), validators.Optional()])
    surname = StringField('Фамилия', [validators.Length(min=2, max=Student.surname.property.columns[0].type.length), validators.Optional()])
    firstname = StringField('Имя', [validators.Length(min=2, max=Student.firstname.property.columns[0].type.length), validators.Optional()])
    middlename = StringField('Отчество', [validators.Length(min=2, max=Student.middlename.property.columns[0].type.length), validators.Optional()])
    semester = IntegerField('Семестр', [validators.NumberRange(min=1, max=10), validators.Optional()])
    stud_group = QuerySelectField('Группа',
                                  query_factory=lambda: db.session.query(StudGroup).filter(StudGroup.active).order_by(
                                      StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс группа %s" % (g.course, g.num_print),
                                  blank_text='Неизвестно', allow_blank=True)
    alumnus_year = IntegerField('Учебный год выпуск',
                                [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])
    expelled_year = IntegerField('Учебный год отчисления',
                                 [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])
    login = StringField('Login')
    button_search = SubmitField('Поиск')


class SubjectForm(ModelForm):
    class Meta:
        model = Subject
    name = StringField('Название предмета', [validators.DataRequired(), Unique(Subject.name, get_session=lambda: db.session, message='Предмет с таким названием существует')])
    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class TeacherForm(_PersonForm, ModelForm):
    class Meta:
        model = Teacher

    rank = StringField('Должность', [validators.DataRequired()])
    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')




class AttMarkForm(ModelForm):
    class Meta:
        model = AttMark
        include_primary_keys = True

    att_mark_1 = IntegerField('Оценка за 1-ю аттестацию', [validators.NumberRange(min=0, max=50), validators.Optional()])
    att_mark_2 = IntegerField('Оценка за 2-ю аттестацию', [validators.NumberRange(min=0, max=50), validators.Optional()])
    att_mark_3 = IntegerField('Оценка за 3-ю аттестацию', [validators.NumberRange(min=0, max=50), validators.Optional()])
    att_mark_exam = IntegerField('Оценка за экзамен', [validators.NumberRange(min=0, max=50), validators.Optional()])
    att_mark_append_ball = IntegerField('Доп. балл', [validators.NumberRange(min=0, max=10), validators.Optional()])
    att_mark_id = HiddenField()


class CurriculumUnitForm(ModelForm):
    class Meta:
        model = CurriculumUnit

    stud_group = QuerySelectField('Группа',
                                  query_factory=lambda: db.session.query(StudGroup).filter(StudGroup.active).order_by(
                                    StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс группа %s" % (g.course, g.num_print),
                                  allow_blank=False)

    teacher = QuerySelectField('Преподаватель',
                                  query_factory=lambda: db.session.query(Teacher).order_by(
                                    Teacher.surname, Teacher.firstname, Teacher.middlename).all(),
                                  get_pk=lambda t: t.id,
                                  get_label=lambda t: t.full_name_short,
                                  blank_text='Не указан', allow_blank=True, validators=[validators.DataRequired()])

    subject = QuerySelectField('Предмет',
                               query_factory=lambda: db.session.query(Subject).order_by(
                                   Subject.name).all(),
                               get_pk=lambda s: s.id,
                               get_label=lambda s: s.name,
                               blank_text='Не указан', allow_blank=True, validators=[validators.DataRequired()])

    hours_att_1 = IntegerField('Часов на 1-ю аттестацию',
                                [validators.NumberRange(min=1), validators.DataRequired()])
    hours_att_2 = IntegerField('Часов на 2-ю аттестацию',
                               [validators.NumberRange(min=1), validators.DataRequired()])
    hours_att_3 = IntegerField('Часов на 3-ю аттестацию',
                               [validators.NumberRange(min=1), validators.DataRequired()])

    mark_type = QuerySelectField('Тип отчётности', query_factory=lambda: MarkType,
                                 get_pk=lambda t: t,
                                 get_label=lambda t: MarkType[t][1],
                                 blank_text='Не указан', allow_blank=True, validators=[validators.DataRequired()])

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class CurriculumUnitAttMarksForm(CurriculumUnitForm):
    att_marks = ModelFieldList(FormField(AttMarkForm))
    button_clear = SubmitField('Очистить данные ведомости')


class AdminUserForm(_PersonForm, ModelForm):
    class Meta:
        model = AdminUser

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')