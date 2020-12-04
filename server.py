import os
import datetime
import pprint

from flask import Flask, request

from config import *

app_option = {
    'static_folder': WIKI_FOLDER,
}

app_run_option = {
    'debug': DEBUG_MODE,
    'host': LISTEN_ADDR,
    'port': LISTEN_PORT,
}

app = Flask(__name__, **app_option)

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file(FAVICON_FILE)

@app.route('/', methods=['GET'])
def show_wiki():
    if AUTH_ENABLE:
        auth = request.authorization
        if not auth or auth.username != USERNAME or auth.password != PASSWORD:
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'
            })
    return app.send_static_file(WIKI_FILENAME)
    pass


@app.route('/save', methods=['POST'])
def save_wiki():
    # parse request data
    data_str: str = request.form['UploadPlugin']
    data_list = data_str.split(';')
    data = {}
    for _ in data_list:
        idx = _.find('=')
        if idx != -1:
            data[_[:idx]] = _[idx + 1:]
        pass

    if 'user' not in data or 'password' not in data or data['user'] != USERNAME or data['password'] != PASSWORD:
        return 'ERROR: username or password do not match'

    # handle folder
    upload_folder = WIKI_FOLDER
    backup_folder = BACKUP_FOLDER

    if USE_REQUEST_DIR:
        if 'uploaddir' in data:
            upload_folder = data['uploaddir']
        if 'backupDir' in data:
            backup_folder = data['backupDir']

    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), upload_folder)
    backup_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), backup_folder)

    if os.path.exists(upload_folder):
        if not os.path.isdir(upload_folder):
            return 'ERROR: upload dir invalid, not a dir'
        if not os.access(upload_folder, os.W_OK):
            return 'ERROR: upload dir invalid, not writable'
    else:
        os.mkdir(upload_folder)
        if not os.path.exists(upload_folder):
            return 'ERROR: upload dir invalid, failed to create dir'
        pass

    if os.path.exists(backup_folder):
        if not os.path.isdir(backup_folder):
            return 'ERROR: backup dir invalid, not a dir'
        if not os.access(backup_folder, os.W_OK):
            return 'ERROR: backup dir invalid, not writable'
    else:
        os.mkdir(backup_folder)
        if not os.path.exists(backup_folder):
            return 'ERROR: backup dir invalid, failed to create dir'
        pass

    # backup file
    current_filepath = os.path.join(upload_folder, WIKI_FILENAME)
    if DO_BACKUP:
        current_filename = WIKI_FILENAME.rsplit('.', 1)
        backup_time_string = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = '{}_{}'.format(current_filename[0], backup_time_string)
        if len(current_filename) > 1:
            # append extension name
            backup_filename += '.' + current_filename[1]
        backup_filepath = os.path.join(backup_folder, backup_filename)

        if os.path.exists(current_filepath):
            os.rename(current_filepath, backup_filepath)
        pass

    backup_files = [os.path.join(backup_folder, f) for f in os.listdir(backup_folder) if
                    os.path.isfile(os.path.join(backup_folder, f))]
    delete_number = len(backup_files) - BACKUP_FILE_LIMIT
    if delete_number > 0:
        backup_files_by_date = []
        for file in backup_files:
            backup_files_by_date.append((os.path.getmtime(file), file))
        backup_files_by_date.sort(key=lambda x: x[0])

        # sort by time stamp ascending, delete files in the first
        files_to_delete = [_[1] for _ in backup_files_by_date[:delete_number]]
        for _ in files_to_delete:
            try:
                os.remove(_)
            except:
                pass
        pass

    # handle upload
    if 'userfile' not in request.files:
        return 'ERROR: no uploaded file'
    request.files['userfile'].save(current_filepath)
    return ''
    pass


@app.errorhandler(Exception)
def all_error_handler(e):
    return 'ERROR: unhandled error {}'.format(str(e))


if __name__ == '__main__':
    app.run(**app_run_option)
    pass
