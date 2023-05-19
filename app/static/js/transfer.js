$(document).ready(function() {
    $('.transfer-button').on('click', function() {
        path = window.location.pathname + '/' + $(this).closest('tr').find('a').text();
        url = '/api/check_folder_conditions' + path;
        url = url.replace(/([^:]\/)\/+/g, "$1");
        send_url = '/api/folder/mzk/send' + path;
        send_url = send_url.replace(/([^:]\/)\/+/g, "$1");
        progress_url = '/api/folder/mzk/progress' + path;
        progress_url = progress_url.replace(/([^:]\/)\/+/g, "$1");
        $('#modalMessage').text('Kontroluji NF disk ...');
        $('#modalInfo').modal('show');
        $.ajax({
            type: 'GET',
            async: true,
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
                //
                $('#modalInfo').modal('hide');
                $('#transferModal').modal('show');
                /*
                $('#jstree').bind("dblclick.jstree", function (data) {
                    let selected_node = $('#jstree').jstree('get_selected', true)[0].text;
                    let new_path = $('#jstreeCurrentDirectory').text() + '/' + selected_node
                    new_path = new_path.replace(/([^:]\/)\/+/g, "$1");
                    //console.log(new_path);
                    render_jstree(new_path);
                });*/

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
                            "types" : {
                                "default" : {
                                    "icon" : "fa fa-folder-open"
                                },
                                "f-closed" : {
                                    "icon" : "fa fa-folder-open"
                                },
                                "file" : {
                                    "icon" : "fa fa-file"
                                }
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
                    console.log(new_path);
                    render_jstree(new_path);
                });

                $('#jstree').on('select_node.jstree', function (e, data) {
                    console.log("SELECTED: ", data.node.text);
                });
                
                //render_jstree('/');

                $('#transferNowButton').on('click', function() {
                    folder_name = $("#jstree").jstree("get_selected", true)[0].text;
                    folder_path = $('#jstreeCurrentDirectory').text() + '/' + folder_name;
                    folder = new Object();
                    folder["dst_folder"] = folder_path;
                    $.ajax({
                        type: "POST",
                        url: send_url,
                        data: JSON.stringify(folder),
                        contentType: 'application/json; charset=utf-8',
                        dataType: "json",
                        success: function(result){
                            $('#jstree').jstree('destroy');
                            //update_transfer_progress(progress_url);
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
        $('#jstree').jstree('destroy');
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
        },
        error: function(result) {
            console.log(result);
        }
    })
}