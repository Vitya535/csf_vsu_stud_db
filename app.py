from datetime import datetime
from flask import request, render_template, redirect, url_for

from app_config import app, db
from model import StudGroup, Subject, Teacher, Student, CurriculumUnit, AttMark, AdminUser
from forms import StudGroupForm, StudentForm, StudentSearchForm, SubjectForm, TeacherForm, CurriculumUnitForm, CurriculumUnitAttMarksForm, AdminUserForm

from sqlalchemy import not_


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stud_groups')
def stud_groups():
    groups = db.session.query(StudGroup). \
        filter(StudGroup.active). \
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum). \
        all()
    return render_template('stud_groups.html', stud_groups=groups)


@app.route('/stud_group/<id>', methods=['GET', 'POST'])
def stud_group(id):
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
            return 'Bad Request', 400
        group = db.session.query(StudGroup).filter(StudGroup.id == id).one_or_none()

    if group is None:
        return 'Not Found', 404

    form = StudGroupForm(request.form, obj=group)

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
            db.session.flush() # ???
            return redirect(url_for('stud_groups'))

    return render_template('stud_group.html', group=group, form=form)


@app.route('/student/<id>', methods=['GET', 'POST'])
def student(id):
    if id == 'new':
        s = Student()
    else:
        try:
            id = int(id)
        except ValueError:
            return 'Bad Request', 400
        s = db.session.query(Student).filter(Student.id == id).one_or_none()
        if s is None:
            return 'Not Found', 404

    form = StudentForm(request.form, obj=s)

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
        form.populate_obj(s)
        if s.stud_group is not None:
            s.semester = s.stud_group.semester
            s.alumnus_year = None
            s.expelled_year = None
            form = StudentForm(obj=s)

        db.session.add(s)
        db.session.commit()
        if id == 'new':
            db.session.flush() # ???
        if s.id != id:
            return redirect(url_for('student', id=s.id))

    return render_template('student.html', student=s, form=form)


@app.route('/students', methods=['GET'])
def students():
    form = StudentSearchForm(request.args)
    result = None
    if form.button_search.data and form.validate():
        q = db.session.query(Student)
        if form.id.data is not None:
            q = q.filter(Student.id == form.id.data)
        if form.surname.data != '':
            q = q.filter(Student.surname.like(form.surname.data+'%'))
        if form.firstname.data != '':
            q = q.filter(Student.firstname == form.firstname.data)
        if form.middlename.data != '':
            q = q.filter(Student.middlename == form.middlename.data)

        if form.stud_group.data is not None:
            q = q.filter(Student.stud_group_id == form.stud_group.data.id)

        if form.alumnus_year.data is not None:
            q = q.filter(Student.alumnus_year == form.alumnus_year.data)

        if form.expelled_year.data is not None:
            q = q.filter(Student.expelled_year == form.expelled_year.data)

        if form.login.data != '':
            q = q.filter(Student.login == form.login.data)

        q = q.order_by(Student.surname, Student.firstname, Student.middlename)
        result = q.all()

    return render_template('students.html', students=result, form=form)


@app.route('/subjects')
def subjects():
    s = db.session.query(Subject).order_by(Subject.name)
    return render_template('subjects.html', subjects=s)


@app.route('/subject/<id>', methods=['GET', 'POST'])
def subject(id):
    if id == 'new':
        s = Subject()
    else:
        try:
            id = int(id)
        except ValueError:
            return 'Bad Request', 400
        s = db.session.query(Subject).filter(Subject.id == id).one_or_none()
        if s is None:
            return 'Not Found', 404

    form = SubjectForm(request.form, obj=s)
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
def teachers():
    return render_template('teachers.html', teachers=db.session.query(Teacher).order_by(Teacher.surname, Teacher.firstname, Teacher.middlename))


@app.route('/teacher/<id>', methods=['GET', 'POST'])
def teacher(id):
    if id == 'new':
        t = Teacher()
    else:
        try:
            id = int(id)
        except ValueError:
            return 'Bad Request', 400
        t = db.session.query(Teacher).filter(Teacher.id == id).one_or_none()
        if t is None:
            return 'Not Found', 404

    form = TeacherForm(request.form, obj=t)

    if form.button_delete.data:
        form.validate()
        if db.session.query(CurriculumUnit).filter(CurriculumUnit.teacher_id == t.id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить преподавателя, к которому привязаны единицы учебного плана')
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


@app.route('/curriculum_unit/<id>', methods=['GET', 'POST'])
def curriculum_unit(id):
    if id == 'new':
        sg = None
        if 'stud_group_id' in request.args:
            try:
                sg = db.session.query(StudGroup).\
                    filter(StudGroup.id == int(request.args['stud_group_id'])).one_or_none()
            except ValueError:
                sg = None

        cu = CurriculumUnit(stud_group=sg)
    else:
        try:
            id = int(id)
        except ValueError:
            return 'Bad Request', 400
        cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
        if cu is None:
            return 'Not Found', 404

    form = CurriculumUnitForm(request.form, obj=cu)

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
        q = db.session.query(CurriculumUnit).filter(CurriculumUnit.stud_group_id == form.stud_group.data.id).\
            filter(CurriculumUnit.subject_id == form.subject.data.id)
        if id != 'new':
            q = q.filter(CurriculumUnit.id != id)
        if q.count() > 0:
            form.subject.errors.append('Уже существует единица учебного плана с таким предметом у данной группы')
        else:

            form.populate_obj(cu)
            db.session.add(cu)
            db.session.commit()
            if id == 'new':
                db.session.flush()
                return redirect(url_for('curriculum_unit', id=cu.id))

    if cu.stud_group is not None:
        form.stud_group.render_kw = {"disabled": True}

    return render_template('curriculum_unit.html', curriculum_unit=cu, form=form)


@app.route('/att_marks/<id>', methods=['GET', 'POST'])
def att_marks(id):
    try:
        id = int(id)
    except ValueError:
        return 'Bad Request', 400

    cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
    if cu is None:
        return 'Not Found', 404

    # Создание записей AttMark если их нет для данной единицы учебного плана
    _students = db.session.query(Student).filter(Student.stud_group_id == cu.stud_group.id).\
        filter(not_(Student.id.in_(db.session.query(AttMark.student_id).filter(AttMark.curriculum_unit_id == id)))).\
        all()
    if len(_students) > 0:
        for s in _students:
            att_mark = AttMark(curriculum_unit=cu, student=s)
            db.session.add(att_mark)
        db.session.flush()
        db.session.commit()
        cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()

    cu.att_marks.sort(key=lambda m: (m.student.surname, m.student.firstname, m.student.middlename))

    form = CurriculumUnitAttMarksForm(request.form, obj=cu)

    if form.button_clear.data:
        db.session.query(AttMark).filter(AttMark.curriculum_unit_id == id).delete()
        db.session.flush()
        db.session.commit()
        return redirect(url_for('curriculum_unit', id=cu.id))

    if form.button_save.data and form.validate():
        form.populate_obj(cu)
        for m in cu.att_marks:
            db.session.add(m)
        db.session.commit()

    return render_template('att_marks.html', curriculum_unit=cu, form=form)


@app.route('/att_marks_report_stud_group/<id>')
def att_marks_report_stud_group(id):
    try:
        id = int(id)
    except ValueError:
        return 'Bad Request', 400
    group = db.session.query(StudGroup).filter(StudGroup.id == id).one_or_none()

    if group is None:
        return 'Not Found', 404

    students_map = {}

    ball_avg =[]

    for cu_index in range(len(group.curriculum_units)):
        ball_avg.append({"att_mark_1":0, "att_mark_2": 0, "att_mark_3":0, "total":0})

    for cu_index, cu in enumerate(group.curriculum_units):
        for att_mark in cu.att_marks:
            if att_mark.student_id not in students_map:
                students_map[att_mark.student_id] = {"student": att_mark.student, "att_marks": [None]*len(group.curriculum_units)}
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

    if len(result)>0:
        for cu_index in range(len(group.curriculum_units)):
            for attr_name in ball_avg[cu_index]:
                if ball_avg[cu_index][attr_name] is not None:
                    ball_avg[cu_index][attr_name] = round(ball_avg[cu_index][attr_name]/len(result),2)

    return render_template('att_marks_report_stud_group.html', stud_group=group, result=result, ball_avg=ball_avg)


@app.route('/att_marks_report_student/<id>')
def att_marks_report_student(id):
    try:
        id = int(id)
    except ValueError:
        return 'Bad Request', 400
    s = db.session.query(Student).filter(Student.id == id).one_or_none()

    if s is None:
        return 'Not Found', 404

    result = db.session.query(AttMark).join(CurriculumUnit).join(StudGroup).filter(AttMark.student_id == id).\
        order_by(StudGroup.year, StudGroup.semester, AttMark.curriculum_unit_id).all()

    return render_template('att_marks_report_student.html', student=s, result=result)


@app.route('/admin_users')
def admin_users():
    return render_template('admin_users.html',
                           admin_users=db.session.query(AdminUser).order_by(AdminUser.surname, AdminUser.firstname,
                                                                       AdminUser.middlename))


@app.route('/admin_user/<id>', methods=['GET', 'POST'])
def admin_user(id):
    if id == 'new':
        u = AdminUser()
    else:
        try:
            id = int(id)
        except ValueError:
            return 'Bad Request', 400
        u = db.session.query(AdminUser).filter(AdminUser.id == id).one_or_none()
        if u is None:
            return 'Not Found', 404

    form = AdminUserForm(request.form, obj=u)

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


if __name__ == '__main__':
    app.run()
