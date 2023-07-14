function get_active_processes() {
    fetch('/api/processes/celery/active')
        .then(res => res.json())
        .then(data => {
            console.log(data.active);
        })
}

function set_transfer_buttons() {
    // This code checks whether folder exists in MZK or not
    $('#tableContent tr td:first-child').each(function() {
        let column = $(this);
        let foldername = column.text();
        const blacklisted_folders = ["1", "2", "3", "4"]; 
        let regex = /^[k]?dig/i;
        if (!regex.test(foldername) || blacklisted_folders.includes(foldername)) {
            button = column.next('td').find('.transfer-button');
            button.css('visibility','hidden');
            return;
        }
        return
        let url = '/api/folder/mzk/' + foldername
        $.ajax({
            type: 'GET',
            url: url,
            async: true,
            dataType: 'json',
            success: function(data) {
                button = column.next('td').find('.transfer-button');
                let text = "";
                if(data.result == null) {
                    text = "Odeslat do MZK";
                    $(button).text(text);
                    $(button).prop('disabled', false);
                } else {
                    text = "Odesláno";
                    $(button).text(text);
                    $(button).prop('disabled', true);
                    $(button).attr('title', data.result);
                }
                
            },
            error: function(data) {
                console.log("prepare_folders failed");
            }
        });
    });
}

function handle_transfer_buttons() {
    fetch('/api/mzk/connection')
        .then(res => res.json())
        .then(data => {
            console.log(data)
            red = "rgb(255, 0, 0)";
            green = "rgb(0, 128, 0)";
            if(data.connection) {
                $('#connectionDot').css("color", "green");
            } else {
                $('#connectionDot').css("color", "red");
                $('.transfer-button').prop('title', '');
            }
            if(data.mount_exists) {
                $('#mountAvailableDot').css("color", "green");
                set_transfer_buttons();
            } else {
                $('#mountAvailableDot').css("color", "red");
                $('.transfer-button').attr('disabled', true);
                $('.transfer-button').text('X');
                $('.transfer-button').prop('title', 'MZK disk není připojen.');
            }
        })
}

$( document ).ready(function() {
    $('#myInput').keyup(function() {
        let filter = $('#myInput').val()
        getDirs(filter);
    });

    function getDirs(filter) {
        let dataset = $('#dirTable tbody').find('tr');
        //$('#dirTable tbody').hide();
        dataset.show();
        dataset.filter(function(index, item) {
            return $(item).find('td:first-child').text().indexOf(filter) === -1;
        }).hide();
    }
    handle_transfer_buttons();
});