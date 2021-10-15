$(function () {
    $('#table_with_records > thead > tr')
        .clone(true)
        .addClass('filters')
        .appendTo('#table_with_records > thead');
    $('#table_with_records > thead > tr.filters > th.no-sorting').empty();

    $('#table_with_records').DataTable({
        "language": {
            "info": "Показ _START_.._END_ из _TOTAL_ записей",
            "lengthMenu": "Записей на странице: _MENU_",
            "paginate": {
                "first": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" fill=\"currentColor\" class=\"bi bi-skip-start-fill\" viewBox=\"0 0 16 16\">\n" +
                    "<path d=\"M4 4a.5.5 0 0 1 1 0v3.248l6.267-3.636c.54-.313 1.232.066 1.232.696v7.384c0 .63-.692 1.01-1.232.697L5 8.753V12a.5.5 0 0 1-1 0V4z\" />\n" +
                    "</svg>",
                "previous": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" fill=\"currentColor\" class=\"bi bi-caret-left-fill\" viewBox=\"0 0 16 16\">\n" +
                    "<path d=\"m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z\" />\n" +
                    "</svg>",
                "next": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" fill=\"currentColor\" class=\"bi bi-caret-right-fill\" viewBox=\"0 0 16 16\">\n" +
                    "<path d=\"m12.14 8.753-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 4.796a1 1 0 0 1 0 1.506z\" />\n" +
                    "</svg>",
                "last": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" fill=\"currentColor\" class=\"bi bi-skip-end-fill\" viewBox=\"0 0 16 16\">\n" +
                    "<path d=\"M12.5 4a.5.5 0 0 0-1 0v3.248L5.233 3.612C4.693 3.3 4 3.678 4 4.308v7.384c0 .63.692 1.01 1.233.697L11.5 8.753V12a.5.5 0 0 0 1 0V4z\" />\n" +
                    "</svg>"
            },
            "emptyTable": "",
            "infoEmpty": "",
            "zeroRecords": ""
        },
        "lengthChange": isLengthChangeTrue(),
        "pagingType": "input",
        "dom": "rt<'row'<'col'i><'col'p><'col'l>>",
        "columnDefs": [{
            "targets": getIndexesOfTh(),
            "orderable": false
        }],
        "aaSorting": [],
        orderCellsTop: true,
        fixedHeader: true,
        initComplete: function () {
            let api = this.api();

            api.columns().eq(0).each(function (colIdx) {
                    const index = $(api.column(colIdx).header()).index();
                    const cell = $(`.filters > th:not(.no-sorting):eq(${index})`);
                    const title = $(cell).text();
                    $(cell).html(`<input type="text" placeholder="${title}" />`);

                    $('input', cell)
                        .on('keyup change', function (e) {
                            e.stopPropagation();

                            $(this).attr('title', $(this).val());
                            let regexp = '({search})';

                            let cursorPosition = this.selectionStart;
                            api.column(colIdx).search(
                                    this.value ? regexp.replace('{search}', `${this.value}`) : '',
                                    this.value,
                                    !this.value
                                )
                                .draw();

                            $(this).trigger("focus")[0].setSelectionRange(cursorPosition, cursorPosition);
                        });
                });
        }
    });

    $('.paginate_input')
        .off('keyup')
        .on("keydown", function(e) {
        if (e.which === 13) {
            let table = $('#table_with_records').DataTable();
            let info = table.page.info();
            if (this.value.match(/[^0-9]/) || this.value < 1 || this.value > info.pages) {
                alert(`Пожалуйста, введите целое число от 1 до ${info.pages}`);
                return;
            }
            table.page(this.value - 1).draw(false);
        }
    });

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

    $('#button_delete').on("click",function () {
        const checkboxesForOperations = $('.checkbox_for_operations:checked');
        if (!$(checkboxesForOperations).length)
        {
            alert('Вы должны выбрать как минимум один обьект!');
            return;
        }
        const idsToDelete = getIdsForCheckboxes(checkboxesForOperations);
        $.post(
            '/delete_record',
            {table_name: window.location.pathname.replace(/^\//, ''), ids_to_delete: JSON.stringify(idsToDelete)},
            function() {
                location.reload();
            }
        );
    });

    $('#button_edit').on("click",function () {
        const checkboxesForOperations = $('.checkbox_for_operations:checked');
        if (!$(checkboxesForOperations).length)
        {
            alert('Вы должны выбрать как минимум один обьект!');
            return;
        }
        const idsToEdit = getIdsForCheckboxes(checkboxesForOperations);
        $.post(
            '/handle_data_for_multiple_edit',
            {table_name: window.location.pathname.replace(/^\//, ''), ids_to_edit: JSON.stringify(idsToEdit)},
            function () {
                window.location.href = "/multiple_edit";
            }
        );
    });

    $('#check_all').on("click",function () {
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