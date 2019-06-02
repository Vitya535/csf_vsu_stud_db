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


class _Person:
    @property
    def full_name(self):
        if self.surname is None or self.firstname is None:
            return None
        return " ".join((self.surname, self.firstname, self.middlename) if self.middlename is not None else (
            self.surname, self.firstname))

    @property
    def full_name_short(self):
        return "%s %s. %s." % (self.surname, self.firstname[0], self.middlename[0]) if self.middlename is not None \
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


class StudGroup(db.Model):
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
    def course(self):
        if self.semester is None:
            return None
        return (self.semester // 2) + 1

    @property
    def year_print(self):
        if self.year is None:
            return None
        return "%d-%d" % (self.year, self.year + 1)

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

    @property
    def role_name(self):
        return 'Teacher'


class CurriculumUnit(db.Model):
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

    @property
    def mark_type_name(self):
        return MarkTypeDict[self.mark_type]

    @property
    def fill_data(self):
        r = {}
        for m in self.att_marks:
            if m.student.stud_group_id == self.stud_group_id:
                for rm_k, rm_v in m.fill_data.items():
                    r[rm_k] = r.get(rm_k, True) and rm_v

        return r


class Student(db.Model, _Person):
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
    login = db.Column('student_login', db.String(45), nullable=False, unique=True)

    @property
    def status_name(self):
        return StudentStateDict[self.status]

    @property
    def role_name(self):
        return 'Student'


class AdminUser(db.Model, _Person):
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
        min_ball =  MarkResult["test_simple"][1]["min"]
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
