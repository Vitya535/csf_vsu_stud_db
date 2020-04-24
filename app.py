import os
from datetime import datetime

from flask import request, render_template, redirect, url_for, send_from_directory, jsonify
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from sqlalchemy import not_


from app_config import app, db
from forms import StudGroupForm, StudentForm, StudentSearchForm, SubjectForm, TeacherForm, CurriculumUnitForm, \
    CurriculumUnitCopyForm, CurriculumUnitUnionForm, CurriculumUnitAddAppendStudGroupForm, AdminUserForm, LoginForm
from forms import StudentsUnallocatedForm
from model import StudGroup, Subject, Teacher, Student, CurriculumUnit, CurriculumUnitUnion, AttMark, AdminUser, \
    Person, LessonType
from orm_db_actions import get_all_groups_by_semester
from orm_db_actions import get_current_half_year
from orm_db_actions import get_curriculum_units_by_group_id_and_lesson_type
from orm_db_actions import get_group_by_semester_and_group_number
from orm_db_actions import get_group_of_current_user_by_id
from orm_db_actions import get_student_by_id_and_fio
from orm_db_actions import get_teaching_lesson_id_by_subject_name
from orm_db_actions import update_attendance
from orm_db_actions import update_can_expose_group_leader_attr_by_teaching_lesson_id
from orm_db_actions import get_attr_can_expose_group_leader_by_teaching_lesson_id
from password_checker import password_checker
from utils import get_current_and_next_week_text_dates

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# login page
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if form.button_login.data and form.validate():
        user_name = form.login.data
        role_name = form.user_type.data
        user = None
        class_map = Person.get_class_map()
        if not role_name:
            for clazz in class_map.values():
                user = user or db.session.query(clazz).filter(clazz.login == user_name).one_or_none()
        elif role_name in class_map.keys():
            clazz = class_map[role_name]
            user = user or db.session.query(clazz).filter(clazz.login == user_name).one_or_none()

        if user is not None:
            password = form.password.data
            if password_checker(user_name, password):
                login_user(user)
                return redirect(request.args.get("next") or url_for('index'))
            else:
                form.password.errors.append("Неверный пароль")
        else:
            form.login.errors.append("Пользователя с таким учётным именем не существует")
    return render_template('login.html', form=form)


@login_manager.user_loader
def load_user(user_name):
    if "@" not in user_name:
        return None
    role_name, ulogin = user_name.split("@", 1)
    class_map = Person.get_class_map()
    user = None
    if role_name in class_map.keys():
        clazz = class_map[role_name]
        user = user or db.session.query(clazz).filter(clazz.login == ulogin).one_or_none()
    return user


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


def render_error(code):
    return render_template('_errors/%d.html' % code), code


@app.route('/')
@login_required
def index():
    if current_user.role_name == "Student":
        return redirect(url_for('att_marks_report_student', id=current_user.id))

    if current_user.role_name == "Teacher":
        return redirect(url_for('teacher_report', id=current_user.id))

    return render_template('index.html')


@app.route('/stud_groups')
@login_required
def stud_groups():
    groups = db.session.query(StudGroup). \
        filter(StudGroup.active). \
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum). \
        all()
    return render_template('stud_groups.html', stud_groups=groups)


@app.route('/stud_group/<id>', methods=['GET', 'POST'])
@login_required
def stud_group(id):
    if current_user.role_name != 'AdminUser':
        return render_error(403)

    if id == 'new':
        group = StudGroup()
        group.subnum = 0
        now = datetime.now()
        if now.month >= 7 and now.day >= 1:
            group.year = now.year
        else:
            group.year = now.year - 1
        group.active = True

    else:
        try:
            id = int(id)
        except ValueError:
            return render_error(400)
        group = db.session.query(StudGroup).filter(StudGroup.id == id).one_or_none()

    if group is None:
        return render_error(404)

    # Запрет на редактирование неактивной группы
    if not group.active:
        return render_error(403)

    form = StudGroupForm(request.form if request.method == 'POST' else None, obj=group)

    if form.button_save.data and form.validate():
        # unique check
        q = db.session.query(StudGroup). \
            filter(StudGroup.year == form.year.data). \
            filter(StudGroup.semester == form.semester.data). \
            filter(StudGroup.num == form.num.data)
        if form.subnum.data > 0:
            q = q.filter(db.or_(StudGroup.subnum == form.subnum.data, StudGroup.subnum == 0))
        if id != 'new':
            q = q.filter(StudGroup.id != id)

        if q.count() > 0:
            form.subnum.errors.append('Группа с таким номером уже существует')
        else:
            form.populate_obj(group)
            db.session.add(group)
            db.session.commit()

            if id == 'new':
                db.session.flush()
                return redirect(url_for('stud_group', id=group.id))

    if form.button_delete.data and id != 'new':
        form.validate()
        if db.session.query(Student).filter(Student.stud_group_id == id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить группу, в которой есть студенты')
        if db.session.query(CurriculumUnit).filter(CurriculumUnit.stud_group_id == id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить группу, к которой привязаны единицы учебного плана')

        if len(form.button_delete.errors) == 0:
            db.session.delete(group)
            db.session.commit()
            db.session.flush()  # ???
            return redirect(url_for('stud_groups'))

    return render_template('stud_group.html', group=group, form=form)


@app.route('/student/<id>', methods=['GET', 'POST'])
@login_required
def student(id):
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    if id == 'new':
        s = Student()
    else:
        try:
            id = int(id)
        except ValueError:
            return render_error(400)
        s = db.session.query(Student).filter(Student.id == id).one_or_none()
        if s is None:
            return render_error(404)

    form = StudentForm(request.form if request.method == 'POST' else None, obj=s)  # WFORMS-Alchemy Объект на форму

    if form.button_delete.data:
        form.validate()
        if db.session.query(AttMark).filter(AttMark.student_id == s.id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить студента, у которого есть оценки за аттестации')

        if len(form.button_delete.errors) == 0:
            db.session.delete(s)
            db.session.commit()
            db.session.flush()
            return redirect(url_for('students'))

    if form.button_save.data and form.validate():
        form.populate_obj(s)  # WFORMS-Alchemy с формы на объект
        if s.status == "alumnus":
            s.stud_group = None
            s.expelled_year = None
            s.semester = None
            if s.alumnus_year is None:
                s.alumnus_year = datetime.now().year

        if s.status in ("expelled", "academic_leave"):
            s.stud_group = None
            s.alumnus_year = None
            if s.expelled_year is None:
                s.expelled_year = datetime.now().year

        if s.stud_group is not None:
            s.status = "study"
            s.semester = s.stud_group.semester
        else:
            s.group_leader = False

        if s.status == "study":
            s.alumnus_year = None
            s.expelled_year = None

        form = StudentForm(obj=s)

        if form.validate():
            if s.status != "alumnus" and s.semester is None:
                form.semester.errors.append("Укажите семестр")
            if len(form.semester.errors) == 0:
                db.session.add(s)
                db.session.commit()
                if id == 'new':
                    db.session.flush()  # ???
                if s.id != id:
                    return redirect(url_for('student', id=s.id))

    return render_template('student.html', student=s, form=form)


@app.route('/students', methods=['GET'])
@login_required
def students():
    if current_user.role_name != 'AdminUser':
        return render_error(403)

    form = StudentSearchForm(request.args)
    result = None
    if form.button_search.data and form.validate():
        q = db.session.query(Student)
        if form.id.data is not None:
            q = q.filter(Student.id == form.id.data)
        if form.surname.data != '':
            q = q.filter(Student.surname.like(form.surname.data + '%'))
        if form.firstname.data != '':
            q = q.filter(Student.firstname == form.firstname.data)
        if form.middlename.data != '':
            q = q.filter(Student.middlename == form.middlename.data)

        if form.status.data is not None:
            q = q.filter(Student.status == form.status.data)

        if form.stud_group.data is not None:
            q = q.filter(Student.stud_group_id == form.stud_group.data.id)

        if form.semester.data is not None:
            q = q.filter(Student.semester == form.semester.data)

        if form.alumnus_year.data is not None:
            q = q.filter(Student.alumnus_year == form.alumnus_year.data)

        if form.expelled_year.data is not None:
            q = q.filter(Student.expelled_year == form.expelled_year.data)

        if form.group_leader.data == 'yes':
            q = q.filter(Student.group_leader)
        if form.group_leader.data == 'no':
            q = q.filter(not_(Student.group_leader))

        if form.login.data != '':
            q = q.filter(Student.login == form.login.data)

        if form.card_number.data is not None:
            q = q.filter(Student.card_number == form.card_number.data)

        q = q.order_by(Student.surname, Student.firstname, Student.middlename)
        result = q.all()

    return render_template('students.html', students=result, form=form)


# Нераспределённые студенты
@app.route('/students_unallocated', methods=['GET', 'POST'])
@login_required
def students_unallocated():
    if current_user.role_name != 'AdminUser':
        return render_error(403)

    q = db.session.query(Student) \
        .filter(Student.status == "study") \
        .filter(Student.stud_group_id.is_(None)) \
        .order_by(Student.semester, Student.surname, Student.firstname, Student.middlename)
    students = q.all()

    result = {}
    for s in students:
        if s.semester not in result:
            result[s.semester] = []
        result[s.semester].append(s)

    r_form = None
    forms = []
    semesters = sorted(result.keys())
    for semester in semesters:
        _students = result[semester]
        if 'semester' in request.form and request.form['semester'].isdigit() and int(
                request.form['semester']) == semester:
            r_form = form = StudentsUnallocatedForm(request.form)
        else:
            form = StudentsUnallocatedForm()
            form.semester.data = semester

        form.students_selected.query_factory = lambda: _students

        form.stud_group.query_factory = \
            lambda: db.session.query(StudGroup) \
                .filter(StudGroup.semester == semester) \
                .filter(StudGroup.active) \
                .order_by(StudGroup.num, StudGroup.subnum).all()

        forms.append(form)

    # Перенос студентов в группы
    result_transfer = None
    if r_form is not None:
        if r_form.button_transfer.data and r_form.validate() and len(r_form.students_selected.data) > 0:
            g = r_form.stud_group.data
            semester = int(r_form.semester.data)
            result_transfer = {
                "students": [],
                "stud_group": g,
                "semester": semester
            }

            for s in r_form.students_selected.data:
                s.stud_group = g
                db.session.add(s)
                result_transfer["students"].append(s)
                result[semester].remove(s)
            db.session.commit()
            # удалить пустую форму
            if len(result[semester]) == 0:
                forms.remove(r_form)
                semesters.remove(semester)

            result_transfer["student_ids"] = set(str(s.id) for s in result_transfer["students"])

    return render_template('students_unallocated.html', forms=forms, semesters=semesters, result=result_transfer)


# Перевод студентов на следующий семестр
@app.route('/students_transfer', methods=['GET', 'POST'])
@login_required
def students_transfer():
    if current_user.role_name != 'AdminUser':
        return render_error(403)


@app.route('/subjects')
@login_required
def subjects():
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    s = db.session.query(Subject).order_by(Subject.name)
    return render_template('subjects.html', subjects=s)


@app.route('/subject/<id>', methods=['GET', 'POST'])
@login_required
def subject(id):
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    if id == 'new':
        s = Subject()
    else:
        try:
            id = int(id)
        except ValueError:
            return render_error(400)
        s = db.session.query(Subject).filter(Subject.id == id).one_or_none()
        if s is None:
            return render_error(404)

    form = SubjectForm(request.form if request.method == 'POST' else None, obj=s)
    if form.button_delete.data:
        form.validate()
        if db.session.query(CurriculumUnit).filter(CurriculumUnit.subject_id == s.id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить предмет, к которому привязаны единицы учебного плана')
        if len(form.button_delete.errors) == 0:
            db.session.delete(s)
            db.session.commit()
            db.session.flush()
            return redirect(url_for('subjects'))

    if form.button_save.data and form.validate():
        form.populate_obj(s)
        db.session.add(s)
        db.session.commit()
        if id == 'new':
            db.session.flush()
            return redirect(url_for('subject', id=s.id))

    return render_template('subject.html', subject=s, form=form)


@app.route('/teachers')
@login_required
def teachers():
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    return render_template('teachers.html',
                           teachers=db.session.query(Teacher).order_by(Teacher.surname, Teacher.firstname,
                                                                       Teacher.middlename))


@app.route('/teacher/<id>', methods=['GET', 'POST'])
@login_required
def teacher(id):
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    if id == 'new':
        t = Teacher()
    else:
        try:
            id = int(id)
        except ValueError:
            return render_error(400)
        t = db.session.query(Teacher).filter(Teacher.id == id).one_or_none()
        if t is None:
            return render_error(404)

    form = TeacherForm(request.form if request.method == 'POST' else None, obj=t)

    if form.button_delete.data:
        form.validate()
        if db.session.query(CurriculumUnit).filter(CurriculumUnit.teacher_id == t.id).count() > 0:
            form.button_delete.errors.append(
                'Невозможно удалить преподавателя, к которому привязаны единицы учебного плана')
        if len(form.button_delete.errors) == 0:
            db.session.delete(t)
            db.session.commit()
            db.session.flush()
            return redirect(url_for('teachers'))

    if form.button_save.data and form.validate():
        form.populate_obj(t)
        db.session.add(t)
        db.session.commit()
        if id == 'new':
            db.session.flush()
            return redirect(url_for('teacher', id=t.id))

    return render_template('teacher.html', teacher=t, form=form)


@app.route('/teacher_report/<int:id>')
@login_required
def teacher_report(id):
    # Проверка прав доступа
    if not (current_user.role_name == 'AdminUser' or (
            current_user.role_name == "Teacher" and current_user.id == id)):
        return render_error(403)

    t = db.session.query(Teacher).filter(Teacher.id == id).one_or_none()
    if t is None:
        return render_error(404)

    curriculum_units = db.session.query(CurriculumUnit).join(StudGroup) \
        .filter(CurriculumUnit.teacher_id == id) \
        .filter(StudGroup.active) \
        .order_by(CurriculumUnit.subject_id, StudGroup.semester, StudGroup.num, StudGroup.subnum) \
        .all()

    return render_template('teacher_report.html', curriculum_units=curriculum_units, teacher=t)


@app.route('/curriculum_unit/<id>', methods=['GET', 'POST'])
@login_required
def curriculum_unit(id):
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    if id == 'new':
        sg = None
        if 'stud_group_id' in request.args:
            try:
                sg = db.session.query(StudGroup). \
                    filter(StudGroup.id == int(request.args['stud_group_id'])).one_or_none()
            except ValueError:
                sg = None

        cu = CurriculumUnit(stud_group=sg)
    else:
        try:
            id = int(id)
        except ValueError:
            return render_error(400)
        cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
        if cu is None:
            return render_error(404)

    form = CurriculumUnitForm(request.form if request.method == 'POST' else None, obj=cu)

    if form.button_delete.data:
        form.validate()
        if db.session.query(AttMark).filter(AttMark.curriculum_unit_id == cu.id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить единицу учебного плана к которой привязаны оценки')
        if len(form.button_delete.errors) == 0:
            db.session.delete(cu)
            db.session.commit()
            db.session.flush()
            return redirect(url_for('stud_group', id=cu.stud_group.id, _anchor='curriculum_units'))

    if form.button_save.data and form.validate():
        # unique check
        q = db.session.query(CurriculumUnit).filter(CurriculumUnit.stud_group_id == form.stud_group.data.id). \
            filter(CurriculumUnit.subject_id == form.subject.data.id)
        if id != 'new':
            q = q.filter(CurriculumUnit.id != id)
        if q.count() > 0:
            form.subject.errors.append('Уже существует единица учебного плана с таким предметом у данной группы')
        else:

            form.populate_obj(cu)
            if not cu.stud_group.active:
                form.stud_group.errors.append('Невозможно добавить запись для неактивной студенческой группы')
            else:
                db.session.add(cu)
                db.session.commit()
                if id == 'new':
                    db.session.flush()
                    return redirect(url_for('curriculum_unit', id=cu.id))

    if cu.stud_group is not None:
        form.stud_group.render_kw = {"disabled": True}

    return render_template('curriculum_unit.html', curriculum_unit=cu, form=form)


@app.route('/curriculum_unit_copy/<int:id>', methods=['GET', 'POST'])
@login_required
def curriculum_unit_copy(id):
    if current_user.role_name != 'AdminUser':
        return render_error(403)

    cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
    if cu is None:
        return render_error(404)

    form = CurriculumUnitCopyForm(request.form)
    form.stud_groups_selected.query_factory = lambda: db.session.query(StudGroup). \
        filter(StudGroup.active). \
        filter(StudGroup.year == cu.stud_group.year). \
        filter(StudGroup.semester == cu.stud_group.semester). \
        filter(not_(StudGroup.id.in_(
        db.session.query(CurriculumUnit.stud_group_id).filter(CurriculumUnit.subject_id == cu.subject.id).subquery()))). \
        order_by(StudGroup.num, StudGroup.subnum).all()

    stud_group_ids = set()
    if form.button_copy.data and form.validate() and len(form.stud_groups_selected.data) > 0:
        for sg in form.stud_groups_selected.data:
            cu_new = CurriculumUnit(
                stud_group=sg,
                subject=cu.subject,
                teacher=cu.teacher,
                hours_att_1=cu.hours_att_1,
                hours_att_2=cu.hours_att_2,
                hours_att_3=cu.hours_att_3,
                mark_type=cu.mark_type
            )
            db.session.add(cu_new)
            stud_group_ids.add(sg.id)
        db.session.commit()

    curriculum_units_other = db.session.query(CurriculumUnit).join(StudGroup). \
        filter(StudGroup.semester == cu.stud_group.semester). \
        filter(CurriculumUnit.subject_id == cu.subject.id). \
        filter(StudGroup.id != cu.stud_group.id). \
        order_by(StudGroup.num, StudGroup.subnum).all()

    return render_template('curriculum_unit_copy.html',
                           curriculum_unit=cu,
                           curriculum_units_other=curriculum_units_other,
                           stud_group_ids=stud_group_ids,
                           form=form)


@app.route('/att_marks/<int:id>', methods=['GET', 'POST'])
@login_required
def att_marks(id):
    cu_first = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
    if cu_first is None:
        return render_error(404)

    # Проверка прав доступа
    if not (current_user.role_name == 'AdminUser' or (
            current_user.role_name == "Teacher" and current_user.id == cu_first.teacher_id)):
        return render_error(403)

    # запрет для редактирования оценок для неактивной студенческой группы
    if not cu_first.stud_group.active:
        return render_error(403)

    # Доп. единицы учебного плана для объединённой ведомости на несколько групп (подгрупп)
    curriculum_units_relative = db.session.query(CurriculumUnit).join(StudGroup). \
        filter(CurriculumUnit.id != cu_first.id). \
        filter(StudGroup.active). \
        filter(StudGroup.year == cu_first.stud_group.year). \
        filter(StudGroup.semester == cu_first.stud_group.semester). \
        filter(CurriculumUnit.subject_id == cu_first.subject.id). \
        filter(CurriculumUnit.teacher_id == cu_first.teacher.id). \
        filter(CurriculumUnit.mark_type == cu_first.mark_type). \
        filter(CurriculumUnit.hours_att_1 == cu_first.hours_att_1). \
        filter(CurriculumUnit.hours_att_2 == cu_first.hours_att_2). \
        filter(CurriculumUnit.hours_att_3 == cu_first.hours_att_3). \
        order_by(StudGroup.num, StudGroup.subnum). \
        all()

    curriculum_units = [cu_first]

    form_relative_curriculum_units = None
    if len(curriculum_units_relative) > 0:
        form_relative_curriculum_units = CurriculumUnitAddAppendStudGroupForm(request.args)
        form_relative_curriculum_units.relative_curriculum_units.query_factory = lambda: curriculum_units_relative
        curriculum_units.extend(form_relative_curriculum_units.relative_curriculum_units.data)

    for cu in curriculum_units:
        # Создание записей AttMark если их нет для данной единицы учебного плана
        _students = db.session.query(Student).filter(Student.stud_group_id == cu.stud_group.id). \
            filter(not_(Student.id.in_(
            db.session.query(AttMark.student_id).filter(AttMark.curriculum_unit_id == cu.id).subquery()))). \
            all()
        if len(_students) > 0:
            for s in _students:
                att_mark = AttMark(curriculum_unit=cu, student=s)
                cu.att_marks.append(att_mark)
                db.session.add(att_mark)
            db.session.commit()

    curriculum_units.sort(key=lambda cu: (cu.stud_group.num, cu.stud_group.subnum))
    cu_union = CurriculumUnitUnion(curriculum_units)

    form = CurriculumUnitUnionForm(request.form, obj=cu_union)

    if form.button_clear.data:
        if current_user.role_name != 'AdminUser':
            return render_error(403)

        db.session.query(AttMark).filter(AttMark.curriculum_unit_id.in_(cu_union.ids)).delete(synchronize_session=False)
        db.session.flush()
        db.session.commit()
        return redirect(url_for('curriculum_unit', id=cu_first.id))

    if form.button_save.data and form.validate():
        for f_elem in form.att_marks:
            m = f_elem.object_data
            # update att_mark
            if m.att_mark_id not in cu_union.att_marks_readonly_ids:
                for k, v in f_elem.data.items():
                    setattr(m, k, v)
                db.session.add(m)

        db.session.commit()

    return render_template(
        'att_marks.html',
        curriculum_unit=cu_union,
        form=form,
        form_relative_curriculum_units=form_relative_curriculum_units
    )


@app.route('/att_marks_report_stud_group/<int:id>')
@login_required
def att_marks_report_stud_group(id):
    group = db.session.query(StudGroup).filter(StudGroup.id == id).one_or_none()

    if group is None:
        return render_error(404)

    students_map = {}

    ball_avg = []

    for cu_index in range(len(group.curriculum_units)):
        ball_avg.append({"att_mark_1": 0, "att_mark_2": 0, "att_mark_3": 0, "total": 0})

    for cu_index, cu in enumerate(group.curriculum_units):
        for att_mark in cu.att_marks:
            if att_mark.student_id not in students_map:
                students_map[att_mark.student_id] = {"student": att_mark.student,
                                                     "att_marks": [None] * len(group.curriculum_units)}
            students_map[att_mark.student_id]["att_marks"][cu_index] = att_mark

            for attr_name in ["att_mark_1", "att_mark_2", "att_mark_3", "total"]:
                if attr_name == "total":
                    val = None if att_mark.result_print is None else att_mark.result_print[0]
                else:
                    val = getattr(att_mark, attr_name)
                if ball_avg[cu_index][attr_name] is not None:
                    if val is not None:
                        ball_avg[cu_index][attr_name] += val
                    else:
                        ball_avg[cu_index][attr_name] = None

    result = list(students_map.values())
    result.sort(key=lambda r: (r["student"].surname, r["student"].firstname, r["student"].middlename))

    if len(result) > 0:
        for cu_index in range(len(group.curriculum_units)):
            for attr_name in ball_avg[cu_index]:
                if ball_avg[cu_index][attr_name] is not None:
                    ball_avg[cu_index][attr_name] = round(ball_avg[cu_index][attr_name] / len(result), 2)

    return render_template('att_marks_report_stud_group.html', stud_group=group, result=result, ball_avg=ball_avg)


@app.route('/att_marks_report_student/<int:id>')
@login_required
def att_marks_report_student(id):
    s = db.session.query(Student).filter(Student.id == id).one_or_none()

    if s is None:
        return render_error(404)

    result = db.session.query(AttMark).join(CurriculumUnit).join(StudGroup).filter(AttMark.student_id == id). \
        order_by(StudGroup.year, StudGroup.semester, AttMark.curriculum_unit_id).all()

    return render_template('att_marks_report_student.html', student=s, result=result)


@app.route('/admin_users')
@login_required
def admin_users():
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    return render_template(
        'admin_users.html',
        admin_users=db.session.query(AdminUser).order_by(AdminUser.surname, AdminUser.firstname, AdminUser.middlename)
    )


@app.route('/admin_user/<id>', methods=['GET', 'POST'])
@login_required
def admin_user(id):
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    if id == 'new':
        u = AdminUser()
    else:
        try:
            id = int(id)
        except ValueError:
            return render_error(400)
        u = db.session.query(AdminUser).filter(AdminUser.id == id).one_or_none()
        if u is None:
            return render_error(404)

    form = AdminUserForm(request.form if request.method == 'POST' else None, obj=u)

    if form.button_delete.data:
        db.session.delete(u)
        db.session.commit()
        db.session.flush()
        return redirect(url_for('admin_users'))

    if form.button_save.data and form.validate():
        form.populate_obj(u)
        db.session.add(u)
        db.session.commit()
        if id == 'new':
            db.session.flush()
            return redirect(url_for('admin_user', id=u.id))

    return render_template('admin_user.html', admin_user=u, form=form)


app.register_error_handler(404, lambda code: render_error(404))


# stud_attendance

@app.route("/attendance", methods=['GET', 'POST'])
def attendance():
    """Веб-страничка для отображения посещаемости"""

    if current_user.role_name not in ('Student', 'GroupLeader') or request.method == 'POST':
        group_num = int(request.values.get('group_num', 1))
        group_subnum = int(request.values.get('group_subnum', 0))
        course = int(request.values.get('course', 1))
    else:
        current_user_group = get_group_of_current_user_by_id(current_user.stud_group_id)
        group_num = int(request.values.get('group_num', current_user_group.num))
        group_subnum = int(request.values.get('group_subnum', current_user_group.subnum))
        course = int(request.values.get('course', current_user.course))

    selected_lesson_type = request.values.get('lesson_type', 'lection')

    # current_year = datetime.now().year
    current_year = 2018
    current_half_year = get_current_half_year(current_year)

    semester = 2 * (course - 1) + current_half_year

    groups = get_all_groups_by_semester(semester)
    group = get_group_by_semester_and_group_number(semester, group_num, group_subnum)
    curriculum_units = get_curriculum_units_by_group_id_and_lesson_type(group.id, selected_lesson_type)

    # subjects_from_units = [unit.subject.to_dict() for unit in curriculum_units]
    selected_subject = None
    if subjects_from_units := [unit.subject.to_dict() for unit in curriculum_units]:
        selected_subject = request.values.get('lesson', subjects_from_units[0]['name'])

    teaching_lesson_id = get_teaching_lesson_id_by_subject_name(selected_subject)

    can_expose_group_leader_value = get_attr_can_expose_group_leader_by_teaching_lesson_id(teaching_lesson_id)

    current_and_next_week_text_dates = get_current_and_next_week_text_dates()

    if request.method == 'GET':
        return render_template('attendance.html',
                               teaching_lesson_id=teaching_lesson_id,
                               course=course,
                               groups=groups,
                               lesson_types=[lesson_type.value for lesson_type in LessonType],
                               selected_lesson_type=selected_lesson_type,
                               selected_subject=selected_subject,
                               students=group.students,
                               subjects=subjects_from_units,
                               group_num=group_num,
                               group_subnum=group_subnum,
                               week_dates=current_and_next_week_text_dates,
                               can_expose_group_leader=can_expose_group_leader_value)
    return jsonify(teaching_lesson_id=teaching_lesson_id,
                   course=course,
                   groups=[group.to_dict() for group in groups],
                   lesson_types=[lesson_type.value for lesson_type in LessonType],
                   selected_lesson_type=selected_lesson_type,
                   selected_subject=selected_subject,
                   students=[stud.to_dict() for stud in group.students],
                   subjects=subjects_from_units,
                   group_num=group_num,
                   group_subnum=group_subnum,
                   week_dates=current_and_next_week_text_dates,
                   can_expose_group_leader=can_expose_group_leader_value)


@app.route("/mark_attendance", methods=['POST'])
def mark_attendance_for_student():
    """Урл для отметки посещаемости у студента"""

    lesson_date = datetime.strptime(request.values.get('lesson_date'), '%d.%m.%Y').strftime('%Y-%m-%d')

    attendance_value = bool(request.values.get('attendance_value'))
    group_num = int(request.values.get('group_num'))
    group_subnum = int(request.values.get('group_subnum'))
    course = int(request.values.get('course'))
    selected_subject = request.values.get('selected_subject')
    student_name = request.values.get('student_name')
    student_surname = request.values.get('student_surname')
    student_middlename = request.values.get('student_middlename')

    # current_year = datetime.now().year
    current_year = 2018
    current_half_year = get_current_half_year(current_year)

    semester = 2 * (course - 1) + current_half_year

    group = get_group_by_semester_and_group_number(semester, group_num, group_subnum)
    student_to_mark = get_student_by_id_and_fio(semester, group.id, student_name, student_surname, student_middlename)
    teaching_lesson_id = get_teaching_lesson_id_by_subject_name(selected_subject)

    update_attendance(student_to_mark.id, teaching_lesson_id, lesson_date, attendance_value)

    return jsonify()


@app.route("/update_is_groupleader_mark_attendance", methods=['POST'])
def update_is_groupleader_mark_attendance():
    """Урл, нужный для того, чтобы проапдейтить значение can_expose_group_leader для учебного занятия"""
    can_expose_group_leader_value = bool(request.values.get('can_expose_group_leader_value'))
    selected_subject = request.values.get('selected_subject')

    teaching_lesson_id = get_teaching_lesson_id_by_subject_name(selected_subject)

    print(teaching_lesson_id)
    update_can_expose_group_leader_attr_by_teaching_lesson_id(teaching_lesson_id, can_expose_group_leader_value)

    return jsonify()


if __name__ == '__main__':
    app.run()
