from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

# [수정] 클래스 이름을 AddApiKeyForm으로 변경


class AddApiKeyForm(FlaskForm):
    youtube_api_key = StringField('새 YouTube API 키',
                                  validators=[DataRequired(), Length(min=39, max=39, message='올바른 형식의 API 키를 입력해주세요.')])
    submit = SubmitField('새 키 추가')
class AddAdminApiKeyForm(FlaskForm):
    admin_api_key = StringField('새 공용 API 키',
                                validators=[DataRequired(), Length(min=39, max=39, message='올바른 형식의 API 키를 입력해주세요.')])
    submit = SubmitField('공용 키 추가')