from flask import json
from sqlalchemy.orm.attributes import QueryableAttribute

from app_config import db
from utils import HalfYearEnum
from utils import LessonType

# Типы
StudentStates = ("study", "alumnus", "expelled", "academic_leave")
StudentStateDict = {
    "study": "учится",
    "alumnus": "успешно закончил обучение",
    "expelled": "отчислен",
    "academic_leave": "в академическом отпуске"
}

# Типы отчётности для единицы учебного плана
MarkTypes = ("test_simple", "exam", "test_diff")
MarkTypeDict = {
    "test_simple": "Зачёт",
    "exam": "Экзамен",
    "test_diff": "Зачёт с оценкой"
}

# Связующая таблица для единиц учебного плана и учебных занятий
TEACHING_LESSON_AND_CURRICULUM_UNIT = db.Table('teaching_lesson_and_curriculum_unit', db.metadata,
                                               db.Column('teaching_lesson_id', db.Integer,
                                                         db.ForeignKey('teaching_lessons.teaching_lesson_id',
                                                                       ondelete="CASCADE",
                                                                       onupdate="CASCADE")),
                                               db.Column('curriculum_unit_id', db.Integer,
                                                         db.ForeignKey('curriculum_unit.curriculum_unit_id',
                                                                       ondelete="CASCADE",
                                                                       onupdate="CASCADE")))


class BaseModel(db.Model):
    __abstract__ = True

    def to_dict(self, show=None, _hide=None, _path=None):
        """Return a dictionary representation of this model."""

        if _hide is None:
            _hide = []
        show = show or []

        hidden = self._hidden_fields if hasattr(self, "_hidden_fields") else []
        default = self._default_fields if hasattr(self, "_default_fields") else []
        default.extend(['id', 'modified_at', 'created_at'])

        if not _path:
            _path = self.__tablename__.lower()

            def prepend_path(item):
                item = item.lower()
                if item.split(".", 1)[0] == _path:
                    return item
                if len(item) == 0:
                    return item
                if item[0] != ".":
                    item = ".%s" % item
                item = "%s%s" % (_path, item)
                return item

            _hide[:] = [prepend_path(x) for x in _hide]
            show[:] = [prepend_path(x) for x in show]

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()
        properties = dir(self)

        ret_data = {}

        for key in columns:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                ret_data[key] = getattr(self, key)

        for key in relationships:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                _hide.append(check)
                is_list = self.__mapper__.relationships[key].uselist
                if is_list:
                    items = getattr(self, key)
                    if self.__mapper__.relationships[key].query_class is not None:
                        if hasattr(items, "all"):
                            items = items.all
                    ret_data[key] = []
                    for item in items:
                        if item is not None:
                            ret_data[key].append(
                                item.to_dict(
                                    show=list(show),
                                    _hide=list(_hide),
                                    _path=("%s.%s" % (_path, key.lower())),
                                )
                            )
                else:
                    if (
                            self.__mapper__.relationships[key].query_class is not None
                            or self.__mapper__.relationships[key].instrument_class
                            is not None
                    ):
                        item = getattr(self, key)
                        if item is not None:
                            ret_data[key] = item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        else:
                            ret_data[key] = None
                    else:
                        ret_data[key] = getattr(self, key)

        for key in list(set(properties) - set(columns) - set(relationships)):
            if key.startswith("_"):
                continue
            if not hasattr(self.__class__, key):
                continue
            attr = getattr(self.__class__, key)
            if not (isinstance(attr, property) or isinstance(attr, QueryableAttribute)):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                val = getattr(self, key)
                if hasattr(val, "to_dict"):
                    ret_data[key] = val.to_dict(
                        show=list(show),
                        _hide=list(_hide),
                        _path=("%s.%s" % (_path, key.lower()))
                    )
                else:
                    try:
                        ret_data[key] = json.loads(json.dumps(val))
                    except:
                        pass

        return ret_data


class Person:
    @property
    def full_name(self):
        if self.surname is None or self.firstname is None:
            return None
        return " ".join((self.surname, self.firstname, self.middlename) if self.middlename is not None else (
            self.surname, self.firstname))

    @property
    def full_name_short(self):
        if self.surname is None or self.firstname is None:
            return None
        return "%s %s. %s." % (self.surname, self.firstname[0], self.middlename[0]) if self.middlename is not None \
            else "%s %s." % (self.surname, self.firstname[0])

    @staticmethod
    def get_class_map():
        class_map = {
            "AdminUser": AdminUser,
            "Teacher": Teacher,
            "Student": Student,
            "GroupLeader": Student
        }
        return class_map

    # Flask-Login Support
    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return "%s@%s" % (self.role_name, self.login)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False


class _ObjectWithSemester:
    @property
    def course(self):
        if self.semester is None:
            return None
        return (self.semester // 2) + 1


class _ObjectWithYear:
    @property
    def year_print(self):
        if self.year is None:
            return None
        return "%d-%d" % (self.year, self.year + 1)


class StudGroup(BaseModel, _ObjectWithSemester, _ObjectWithYear):
    __tablename__ = 'stud_group'
    __table_args__ = (
        db.UniqueConstraint('stud_group_year', 'stud_group_semester', 'stud_group_num', 'stud_group_subnum'),
    )

    _default_fields = [
        'num_print',
        'num',
        'subnum'
    ]

    id = db.Column('stud_group_id', db.INTEGER, primary_key=True, autoincrement=True)
    year = db.Column('stud_group_year', db.SMALLINT, nullable=False)
    semester = db.Column('stud_group_semester', db.SMALLINT, nullable=False)
    num = db.Column('stud_group_num', db.SMALLINT, nullable=False)
    subnum = db.Column('stud_group_subnum', db.SMALLINT, nullable=False, default=0)
    specialty = db.Column('stud_group_specialty', db.String(200), nullable=False)
    specialization = db.Column('stud_group_specialization', db.String(200))

    active = db.Column('stud_group_active', db.BOOLEAN, nullable=False, default=True)

    students = db.relationship('Student', lazy=True, backref='stud_group',
                               order_by="Student.surname, Student.firstname, Student.middlename")
    curriculum_units = db.relationship('CurriculumUnit', lazy=True, backref='curriculum_unit',
                                       order_by="CurriculumUnit.id")

    def __repr__(self):
        return f"StudGroup(id={self.id}, " \
               f"year={self.year}, " \
               f"semester={self.semester}, " \
               f"num={self.num}, " \
               f"subnum={self.subnum}, " \
               f"specialty={self.specialty}, " \
               f"specialization={self.specialization}, " \
               f"active={self.active}, " \
               f"students={self.students}, " \
               f"curriculum_units={self.curriculum_units})"

    @property
    def num_print(self):
        if self.num is None or self.subnum is None:
            return None
        return "%d.%d" % (self.num, self.subnum) if self.subnum != 0 else str(self.num)


class Subject(BaseModel):
    __tablename__ = 'subject'

    _default_fields = [
        'name'
    ]

    id = db.Column('subject_id', db.INTEGER, primary_key=True, autoincrement=True)
    name = db.Column('subject_name', db.String(64), nullable=False, unique=True)

    def __repr__(self):
        return f"Subject(id={self.id}, " \
               f"name={self.name})"


class Teacher(db.Model, Person):
    __tablename__ = 'teacher'

    id = db.Column('teacher_id', db.INTEGER, primary_key=True, autoincrement=True)
    surname = db.Column('teacher_surname', db.String(45), nullable=False)
    firstname = db.Column('teacher_firstname', db.String(45), nullable=False)
    middlename = db.Column('teacher_middlename', db.String(45))
    rank = db.Column('teacher_rank', db.String(45), nullable=False)
    login = db.Column('teacher_login', db.String(45), nullable=False, unique=True)

    def __repr__(self):
        return f"Teacher(id={self.id}, " \
               f"surname={self.surname}, " \
               f"firstname={self.firstname}, " \
               f"middlename={self.middlename}, " \
               f"rank={self.rank}, " \
               f"login={self.login})"

    @property
    def role_name(self):
        return 'Teacher'


class _CurriculumUnit:
    @property
    def mark_type_name(self):
        return MarkTypeDict[self.mark_type]

    @property
    def fill_data(self):
        r = {}
        for m in self.att_marks:
            if m.student.stud_group_id == m.curriculum_unit.stud_group_id:
                for rm_k, rm_v in m.fill_data.items():
                    r[rm_k] = r.get(rm_k, True) and rm_v

        return r

    @property
    def hours(self):
        attrs = ('hours_att_1', 'hours_att_2', 'hours_att_3')
        if any(getattr(self, a) is None for a in attrs):
            return None
        return sum(getattr(self, a) for a in attrs)


class CurriculumUnit(db.Model, _CurriculumUnit):
    __tablename__ = 'curriculum_unit'
    __table_args__ = (
        db.UniqueConstraint('subject_id', 'stud_group_id'),
    )

    id = db.Column('curriculum_unit_id', db.INTEGER, primary_key=True, autoincrement=True)
    subject_id = db.Column(db.ForeignKey('subject.subject_id'), nullable=False, index=True)
    stud_group_id = db.Column(db.ForeignKey('stud_group.stud_group_id'), nullable=False, index=True)
    teacher_id = db.Column(db.ForeignKey('teacher.teacher_id'), nullable=False, index=True)
    mark_type = db.Column('mark_type', db.Enum(*MarkTypeDict.keys()), nullable=False)
    hours_att_1 = db.Column('hours_att_1', db.SMALLINT, nullable=False)
    hours_att_2 = db.Column('hours_att_2', db.SMALLINT, nullable=False)
    hours_att_3 = db.Column('hours_att_3', db.SMALLINT, nullable=False)

    subject = db.relationship('Subject')
    teacher = db.relationship('Teacher')
    att_marks = db.relationship('AttMark', lazy=True, backref='curriculum_unit')
    teaching_lessons = db.relationship('TeachingLessons', secondary='teaching_lesson_and_curriculum_unit')

    def __repr__(self):
        return f"CurriculumUnit(id={self.id}, " \
               f"subject_id={self.subject_id}, " \
               f"stud_group_id={self.stud_group_id}, " \
               f"teacher_id={self.teacher_id}, " \
               f"mark_type={self.mark_type}, " \
               f"hours_att_1={self.hours_att_1}, " \
               f"hours_att_2={self.hours_att_2}, " \
               f"hours_att_3={self.hours_att_3}, " \
               f"subject={self.subject}, " \
               f"teacher={self.teacher}, " \
               f"att_marks={self.att_marks}, " \
               f"teaching_lessons={self.teaching_lessons})"


class CurriculumUnitUnionException(Exception):
    pass


# Объединённый CurriculumUnit
class CurriculumUnitUnion(_CurriculumUnit, _ObjectWithSemester, _ObjectWithYear):
    def __init__(self, curriculum_units):
        if len(curriculum_units) == 0:
            raise CurriculumUnitUnionException()

        cu_first = curriculum_units[0]

        self.subject_id = cu_first.subject_id or cu_first.subject.id
        self.subject = cu_first.subject
        self.teacher_id = cu_first.teacher_id or cu_first.teacher.id
        self.teacher = cu_first.teacher
        self.mark_type = cu_first.mark_type
        self.hours_att_1 = cu_first.hours_att_1
        self.hours_att_2 = cu_first.hours_att_2
        self.hours_att_3 = cu_first.hours_att_3

        self.year = cu_first.stud_group.year
        self.semester = cu_first.stud_group.semester

        for cu in curriculum_units[1:]:
            if (
                    cu.subject_id or cu.subject.id,
                    cu.teacher_id or cu.teacher.id,
                    cu.mark_type,
                    cu.hours_att_1,
                    cu.hours_att_2,
                    cu.hours_att_3,
                    cu.stud_group.year,
                    cu.stud_group.semester
            ) != (
                    self.subject_id,
                    self.teacher_id,
                    self.mark_type,
                    self.hours_att_1,
                    self.hours_att_2,
                    self.hours_att_3,
                    self.year,
                    self.semester
            ):
                raise CurriculumUnitUnionException()

        self.ids = tuple(cu.id for cu in curriculum_units)
        self.stud_group_ids = tuple(cu.stud_group_id or cu.stud_group.id for cu in curriculum_units)
        self.stud_groups = tuple(cu.stud_group for cu in curriculum_units)
        self.att_marks = []
        for cu in curriculum_units:
            self.att_marks.extend(cu.att_marks)
        self.att_marks.sort(key=lambda m: (m.student.surname, m.student.firstname, m.student.middlename))
        self.att_marks_readonly_ids = tuple(
            m.att_mark_id for m in self.att_marks if m.student.stud_group_id != m.curriculum_unit.stud_group_id)


class Student(BaseModel, Person, _ObjectWithSemester):
    __tablename__ = 'student'

    _default_fields = [
        'full_name',
        'attendance',
        'card_number'
    ]

    id = db.Column('student_id', db.BIGINT, primary_key=True)
    surname = db.Column('student_surname', db.String(45), nullable=False)
    firstname = db.Column('student_firstname', db.String(45), nullable=False)
    middlename = db.Column('student_middlename', db.String(45))
    stud_group_id = db.Column(db.ForeignKey('stud_group.stud_group_id', ondelete='SET NULL', onupdate='SET NULL'),
                              index=True)
    semester = db.Column('student_semestr', db.SMALLINT)
    alumnus_year = db.Column('student_alumnus_year', db.SMALLINT)
    expelled_year = db.Column('student_expelled_year', db.SMALLINT)
    status = db.Column('student_status', db.Enum(*StudentStateDict.keys()), nullable=False)
    login = db.Column('student_login', db.String(45), unique=True)
    card_number = db.Column('card_number', db.BIGINT, unique=True)
    group_leader = db.Column('stud_group_leader', db.BOOLEAN, nullable=False, default=False)
    attendance = db.relationship('Attendance')

    def __repr__(self):
        return f"Student(id={self.id}, " \
               f"surname={self.surname}, " \
               f"firstname={self.firstname}, " \
               f"middlename={self.middlename}, " \
               f"stud_group_id={self.stud_group_id}, " \
               f"semester={self.semester}, " \
               f"alumnus_year={self.alumnus_year}, " \
               f"expelled_year={self.expelled_year}, " \
               f"status={self.status}, " \
               f"login={self.login}, " \
               f"card_number={self.card_number}, " \
               f"group_leader={self.group_leader}, " \
               f"attendance={self.attendance})"

    @property
    def status_name(self):
        if self.status and self.status in StudentStateDict:
            return StudentStateDict[self.status]

    @property
    def role_name(self):
        if not self.group_leader:
            return 'Student'
        else:
            return 'GroupLeader'


class AdminUser(db.Model, Person):
    id = db.Column('admin_user_id', db.BIGINT, primary_key=True)
    surname = db.Column('admin_user_surname', db.String(45), nullable=False)
    firstname = db.Column('admin_user_firstname', db.String(45), nullable=False)
    middlename = db.Column('admin_user_middlename', db.String(45))
    login = db.Column('admin_user_login', db.String(45), nullable=False, unique=True)

    def __repr__(self):
        return f"AdminUser(id={self.id}, " \
               f"surname={self.surname}, " \
               f"firstname={self.firstname}, " \
               f"middlename={self.middlename}, " \
               f"login={self.login})"

    @property
    def role_name(self):
        return 'AdminUser'


MarkResult = {
    "test_simple": (
        {"min": 0, "max": 24, "value": False, "value_text": "не зачтено"},
        {"min": 25, "max": 50, "value": True, "value_text": "зачтено"}
    ),
    "exam": (
        {"min": 0, "max": 49, "value": 2, "value_text": "неудовлетворительно"},
        {"min": 50, "max": 69, "value": 3, "value_text": "удовлетворительно"},
        {"min": 70, "max": 89, "value": 4, "value_text": "хорошо"},
        {"min": 90, "max": 100, "value": 5, "value_text": "отлично"}
    ),
    "test_diff": (
        {"min": 0, "max": 24, "value": 2, "value_text": "неудовлетворительно"},
        {"min": 25, "max": 34, "value": 3, "value_text": "удовлетворительно"},
        {"min": 35, "max": 44, "value": 4, "value_text": "хорошо"},
        {"min": 45, "max": 50, "value": 5, "value_text": "отлично"}
    )
}


class AttMark(db.Model):
    __tablename__ = 'att_mark'
    __table_args__ = (
        db.UniqueConstraint('curriculum_unit_id', 'student_id'),
    )

    att_mark_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    curriculum_unit_id = db.Column(db.ForeignKey('curriculum_unit.curriculum_unit_id'), nullable=False)
    student_id = db.Column(db.ForeignKey('student.student_id'), nullable=False, index=True)
    att_mark_1 = db.Column(db.SMALLINT)
    att_mark_2 = db.Column(db.SMALLINT)
    att_mark_3 = db.Column(db.SMALLINT)
    att_mark_exam = db.Column(db.SMALLINT)
    att_mark_append_ball = db.Column(db.SMALLINT)
    student = db.relationship('Student')

    def __repr__(self):
        return f"AttMark(att_mark_id={self.att_mark_id}, " \
               f"curriculum_unit_id={self.curriculum_unit_id}, " \
               f"student_id={self.student_id}, " \
               f"att_mark_1={self.att_mark_1}, " \
               f"att_mark_2={self.att_mark_2}, " \
               f"att_mark_3={self.att_mark_3}, " \
               f"att_mark_exam={self.att_mark_exam}, " \
               f"att_mark_append_ball={self.att_mark_append_ball}, " \
               f"student={self.student})"

    @property
    def result_print(self):
        att_marks = (self.att_mark_1, self.att_mark_2, self.att_mark_3)
        if any(m is None for m in att_marks):
            return None

        mark_results = MarkResult[self.curriculum_unit.mark_type]
        min_ball = MarkResult["test_simple"][1]["min"]
        max_ball = mark_results[-1]["max"]

        if self.curriculum_unit.mark_type == "exam" and self.att_mark_exam is None:
            return None

        if any(m < min_ball for m in att_marks):
            return min(att_marks), mark_results[0]

        hours = (self.curriculum_unit.hours_att_1, self.curriculum_unit.hours_att_2, self.curriculum_unit.hours_att_3)
        ball_raw = sum([att_marks[i] * hours[i] for i in range(len(att_marks))]) / sum(hours)
        # Округление
        ball = int(ball_raw)
        if ball_raw - ball >= 0.5:
            ball += 1

        if self.curriculum_unit.mark_type == "exam":
            ball += self.att_mark_exam

        if self.curriculum_unit.mark_type in ("exam", "test_diff") and self.att_mark_append_ball is not None:
            ball += self.att_mark_append_ball

        if ball > max_ball:
            ball = max_ball

        for mr in mark_results:
            if mr["min"] <= ball <= mr["max"]:
                return ball, mr

    @property
    def fill_data(self):
        r = {"att_1": self.att_mark_1 is not None, "att_2": False, "att_3": False, "all": False}

        r["att_2"] = r["att_1"] and self.att_mark_2 is not None
        r["all"] = r["att_3"] = r["att_2"] and self.att_mark_3 is not None

        if self.curriculum_unit.mark_type == "exam":
            r["all"] = r["all"] and self.att_mark_exam is not None

        return r


# for stud_attendance


class TeachingLessons(db.Model):
    """Класс для сущности 'Учебное занятие'"""
    __tablename__ = 'teaching_lessons'

    teaching_lesson_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)

    pair_number_numerator = db.Column(db.INTEGER, nullable=False)
    day_number_numerator = db.Column(db.INTEGER, nullable=False)
    pair_number_denominator = db.Column(db.INTEGER, nullable=False)
    day_number_denominator = db.Column(db.INTEGER, nullable=False)
    can_expose_group_leader = db.Column(db.Boolean, nullable=False)

    lesson_type = db.Column(db.Enum(LessonType), nullable=False)

    curriculum_units = db.relationship('CurriculumUnit', secondary='teaching_lesson_and_curriculum_unit',
                                       overlaps="teaching_lessons")
    teaching_pairs = db.relationship('TeachingPairs')

    def __repr__(self):
        return f"TeachingLessons(teaching_lesson_id={self.teaching_lesson_id}," \
               f" pair_number_numerator={self.pair_number_numerator}," \
               f" day_number_numerator={self.day_number_numerator}," \
               f" pair_number_denominator={self.pair_number_denominator}," \
               f" day_number_denominator={self.day_number_denominator}," \
               f" can_expose_group_leader={self.can_expose_group_leader}," \
               f" lesson_type={self.lesson_type})"

    def __init__(self, pair_number_numerator=None, day_number_numerator=None, pair_number_denominator=None,
                 day_number_denominator=None, can_expose_group_leader=None, lesson_type=None):
        self.pair_number_numerator = pair_number_numerator
        self.day_number_numerator = day_number_numerator
        self.pair_number_denominator = pair_number_denominator
        self.day_number_denominator = day_number_denominator
        self.can_expose_group_leader = can_expose_group_leader
        self.lesson_type = lesson_type

    def get_attrs_and_values_for_update(self):
        return dict((self.pair_number_numerator, self.day_number_numerator,
                     self.pair_number_denominator, self.day_number_denominator,
                     self.can_expose_group_leader, self.lesson_type))


class Attendance(BaseModel):
    """Класс для сущности 'Посещаемость'"""
    __tablename__ = 'attendance'

    _default_fields = [
        'lesson_attendance'
        'teaching_pair_id'
    ]

    attendance_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lesson_attendance = db.Column(db.Boolean, nullable=False, default=False)
    lesson_date = db.Column(db.Date, nullable=False, primary_key=True)
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.student_id'), nullable=False, primary_key=True)
    teaching_pair_id = db.Column(db.INTEGER, db.ForeignKey('teaching_pairs.pair_id'), primary_key=True,
                                 nullable=False)

    def __repr__(self):
        return f"Attendance(attendance_id={self.attendance_id}," \
               f" lesson_attendance={self.lesson_attendance}," \
               f" lesson_date={self.lesson_date}," \
               f" student_id={self.student_id})," \
               f" teaching_pair_id={self.teaching_pair_id}"

    def __init__(self, lesson_attendance, lesson_date, student_id, teaching_pair_id):
        self.lesson_attendance = lesson_attendance
        self.lesson_date = lesson_date
        self.student_id = student_id
        self.teaching_pair_id = teaching_pair_id


class LessonsBeginning(db.Model):
    """Класс для сущности 'Начало занятий'"""
    __tablename__ = 'lessons_beginning'

    year = db.Column(db.INTEGER, nullable=False, primary_key=True)
    half_year = db.Column(db.Enum(HalfYearEnum), nullable=False, primary_key=True)
    beginning_date = db.Column(db.DATE, nullable=False)
    end_date = db.Column(db.DATE, nullable=False)

    def __repr__(self):
        return f"LessonsBeginning(year={self.year}," \
               f" half_year={self.half_year}," \
               f" beginning_date={self.beginning_date}," \
               f" end_date={self.end_date})"

    def __init__(self, year=None, half_year=None, beginning_date=None, end_date=None):
        self.year = year
        self.half_year = half_year
        self.beginning_date = beginning_date
        self.end_date = end_date

    def get_attrs_and_values_for_update(self):
        return dict((self.year, self.half_year, self.beginning_date, self.end_date))


class TeachingPairs(db.Model):
    """Класс для сущности 'Учебные пары'"""
    __tablename__ = 'teaching_pairs'

    pair_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    pair_number = db.Column(db.INTEGER, nullable=False)
    time_of_beginning = db.Column(db.TIME, nullable=False)
    time_of_ending = db.Column(db.TIME, nullable=False)

    teaching_lesson_id = db.Column(db.Integer, db.ForeignKey('teaching_lessons.teaching_lesson_id'))
    attendance = db.relationship('Attendance')

    def __repr__(self):
        return f"TeachingPairs(pair_id={self.pair_id}," \
               f" pair_number={self.pair_number}," \
               f" time_of_beginning={self.time_of_beginning}," \
               f" time_of_ending={self.time_of_ending})"

    def __init__(self, pair_number=None, time_of_beginning=None, time_of_ending=None):
        self.pair_number = pair_number
        self.time_of_beginning = time_of_beginning
        self.time_of_ending = time_of_ending

    def get_attrs_and_values_for_update(self):
        return dict((self.pair_number, self.time_of_beginning, self.time_of_ending))
