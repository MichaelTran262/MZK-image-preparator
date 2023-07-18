$( document ).ready(function() {
    $('.remove-folder').on('click', function () {
        folder_id = $(this).closest('tr').attr('id');
        proc_id = $('#procId').text();
        $.ajax({
            type: "POST",
            url: '/api/process_folders/' + proc_id +'/remove/'+folder_id,
            async: false,
            success: function (result) {
                console.log("Folder successfully removed");
                $('#' + folder_id).remove();
            }
        });
    });
});