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

    $('#tableContent tr td:first-child').each(function() {
        let column = $(this);
        let foldername = column.text();
        const blacklisted_folders = ["1", "2", "3", "4"]; 
        let regex = /^(d|k)ig/i;
        if (!regex.test(foldername) || blacklisted_folders.includes(foldername)) {
            button = column.next('td').find('.transfer-button');
            button.css('visibility','hidden');
            return;
        }
        let url = '/api/folder/mzk/' + foldername
        $.ajax({
            type: 'GET',
            url: url,
            dataType: 'json',
            success: function(data) {
                button = column.next('td').find('.transfer-button');
                let text = "";
                if(data.result == null) {
                    text = "Odeslat do MZK";
                } else {
                    text = "Odesláno";
                }
                $(button).text(text);
            },
            error: function(data) {
                console.log("prepare_folders failed");
            }
        });
    });

    function get_connection_status() {
        fetch('/api/mzk/connection')
            .then(res => res.json())
            .then(data => {
                console.log(data)
                if(data.connection) {
                    $('#connectionDot').css("color", "green");
                } else {
                    $('#connectionDot').css("color", "red");
                }
                
            })
    }
    
    get_connection_status();
    setInterval(get_connection_status, 10000);
});