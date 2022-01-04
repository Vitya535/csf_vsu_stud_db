import os
from datetime import datetime
from itertools import islice
from json import dumps
from json import loads

from flask import request, render_template, redirect, url_for, send_from_directory, jsonify, session
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from sqlalchemy import not_
from sqlalchemy.exc import IntegrityError

from app_config import app, db
from forms import StudGroupForm, StudentForm, StudentSearchForm, SubjectForm, TeacherForm, CurriculumUnitForm, \
    CurriculumUnitCopyForm, CurriculumUnitUnionForm, CurriculumUnitAddAppendStudGroupForm, AdminUserForm, LoginForm
from forms import StudentsUnallocatedForm, LessonBeginningForm, TeachingPairsForm, TeachingLessonForm
from model import StudGroup, Subject, Teacher, Student, CurriculumUnit, CurriculumUnitUnion, AttMark, AdminUser, \
    Person, LESSON_TYPES, LessonsBeginning, TeachingPairs, TeachingLessons
from orm_db_actions import delete_record_from_table
from orm_db_actions import filter_students_attendance
from orm_db_actions import get_all_groups_by_semester
from orm_db_actions import get_all_lessons_beginning
from orm_db_actions import get_all_teaching_lessons
from orm_db_actions import get_all_teaching_pairs
from orm_db_actions import get_attr_can_expose_group_leader_by_teaching_lesson_id
from orm_db_actions import get_current_half_year
from orm_db_actions import get_curriculum_units_by_group_id_and_lesson_type
from orm_db_actions import get_group_by_semester_and_group_number
from orm_db_actions import get_group_of_current_user_by_id
from orm_db_actions import get_lesson_beginning_by_year_and_half_year
from orm_db_actions import get_lesson_dates_for_subject
from orm_db_actions import get_object_for_form_filling
from orm_db_actions import get_student_by_card_number
from orm_db_actions import get_student_by_id_and_fio
from orm_db_actions import get_teaching_lesson_by_id
from orm_db_actions import get_teaching_lesson_id_by_subject_name
from orm_db_actions import get_teaching_pair_by_id
from orm_db_actions import get_teaching_pair_ids
from orm_db_actions import insert_or_update_attendance
from orm_db_actions import multiple_edit_records
from orm_db_actions import update_can_expose_group_leader_attr_by_teaching_lesson_id
from password_checker import password_checker

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
    studying_students = q.all()

    result = {}
    for s in studying_students:
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
            lambda: db.session.query(StudGroup). \
                filter(StudGroup.semester == semester). \
                filter(StudGroup.active). \
                order_by(StudGroup.num, StudGroup.subnum).all()

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
        db.session.query(CurriculumUnit.stud_group_id).
            filter(CurriculumUnit.subject_id == cu.subject.id).subquery()))). \
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

    curriculum_units.sort(key=lambda cur: (cur.stud_group.num, cur.stud_group.subnum))
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

@app.route("/attendance", methods=('GET', 'POST'))
def attendance():
    """Веб-страничка для отображения посещаемости"""

    if current_user.role_name not in ('Student', 'GroupLeader') or request.method == 'POST':
        group_num = request.values.get('group_num', 1, type=int)
        group_subnum = request.values.get('group_subnum', 0, type=int)
        course = request.values.get('course', 1, type=int)
    else:
        current_user_group = get_group_of_current_user_by_id(current_user.stud_group_id)
        group_num = request.values.get('group_num', current_user_group.num, type=int)
        group_subnum = request.values.get('group_subnum', current_user_group.subnum, type=int)
        course = request.values.get('course', current_user.course, type=int)

    selected_lesson_type = request.values.get('lesson_type', 'Лекция')

    # current_year = datetime.now().year
    current_year = 2018
    current_half_year = int(get_current_half_year(current_year))

    semester = 2 * (course - 1) + current_half_year

    groups = get_all_groups_by_semester(semester)
    group = get_group_by_semester_and_group_number(semester, group_num, group_subnum)
    curriculum_units = get_curriculum_units_by_group_id_and_lesson_type(group.id, selected_lesson_type)

    selected_subject = None
    subjects_from_units = tuple(unit.subject.to_dict() for unit in curriculum_units)
    if subjects_from_units is not None:
        selected_subject = request.values.get('lesson', subjects_from_units[0]['name'])

    teaching_lesson_id = get_teaching_lesson_id_by_subject_name(selected_subject)

    can_expose_group_leader_value = get_attr_can_expose_group_leader_by_teaching_lesson_id(teaching_lesson_id)

    current_and_next_week_text_dates = get_lesson_dates_for_subject(selected_subject, current_year,
                                                                    current_half_year)

    set_text_dates = set(datetime.strptime(text_date[:10], '%d.%m.%Y').strftime('%Y-%m-%d')
                         for text_date in current_and_next_week_text_dates)

    students_with_filtered_attendance = filter_students_attendance(group.students, selected_subject, set_text_dates)

    teaching_pair_ids = get_teaching_pair_ids(selected_subject)

    common_context_values = {
        'course': course,
        'groups': tuple(group.to_dict() for group in groups),
        'selected_lesson_type': selected_lesson_type,
        'selected_subject': selected_subject,
        'students': tuple(filtered_student.get_dict() for filtered_student in students_with_filtered_attendance),
        'subjects': subjects_from_units,
        'selected_group': group.to_dict(),
        'week_dates': current_and_next_week_text_dates,
        'teaching_pair_ids': teaching_pair_ids,
        'can_expose_group_leader': can_expose_group_leader_value
    }

    if request.method == 'GET':
        return render_template('attendance.html',
                               **common_context_values,
                               lesson_types=LESSON_TYPES)
    return jsonify(**common_context_values)


@app.route("/mark_attendance", methods=('POST',))
def mark_attendance_for_student():
    """Урл для отметки посещаемости у студента"""

    lesson_date = datetime.strptime(request.values.get('lesson_date')[:10], '%d.%m.%Y').strftime('%Y-%m-%d')

    attendance_value = request.values.get('attendance_value', type=bool)
    group_num = request.values.get('group_num', type=int)
    group_subnum = request.values.get('group_subnum', type=int)
    course = request.values.get('course', type=int)
    student_name = request.values.get('student_name')
    student_surname = request.values.get('student_surname')
    student_middlename = request.values.get('student_middlename')
    teaching_pair_id = request.values.get('teaching_pair_id', type=int)

    # current_year = datetime.now().year
    current_year = 2018
    current_half_year = get_current_half_year(current_year)

    semester = 2 * (course - 1) + int(current_half_year)

    group = get_group_by_semester_and_group_number(semester, group_num, group_subnum)
    student_to_mark = get_student_by_id_and_fio(semester, group.id, student_name, student_surname, student_middlename)

    insert_or_update_attendance(student_to_mark.id, teaching_pair_id, lesson_date, attendance_value)

    return jsonify()


@app.route("/update_is_groupleader_mark_attendance", methods=('POST',))
def update_is_groupleader_mark_attendance():
    """Урл, нужный для того, чтобы проапдейтить значение can_expose_group_leader для учебного занятия"""
    can_expose_group_leader_value = request.values.get('can_expose_group_leader_value', type=bool)
    selected_subject = request.values.get('selected_subject')

    teaching_lesson_id = get_teaching_lesson_id_by_subject_name(selected_subject)

    update_can_expose_group_leader_attr_by_teaching_lesson_id(teaching_lesson_id, can_expose_group_leader_value)

    return jsonify()


@app.route('/mark_by_card_number', methods=('POST',))
def mark_attendance_by_student_card_number():
    """Отметка посещения студента занятием по номеру его карты"""
    card_number = request.form.get('card_number', type=int)
    lesson_date = datetime.strptime(request.values.get('lesson_date'), '%d.%m.%Y').strftime('%Y-%m-%d')
    teaching_pair_id = request.values.get('teaching_pair_id', type=int)

    student_with_card_number = get_student_by_card_number(card_number)

    if student_with_card_number:
        insert_or_update_attendance(student_with_card_number.id, teaching_pair_id, lesson_date, True)
        return jsonify(student_with_card_number.to_dict())
    return jsonify()


@app.route('/delete_record', methods=('POST',))
def delete_record():
    """Удаление одной или нескольких записей из таблицы"""
    table_name = request.values.get('table_name')
    ids_to_delete = loads(request.values.get('ids_to_delete'))
    delete_record_from_table(table_name, ids_to_delete)
    return jsonify()


@app.route('/teaching_lessons')
@login_required
def teaching_lessons():
    """Страничка с интерфейсом для редактирования учебных занятий"""
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    all_teaching_lessons = get_all_teaching_lessons()
    return render_template('teaching_lessons.html', all_teaching_lessons=all_teaching_lessons)


@app.route('/teaching_lesson/<teaching_lesson_id>', methods=('GET', 'POST'))
@login_required
def teaching_lesson(teaching_lesson_id: [int, str]):
    """Страничка с интерфейсом для редактирования конкретного учебного занятия"""
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    if teaching_lesson_id == 'new':
        new_teaching_lesson = TeachingLessons()
    else:
        try:
            teaching_lesson_id = int(teaching_lesson_id)
        except ValueError:
            return render_error(400)
        new_teaching_lesson = get_teaching_lesson_by_id(teaching_lesson_id)
        if new_teaching_lesson is None:
            return render_error(404)

    form = TeachingLessonForm(request.form if request.method == 'POST' else None,
                              obj=new_teaching_lesson)

    if form.button_save.data and form.validate():
        form.populate_obj(new_teaching_lesson)
        teaching_lessons_to_add = (new_teaching_lesson,) * form.objects_count.data
        db.session.bulk_save_objects(teaching_lessons_to_add)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        if teaching_lesson_id == 'new':
            db.session.flush()
        return redirect(url_for('teaching_lessons'))
    return render_template('teaching_lesson.html',
                           form=form,
                           teaching_lesson=new_teaching_lesson)


@app.route('/teaching_pairs')
@login_required
def teaching_pairs():
    """Страничка с интерфейсом для редактирования учебных пар"""
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    all_teaching_pairs = get_all_teaching_pairs()
    return render_template('teaching_pairs.html', all_teaching_pairs=all_teaching_pairs)


@app.route('/teaching_pair/<teaching_pair_id>', methods=('GET', 'POST'))
@login_required
def teaching_pair(teaching_pair_id: [int, str]):
    """Страничка с интерфейсом для редактирования конкретной учебной пары"""
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    if teaching_pair_id == 'new':
        new_teaching_pair = TeachingPairs()
    else:
        try:
            teaching_pair_id = int(teaching_pair_id)
        except ValueError:
            return render_error(400)
        new_teaching_pair = get_teaching_pair_by_id(teaching_pair_id)
        if new_teaching_pair is None:
            return render_error(404)

    form = TeachingPairsForm(request.form if request.method == 'POST' else None,
                             obj=new_teaching_pair)

    if form.button_save.data and form.validate():
        form.populate_obj(new_teaching_pair)
        teaching_pairs_to_add = (new_teaching_pair,) * form.objects_count.data
        db.session.bulk_save_objects(teaching_pairs_to_add)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        if teaching_pair_id == 'new':
            db.session.flush()
        return redirect(url_for('teaching_pairs'))
    return render_template('teaching_pair.html',
                           form=form,
                           teaching_pair=new_teaching_pair)


@app.route('/lessons_beginning')
@login_required
def lessons_beginning():
    """Страничка с интерфейсом для редактирования списка начала занятий"""
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    all_lessons_beginning = get_all_lessons_beginning()
    return render_template('lessons_beginning.html', all_lessons_beginning=all_lessons_beginning)


@app.route('/lesson_beginning/<year>/<half_year>', methods=('GET', 'POST'))
@login_required
def lesson_beginning(year: [int, str], half_year: [int, str]):
    """Страничка для конкретного начала занятий"""
    if current_user.role_name != 'AdminUser':
        return render_error(403)
    if year == 'new_year' and half_year == 'new_half_year':
        lesson_beginning_with_year_and_half_year = LessonsBeginning()
    else:
        try:
            year = int(year)
            half_year = int(half_year)
        except ValueError:
            return render_error(400)
        lesson_beginning_with_year_and_half_year = get_lesson_beginning_by_year_and_half_year(year, half_year)
        if lesson_beginning_with_year_and_half_year is None:
            return render_error(404)

    form = LessonBeginningForm(request.form if request.method == 'POST' else None,
                               obj=lesson_beginning_with_year_and_half_year)

    if form.button_save.data and form.validate():
        form.populate_obj(lesson_beginning_with_year_and_half_year)
        lessons_beginning_to_add = (lesson_beginning_with_year_and_half_year,) * form.objects_count.data
        db.session.bulk_save_objects(lessons_beginning_to_add)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        if year == 'new_year' and half_year == 'new_half_year':
            db.session.flush()
        return redirect(url_for('lessons_beginning'))
    return render_template('lesson_beginning.html',
                           form=form,
                           lesson_beginning=lesson_beginning_with_year_and_half_year)


@app.route('/handle_data_for_multiple_edit', methods=('POST',))
def handle_data_for_multiple_edit():
    """Обработка данных для редактирования нескольких записей"""
    session['table_name'] = request.values.get('table_name')
    session['ids_to_edit'] = loads(request.values.get('ids_to_edit'))
    return dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route('/multiple_edit', methods=('GET', 'POST'))
def multiple_edit():
    """Страничка для редактирования нескольких записей"""
    titles_dict = {'lessons_beginning': 'Начало занятий',
                   'teaching_pairs': 'Учебная пара',
                   'teaching_lessons': 'Учебное занятие'}
    forms_dict = {'lessons_beginning': LessonBeginningForm,
                  'teaching_pairs': TeachingPairsForm,
                  'teaching_lessons': TeachingLessonForm}
    table_name = session.get('table_name')
    ids_to_edit = session.get('ids_to_edit')
    title = titles_dict.get(table_name)
    class_form = forms_dict.get(table_name)
    record_for_multiple_edit = get_object_for_form_filling(table_name, ids_to_edit)
    form = class_form(request.form if request.method == 'POST' else None, obj=record_for_multiple_edit)
    if request.method == 'POST':
        if form.button_save.data and form.validate():
            class_table = class_form.Meta.model
            object_from_form_data = class_table(*islice(form.data.items(), 2, len(form.data.items())))
            multiple_edit_records(object_from_form_data, ids_to_edit)
            return redirect(url_for(table_name))
    return render_template('multiple_edit.html', title=title, form=form)


if __name__ == '__main__':
    app.run()
