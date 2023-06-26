from flask import jsonify, request
from flask import current_app as app
import subprocess
from . import api


@api.route('/speedtest')
def disk_speed():
    try:
        # Replace '/mnt/nfs' with your actual NFS mount path
        cmd = 'dd if=/dev/zero of=/mnt/MZK/MUO/test_tran/testfile bs=1M count=50 conv=fdatasync'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            output = result.stderr
        except Exception as e:
            print(e)
        # Parse the output to extract the transfer speed
        for line in output.splitlines():
            print(line)
            if 'MB/s' in line:
                speed_line = line.strip()
                break
        else:
            return jsonify(error='Failed to retrieve NFS transfer speed.')

        delete_cmd = 'rm /mnt/MZK/MUO/test_tran/testfile'
        result = subprocess.run(delete_cmd, shell=True, capture_output=True, text=True, check=True)
        speed = speed_line.split()[-2]
        return jsonify(speed=speed)

    except Exception as e:
        return jsonify(error=str(e))