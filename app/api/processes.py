from flask import jsonify, request, g, url_for, current_app
from .. import db, socketIo
from ..models import ProcessDb
from . import api


@api.route('/processes/')
def get_processes():
    procs = ProcessDb.query.paginate()


@api.route('/processes/<int:id>/')
def get_process_api(id):
    proc = ProcessDb.query.get_or_404(id)
    return jsonify(proc.to_json())


@api.route('/processes/folders/<int:id>/')
def get_process_folders(id):
    proc = ProcessDb.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = proc.folders.paginate(page=page, per_page=25, error_out=False)
    folders = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_process_folders', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_process_folders', id=id, page=page+1)
    return jsonify({
        'folders': [folder.to_json() for folder in folders],
        'page': page,
        'prev': prev,
        'next': next,
        'count': pagination.total
    })