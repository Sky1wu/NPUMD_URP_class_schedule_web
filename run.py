from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from getCaptcha import getCaptcha
from const import startTime, endTime, weekName, beginDate
from bs4 import BeautifulSoup
import requests
import re
import datetime
import os

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'npumd'


class LoginForm(FlaskForm):
    username = StringField(u'账号', validators=[
        DataRequired(message=u'账号不能为空')])
    password = PasswordField(u'密码',
                             validators=[DataRequired(message=u'密码不能为空')])
    submit = SubmitField(u'登录')


@app.route('/', methods=['POST', 'GET'])
def index():
    dirpath = app.root_path+'/download/'
    if(os.path.exists(dirpath)):
        count = len(os.listdir(dirpath))

    session = requests.session()

    form = LoginForm()
    # captcha_img = getChaptcha(session)

    if form.validate_on_submit():
        flag = False
        for _ in range(5):
            username = form.username.data
            password = form.password.data

            login_url = 'http://urp.npumd.cn/loginAction.do'

            post_data = {
                'zjh': username,
                'mm': password,
                'v_yzm': getCaptcha(session)
            }

            session.post(login_url, data=post_data)

            outline_url = 'http://urp.npumd.cn/outlineAction.do'

            outline_res = session.get(outline_url)

            if(outline_res.status_code == 200):
                flag = True

                VCALENDAR = '''BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:%(username)s 课程表
X-WR-TIMEZONE:Asia/Shanghai
X-WR-CALDESC:%(username)s 课程表
BEGIN:VTIMEZONE
TZID:Asia/Shanghai
X-LIC-LOCATION:Asia/Shanghai
BEGIN:STANDARD
TZOFFSETFROM:+0800
TZOFFSETTO:+0800
TZNAME:CST
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE
''' % {'username': form.username.data}

                table_url = 'http://urp.npumd.cn/xkAction.do'

                data = {
                    'actionType': 6
                }
                tablePage = session.get(
                    table_url, params=data).content.decode("gb2312")

                soup = BeautifulSoup(tablePage, 'lxml')

                classes = soup.find_all('tr', class_='odd')

                if not os.path.exists(dirpath):
                    os.makedirs(dirpath)

                filepath = dirpath+form.username.data+'.ics'

                file = open(filepath, 'w')
                file.write(VCALENDAR)
                for Class in classes:
                    VEVENT = ''

                    Class = Class.find_all('td')
                    if len(Class) == 18:
                        className = Class[2].text.strip()  # 课程名
                        classWeekTimes = Class[11].text.strip()  # 周次
                        classWeek = Class[12].text.strip()  # 星期
                        classSession = Class[13].text.strip()  # 节次
                        classAmount = Class[14].text.strip()  # 节数
                        classBuilding = Class[16].text.strip()  # 教学楼
                        classRoom = Class[17].text.strip()  # 教室
                    elif len(Class) == 7:
                        classWeekTimes = Class[0].text.strip()  # 周次
                        classWeek = Class[1].text.strip()  # 星期
                        classSession = Class[2].text.strip()  # 节次
                        classAmount = Class[3].text.strip()  # 节数
                        classBuilding = Class[5].text.strip()  # 教学楼
                        classRoom = Class[6].text.strip()  # 教室

                    # print(className, classWeekTimes, classWeek, classSession, classAmount, classBuilding, classRoom)

                    VEVENT += 'BEGIN:VEVENT\n'
                    WeekTimes = re.findall(r"\d+\.?\d*", classWeekTimes)
                    delta = datetime.timedelta(weeks=int(WeekTimes[0])-1)
                    delta += datetime.timedelta(days=int(classWeek)-1)
                    classStartTime = beginDate+delta
                    VEVENT += ('DTSTART;TZID=Asia/Shanghai:' +
                               classStartTime.strftime("%Y%m%dT")+startTime[int(classSession)]+'\n')
                    VEVENT += ('DTEND;TZID=Asia/Shanghai:' +
                               classStartTime.strftime("%Y%m%dT")+endTime[int(classSession)+int(classAmount)-1]+'\n')
                    if '-'in classWeekTimes:
                        VEVENT += ('RRULE:FREQ=WEEKLY;WKST=MO;COUNT=' +
                                   str(int(WeekTimes[1])-int(WeekTimes[0])+1)+';BYDAY='+weekName[int(classWeek)]+'\n')
                    else:
                        interval = int(WeekTimes[1])-int(WeekTimes[0])
                        VEVENT += ('RRULE:FREQ=WEEKLY;WKST=MO;COUNT=' +
                                   str(len(WeekTimes))+';INTERVAL='+str(interval)+';BYDAY='+weekName[int(classWeek)]+'\n')
                    VEVENT += ('LOCATION:'+classBuilding+classRoom+'\n')
                    VEVENT += ('SUMMARY:'+className+'\n')
                    VEVENT += 'END:VEVENT\n'
                    file.write(VEVENT)
                file.write('END:VCALENDAR')
                file.close()

        if flag:
            # return render_template('result.html', file='result')
            dirpath = app.root_path+'/download'
            return send_from_directory(dirpath, os.path.basename(filepath), as_attachment=True)
            # return 'yes'
        else:
            # return redirect(url_for('index'))
            return '登录失败'

    return render_template('index.html', form=form, count=count)


@app.route('/result/?<path:filename>')
def result(filename):
    # dirpath = os.path.join(app.root_path, '/')
    dirpath = app.root_path
    return send_from_directory(dirpath, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
