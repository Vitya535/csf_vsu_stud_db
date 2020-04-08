let previous_clicked_td;

let current_course = $("#course").children("option:selected").val().split(' ')[0];
let group = $("#group").children("option:selected").val();
let group_split = group.split(' ')[0].split('.');
let current_group_num = group_split[0];
let current_group_subnum;
if (group_split[1] !== undefined) {
    current_group_subnum = group_split[1];
} else {
    current_group_subnum = 0;
}
let current_type_of_lesson = $("#lesson_type").children("option:selected").val();
let current_subject = $("#lesson").children("option:selected").val();

function attendancePostQuery() {
    let course = $("#course").children("option:selected").val().split(' ')[0];
    let group = $("#group").children("option:selected").val();
    let group_split = group.split(' ')[0].split('.');
    let group_num = group_split[0];
    let group_subnum;
    if (group_split[1] !== undefined) {
        group_subnum = group_split[1];
    } else {
        group_subnum = 0;
    }
    let lesson_type = $("#lesson_type").children("option:selected").val();
    let lesson = $("#lesson").children("option:selected").val();
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
                $('#course').append('<option>' + i + ' курс');
            } else {
                $('#course').append('<option selected>' + i + ' курс');
            }
        }
        $.each(data.groups, function (index, group) {
            if (group.num === data.group_num && group.subnum === data.group_subnum) {
                if (group.subnum === 0) {
                    $('#group').append('<option selected>' + group.num + ' группа');
                } else {
                    $('#group').append('<option selected>' + group.num + '.' + group.subnum + ' группа');
                }
            } else {
                if (group.subnum === 0) {
                    $('#group').append('<option>' + group.num + ' группа');
                } else {
                    $('#group').append('<option>' + group.num + '.' + group.subnum + ' группа');
                }
            }
        });
        $.each(data.lesson_types, function (index, lesson_type) {
            if (lesson_type === data.selected_lesson_type) {
                $('#lesson_type').append('<option selected>' + lesson_type);
            } else {
                $('#lesson_type').append('<option>' + lesson_type);
            }
        });
        $.each(data.subjects, function (index, subject) {
            if (subject.name === data.selected_subject) {
                $('#lesson').append('<option selected>' + subject.name);
            } else {
                $('#lesson').append('<option>' + subject.name);
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
                if (attend.lesson_attendance) {
                    $(tr).append('<td class="align-middle h2">+');
                } else {
                    $(tr).append('<td class="align-middle h2">-');
                }
            });
        });
        current_course = course;
        current_group_num = group_num;
        current_group_subnum = group_subnum;
        current_type_of_lesson = lesson_type;
        current_subject = lesson;
    });
}

$('select.custom-select').on('change', attendancePostQuery);

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

    function markAttendStudent() {
        if ($(this).text() === '-') {
            $(this).text('+');
        } else {
            $(this).text('-');
        }
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