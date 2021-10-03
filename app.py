import os

from flask import Flask, render_template, send_file, redirect, url_for, request, flash, session, abort, after_this_request, make_response
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
        user_file = form.file.data
        user_file_name = secure_filename(user_file.filename)
        session['inputed_xl_file_name'] = user_file_name

        if user_file_name == '':
            flash('Ошибка. No selected file')
            return redirect(url_for('render_index'))

        if not allowed_xl_file(user_file_name):
            flash('Ошибка. Недопустимый формат файла.\nДопустимые форматы: xls, xlsx, xlsm, xlsb.')
            return redirect(url_for('render_index'))            

        user_file.save(os.path.join(app.config['UPLOAD_FOLDER'], user_file_name))
        session['EXCEL_FILE_RECIEVED'] = True
        flash("Файл успешно загружен. Можно получить прогноз.")
        return redirect(url_for('render_index'))

    return render_template("index.html", form=form, session=session)


@app.route('/create_report')
def create_report():
    excel_file_recieved = session.get('EXCEL_FILE_RECIEVED')
    forecast_started = session.get('FORECAST_STARTED')
    if excel_file_recieved and not forecast_started:
        session['FORECAST_STARTED'] = True
        users_filename = os.path.join(
            app.config['UPLOAD_FOLDER'], 
            session['inputed_xl_file_name']
        )

        try:
            get_weekly_forecast_from_xl(users_filename)
        except Exception as error:
            flash(error)
            return redirect(url_for('render_index'))

        if not session.get('report_name'):
            session.clear()
            flash("Ошибка. Неправильный Excel файл. Должен быть единственный лист, где в ячейке А1 указана шапка \"Город\", в ячейках А2 и ниже указаны сами города.")
            return redirect(url_for('render_index'))

        forecast_file_name = os.path.join(
                app.config['UPLOAD_FOLDER'], 
                session['report_name']
            )
        session.clear()
        try:
            return send_file(forecast_file_name)

        except FileNotFoundError:
            abort(404)
        
    elif excel_file_recieved and forecast_started:
        flash("Прогноз собирается, ожидайте...")
        return redirect(url_for('render_index'))

    elif not excel_file_recieved:
        flash("Ошибка. Сначала нужно загрузить excel файл с городами.")
        return redirect(url_for('render_index'))


@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect(url_for('render_index'))


if __name__ == "__main__":
    app.run()