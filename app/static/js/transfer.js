$(document).ready(function() {
    $('.transfer-button').on('click', function() {
        path = window.location.pathname + '/' + $(this).closest('tr').find('a').text();
        url = '/api/check_folder_conditions' + path;
        url = url.replace(/([^:]\/)\/+/g, "$1");
        var socket = io.connect();
        socket.on('progress', function(data) {
            console.log("Socket listening on progress");
            // get the row ID for this transfer process
            let percent = Math.floor((data.current/data.total)*100);
            let width_style = percent.toString() + "%";
            console.log(width_style)
            let label = data.current + "/" + data.total;
            $("#progressBar").css("width", width_style);
            $("#progressNumbered").html(label);
        });
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
                    $('#modalMessage').text('Složka již je v MZK!');
                    $('#modalInfo').modal('show');
                    return;
                }
                console.log("it is ok");
                $('#transferModal').modal('show');
                $('#transferNowButton').on('click', function() {
                url = "/api/send_to_mzk_now/" + path
                url = url.replace(/([^:]\/)\/+/g, "$1");
                $.ajax({
                    type: "POST",
                    url: url,
                    dataType: "json",
                    success: function(result){
                        $('#transferNowButton').hide();
                        $('#transferLaterButton').hide();
                        $("#modalBody").append('<p id="transferInfo">Přenos proběhne i po zavření okna</p>');
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
        $("#transferInfo").remove()
        $('#transferNowButton').show();
        $('#transferLaterButton').show();
        $("#progressBar").css("width", "0%");
        $("#progressNumbered").html("");
    })
    $('#dirTable').on('click', '.transfer-button', function() {
        path = window.location.pathname + '/' + $(this).closest('tr').find('a').text();
        // remove trailing slashes
        path = path.replace(/([^:]\/)\/+/g, "$1");
        // listen for progress updates
    });
});