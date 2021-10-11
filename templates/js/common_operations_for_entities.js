$(document).ready(function () {
    $('#table_with_records').DataTable({
        "searching": false,
        "language": {
            "info": "Showing _START_.._END_ of _TOTAL_ entries",
            "lengthMenu": "Show Items per Page: _MENU_",
            "paginate": {
                "first": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" fill=\"currentColor\" class=\"bi bi-skip-start-fill\" viewBox=\"0 0 16 16\">\n" +
                    "  <path d=\"M4 4a.5.5 0 0 1 1 0v3.248l6.267-3.636c.54-.313 1.232.066 1.232.696v7.384c0 .63-.692 1.01-1.232.697L5 8.753V12a.5.5 0 0 1-1 0V4z\"/>\n" +
                    "</svg>",
                "previous": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" fill=\"currentColor\" class=\"bi bi-caret-left-fill\" viewBox=\"0 0 16 16\">\n" +
                    "  <path d=\"m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z\"/>\n" +
                    "</svg>",
                "next": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" fill=\"currentColor\" class=\"bi bi-caret-right-fill\" viewBox=\"0 0 16 16\">\n" +
                    "  <path d=\"m12.14 8.753-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 4.796a1 1 0 0 1 0 1.506z\"/>\n" +
                    "</svg>",
                "last": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" fill=\"currentColor\" class=\"bi bi-skip-end-fill\" viewBox=\"0 0 16 16\">\n" +
                    "  <path d=\"M12.5 4a.5.5 0 0 0-1 0v3.248L5.233 3.612C4.693 3.3 4 3.678 4 4.308v7.384c0 .63.692 1.01 1.233.697L11.5 8.753V12a.5.5 0 0 0 1 0V4z\"/>\n" +
                    "</svg>"
            },
            "emptyTable": "",
            "infoEmpty": "",
            "zeroRecords": ""
        },
        "lengthChange": isLengthChangeTrue(),
        "pagingType": "input",
        "dom": "rt<'bottom'<'row'<'col'i><'col'p><'col'l>>>",
        "columnDefs": [{
            "targets": getIndexesOfTh(),
            "orderable": false
        }],
        "aaSorting": []
    });

    const paginateInput = $('.paginate_input');

    $(paginateInput).off('keyup');

    $(paginateInput).keydown(function(e) {
        if (e.which === 13) {
            let table = $('#table_with_records').DataTable();
            let info = table.page.info();
            if (this.value === '' || this.value.match(/[^0-9]/) || this.value < 1 || this.value > info.pages) {
                alert(`Пожалуйста, введите целое число от 1 до ${info.pages}`);
                return;
            }
            table.page(this.value - 1).draw(false);
        }
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

    function isLengthChangeTrue() {
        const records = $('.checkbox_for_operations');
        return $(records).length;
    }

    function getIndexesOfTh() {
        let indexes = [];
        $('#table_with_records > thead > tr:first > th.no-sorting').each(function (){
           indexes.push($(this).index());
        });
        return indexes;
    }

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
                location.reload();
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
});