$(document).ready(function() {
    $('.prepare-button').on('click', function() {
        path = window.location.pathname + '/' + $(this).closest('tr').find('a').text();
        url = '/api/prepare/check_folder_condition' + path;
        url = url.replace(/([^:]\/)\/+/g, "$1");
        prepare_url = '/api/prepare/prepare_folder' + path;
        prepare_url = prepare_url.replace(/([^:]\/)\/+/g, "$1");
        progress_url = '/api/prepare/progress' + path;
        progress_url = progress_url.replace(/([^:]\/)\/+/g, "$1");
        $.ajax({
            type: 'GET',
            async: false,
            url: url,
            dataType: 'json',
            success: function(data) {
                if (!data.folder_two) {
                    $('#modalMessage').text('Chybí Složka s názvem 2!');
                    $('#modalInfo').modal('show');
                    return;
                }
                if (!data.folder_three_empty && !data.folder_four_empty) {
                    $('#modalMessage').text('Složky 3 a 4 již existují a nejsou prázdné!');
                    $('#modalInfo').modal('show');
                    return;
                }
                if (!data.folder_three_empty) {
                    $('#modalMessage').text('Složka 3 již existuje a není prázdná!');
                    $('#modalInfo').modal('show');
                    return;
                }
                if (!data.folder_four_empty) {
                    $('#modalMessage').text('Složka 4 již existuje a není prázdná!');
                    $('#modalInfo').modal('show');
                    return;
                }
                $('#prepareModal').modal('show');
                $.ajax({
                    type: 'POST',
                    url: prepare_url,
                    dataType: 'json',
                    success: function(data) {
                        console.log("HELLO", data);
                    },
                    error: function(data) {
                        console.log("prepare_folders failed");
                    }
                });
            },
            error: function(data) {
                console.log("WTF");
            }
        });
        update_progress(progress_url);
    });
});

function update_progress(url) {

    progressIntId = setInterval(function() {
        $.ajax({
            type: 'GET',
            url: url,
            dataType: 'json',
            success: function(data) {
                if (data.current == data.total) {
                    clearInterval(progressIntId);
                }
                let percent = Math.floor((data.current/data.total)*100);
                let width_style = percent.toString() + "%";
                let label = data.current + "/" + data.total;
                $("#preparationProgressBar").css("width", width_style);
                $("#preparationProgressNumbered").html(label);
            },
            error: function(data) {
                console.log("get_progress failed");
            }
        });
    }, 1000);
}
// get the row ID for this transfer process