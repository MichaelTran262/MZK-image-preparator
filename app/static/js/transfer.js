$(document).ready(function() {
    $('.transfer-button').on('click', function() {
        path = window.location.pathname + '/' + $(this).closest('tr').find('a').text();
        url = '/api/check_folder_conditions' + path;
        url = url.replace(/([^:]\/)\/+/g, "$1");
        send_url = '/api/folder/mzk/send' + path;
        send_url = send_url.replace(/([^:]\/)\/+/g, "$1");
        $('#modalMessage').text('Kontroluji NF disk ...');
        $('#modalInfo').modal('show');
        $('#transferNowButton').prop('disabled', true);
        $.ajax({
            type: 'GET',
            async: false,
            url: url,
            dataType: 'json',
            success: function(data) {
                if (!data.folder_two) {
                    $('#modalMessage').text('Chybí Složka 2!');
                    return;
                }
                
                if (data.exists_at_mzk) {
                    // Handle missing results case
                    $('#modalMessage').text('Složka s daným názvem se již nachází v MZK!');
                    $('#modalInfo').modal('show');
                    return;
                }
                //
                $('#transferModal').modal('show');

                $.ajax({
                    type: "GET",
                    url: "/api/mzk/dst-folders",
                    data: {path: '/'},
                    dataType: "json",
                    async: false,
                    success: function(data) {
                        $('#jstree').jstree({
                            'core': {
                              'data': data.folders,
                              'check_callback': true,
                              'multiple': false,
                            },
                            "plugins": ["types"]
                        });
                        $('#jstreeCurrentDirectory').text("/MUO")
                    },
                    error: function(result) {
                        console.log(result);
                    }
                })
                $('#jstree').on('dblclick.jstree', function(event) {
                    var node = $(event.target).closest('li');
                    
                    // Fetch and render the contents of the selected folder
                    new_path = $('#jstreeCurrentDirectory').text() + '/' + node.text()
                    new_path = new_path.replace(/([^:]\/)\/+/g, "$1");
                    $('#transferNowButton').prop('disabled', true);
                    render_jstree(new_path);
                });
                $('#jstree').on('select_node.jstree', function (e, data) {
                    if(data.node.text == '..') {
                        $('#transferNowButton').prop('disabled', true);
                    } else {
                        $('#transferNowButton').prop('disabled', false);
                    }
                });
                //render_jstree('/');

                $('#transferNowButton').on('click', function() {
                    if($("#jstree").jstree("get_selected", true)[0].text === undefined) {
                        return
                    }
                    folder_name = $("#jstree").jstree("get_selected", true)[0].text;
                    folder_path = $('#jstreeCurrentDirectory').text() + '/' + folder_name;
                    folder = new Object();
                    folder["dst_folder"] = folder_path;
                    $.ajax({
                        type: "POST",
                        url: send_url,
                        async: false,
                        data: JSON.stringify(folder),
                        contentType: 'application/json; charset=utf-8',
                        dataType: "json",
                        success: function(result){
                            window.location.href = '/processes'
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
        $('#modalInfo').modal('hide');
        $('#jstree').jstree('destroy');
        $('#transferNowButton').show();
        $('#transferLaterButton').show();
        $("#transferProgressBar").css("width", "0%");
        $("#transferProgressNumbered").html("");
    });

    $('#transferModal').on('shown.bs.modal', function () {
        $('#modalInfo').modal('hide');
        $('#transferNowButton').show();
        $('#transferLaterButton').show();
        $("#transferProgressBar").css("width", "0%");
        $("#transferProgressNumbered").html("");
    });

});
// Document ready end

function render_jstree(root_path) {
    $.ajax({
        type: "GET",
        url: "/api/mzk/dst-folders",
        data: {path: root_path},
        dataType: "json",
        async: false,
        success: function(data) {
            console.log(data.folders);
            $('#jstree').jstree('destroy');
            $('#jstree').jstree({
                'core': {
                    'data': data.folders,
                    'check_callback': true,
                    'multiple': false,
                },
                "types" : {
                    "default" : {
                        "icon" : "fa fa-folder text-warning"
                    },
                    "file" : {
                        "icon" : "fa fa-file  text-warning"
                    }
                },
                "plugins": ["types"]
            });
            $('#jstreeCurrentDirectory').text(data.current_folder)
            $('#jstree').on('dblclick.jstree', function(event) {
                var node = $(event.target).closest('li');
                // Fetch and render the contents of the selected folder
                new_path = $('#jstreeCurrentDirectory').text() + '/' + node.text()
                new_path = new_path.replace(/([^:]\/)\/+/g, "$1");
                console.log(new_path);
                render_jstree(new_path);
            });
            $('#jstree').on('select_node.jstree', function (e, data) {
                if(data.node.text == '..') {
                    $('#transferNowButton').prop('disabled', true);
                } else {
                    $('#transferNowButton').prop('disabled', false);
                }
            });
        },
        error: function(result) {
            console.log(result);
        }
    })
}