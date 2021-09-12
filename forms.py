from datetime import datetime

from wtforms import validators, Form, SubmitField, IntegerField, StringField, SelectField, HiddenField, PasswordField, \
    FormField, BooleanField, DateField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms_alchemy import ModelForm, ModelFieldList, QuerySelectMultipleField
from wtforms_alchemy.fields import QuerySelectField
from wtforms_alchemy.validators import Unique
from wtforms_components import TimeField

from app_config import db
from model import StudGroup, Subject, Teacher, Student, StudentStates, StudentStateDict, CurriculumUnit, AttMark, \
    MarkTypes, MarkTypeDict, AdminUser, LessonsBeginning, TeachingPairs, TeachingLessons
from utils import HalfYearEnum
from utils import LessonType
from utils import get_field


class _PersonForm:
    surname = StringField('Фамилия', [validators.Length(min=2, max=45), validators.DataRequired()])
    firstname = StringField('Имя', [validators.Length(min=2, max=45), validators.DataRequired()])
    middlename = StringField(
        'Отчество',
        validators=[validators.Length(min=2, max=45), validators.Optional()],
        filters=[lambda val: val or None]
    )
    login = StringField('Login', filters=[lambda val: val or None])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        clazz = self.Meta.model
        self.login.validators = [
            validators.Optional(),
            validators.Length(min=3, max=45),
            validators.Regexp("^[a-z0-9_]+$",
                              message="Учётное имя может содержать только латинкие символы, цифры и знак подчёркивания"
                              ),
            Unique(clazz.login, get_session=lambda: db.session, message='Логин занят')
        ]


class StudGroupForm(ModelForm):
    class Meta:
        model = StudGroup
        exclude = ['active']

    year = IntegerField('Учебный год с 1 сентября',
                        [validators.DataRequired(), validators.NumberRange(min=2000, max=datetime.now().year + 1)])
    semester = IntegerField('Семестр', [validators.DataRequired(), validators.NumberRange(min=1, max=10)])
    num = IntegerField('Группа', [validators.DataRequired(), validators.NumberRange(min=1, max=255)])
    subnum = IntegerField('Подгруппа', [validators.NumberRange(min=0, max=3)])
    specialty = StringField('Направление (специальность)',
                            [validators.Length(min=4, max=StudGroup.specialty.property.columns[0].type.length),
                             validators.DataRequired()])
    specialization = StringField(
        'Профиль',
        validators=[validators.Length(min=4, max=StudGroup.specialization.property.columns[0].type.length),
                    validators.Optional()],
        filters=[lambda val: val or None]
    )

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class StudentForm(_PersonForm, ModelForm):
    class Meta:
        model = Student
        include_primary_keys = True

    id = IntegerField('Номер студенческого билета', [validators.DataRequired(), validators.NumberRange(min=1),
                                                     Unique(Student.id, get_session=lambda: db.session,
                                                            message='Номер студенческого билета занят')])
    status = QuerySelectField('Состояние',
                              query_factory=lambda: StudentStates,
                              get_pk=lambda s: s,
                              get_label=lambda s: StudentStateDict[s],
                              allow_blank=False, validators=[validators.DataRequired()])
    semester = IntegerField('Семестр', [validators.NumberRange(min=1, max=10), validators.Optional()])
    stud_group = QuerySelectField('Группа',
                                  query_factory=lambda: db.session.query(StudGroup).filter(StudGroup.active).order_by(
                                      StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс группа %s" % (g.course, g.num_print),
                                  blank_text='Не указана', allow_blank=True)
    alumnus_year = IntegerField('Учебный год выпуск',
                                [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])
    expelled_year = IntegerField('Учебный год отчисления',
                                 [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])

    card_number = IntegerField('Номер карты (пропуска)', [validators.Optional(), validators.NumberRange(min=1),
                                                          Unique(Student.card_number, get_session=lambda: db.session,
                                                                 message='Номер занят')])
    group_leader = BooleanField('Староста')

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class StudentSearchForm(Form):
    id = IntegerField('Номер студенческого билета', [validators.NumberRange(min=1), validators.Optional()])
    surname = StringField('Фамилия', [validators.Length(min=2, max=Student.surname.property.columns[0].type.length),
                                      validators.Optional()])
    firstname = StringField('Имя', [validators.Length(min=2, max=Student.firstname.property.columns[0].type.length),
                                    validators.Optional()])
    middlename = StringField('Отчество',
                             [validators.Length(min=2, max=Student.middlename.property.columns[0].type.length),
                              validators.Optional()])
    status = QuerySelectField('Состояние',
                              query_factory=lambda: StudentStates,
                              get_pk=lambda s: s,
                              get_label=lambda s: StudentStateDict[s],
                              blank_text='Не указано', allow_blank=True, validators=[validators.Optional()])
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
    card_number = IntegerField('Номер карты (пропуска)', [validators.Optional(), validators.NumberRange(min=1)])
    group_leader = SelectField('Староста', choices=[('any', 'Не важно'), ('yes', 'Да'), ('no', 'Нет')])
    button_search = SubmitField('Поиск')


class StudentsUnallocatedForm(Form):
    semester = HiddenField()
    students_selected = QuerySelectMultipleField(
        'Студенты',
        get_pk=lambda s: s.id,
        get_label=lambda s: "%d %s" % (s.id, s.full_name),
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput()
    )
    stud_group = QuerySelectField('Группа в которую нужно перевести',
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: g.num_print,
                                  blank_text='Не указана', allow_blank=True,
                                  validators=[validators.DataRequired('Укажите группу')])

    button_transfer = SubmitField('Перевести в выбранную группу')


class SubjectForm(ModelForm):
    class Meta:
        model = Subject

    name = StringField('Название предмета', [validators.DataRequired(),
                                             validators.Length(min=3, max=Subject.name.property.columns[0].type.length),
                                             Unique(Subject.name, get_session=lambda: db.session,
                                                    message='Предмет с таким названием существует')])
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

    att_mark_1 = IntegerField('Оценка за 1-ю аттестацию',
                              [validators.NumberRange(min=0, max=50), validators.Optional()])
    att_mark_2 = IntegerField('Оценка за 2-ю аттестацию',
                              [validators.NumberRange(min=0, max=50), validators.Optional()])
    att_mark_3 = IntegerField('Оценка за 3-ю аттестацию',
                              [validators.NumberRange(min=0, max=50), validators.Optional()])
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

    mark_type = QuerySelectField('Тип отчётности', query_factory=lambda: MarkTypes,
                                 get_pk=lambda t: t,
                                 get_label=lambda t: MarkTypeDict[t],
                                 blank_text='Не указан', allow_blank=True, validators=[validators.DataRequired()])

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class CurriculumUnitUnionForm(ModelForm):
    att_marks = ModelFieldList(FormField(AttMarkForm))
    button_save = SubmitField('Сохранить')
    button_clear = SubmitField('Очистить данные ведомости')


class CurriculumUnitAddAppendStudGroupForm(Form):
    relative_curriculum_units = QuerySelectMultipleField(
        'Группы',
        get_pk=lambda cu: cu.id,
        get_label=lambda cu: cu.stud_group.num_print,
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput()
    )


class CurriculumUnitCopyForm(Form):
    stud_groups_selected = QuerySelectMultipleField(
        'Группы',
        get_pk=lambda g: g.id,
        get_label=lambda g: "%s %s%s" % (
            g.num_print, g.specialty, " (%s)" % g.specialization if g.specialization else ""),
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput()
    )
    button_copy = SubmitField('Копировать')


class AdminUserForm(_PersonForm, ModelForm):
    class Meta:
        model = AdminUser

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class LoginForm(Form):
    login = StringField('Login')
    password = PasswordField('Пароль')
    user_type = SelectField('Тип пользователя',
                            choices=[('', 'Авто'), ('Student', 'Студент'), ('Teacher', 'Преподаватель'),
                                     ('AdminUser', 'Администратор'), ('GroupLeader', 'Староста')])
    button_login = SubmitField('Вход')


# code for attendance

class MainForm(ModelForm):
    objects_count = IntegerField('Количество обьектов',
                                 (validators.DataRequired(),
                                  validators.NumberRange(min=1,
                                                         message='Количество обьектов должно быть больше нуля!')),
                                 default=1)
    button_save = SubmitField('Сохранить')


class LessonBeginningForm(MainForm):
    class Meta:
        model = LessonsBeginning

    __order = ('year', 'half_year', 'beginning_date', 'end_date', 'objects_count', 'button_save')

    year = IntegerField('Год обучения',
                        (validators.DataRequired(),
                         validators.NumberRange(min=datetime.now().year - 20, max=datetime.now().year + 1,
                                                message=f'Год обучения должен быть в диапазоне от '
                                                        f'{datetime.now().year - 20} до {datetime.now().year + 1}'),
                         Unique((LessonsBeginning.year, LessonsBeginning.half_year),
                                get_session=lambda: db.session,
                                message='Начало занятий с таким учебным годом уже существует')))
    half_year = SelectField('Полугодие',
                            (Unique((LessonsBeginning.year, LessonsBeginning.half_year),
                                    get_session=lambda: db.session,
                                    message='Начало занятий с таким полугодием уже существует'),),
                            choices=((HalfYearEnum.first_half_year.name, 'Первое'),
                                     (HalfYearEnum.second_half_year.name, 'Второе')))
    beginning_date = DateField('Начало занятий', (validators.DataRequired(),))
    end_date = DateField('Конец занятий', (validators.DataRequired(),))

    def __iter__(self):
        fields = tuple(super(MainForm, self).__iter__())
        return (get_field(field_id, fields) for field_id in self.__order)


class TeachingPairsForm(MainForm):
    class Meta:
        model = TeachingPairs

    __order = ('pair_number', 'time_of_beginning', 'time_of_ending', 'objects_count', 'button_save')

    pair_number = IntegerField('Номер пары',
                               (validators.DataRequired(),
                                validators.NumberRange(min=1, max=7,
                                                       message='Номер пары должен быть в диапазоне от 1 до 7')))
    time_of_beginning = TimeField('Время начала пары', (validators.DataRequired(),))
    time_of_ending = TimeField('Время конца пары', (validators.DataRequired(),))

    def validate(self):
        rv = LessonBeginningForm.validate(self)
        if not rv:
            return False

        if self.time_of_beginning.data < self.time_of_ending.data:
            return True
        self.time_of_beginning.errors.append('Время начала пары не должно быть больше или равно времени конца пары!')
        self.time_of_ending.errors.append('Время конца пары не должно быть меньше или равно времени начала пары!')
        return False

    def __iter__(self):
        fields = tuple(super(MainForm, self).__iter__())
        return (get_field(field_id, fields) for field_id in self.__order)


class TeachingLessonForm(MainForm):
    class Meta:
        model = TeachingLessons

    __order = ('pair_number_denominator', 'day_number_denominator', 'pair_number_numerator',
               'day_number_numerator', 'can_expose_group_leader', 'lesson_type', 'objects_count', 'button_save')

    pair_number_denominator = IntegerField('Номер пары по знаменателю',
                                           (validators.DataRequired(),
                                            validators.NumberRange(min=1, max=7,
                                                                   message='Номер пары по знаменателю должен быть в диапазоне от 1 до 7')))
    day_number_denominator = IntegerField('Номер дня по знаменателю',
                                          (validators.DataRequired(),
                                           validators.NumberRange(min=1, max=7,
                                                                  message='Номер дня по знаменателю должен быть в диапазоне от 1 до 7')))
    pair_number_numerator = IntegerField('Номер пары по числителю',
                                         (validators.DataRequired(),
                                          validators.NumberRange(min=1, max=7,
                                                                 message='Номер пары по числителю должен быть в диапазоне от 1 до 7')))
    day_number_numerator = IntegerField('Номер дня по числителю',
                                        (validators.DataRequired(),
                                         validators.NumberRange(min=1, max=7,
                                                                message='Номер дня по числителю должен быть в диапазоне от 1 до 7')))
    can_expose_group_leader = BooleanField('Выставляет посещаемость староста')
    lesson_type = SelectField('Тип занятия',
                              choices=(('lection', LessonType.lection.value),
                                       ('practice', LessonType.practice.value),
                                       ('seminar', LessonType.seminar.value)))

    def __iter__(self):
        fields = tuple(super(MainForm, self).__iter__())
        return (get_field(field_id, fields) for field_id in self.__order)
