let previous_clicked_td;

let html_element_course = $("#course");
let html_element_group = $("#group");
let html_element_lesson_type = $("#lesson_type");
let html_element_lesson = $("#lesson");

let current_course = $(html_element_course).children("option:selected").val().split(' ')[0];
let group = $(html_element_group).children("option:selected").val();
let group_split = group.split(' ')[0].split('.');
let current_group_num = group_split[0];
let current_group_subnum;
if (group_split[1] !== undefined) {
    current_group_subnum = group_split[1];
} else {
    current_group_subnum = 0;
}
let current_type_of_lesson = $(html_element_lesson_type).children("option:selected").val();
let current_subject = $(html_element_lesson).children("option:selected").val();

function attendancePostQuery() {
    let course = $(html_element_course).children("option:selected").val().split(' ')[0];
    let group = $(html_element_group).children("option:selected").val();
    let group_split = group.split(' ')[0].split('.');
    let group_num = group_split[0];
    let group_subnum;
    if (group_split[1] !== undefined) {
        group_subnum = group_split[1];
    } else {
        group_subnum = 0;
    }
    let lesson_type = $(html_element_lesson_type).children("option:selected").val();
    let lesson = $(html_element_lesson).children("option:selected").val();
    let post_params;
    if (current_course !== course) {
        post_params = {
            course: course,
        };
    } else if (current_group_num !== group_num || current_group_subnum !== group_subnum) {
        post_params = {
            course: course,
            group_num: group_num,
            group_subnum: group_subnum
        };
    } else if (current_type_of_lesson !== lesson_type) {
        post_params = {
            course: course,
            group_num: group_num,
            group_subnum: group_subnum,
            lesson_type: lesson_type
        };
    } else if (current_subject !== lesson) {
        post_params = {
            course: course,
            group_num: group_num,
            group_subnum: group_subnum,
            lesson_type: lesson_type,
            lesson: lesson
        };
    }
    $.post('/attendance', post_params, function (data) {
        console.log(data);
        let table = $('#table-attendance');
        $('select.custom-select').empty();
        $(table)
            .children('thead')
            .children('tr:first')
            .empty();
        $(table)
            .children('tbody')
            .empty();
        for (let i = 1; i < 5; i++) {
            if (i !== data.course) {
                $(html_element_course).append('<option>' + i + ' курс');
            } else {
                $(html_element_course).append('<option selected>' + i + ' курс');
            }
        }
        $.each(data.groups, function (index, group) {
            if (group.num === data.group_num && group.subnum === data.group_subnum) {
                if (group.subnum === 0) {
                    $(html_element_group).append('<option selected>' + group.num + ' группа');
                } else {
                    $(html_element_group).append('<option selected>' + group.num + '.' + group.subnum + ' группа');
                }
            } else {
                if (group.subnum === 0) {
                    $(html_element_group).append('<option>' + group.num + ' группа');
                } else {
                    $(html_element_group).append('<option>' + group.num + '.' + group.subnum + ' группа');
                }
            }
        });
        $.each(data.lesson_types, function (index, lesson_type) {
            if (lesson_type === data.selected_lesson_type) {
                $(html_element_lesson_type).append('<option selected>' + lesson_type);
            } else {
                $(html_element_lesson_type).append('<option>' + lesson_type);
            }
        });
        $.each(data.subjects, function (index, subject) {
            if (subject.name === data.selected_subject) {
                $(html_element_lesson).append('<option selected>' + subject.name);
            } else {
                $(html_element_lesson).append('<option>' + subject.name);
            }
        });
        let table_header = $(table)
            .children('thead')
            .children('tr:first');
        $(table_header).append('<th scope="col">ФИО студента/Дата проведения занятия');
        $.each(data.week_dates, function (index, week_date) {
            $(table_header).append('<th scope="col" class="align-middle">' + week_date);
        });
        let tbody = $(table).children('tbody');
        $.each(data.students, function (index, student) {
            $(tbody).append('<tr>');
            let tr = $(tbody).children('tr:last');
            $(tr).append('<td class="align-middle font-weight-bold">' +
                student.surname + " " + student.firstname + " " + student.middlename);
            $.each(student.attendance, function (index, attend) {
                if (attend.lesson_attendance && attend.teaching_lesson_id === data.teaching_lesson_id) {
                    $(tr).append('<td class="align-middle h2">+');
                } else {
                    $(tr).append('<td class="align-middle h2">-');
                }
            });
        });
        let checkbox_is_groupleader_mark_attendance_form = $('#checkbox_is_groupleader_mark_attendance_form');
        $(checkbox_is_groupleader_mark_attendance_form).empty();
        if (data.can_expose_group_leader) {
            $(checkbox_is_groupleader_mark_attendance_form).append("<input type=\"checkbox\" class=\"form-check-input\"" +
                " id=\"checkbox_is_groupleader_mark_attendance\" checked>");
        } else {
            $(checkbox_is_groupleader_mark_attendance_form).append("<input type=\"checkbox\" class=\"form-check-input\"" +
                " id=\"checkbox_is_groupleader_mark_attendance\">");
        }
        $(checkbox_is_groupleader_mark_attendance_form).append("<label class=\"form-check-label\"" +
            " for=\"checkbox_is_groupleader_mark_attendance\">Староста отмечает\n" +
            " посещаемость</label>");
        current_course = course;
        current_group_num = group_num;
        current_group_subnum = group_subnum;
        current_type_of_lesson = lesson_type;
        current_subject = lesson;
    });
}

function markAttendStudent() {
    let attendance_value;
    if ($(this).text() === '-') {
        $(this).text('+');
        attendance_value = "true";
    } else {
        $(this).text('-');
        attendance_value = "";
    }
    let clicked_td_index = $(this).index();
    let th_for_clicked_td = $(table)
        .children('thead')
        .children('tr')
        .children('th')
        .eq(clicked_td_index);

    let parent_tr = $(this).parent();
    let FIO = $(parent_tr).children('td:first').text();

    let splittedFIO = FIO.split(" ");
    let surname = splittedFIO[0];
    let name = splittedFIO[1];
    let middlename = splittedFIO[2];

    let lesson_date = $(th_for_clicked_td).text();
    let post_params = {
        attendance_value: attendance_value,
        lesson_date: lesson_date,
        group_num: current_group_num,
        group_subnum: current_group_subnum,
        course: current_course,
        selected_subject: current_subject,
        student_name: name,
        student_surname: surname,
        student_middlename: middlename
    }
    $.post('/mark_attendance', post_params);
}

function updateIsGroupLeaderMarkAttendance() {
    let can_expose_group_leader_value = $(this).is(':checked');
    let can_expose_group_leader_text_value;
    if (can_expose_group_leader_value) {
        can_expose_group_leader_text_value = "true";
    } else {
        can_expose_group_leader_text_value = "";
    }
    console.log(can_expose_group_leader_value);
    let post_params = {
        can_expose_group_leader_value: can_expose_group_leader_text_value,
        selected_subject: current_subject
    };
    console.log(post_params);
    $.post('/update_is_groupleader_mark_attendance', post_params);
}

$('select.custom-select').on('change', attendancePostQuery);
$('#checkbox_is_groupleader_mark_attendance').on('click', updateIsGroupLeaderMarkAttendance);

function init() {
    let table = $("#table-attendance");
    let now_date = new Date().toLocaleDateString();
    let tr_with_now_date = $(table)
        .children('thead')
        .children('tr:first')
        .children('th:contains(' + now_date + '):first');

    let now_date_index = $(tr_with_now_date).index();
    let td_on_one_line_with_now_date;
    if (now_date_index !== -1) {
        td_on_one_line_with_now_date = $(table)
            .children('tbody')
            .children('tr')
            .find('td:eq(' + now_date_index + ')');
    }
    $(tr_with_now_date).css({backgroundColor: 'red'});
    $(td_on_one_line_with_now_date).css({backgroundColor: 'red', cursor: 'pointer'});

    function highlightRed() {
        $(previous_clicked_td).css({backgroundColor: 'red'});
        previous_clicked_td = $(this);
        $(this).css({backgroundColor: 'blue'});
    }

    $(td_on_one_line_with_now_date).on('click', highlightRed);

    {% if current_user.role_name in ('GroupLeader') %}
        $(td_on_one_line_with_now_date).on('dblclick', markAttendStudent);
    {% elif current_user.role_name in ('Teacher', 'AdminUser') %}
        $(table).find('td').on('dblclick', markAttendStudent);
    {% endif %}
}

$(document).ready(function () {
    init();
});

$(document).ajaxComplete(function () {
    init();
});