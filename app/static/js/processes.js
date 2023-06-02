$(document).ready(function() {
    generate_table();
    setInterval(generate_table, 1000);
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

function generate_table() {
    url = '/api/processes'
    const urlParams = new URLSearchParams(window.location.search);
    const page = urlParams.get('page');
    $.ajax({
        type: 'GET',
        async: true,
        url: url,
        data: {'page': page},
        dataType: 'json',
        success: function(data) {
            let content = $('#tableContent');
            content.empty();
            for(let i = 0; i < data.procs.length; i++) {
                var row = "";
                row += '<td>' + data.procs[i].id + '</td>';
                row += '<td>' + data.procs[i].created + '</td>';
                row += '<td>' + data.procs[i].state + '</td>';
                row += `<td><a href="/celery_task/${ data.procs[i].celery_task_id }">${ data.procs[i].celery_task_id }</a></td>`
                row += '<td><a class="btn btn-primary" role="button" href="/get_process_folders/'+ data.procs[i].id + '">Zobrazit</a></td>'
                if(data.procs[i].state == 'STARTED') {
                    row += '<td><button type="button" class="cancel-button btn btn-danger" disabled>Ukončit</button><a class="btn btn-info" role="button" href="/process/'+ data.procs[i].id + '">Info</a></td>';
                } else {
                    row += '<td><a class="btn btn-info" role="button" href="/process/'+ data.procs[i].id + '">Info</a></td>';
                }
                content.append("<tr>"+row+"</tr>");
                if(data.procs[i].state == 'STARTED') {
                    progress = `
                    <tr >
                        <td class="border-left" colspan="6">
                        <div class="progress" style="height: 32px;">
                            <div id="transferProgressBar-${ data.procs[i].id }" class="progress-bar progress-bar-striped progress-bar-animated" style="display:block"></div>
                        </div>
                        <div id="transferProgressText-${ data.procs[i].id }"></div>
                        </td>
                    </tr>`;
                    content.append(progress); 
                    id = data.procs[i].id;
                    url = '/api/processes/progress/' + id;
                    $.ajax({
                        type: 'GET',
                        url: url,
                        async: false,
                        dataType: 'json',
                        success: function(data) {
                            if (data.total_files == 0) {
                                return;
                            }
                            if (data.current_files == data.total_files) {
                                $('#transferProgressBar-' + id).closest('tr').hide();
                                $('#cancel-' + id).html('-');
                                $('#status-' + id).html('SUCCESS');
                            }
                            let percent = Math.floor((data.current_files/data.total_files)*100);
                            let width_style = percent.toString() + "%";
                            let label = data.current_files + "/" + data.total_files + ' , ' + data.current_space.toFixed(2) + '/' + data.total_space.toFixed(2) + ' MB';
                            $('#transferProgressBar-' + id).css("width", width_style);
                            $('#transferProgressText-' + id).html(label);
                        },
                        error: function(data) {
                            console.log("update_transfer_progress failed");
                        }
                    });
                }
            }
        },
        error: function(data) {
            console.log(data);
        }
    });
}