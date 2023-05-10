$(document).ready(function() {
    $('.transfer-button').on('click', function() {
        path = window.location.pathname + '/' + $(this).closest('tr').find('a').text();
        url = '/api/check_folder_conditions' + path;
        url = url.replace(/([^:]\/)\/+/g, "$1");
        send_url = '/api/send_to_mzk_now/' + path;
        send_url = send_url.replace(/([^:]\/)\/+/g, "$1");
        progress_url = '/api/send_to_mzk_now/progress' + path;
        progress_url = progress_url.replace(/([^:]\/)\/+/g, "$1");
        $.ajax({
            type: 'GET',
            async: false,
            url: url,
            dataType: 'json',
            success: function(data) {
                if (!data.folder_two) {
                    $('#modalMessage').text('Chybí Složka 2!');
                    $('#modalInfo').modal('show');
                    return;
                }
                
                if (data.exists_at_mzk) {
                    // Handle missing results case
                    $('#modalMessage').text('Složka s daným názvem se již nachází v MZK!');
                    $('#modalInfo').modal('show');
                    return;
                }
                $('#transferModal').modal('show');
                $('#transferNowButton').on('click', function() {
                    $.ajax({
                        type: "POST",
                        url: send_url,
                        dataType: "json",
                        success: function(result){
                            update_transfer_progress(progress_url);
                            $('#transferNowButton').hide();
                            $('#transferLaterButton').hide();
                        }
                    });
                });
            },
            error: function(data) {
                console.log("WTF");
            }
        });
    });

    $('#transferModal').on('hidden.bs.modal', function () {
        $('#transferNowButton').show();
        $('#transferLaterButton').show();
        $("#transferProgressBar").css("width", "0%");
        $("#transferProgressNumbered").html("");
    });

});
// Document ready end

function update_transfer_progress(url) {
    progressId = setInterval(function() {
        $.ajax({
            type: 'GET',
            url: url,
            dataType: 'json',
            success: function(data) {
                if (data.total == 0) {
                    return;
                }
                if (data.current == data.total) {
                    console.log("current equals total")
                    clearInterval(progressId);
                }
                let percent = Math.floor((data.current/data.total)*100);
                let width_style = percent.toString() + "%";
                let label = data.current + "/" + data.total;
                $("#transferProgressBar").css("width", width_style);
                $("#transferProgressNumbered").html(label)
            },
            error: function(data) {
                console.log("update_transfer_progress failed");
            }
        });
    }, 1000);
}