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

    function get_proc_count() {
        fetch('/active_proc_count')
            .then(res => res.json())
            .then(data => {
                console.log(data.proc_count)
                $('#proc_count').html(data.proc_count)
            })
    }
    
    //get_proc_count();
    //setInterval(get_proc_count, 1000);
});