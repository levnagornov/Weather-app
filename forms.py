from wtforms import SubmitField
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired


class FileForm(FlaskForm):
    """Form for getting a file"""

    file = FileField(validators=[FileRequired()])
    submit = SubmitField("Загрузить Excel файл")