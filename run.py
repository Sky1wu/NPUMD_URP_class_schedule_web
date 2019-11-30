from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, Response
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from getCaptcha import getCaptcha
from bs4 import BeautifulSoup
import requests
import re
import datetime
import os
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = config['Flask'].get('SECRET_KEY')

url = config['URP'].get('url')
startYear = config['startDate'].getint('year')
startMonth = config['startDate'].getint('month')
startDay = config['startDate'].getint('day')
beginDate = datetime.date(startYear, startMonth, startDay)

startTime = [None]
startTime.extend(config['time'].get('startTime').replace(' ', '').split(','))

endTime = [None]
endTime.extend(config['time'].get('endTime').replace(' ', '').split(','))

weekName = [None]
weekName.extend(config['time'].get('weekName').replace(' ', '').split(','))


class LoginForm(FlaskForm):
    username = StringField(u'账号', validators=[
        DataRequired(message=u'账号不能为空')])
    password = PasswordField(u'密码',
                             validators=[DataRequired(message=u'密码不能为空')])
    submit = SubmitField(u'获取课程表')


@app.route('/.well-known/acme-challenge/<filename>')
def well_known(filename):
    return render_template('.well-known/acme-challenge/' + filename)


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

            login_url = url+'loginAction.do'

            post_data = {
                'zjh': username,
                'mm': password,
                'v_yzm': getCaptcha(session)
            }

            session.post(login_url, data=post_data)

            outline_url = url+'outlineAction.do'

            outline_res = session.get(outline_url)

            if(outline_res.status_code == 200):
                flag = True

                file = open('template.ics', 'r')
                VCALENDAR = file.read().format(username=username)
                file.close()

                table_url = url+'xkAction.do'

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
                    # 周次
                    WeekTimes = re.findall(r"\d+\.?\d*", classWeekTimes)
                    # 开始周
                    delta = datetime.timedelta(weeks=int(WeekTimes[0])-1)
                    # 开始星期
                    delta += datetime.timedelta(days=int(classWeek)-1)
                    classStartTime = beginDate+delta
                    # 开始日期
                    classStartDate = beginDate+delta
                    # 开始时间
                    classStartTime = datetime.datetime.strptime(
                        startTime[int(classSession)], '%H:%M').time()
                    # 结束时间
                    classEndTime = datetime.datetime.strptime(
                        endTime[int(classSession)+int(classAmount)-1], '%H:%M').time()
                    # 最终开始时间
                    classStartDateTime = datetime.datetime.combine(
                        classStartDate, classStartTime)
                    # 最终结束时间
                    classEndDateTime = datetime.datetime.combine(
                        classStartDate, classEndTime)
                    # 写入开始时间
                    VEVENT += 'DTSTART;TZID=Asia/Shanghai:{classStartDateTime}\n'.format(classStartDateTime=classStartDateTime.strftime(
                        '%Y%m%dT%H%M%S'))
                    # 写入结束时间
                    VEVENT += 'DTEND;TZID=Asia/Shanghai:{classEndDateTime}\n'.format(classEndDateTime=classEndDateTime.strftime(
                        '%Y%m%dT%H%M%S'))

                    # 设置循环
                    if '-'in classWeekTimes:
                        VEVENT += 'RRULE:FREQ=WEEKLY;WKST=MO;COUNT={count};BYDAY={byday}\n'.format(count=str(
                            int(WeekTimes[1])-int(WeekTimes[0])+1), byday=weekName[int(classWeek)])
                    else:
                        interval = int(WeekTimes[1])-int(WeekTimes[0])
                        VEVENT += 'RRULE:FREQ=WEEKLY;WKST=MO;COUNT={count};INTERVAL={interval};BYDAY={byday}\n'.format(
                            count=str(len(WeekTimes)), interval=str(interval), byday=weekName[int(classWeek)])

                    # 地点
                    VEVENT += ('LOCATION:'+classBuilding+classRoom+'\n')
                    # 名称
                    VEVENT += ('SUMMARY:'+className+'\n')
                    VEVENT += 'END:VEVENT\n'
                    file.write(VEVENT)
                file.write('END:VCALENDAR')
                file.close()

        if flag:
            dirpath = app.root_path+'/download'
            return send_from_directory(dirpath, os.path.basename(filepath), as_attachment=True)
        else:
            return '登录失败'

    return render_template('index.html', form=form, count=count)


@app.route('/result/?<path:filename>')
def result(filename):
    dirpath = app.root_path
    return send_from_directory(dirpath, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=config['debug'].getboolean('debug'))
