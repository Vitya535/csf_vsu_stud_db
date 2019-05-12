from app_config import db


class _ObjectWithYear:
    @property
    def course(self):
        if self.semester is None:
            return None
        return (self.semester // 2) + 1

    @property
    def year_print(self):
        if self.year is None:
            return None
        return "%d-%d" % (self.year, self.year+1)


class _Person:
    @property
    def full_name(self):
        if self.surname is None or self.firstname is None:
            return None
        return " ".join((self.surname, self.firstname, self.middlename) if self.middlename is not None else (self.surname, self.firstname))

    @property
    def full_name_short(self):
        return "%s %s. %s." % (self.surname, self.firstname[0], self.middlename[0]) if self.middlename is not None\
            else "%s %s." % (self.surname, self.firstname[0])

    # Flask-Login Support
    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.login

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False


class StudGroup(db.Model, _ObjectWithYear):
    __tablename__ = 'stud_group'
    __table_args__ = (
        db.UniqueConstraint('stud_group_year', 'stud_group_semester', 'stud_group_num', 'stud_group_subnum'),
    )

    id = db.Column('stud_group_id', db.SMALLINT, primary_key=True, autoincrement=True)
    year = db.Column('stud_group_year', db.SMALLINT, nullable=False)
    semester = db.Column('stud_group_semester', db.SMALLINT, nullable=False)
    num = db.Column('stud_group_num', db.SMALLINT, nullable=False)
    subnum = db.Column('stud_group_subnum', db.SMALLINT, nullable=False, default=0)
    active = db.Column('stud_group_active', db.BOOLEAN, nullable=False, default=True)

    students = db.relationship('Student', lazy=True, backref='stud_group',\
                            order_by="Student.surname, Student.firstname, Student.middlename")
    curriculum_units = db.relationship('CurriculumUnit', lazy=True, backref='stud_group', order_by="CurriculumUnit.id")

    @property
    def num_print(self):
        if self.num is None or self.subnum is None:
            return None
        return "%d.%d" % (self.num, self.subnum) if self.subnum != 0 else str(self.num)


class Subject(db.Model):
    __tablename__ = 'subject'

    id = db.Column('subject_id', db.INTEGER, primary_key=True, autoincrement=True)
    name = db.Column('subject_name', db.String(45), nullable=False, unique=True)


class Teacher(db.Model, _Person):
    __tablename__ = 'teacher'

    id = db.Column('teacher_id', db.INTEGER, primary_key=True, autoincrement=True)
    surname = db.Column('teacher_surname', db.String(45), nullable=False)
    firstname = db.Column('teacher_firstname', db.String(45), nullable=False)
    middlename = db.Column('teacher_middlename', db.String(45))
    rank = db.Column('teacher_rank', db.String(45), nullable=False)
    login = db.Column('teacher_login', db.String(45), nullable=False, unique=True)


# Типы отчётности для единицы учебного плана
MarkType = {
    # Зачёт
    1: ("test_simple", "Зачёт"),
    # Экзамен
    2: ("exam", "Экзамен"),
    # Зачёт с оценкой
    3: ("test_diff", "Зачёт с оценкой")
}


class CurriculumUnit(db.Model):
    __tablename__ = 'curriculum_unit'
    __table_args__ = (
        db.UniqueConstraint('subject_id', 'stud_group_id'),
    )

    id = db.Column('curriculum_unit_id', db.INTEGER, primary_key=True, autoincrement=True)
    subject_id = db.Column(db.ForeignKey('subject.subject_id'), nullable=False, index=True)
    stud_group_id = db.Column(db.ForeignKey('stud_group.stud_group_id'), nullable=False, index=True)
    teacher_id = db.Column(db.ForeignKey('teacher.teacher_id'), nullable=False, index=True)
    mark_type = db.Column('mark_type', db.SMALLINT, nullable=False)
    hours_att_1 = db.Column('hours_att_1', db.SMALLINT, nullable=False)
    hours_att_2 = db.Column('hours_att_2', db.SMALLINT, nullable=False)
    hours_att_3 = db.Column('hours_att_3', db.SMALLINT, nullable=False)

    subject = db.relationship('Subject')
    teacher = db.relationship('Teacher')
    att_marks = db.relationship('AttMark', lazy=True, backref='curriculum_unit')

    @property
    def mark_type_name(self):
        return MarkType[self.mark_type]


class Student(db.Model, _Person):
    __tablename__ = 'student'

    id = db.Column('student_id', db.BIGINT, primary_key=True)
    surname = db.Column('student_surname', db.String(45), nullable=False)
    firstname = db.Column('student_firstname', db.String(45), nullable=False)
    middlename = db.Column('student_middlename', db.String(45))
    stud_group_id = db.Column(db.ForeignKey('stud_group.stud_group_id', ondelete='SET NULL', onupdate='SET NULL'), index=True)
    semester = db.Column('student_semestr', db.SMALLINT)
    alumnus_year = db.Column('student_alumnus_year', db.SMALLINT)
    expelled_year = db.Column('student_expelled_year', db.SMALLINT)
    login = db.Column('student_login', db.String(45), nullable=False, unique=True)




class AdminUser(db.Model, _Person):
    id = db.Column('admin_user_id', db.BIGINT, primary_key=True)
    surname = db.Column('admin_user_surname', db.String(45), nullable=False)
    firstname = db.Column('admin_user_firstname', db.String(45), nullable=False)
    middlename = db.Column('admin_user_middlename', db.String(45))
    login = db.Column('admin_user_login', db.String(45), nullable=False, unique=True)


MarkResult = [
    {"min": 0, "max": 49, "value": 2, "value_text": "неудовлетворительно"},
    {"min": 50, "max": 69, "value": 3, "value_text": "удовлетворительно"},
    {"min": 70, "max": 89, "value": 4, "value_text": "хорошо"},
    {"min": 90, "max": 100, "value": 5, "value_text": "отлично"}
]

MarkResultSimple = [
    {"min": 0, "max": 24, "value": False, "value_text": "не зачтено"},
    {"min": 25, "max": 50, "value": True, "value_text": "зачтено"}
]

MarkMinBall = 25
MarkMaxBall = 100


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
        att_marks = [self.att_mark_1, self.att_mark_2, self.att_mark_3]
        if any(m is None for m in att_marks):
            return None

        if self.curriculum_unit.mark_type_name[0] == "exam":
            if self.att_mark_exam is None:
                return None

            if self.att_mark_exam < MarkMinBall:
                return min(att_marks+[self.att_mark_exam]), MarkResult[0]

        if any(m < MarkMinBall for m in att_marks):
            if self.curriculum_unit.mark_type_name[0] == "test_simple":
                return min(att_marks), MarkResultSimple[0]

            if self.curriculum_unit.mark_type_name[0] in ("exam", "test_diff"):
                return min(att_marks), MarkResult[0]

        hours = [self.curriculum_unit.hours_att_1, self.curriculum_unit.hours_att_2, self.curriculum_unit.hours_att_3]
        ball_raw = sum([att_marks[i]*hours[i] for i in range(len(att_marks))])/sum(hours)
        # Округление
        ball = int(ball_raw)
        if ball_raw-ball >= 0.5:
            ball += 1

        if self.curriculum_unit.mark_type_name[0] == "test_simple":
            return ball, MarkResultSimple[1]

        if self.curriculum_unit.mark_type_name[0] == "exam":
            ball += self.att_mark_exam

        if self.curriculum_unit.mark_type_name[0] == "test_diff":
            ball *= 2

        if self.curriculum_unit.mark_type_name[0] in ("exam", "test_diff"):
            if self.att_mark_append_ball is not None:
                ball += self.att_mark_append_ball

            if ball > MarkMaxBall:
                ball = MarkMaxBall

            for mr in MarkResult:
                if mr["min"] <= ball <= mr["max"]:
                    return ball, mr

