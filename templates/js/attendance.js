let previousClickedTd;
let [currentCourse, currentGroupNum, currentGroupSubnum, currentTypeOfLesson, currentSubject, currentDisplayMode] =
    getDataForAttendance();

function getDataForAttendance() {
    const currentCourse = $("#course > option:selected").val();
    const group = $("#group > option:selected").val();
    let [currentGroupNum, currentGroupSubnum] = group.split('.');
    if (!currentGroupSubnum) {
        currentGroupSubnum = 0;
    }
    const currentTypeOfLesson = $("#lesson_type > option:selected").val();
    const currentSubject = $("#lesson > option:selected").val();
    const currentDisplayMode = $("#display-mode > option:selected").val();
    return [currentCourse, currentGroupNum, currentGroupSubnum, currentTypeOfLesson, currentSubject, currentDisplayMode];
}

function getTdForHighlight() {
    let $tdOnOneLineWithNowDate;
    const trWithNowDate = getTrWithNowDate();
    const nowDateIndex = $(trWithNowDate).index();
    if (nowDateIndex !== -1) {
        $tdOnOneLineWithNowDate = $(`#table-attendance > tbody > tr > td:eq(${nowDateIndex})`);
    }
    return $tdOnOneLineWithNowDate;
}

function getTrWithNowDate() {
    const nowDate = new Date();
    const nowDateLocaleDateString = nowDate.toLocaleDateString();
    const ths = $(`#table-attendance > thead > tr:first > th:contains(${nowDateLocaleDateString})`);
    const convertedNowDateLocaleString = nowDateLocaleDateString.replace('.', '-');
    const nowTime = `${nowDate.getHours()}:${nowDate.getMinutes()}:00`;
    const nowDatetime = new Date(`${convertedNowDateLocaleString}T${nowTime}Z`);
    $(ths).each(function () {
        let [dateWithLowerTime, upperTimeString] = $(this).text().split('-');
        const lowerTimeString = `${dateWithLowerTime.split(' ')[1]}:00`;
        upperTimeString = `${upperTimeString.trimStart()}:00`;
        const lowerDatetime = new Date(`${convertedNowDateLocaleString}T${lowerTimeString}Z`);
        const upperDatetime = new Date(`${convertedNowDateLocaleString}T${upperTimeString}Z`);
        if (nowDatetime > lowerDatetime && nowDatetime < upperDatetime) {
            return this;
        }
    });
}

$(document).on('change', '.custom-select', function () {
    const [course, groupNum, groupSubnum, lessonType, lesson, displayMode] = getDataForAttendance();
    let postParams;
    if (currentCourse !== course) {
        postParams = {
            course: course,
            selected_display_mode: displayMode
        };
    } else if (currentGroupNum !== groupNum || currentGroupSubnum !== groupSubnum) {
        postParams = {
            course: course,
            group_num: groupNum,
            group_subnum: groupSubnum,
            selected_display_mode: displayMode
        };
    } else if (currentTypeOfLesson !== lessonType) {
        postParams = {
            course: course,
            group_num: groupNum,
            group_subnum: groupSubnum,
            lesson_type: lessonType,
            selected_display_mode: displayMode
        };
    } else if (currentSubject !== lesson || currentDisplayMode !== displayMode) {
        postParams = {
            course: course,
            group_num: groupNum,
            group_subnum: groupSubnum,
            lesson_type: lessonType,
            lesson: lesson,
            selected_display_mode: displayMode
        };
    }
    $.post('/attendance', postParams, function (data) {
        const $table = $('#table-attendance');
        const $tbody = $table.children('tbody');
        const $tableHeader = $table.children('thead').children('tr:first');
        $('#group, #lesson, #display-mode').empty();
        $tbody.empty();
        $tableHeader.empty();
        $(`#course option[value='${data['course']}']`).prop('selected', true);
        $(data['groups']).each(function () {
            $("#group").append(`<option value="${this['num_print']}">${this['num_print']} группа`);
        });
        $(`#group option[value='${data['selected_group']['num_print']}'],
        #lesson_type option[value='${data['selected_lesson_type']}']`).prop('selected', true);
        $(data['subjects']).each(function () {
            $("#lesson").append(`<option value="${this['name']}">${this['name']}`);
        });
        $(`#lesson option[value='${data['selected_subject']}']`).prop('selected', true);
        $(data['display_modes']).each(function () {
            $("#display-mode").append(`<option value="${this}">${this}`);
        });
        $(`#display-mode option[value='${data['selected_display_mode']}']`).prop('selected', true);
        $tableHeader.append('<th scope="col" class="align-middle">ФИО студента/Дата проведения занятия');
        fillRemainingAttendanceParams(data);
        bindEvents();
    });
    currentCourse = course;
    currentGroupNum = groupNum;
    currentGroupSubnum = groupSubnum;
    currentTypeOfLesson = lessonType;
    currentSubject = lesson;
    currentDisplayMode = displayMode;
});

function markAttendStudent() {
    let [currentCourse, currentGroupNum, currentGroupSubnum, currentTypeOfLesson, currentSubject, currentDisplayMode] =
        getDataForAttendance();
    let attendanceValue;
    if (['', '-'].indexOf($(this).text().trim()) !== -1) {
        $(this).text('+');
        attendanceValue = "1";
    } else {
        $(this).text('-');
        attendanceValue = "";
    }
    const clickedTdIndex = $(this).index();

    const $thForClickedTd = $(`#table-attendance > thead > tr > th:eq(${clickedTdIndex - 1})`);

    const teachingPairId = $thForClickedTd.attr('data-teaching_pair_id');

    const parentTr = $(this).parent();
    const FIO = $(parentTr).children('td:first').text();

    const [surname, name, middlename] = FIO.split(" ");
    const lessonDate = $thForClickedTd.text().trim();
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

$(document).on('click', '#checkbox_is_groupleader_mark_attendance', function () {
    const canExposeGroupLeaderValue = $(this).prop('checked');
    let canExposeGroupLeaderTextValue = "";
    if (canExposeGroupLeaderValue) {
        canExposeGroupLeaderTextValue = "1";
    }
    const postParams = {
        can_expose_group_leader_value: canExposeGroupLeaderTextValue,
        selected_subject: currentSubject
    };
    $.post('/update_is_groupleader_mark_attendance', postParams);
});

$('#card_number').on('change', function () {
    //if (e.key === 'Enter' && $(this).val()) {
    const cardNumber = $(this).val().replace(/^0+/, '');

    const lessonDate = new Date().toLocaleDateString();

    const $table = $('#table-attendance');
    const $thWithLessonDate = $table
        .children('thead')
        .children('tr:first')
        .children(`th:contains(${lessonDate}):first`);

    const nowDateIndex = $thWithLessonDate.index();

    const teachingPairId = $thWithLessonDate.attr('data-teaching_pair_id');

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
            teaching_pair_id: teachingPairId
        },
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
                $tdToMark.text('+');
            }
        });
    $(this).val('');
    //}
});

$(document).on('click', '#dates-left, #dates-right', function () {
    const [course, groupNum, groupSubnum, lessonType, lesson, displayMode] = getDataForAttendance();
    let postParams;
    if (displayMode === 'Неделя') {
        if (this.id === 'dates-left') {
            postParams = {
                course: course,
                group_num: groupNum,
                group_subnum: groupSubnum,
                lesson_type: lessonType,
                lesson: lesson,
                selected_display_mode: displayMode,
                increase: -1
            };
        } else if (this.id === 'dates-right') {
            postParams = {
                course: course,
                group_num: groupNum,
                group_subnum: groupSubnum,
                lesson_type: lessonType,
                lesson: lesson,
                selected_display_mode: displayMode,
                increase: 1
            };
        }
    } else if (displayMode === 'Месяц') {
        if (this.id === 'dates-left') {
            postParams = {
                course: course,
                group_num: groupNum,
                group_subnum: groupSubnum,
                lesson_type: lessonType,
                lesson: lesson,
                selected_display_mode: displayMode,
                increase: -5
            };
        } else if (this.id === 'dates-right') {
            postParams = {
                course: course,
                group_num: groupNum,
                group_subnum: groupSubnum,
                lesson_type: lessonType,
                lesson: lesson,
                selected_display_mode: displayMode,
                increase: 5
            };
        }
    }
    $.post("/dates_change", postParams, function (data) {
        const $table = $('#table-attendance');
        const $tbody = $table.children('tbody');
        const $tableHeader = $table.children('thead').children('tr:first');
        $tbody.empty();
        $tableHeader.empty().append('<th scope="col" class="align-middle">ФИО студента/Дата проведения занятия');
        fillRemainingAttendanceParams(data);
        bindEvents();
    });
});

function fillRemainingAttendanceParams(data) {
    const $table = $('#table-attendance');
    const $tbody = $table.children('tbody');
    const $tableHeader = $table.children('thead').children('tr:first');
    $(data['week_dates']).each(function (index) {
        $tableHeader.append(`<th scope="col" class="p-0 align-middle" data-teaching_pair_id="${data['teaching_pair_ids'][index]}">${this}`);
    });
    if (data['selected_display_mode'] === 'Неделя') {
        $tableHeader.children('th[data-teaching_pair_id]:first')
            .prepend('<div class="float-left"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" ' +
                'class="bi bi-caret-left-fill" id="dates-left" viewBox="0 0 16 16">' +
                '<path d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 ' +
                '4.796a1 1 0 0 0 0 1.506z">');
        $tableHeader.children('th[data-teaching_pair_id]:last')
            .prepend('<div class="float-right"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" ' +
                'class="bi bi-caret-right-fill" id="dates-right" viewBox="0 0 16 16">' +
                '<path d="m12.14 8.753-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 ' +
                '4.796a1 1 0 0 1 0 1.506z">');
    } else if (data['selected_display_mode'] === 'Месяц') {
        $tableHeader.children('th[data-teaching_pair_id]:first')
            .prepend('<div class="float-left mt-2"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" ' +
            'class="bi bi-caret-left-fill" id="dates-left" viewBox="0 0 16 16">' +
            '<path d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 ' +
            '4.796a1 1 0 0 0 0 1.506z">');
        $tableHeader.children('th[data-teaching_pair_id]:last')
            .prepend('<div class="float-right mt-2"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" ' +
            'class="bi bi-caret-right-fill" id="dates-right" viewBox="0 0 16 16">' +
            '<path d="m12.14 8.753-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 ' +
            '4.796a1 1 0 0 1 0 1.506z">');
    }
    $(data['students']).each(function () {
        $tbody.append('<tr>');
        const $tr = $tbody.children('tr:last');
        $tr.append(`<input type="hidden" name="card_number" value="${this['card_number']}">`)
            .append(`<td class="align-middle font-weight-bold">${this['full_name']}`);
        if (this['attendance']) {
            for (let i = 0; i < data['week_dates'].length; i++) {
                $tr.append('<td class="align-middle h2">');
            }
            $(this['attendance']).each(function () {
                const lessonDate = new Date(this['lesson_date']).toLocaleDateString();
                const $thIndex = $tableHeader.children(`th[data-teaching_pair_id=${this['teaching_pair_id']}]:contains(${lessonDate})`).index();
                const $td = $tr.children(`td:eq(${$thIndex})`);
                if (this['lesson_attendance'] === true) {
                    $td.text('+');
                } else if (this['lesson_attendance'] === false) {
                    $td.text('-');
                }
            });
        }
    });
    $('#checkbox_is_groupleader_mark_attendance').prop('checked', data['can_expose_group_leader']);
}

function highlightBlue() {
    $(previousClickedTd).css({backgroundColor: 'white'});
    previousClickedTd = $(this);
    $(previousClickedTd).css({backgroundColor: 'blue'});
}

function highlightNowDateAttendance() {
    let $trWithNowDate = getTrWithNowDate();
    let $tdOnOneLineWithNowDate = getTdForHighlight();
    $trWithNowDate.css({backgroundColor: 'red'});
    $tdOnOneLineWithNowDate.css({backgroundColor: 'red', cursor: 'pointer'});
}

function bindEvents() {
    let $tdOnOneLineWithNowDate = getTdForHighlight();
    if ($tdOnOneLineWithNowDate) {
        highlightNowDateAttendance();
        $tdOnOneLineWithNowDate
            .off('dblclick', highlightBlue)
            .on('dblclick', highlightBlue);
    }
    $('#table-attendance > tbody > tr').each(function () {
        $(this).children('td:not(:first)')
            .off('dblclick', highlightBlue)
            .on('dblclick', highlightBlue)
            .off('dblclick', markAttendStudent)
            .on('dblclick', markAttendStudent);
    });
}

$(function () {
    bindEvents();
});