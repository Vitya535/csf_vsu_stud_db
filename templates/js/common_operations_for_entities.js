$(document).ready(function () {
    $('#table_with_records').DataTable({
        "searching": false,
        "lengthChange": false,
        "info": false,
        "paging": false,
        "columnDefs": [{
            "targets": [0, -1],
            "orderable": false
        }],
        "aaSorting": []
    });

    const val = window.location.pathname.match(/[0-9]+/);
    const mapForDeleteOperation = new Map([
        ['/lessons_beginning', 'lessons_beginning'],
        [`/lessons_beginning/${val}`, 'lessons_beginning'],
        ['/teaching_pairs', 'teaching_pairs'],
        [`/teaching_pairs/${val}`, 'teaching_pairs'],
        ['/teaching_lessons', 'teaching_lessons'],
        [`/teaching_lessons/${val}`, 'teaching_lessons']
    ]);

    function getIdsForCheckboxes(checkboxesForOperations) {
        const aTags = $(checkboxesForOperations).closest('tr').find('td:eq(1) > a');
        let idsForOperation = [];
        for (const aTag of aTags)
        {
            let recordIds = $(aTag).attr('href').split('/').slice(2);
            idsForOperation.push(recordIds);
        }
        return idsForOperation;
    }

    $('#button_delete').click(function () {
        const checkboxesForOperations = $('.checkbox_for_operations:checked');
        if (!$(checkboxesForOperations).length)
        {
            alert('Вы должны выбрать как минимум один обьект!');
            return;
        }
        const idsToDelete = getIdsForCheckboxes(checkboxesForOperations);
        $.post(
            '/delete_record',
            {table_name: mapForDeleteOperation.get(window.location.pathname), ids_to_delete: JSON.stringify(idsToDelete)},
            function() {
                $(checkboxesForOperations).closest('tr').remove();
            }
        );
    });

    $('#button_edit').click(function () {
        const checkboxesForOperations = $('.checkbox_for_operations:checked');
        if (!$(checkboxesForOperations).length)
        {
            alert('Вы должны выбрать как минимум один обьект!');
            return;
        }
        const idsToEdit = getIdsForCheckboxes(checkboxesForOperations);
        $.post(
            '/handle_data_for_multiple_edit',
            {table_name: mapForDeleteOperation.get(window.location.pathname), ids_to_edit: JSON.stringify(idsToEdit)},
            function () {
                window.location.href = "/multiple_edit";
            }
        );
    });

    $('#check_all').click(function () {
        const checked = $(this).prop("checked");
        let checkboxesForOperations;
        if (checked) {
            checkboxesForOperations = $('.checkbox_for_operations:not(:checked)');
        } else {
            checkboxesForOperations = $('.checkbox_for_operations:checked');
        }

        $(checkboxesForOperations).each(function () {
            $(this).prop("checked", checked);
        });
    });

    $('th.sorting').click(function () {
        console.log($(this).index());
    });
});