from flask import jsonify, request
from ..dataMover.DataMover import DataMover
from . import api
import os


@api.route('/mzk/connection', methods=['GET'])
def get_mzk_connection():
    '''
    Checks connection of Moravian Library
    '''
    conn_exists, msg = DataMover.check_connection()
    mount_exists = DataMover.check_mount()
    return jsonify({"connection": conn_exists, "message": msg, "mount_exists": mount_exists})


@api.route('/mzk/dst-folders/', methods=['GET'])
def get_mzk_dst_folders():
    '''
    Gets folders from MZK disk in given Path. The top level is /MUO
    '''
    path = request.args.get("path")
    if path.endswith('..'):
        path = os.path.abspath(os.path.join(path, os.pardir))
    if path == '/':
        path = "/MUO"
    result = []
    i = 0
    for foldername in DataMover.get_mzk_folders(path):
        if foldername not in [u'.']:
            dict = {}
            dict['id'] = "folder" + str(i)
            dict['text'] = foldername
            dict['icon'] = 'jstree-folder'
            result.append(dict)
            i += 1
    response = {"current_folder": path ,"folders": result}
    return jsonify(response)