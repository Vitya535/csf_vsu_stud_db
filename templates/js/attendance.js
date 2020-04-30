let previousClickedTd;

function getDataForAttendance () {
    const currentCourse = $("#course").children("option:selected").val().split(' ')[0];
    const group = $("#group").children("option:selected").val();
    const groupSplit = group.split(' ')[0].split('.');
    let [currentGroupNum, currentGroupSubnum] = groupSplit;
    if (!currentGroupSubnum) {
        currentGroupSubnum = 0;
    }
    const currentTypeOfLesson = $("#lesson_type").children("option:selected").val();
    const currentSubject = $("#lesson").children("option:selected").val();
    return [currentCourse, currentGroupNum, currentGroupSubnum, currentTypeOfLesson, currentSubject];
}

function getTdForHighlightAndTrWithNowDate() {
    const table = $('#table-attendance');
    const nowDate = new Date().toLocaleDateString();
    const trWithNowDate = $(table)
        .children('thead')
        .children('tr:first')
        .children('th:contains(' + nowDate + '):first');

    const nowDateIndex = $(trWithNowDate).index();
    let tdOnOneLineWithNowDate;
    if (nowDateIndex !== -1) {
        tdOnOneLineWithNowDate = $(table)
            .children('tbody')
            .children('tr')
            .find('td:eq(' + nowDateIndex + ')');
    }
    return [trWithNowDate, tdOnOneLineWithNowDate];
}

let [currentCourse, currentGroupNum, currentGroupSubnum, currentTypeOfLesson, currentSubject] =
    getDataForAttendance();
let [trWithNowDate, tdOnOneLineWithNowDate] = getTdForHighlightAndTrWithNowDate();

function attendancePostQuery() {
    const [course, groupNum, groupSubnum, lessonType, lesson] = getDataForAttendance();
    let postParams;
    if (currentCourse !== course) {
        postParams = {
            course: course
        };
    } else if (currentGroupNum !== groupNum || currentGroupSubnum !== groupSubnum) {
        postParams = {
            course: course,
            group_num: groupNum,
            group_subnum: groupSubnum
        };
    } else if (currentTypeOfLesson !== lessonType) {
        postParams = {
            course: course,
            group_num: groupNum,
            group_subnum: groupSubnum,
            lesson_type: lessonType
        };
    } else if (currentSubject !== lesson) {
        postParams = {
            course: course,
            group_num: groupNum,
            group_subnum: groupSubnum,
            lesson_type: lessonType,
            lesson: lesson
        };
    }
    $.post('/attendance', postParams, function (data) {
        console.log(data);
        const table = $('#table-attendance');
        const tableHeader = $(table)
            .children('thead')
            .children('tr:first');
        const tbody = $(table).children('tbody');
        $('#group, #lesson').empty();
        $(tableHeader)
            .empty();
        $(tbody)
            .empty();
        $('#course option[value=' + data.course + ']').prop('selected', true);
        $.each(data.groups, function (index, group) {
            $("#group").append('<option value=' + group.num_print + '>' + group.num_print + ' группа');
        });
        $('#group option[value=' + data.selected_group.num_print + ']').prop('selected', true);
        $('#lesson_type option[value=' + data.selected_lesson_type + ']').prop('selected', true);
        $.each(data.subjects, function (index, subject) {
            $("#lesson").append('<option value=' + subject.name + '>' + subject.name);
        });
        $('#lesson option[value=' + data.selected_subject + ']').prop('selected', true);
        $(tableHeader).append('<th scope="col">ФИО студента/Дата проведения занятия');
        $.each(data.week_dates, function (index, week_date) {
            $(tableHeader).append('<th scope="col" class="align-middle">' + week_date);
        });
        $.each(data.students, function (index, student) {
            $(tbody).append('<tr>');
            const tr = $(tbody).children('tr:last');
            $(tr).append('<td class="align-middle font-weight-bold">' +
                student.full_name);
            $.each(student.attendance, function (index, attend) {
                if (attend.lesson_attendance && attend.teaching_lesson_id === data.teaching_lesson_id) {
                    $(tr).append('<td class="align-middle h2">+');
                } else {
                    $(tr).append('<td class="align-middle h2">-');
                }
            });
        });
        $('#checkbox_is_groupleader_mark_attendance').prop('checked', data.can_expose_group_leader);
        currentCourse = course;
        currentGroupNum = groupNum;
        currentGroupSubnum = groupSubnum;
        currentTypeOfLesson = lessonType;
        currentSubject = lesson;
    });
}

function markAttendStudent() {
    const table = $('#table-attendance');
    let attendanceValue = "";
    if ($(this).text() === '-') {
        $(this).text('+');
        attendanceValue = "true";
    } else {
        $(this).text('-');
    }
    const clickedTdIndex = $(this).index();
    const thForClickedTd = $(table)
        .children('thead')
        .children('tr')
        .children('th:eq(' + clickedTdIndex + ')');

    const parentTr = $(this).parent();
    const FIO = $(parentTr).children('td:first').text();

    const [surname, name, middlename] = FIO.split(" ");

    const lessonDate = $(thForClickedTd).text();
    const postParams = {
        attendance_value: attendanceValue,
        lesson_date: lessonDate,
        group_num: currentGroupNum,
        group_subnum: currentGroupSubnum,
        course: currentCourse,
        selected_subject: currentSubject,
        student_name: name,
        student_surname: surname,
        student_middlename: middlename
    }
    $.post('/mark_attendance', postParams);
}

function updateIsGroupLeaderMarkAttendance() {
    const canExposeGroupLeaderValue = $(this).is(':checked');
    let canExposeGroupLeaderTextValue = "";
    if (canExposeGroupLeaderValue) {
        canExposeGroupLeaderTextValue = "true";
    }
    const postParams = {
        can_expose_group_leader_value: canExposeGroupLeaderTextValue,
        selected_subject: currentSubject
    };
    $.post('/update_is_groupleader_mark_attendance', postParams);
}

$('#card_number').on('keydown', function(e) {
    const table = $('#table-attendance');
    if (e.keyCode === 13 && $(this).val()) {
        const cardNumber = $(this).val().replace(/^0+/, '');

        const lessonDate = new Date().toLocaleDateString();

        const nowDateIndex = $(table)
            .children('thead')
            .children('tr:first')
            .children('th:contains(' + lessonDate + '):first')
            .index();

        const cardNumberIndex = $(table)
            .children('tbody')
            .children('tr')
            .children('input[value=' + cardNumber + ']')
            .parent()
            .index();

        let tdToMark;
        if (nowDateIndex !== -1 && cardNumberIndex !== -1) {
            tdToMark = $(table)
                .children('tbody')
                .children('tr:eq(' + cardNumberIndex + ')')
                .children('td:eq(' + nowDateIndex + ')');
        }
        const attendanceValue = $(tdToMark).text();

        $.post('/mark_by_card_number', {card_number: cardNumber,
                                        selected_subject: currentSubject,
                                        lesson_date: lessonDate,
                                        attendance_value: attendanceValue},
        function (studentWithCardNumber) {
            if ($.isEmptyObject(studentWithCardNumber)) {
                $.toast({
                    heading: 'Error',
                    text: 'Студент с таким номером карты не найден!',
                    showHideTransition: 'fade',
                    icon: 'error',
                    position: 'bottom-right'
                });
            } else {
                $.toast({
                    heading: 'Success',
                    text: 'Отметка прошла успешно',
                    showHideTransition: 'fade',
                    icon: 'success',
                    position: 'bottom-right'
                });
                if (attendanceValue === '+') {
                    $(tdToMark).text('-');
                } else {
                    $(tdToMark).text('+');
                }
            }
        });
        $(this).val('');
    }
});

function highlightRed() {
    $(previousClickedTd).css({backgroundColor: 'red'});
    previousClickedTd = $(this);
    $(previousClickedTd).css({backgroundColor: 'blue'});
}

$('select.custom-select').on('change', attendancePostQuery);
$('#checkbox_is_groupleader_mark_attendance').on('click', updateIsGroupLeaderMarkAttendance);
$(tdOnOneLineWithNowDate).on('click', highlightRed);

{% if current_user.role_name in ('GroupLeader') and can_expose_group_leader_value %}
    $(tdOnOneLineWithNowDate).on('dblclick', markAttendStudent);
{% elif current_user.role_name in ('Teacher', 'AdminUser') %}
    $('#table-attendance').find('td').on('dblclick', markAttendStudent);
{% endif %}

function init() {
    $(trWithNowDate).css({backgroundColor: 'red'});
    $(tdOnOneLineWithNowDate).css({backgroundColor: 'red', cursor: 'pointer'});
}

$(document)
    .ready(function () {
        init();
    })
    .ajaxComplete(function () {
        init();
    });