from enum import Enum

from sqlalchemy import Table

from app_config import db

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
TEACHING_LESSON_AND_CURRICULUM_UNIT = Table('teaching_lesson_and_curriculum_unit', db.metadata,
                                            db.Column('teaching_lesson_id', db.Integer,
                                                      db.ForeignKey('teaching_lesson.teaching_lesson_id',
                                                                    ondelete="CASCADE",
                                                                    onupdate="CASCADE")),
                                            db.Column('curriculum_unit_id', db.Integer,
                                                      db.ForeignKey('curriculum_unit.curriculum_unit_id',
                                                                    ondelete="CASCADE",
                                                                    onupdate="CASCADE")))


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
            "Student": Student
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


class StudGroup(db.Model, _ObjectWithSemester, _ObjectWithYear):
    __tablename__ = 'stud_group'
    __table_args__ = (
        db.UniqueConstraint('stud_group_year', 'stud_group_semester', 'stud_group_num', 'stud_group_subnum'),
    )

    id = db.Column('stud_group_id', db.INTEGER, primary_key=True, autoincrement=True)
    year = db.Column('stud_group_year', db.SMALLINT, nullable=False)
    semester = db.Column('stud_group_semester', db.SMALLINT, nullable=False)
    num = db.Column('stud_group_num', db.SMALLINT, nullable=False)
    subnum = db.Column('stud_group_subnum', db.SMALLINT, nullable=False, default=0)
    specialty = db.Column('stud_group_specialty', db.String(200), nullable=False)
    specialization = db.Column('stud_group_specialization', db.String(200))

    active = db.Column('stud_group_active', db.BOOLEAN, nullable=False, default=True)

    students = db.relationship('Student', lazy=True, backref='stud_group', \
                               order_by="Student.surname, Student.firstname, Student.middlename")
    curriculum_units = db.relationship('CurriculumUnit', lazy=True, backref='stud_group', order_by="CurriculumUnit.id")

    @property
    def num_print(self):
        if self.num is None or self.subnum is None:
            return None
        return "%d.%d" % (self.num, self.subnum) if self.subnum != 0 else str(self.num)

    def as_dict(self):
        class_variables = ['id', 'year', 'semester', 'num',
                           'subnum', 'specialty', 'specialization',
                           'active']
        return {var_name: getattr(self, var_name) for var_name in class_variables}


class Subject(db.Model):
    __tablename__ = 'subject'

    id = db.Column('subject_id', db.INTEGER, primary_key=True, autoincrement=True)
    name = db.Column('subject_name', db.String(64), nullable=False, unique=True)


class Teacher(db.Model, Person):
    __tablename__ = 'teacher'

    id = db.Column('teacher_id', db.INTEGER, primary_key=True, autoincrement=True)
    surname = db.Column('teacher_surname', db.String(45), nullable=False)
    firstname = db.Column('teacher_firstname', db.String(45), nullable=False)
    middlename = db.Column('teacher_middlename', db.String(45))
    rank = db.Column('teacher_rank', db.String(45), nullable=False)
    login = db.Column('teacher_login', db.String(45), nullable=False, unique=True)

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


class Student(db.Model, Person, _ObjectWithSemester):
    __tablename__ = 'student'

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

    @property
    def status_name(self):
        if self.status and self.status in StudentStateDict:
            return StudentStateDict[self.status]

    @property
    def role_name(self):
        return 'Student'

    def as_dict(self):
        class_variables = ['id', 'surname', 'firstname', 'middlename', 'semester', 'alumnus_year', 'expelled_year',
                           'status', 'login', 'card_number', 'group_leader']
        return {var_name: getattr(self, var_name) for var_name in class_variables}


class AdminUser(db.Model, Person):
    id = db.Column('admin_user_id', db.BIGINT, primary_key=True)
    surname = db.Column('admin_user_surname', db.String(45), nullable=False)
    firstname = db.Column('admin_user_firstname', db.String(45), nullable=False)
    middlename = db.Column('admin_user_middlename', db.String(45))
    login = db.Column('admin_user_login', db.String(45), nullable=False, unique=True)

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

        r["att_2"] = r["att_1"] and self.att_mark_2 is not None;
        r["all"] = r["att_3"] = r["att_2"] and self.att_mark_3 is not None;

        if self.curriculum_unit.mark_type == "exam":
            r["all"] = r["all"] and self.att_mark_exam is not None

        return r


# for stud_attendance


class LessonType(Enum):
    """Перечисление для типа занятий"""
    lection = 'Лекция'
    practice = 'Практика'
    seminar = 'Семинар'


class TeachingLesson(db.Model):
    """Класс для сущности 'Учебное занятие'"""
    __tablename__ = 'teaching_lesson'

    teaching_lesson_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)

    pair_number_numerator = db.Column(db.INTEGER, nullable=False)
    day_number_numerator = db.Column(db.INTEGER, nullable=False)
    pair_number_denominator = db.Column(db.INTEGER, nullable=False)
    day_number_denominator = db.Column(db.INTEGER, nullable=False)
    can_expose_group_leader = db.Column(db.Boolean, nullable=False)

    lesson_type = db.Column(db.Enum(LessonType), nullable=False)

    curriculum_units = db.relationship(
        'CurriculumUnit', secondary='teaching_lesson_and_curriculum_unit'
    )

    def __repr__(self):
        return f"TeachingLesson(teaching_lesson_id={self.teaching_lesson_id}," \
               f" pair_number_numerator={self.pair_number_numerator}," \
               f" day_number_numerator={self.day_number_numerator}," \
               f" pair_number_denominator={self.pair_number_denominator}," \
               f" day_number_denominator={self.day_number_denominator}," \
               f" can_expose_captain={self.can_expose_group_leader}," \
               f" lesson_type={self.lesson_type})"


class Attendance(db.Model):
    """Класс для сущности 'Посещаемость'"""
    __tablename__ = 'attendance'

    attendance_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lesson_attendance = db.Column(db.Boolean, nullable=False, default=False)
    lesson_date = db.Column(db.Date, nullable=False, primary_key=True)
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.student_id'), nullable=False, primary_key=True)

    def __repr__(self):
        return f"Attendance(attendance_teaching_lesson_id={self.attendance_id}," \
               f" lesson_attendance={self.lesson_attendance}," \
               f" lesson_date={self.lesson_date}," \
               f" student_id={self.student_id})"


class HalfYearEnum(Enum):
    """Перечисление для типа занятий"""
    first_half_year = 1
    second_half_year = 2


class LessonsBeginning(db.Model):
    """Класс для сущности 'Начало занятий'"""
    __tablename__ = 'lessons_beginning'

    year = db.Column(db.INTEGER, nullable=False, primary_key=True)
    half_year = db.Column(db.Enum(HalfYearEnum), nullable=False, primary_key=True)
    beginning_date = db.Column(db.DATE, nullable=False)

    def __repr__(self):
        return f"LessonsBeginning(year={self.year}," \
               f" half_year={self.half_year}," \
               f" beginning_date={self.beginning_date})"


class TeachingPairs(db.Model):
    """Класс для сущности 'Учебные пары'"""
    __tablename__ = 'teaching_pairs'

    pair_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    pair_number = db.Column(db.INTEGER, nullable=False)
    time_of_beginning = db.Column(db.TIME, nullable=False)
    time_of_ending = db.Column(db.TIME, nullable=False)

    def __repr__(self):
        return f"TeachingPairs(pair_id={self.pair_id}," \
               f" pair_number={self.pair_number}," \
               f" time_of_beginning={self.time_of_beginning}," \
               f" time_of_ending={self.time_of_ending})"
