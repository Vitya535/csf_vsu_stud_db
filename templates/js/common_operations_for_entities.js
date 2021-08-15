$(document).ready(function () {
    $('#button_delete').click(function () {
        const checkboxesForOperations = $('#checkbox_for_operations:checked');
        if ($(checkboxesForOperations).length < 1)
        {
            alert('Вы должны выбрать как минимум один обьект!');
        }
        else
        {
            const val = window.location.pathname.match(/[0-9]+/);
            const mapForDeleteOperation = new Map([
                ['/lessons_beginning', 'lessons_beginning'],
                [`/lessons_beginning/${val}`, 'lessons_beginning'],
                ['/teaching_pairs', 'teaching_pairs'],
                [`/teaching_pairs/${val}`, 'teaching_pairs'],
                ['/teaching_lessons', 'teaching_lesson'],
                [`/teaching_lessons/${val}`, 'teaching_lesson']
            ]);
            const a_tags = $(checkboxesForOperations).closest('tr').find('td:eq(1) > a');
            let ids_to_delete = [];
            for (let a_tag of a_tags)
            {
                let record_ids = $(a_tag).attr('href').split('/').slice(2);
                ids_to_delete.push(record_ids);
            }
            $.post('/delete_record',
                {table_name: mapForDeleteOperation.get(window.location.pathname), ids_to_delete: JSON.stringify(ids_to_delete)},
                function() {
                    $(checkboxesForOperations).closest('tr').remove();
                });
        }
    });

    $('#button_edit').click(function () {
        const checkboxesForOperations = $('#checkbox_for_operations:checked');
        const val = $(checkboxesForOperations).closest('tr').children('td:eq(1)').text();
        const mapForEditOperation = new Map([
            ['/lessons_beginning', `/lesson_beginning/${val}`],
            ['/teaching_pairs', `/teaching_pair/${val}`],
            ['/teaching_lessons', `/teaching_lesson/${val}`]
        ]);
        if ($(checkboxesForOperations).length < 1)
        {
            alert('Вы должны выбрать как минимум один обьект!');
        }
        else
        {
            //ToDo: добавить переход на страницу с редактированием нескольких записей
        }
    });
});