import os

from flask import Flask, render_template, send_file, redirect, url_for, request, flash, session, abort
from flask_wtf.csrf import CSRFProtect

from werkzeug.utils import secure_filename

from config import Config
from forms import FileForm
from utils import allowed_xl_file, get_weekly_forecast_from_xl


app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = os.path.dirname(os.path.realpath(__file__))
csrf = CSRFProtect(app)  

@app.route('/', methods=['GET', 'POST'])
def render_index():
    
    statuses = (
        'EXCEL_FILE_RECIEVED',
        'FORECAST_STARTED',
        'FORECAST_READY',

    )
    for status in statuses:
        if not session.get(status):
            session[status] = False

    form = FileForm()

    if request.method == "POST" and form.validate_on_submit():
        print("Файл получен")
        user_file = form.file.data
        filename = secure_filename(user_file.filename)
        session['inputed_xl_file_name'] = filename
        print(user_file, filename)
        
        if filename == '':
            flash('No selected file')
            print("Файл пустой.")
            return redirect(url_for('render_index'))

        if not allowed_xl_file(filename):
            flash('Недопустимый формат файла.\nДопустимые форматы: xls, xlsx, xlsm, xlsb.')
            print("Неверный формат файла")
            return redirect(url_for('render_index'))            

        print("Сохранение файла")
        user_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print("Файл сохранен")

        session['EXCEL_FILE_RECIEVED'] = True
        flash("Файл успешно загружен. Можно запускать прогноз.")
        
        return redirect(url_for('render_index'))

    return render_template("index.html", form=form, session=session)


@app.route('/create_report')
def create_report():
    if session['EXCEL_FILE_RECIEVED'] and not session['FORECAST_STARTED']:
        
        #do()
        users_filename = os.path.join(app.config['UPLOAD_FOLDER'], session['inputed_xl_file_name'])
        get_weekly_forecast_from_xl(users_filename)
        flash("Прогноз получен и готов к скачиванию.")
        return redirect(url_for('render_index'))
        
    elif session['EXCEL_FILE_RECIEVED'] and session['FORECAST_STARTED']:
        flash("Прогноз уже запущен, ожидайте...")
        return redirect(url_for('render_index'))

    elif not session['EXCEL_FILE_RECIEVED']:
        flash("Сначала нужно загрузить excel файл с городами.")
        return redirect(url_for('render_index'))


@app.route('/download_report')
def download_report():
    if session['FORECAST_READY']:
        try:
            file_name = os.path.join(app.config['UPLOAD_FOLDER'], session['report_name'])
            print(file_name)
            return send_file(file_name)
        except FileNotFoundError:
            abort(404)

    elif session['EXCEL_FILE_RECIEVED'] and session['FORECAST_STARTED'] and not session['FORECAST_READY']:
        flash("Еще не готов.")
        return redirect(url_for('render_index'))

    elif not session['FORECAST_STARTED']:
        flash("Сначала запустите прогноз.")
        return redirect(url_for('render_index'))

    return redirect(url_for('render_index'))


if __name__ == "__main__":
    app.run()