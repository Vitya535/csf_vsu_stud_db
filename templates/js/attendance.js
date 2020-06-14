let previousClickedTd;
let [currentCourse, currentGroupNum, currentGroupSubnum, currentTypeOfLesson, currentSubject] =
    getDataForAttendance();

function getDataForAttendance() {
    const currentCourse = $("#course").children("option:selected").val();
    const group = $("#group").children("option:selected").val();
    let [currentGroupNum, currentGroupSubnum] = group.split('.');
    if (!currentGroupSubnum) {
        currentGroupSubnum = 0;
    }
    const currentTypeOfLesson = $("#lesson_type").children("option:selected").val();
    const currentSubject = $("#lesson").children("option:selected").val();
    return [currentCourse, currentGroupNum, currentGroupSubnum, currentTypeOfLesson, currentSubject];
}

function getTdForHighlight() {
    let $tdOnOneLineWithNowDate;
    const trWithNowDate = getTrWithNowDate();
    const nowDateIndex = $(trWithNowDate).index();
    if (nowDateIndex !== -1) {
        const $table = $('#table-attendance');
        $tdOnOneLineWithNowDate = $table
            .children('tbody')
            .children('tr')
            .find(`td:eq(${nowDateIndex})`);
    }
    return $tdOnOneLineWithNowDate;
}

function getTrWithNowDate() {
    const nowDate = new Date();
    const nowDateLocaleDateString = nowDate.toLocaleDateString();
    const $table = $('#table-attendance');
    const ths = $table
        .children('thead')
        .children('tr:first')
        .children(`th:contains(${nowDateLocaleDateString})`);
    const convertedNowDateLocaleString = nowDateLocaleDateString.replace('.', '-');
    const nowTime = `${nowDate.getHours()}:${nowDate.getMinutes()}:00`;
    const nowDatetime = new Date(`${convertedNowDateLocaleString}T${nowTime}Z`);
    $(ths).each(function () {
       let [dateWithLowerTime, upperTimeString] = $(this).text().split('-');
       const lowerTimeString = `${dateWithLowerTime.split(' ')[1]}:00`;
       upperTimeString = `${upperTimeString.trimLeft()}:00`;
       const lowerDatetime = new Date(`${convertedNowDateLocaleString}T${lowerTimeString}Z`);
       const upperDatetime = new Date(`${convertedNowDateLocaleString}T${upperTimeString}Z`);
       if (nowDatetime > lowerDatetime && nowDatetime < upperDatetime) {
           return this;
       }
    });
}

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
        const $table = $('#table-attendance');
        const $tbody = $table.children('tbody');
        const $tableHeader = $table.children('thead').children('tr:first');
        $('#group, #lesson').empty();
        $tbody.empty();
        $tableHeader.empty();
        $(`#course option[value='${data.course}']`).prop('selected', true);
        $(data.groups).each(function () {
            $("#group").append(`<option value="${this.num_print}">${this.num_print} группа`);
        });
        $(`#group option[value='${data.selected_group.num_print}']`).prop('selected', true);
        $(`#lesson_type option[value='${data.selected_lesson_type}']`).prop('selected', true);
        $(data.subjects).each(function () {
            $("#lesson").append(`<option value="${this.name}">${this.name}`);
        });
        $(`#lesson option[value='${data.selected_subject}']`).prop('selected', true);
        $tableHeader.append('<th scope="col">ФИО студента/Дата проведения занятия');
        $(data.week_dates).each(function () {
            $tableHeader.append('<th scope="col" class="align-middle">' + this);
        });
        $(data.students).each(function () {
            $tbody.append('<tr>');
            const $tr = $tbody.children('tr:last');
            $tr.append(`<input type="hidden" name="card_number" value="${this.card_number}">`);
            $tr.append(`<td class="align-middle font-weight-bold">${this.full_name}`);
            if (this.attendance) {
                $(this.attendance).each(function () {
                    if (this.lesson_attendance) {
                        $tr.append('<td class="align-middle h2">+');
                    } else if (!this.lesson_attendance) {
                        $tr.append('<td class="align-middle h2">-');
                    } else {
                        $tr.append('<td class="align-middle h2">');
                    }
                });
            } else {
                $(data.week_dates).each(function () {
                    $tr.append('<td class="align-middle h2">');
                });
            }
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
    let attendanceValue = "";
    if ($(this).text() === '' || $(this).text() === '-') {
        $(this).text('+');
        attendanceValue = "true";
    } else {
        $(this).text('-');
    }
    const clickedTdIndex = $(this).index();
    const $table = $('#table-attendance');

    const $thForClickedTd = $table
        .children('thead')
        .children('tr')
        .children(`th:eq(${clickedTdIndex})`);

    const teachingPairId = $thForClickedTd.attr('data-teaching_pair_id');

    const parentTr = $(this).parent();
    const FIO = $(parentTr).children('td:first').text();

    const [surname, name, middlename] = FIO.split(" ");
    const lessonDate = $thForClickedTd.text();
    const postParams = {
        attendance_value: attendanceValue,
        lesson_date: lessonDate,
        group_num: currentGroupNum,
        group_subnum: currentGroupSubnum,
        course: currentCourse,
        student_name: name,
        student_surname: surname,
        student_middlename: middlename,
        teaching_pair_id: teachingPairId
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

$('#card_number').on('keydown', function (e) {
    if (e.keyCode === 13 && $(this).val()) {
        const cardNumber = $(this).val().replace(/^0+/, '');

        const lessonDate = new Date().toLocaleDateString();

        const $table = $('#table-attendance');
        const $thWithLessonDate = $table
            .children('thead')
            .children('tr:first')
            .children(`th:contains(${lessonDate}):first`);

        const nowDateIndex = $thWithLessonDate.index();

        const teaching_pair_id = $thWithLessonDate.attr('data-teaching_pair_id');

        const $tbody = $table.children('tbody');
        const cardNumberIndex = $tbody
            .children(`tr:has(input[value=${cardNumber}])`)
            .index();

        let $tdToMark;
        if (nowDateIndex !== -1 && cardNumberIndex !== -1) {
            $tdToMark = $tbody
                .children(`tr:eq(${cardNumberIndex})`)
                .children(`td:eq(${nowDateIndex})`);
        }

        $.post('/mark_by_card_number', {
                card_number: cardNumber,
                lesson_date: lessonDate,
                teaching_pair_id: teaching_pair_id
            },
            function (studentWithCardNumber) {
                console.log(studentWithCardNumber);
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
                    $tdToMark.text('+');
                }
            });
        $(this).val('');
    }
});

function highlightBlue() {
    $(previousClickedTd).css({backgroundColor: 'red'});
    previousClickedTd = $(this);
    $(previousClickedTd).css({backgroundColor: 'blue'});
}

function highlightNowDateAttendance() {
    let $trWithNowDate = getTrWithNowDate();
    let $tdOnOneLineWithNowDate = getTdForHighlight();
    $trWithNowDate.css({backgroundColor: 'red'});
    $tdOnOneLineWithNowDate.css({backgroundColor: 'red', cursor: 'pointer'});
}

$(document)
    .ready(function () {
        let $tdOnOneLineWithNowDate = getTdForHighlight();
        if ($tdOnOneLineWithNowDate) {
            highlightNowDateAttendance();
            $tdOnOneLineWithNowDate.on('click', highlightBlue);
        }

        $('.custom-select').on('change', attendancePostQuery);
        $('#checkbox_is_groupleader_mark_attendance').on('click', updateIsGroupLeaderMarkAttendance);

        {% if current_user.role_name in ('GroupLeader') and can_expose_group_leader_value %}
            $tdOnOneLineWithNowDate.on('dblclick', markAttendStudent);
        {% elif current_user.role_name in ('Teacher', 'AdminUser') %}
            $('#table-attendance').on('dblclick', 'td', markAttendStudent);
        {% endif %}
    })
    .ajaxComplete(function () {
        let $tdOnOneLineWithNowDate = getTdForHighlight();
        if ($tdOnOneLineWithNowDate) {
            highlightNowDateAttendance();
            $tdOnOneLineWithNowDate.on('click', highlightBlue);
        }
    });