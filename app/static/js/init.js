function get_connection_status() {
    fetch('/api/mzk/connection')
        .then(res => res.json())
        .then(data => {
            console.log(data)
            if(data.connection) {
                $('#connectionDot').css("color", "green");
            } else {
                $('#connectionDot').css("color", "red");
                $('.transfer-button').prop('title', '');
            }
            if(data.mount_exists) {
                $('#mountAvailableDot').css("color", "green");
            } else {
                $('#mountAvailableDot').css("color", "red");
                $('.transfer-button').attr('disabled', true);
                $('.transfer-button').prop('title', 'MZK disk není připojen.');
            }
        })
}

function get_active_processes() {
    fetch('/api/processes/celery/active')
        .then(res => res.json())
        .then(data => {
            console.log(data.active);
        })
}

$( document ).ready(function() {
    get_connection_status();
    setInterval(get_connection_status, 10000);
});