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
                    $(button).text(text);
                    $(button).prop('disabled', false);
                } else {
                    text = "Odesláno";
                    $(button).text(text);
                    $(button).attr('title', data.result);
                }
                
            },
            error: function(data) {
                console.log("prepare_folders failed");
            }
        });
    });
});