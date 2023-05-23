$( document ).ready(function() {
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
                if(data.mount_exists) {
                    $('#mountAvailableDot').css("color", "green");
                } else {
                    $('#mountAvailableDot').css("color", "red");
                }
            })
    }
    
    get_connection_status();
    setInterval(get_connection_status, 10000);
});