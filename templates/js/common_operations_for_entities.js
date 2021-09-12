$(document).ready(function () {
    const val = window.location.pathname.match(/[0-9]+/);
    const mapForDeleteOperation = new Map([
        ['/lessons_beginning', 'lessons_beginning'],
        [`/lessons_beginning/${val}`, 'lessons_beginning'],
        ['/teaching_pairs', 'teaching_pairs'],
        [`/teaching_pairs/${val}`, 'teaching_pairs'],
        ['/teaching_lessons', 'teaching_lessons'],
        [`/teaching_lessons/${val}`, 'teaching_lessons']
    ]);

    $('#button_delete').click(function () {
        const checkboxesForOperations = $('#checkbox_for_operations:checked');
        if ($(checkboxesForOperations).length < 1)
        {
            alert('Вы должны выбрать как минимум один обьект!');
            return;
        }
        const aTags = $(checkboxesForOperations).closest('tr').find('td:eq(1) > a');
        let idsToDelete = [];
        for (const aTag of aTags)
        {
            let recordIds = $(aTag).attr('href').split('/').slice(2);
            idsToDelete.push(recordIds);
        }
        $.post(
            '/delete_record',
            {table_name: mapForDeleteOperation.get(window.location.pathname), ids_to_delete: JSON.stringify(idsToDelete)},
            function() {
                $(checkboxesForOperations).closest('tr').remove();
            }
        );
    });

    $('#button_edit').click(function () {
        const checkboxesForOperations = $('#checkbox_for_operations:checked');
        if ($(checkboxesForOperations).length < 1)
        {
            alert('Вы должны выбрать как минимум один обьект!');
            return;
        }
        const aTags = $(checkboxesForOperations).closest('tr').find('td:eq(1) > a');
        let idsToEdit = [];
        for (const aTag of aTags)
        {
            let recordIds = $(aTag).attr('href').split('/').slice(2);
            idsToEdit.push(recordIds);
        }

        const tableName = mapForDeleteOperation.get(window.location.pathname);
        $.post(
            '/handle_data_for_multiple_edit',
            {table_name: tableName, ids_to_edit: JSON.stringify(idsToEdit)},
            function () {
                window.location.href = "/multiple_edit";
            }
        );
    });
});