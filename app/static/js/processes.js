$(document).ready(function() {
    $('.cancel-button').on('click', function() {
        uuid = $(this).closest('tr').attr('id');
        console.log(uuid);
        url = '/api/processes/celery_task/remove/' + uuid
        $.ajax({
            type: 'POST',
            async: true,
            url: url,
            dataType: 'json',
            success: function(data) {
                if(!alert('data.message')){window.location.reload();}
            },
            error: function(data) {
                console.log(data);
            }
        });
    });
});
// Document ready end