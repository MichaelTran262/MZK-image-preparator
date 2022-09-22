$( document ).ready(function() {
    $('#myInput').keyup(function() {
        let filter = $('#myInput').val()
        getDirs(filter);
    });

    function getDirs(filter) {
        console.log(filter)
        let dataset = $('#dirTable tbody').find('tr');
        //$('#dirTable tbody').hide();
        dataset.show();
        dataset.filter(function(index, item) {
            return $(item).find('td:first-child').text().indexOf(filter) === -1;
        }).hide();
    }
});