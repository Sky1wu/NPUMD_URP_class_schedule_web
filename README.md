# NPUMD_URP_classs_schedule_web

[NPUMD_URP_classs_schedule](https://github.com/Sky1wu/NPUMD_URP_classs_schedule) 的 Web 版本。

![效果图](https://i.loli.net/2019/11/23/Zg76kDsXiWajOcz.png)

## Demo

[课程表](https://npumd.online)

## 简介

根据西北工业大学明德学院 URP 教务系统的选课结果生成 ics 日历。

## 功能

OCR 识别教务系统验证码自动登录，抓取选课结果页面信息并生成包含课程信息的 ics 文件，可导入手机、电脑等日历应用中快捷查看课表。

## 安装

请在 Python3 环境下运行。

识别验证码需要 [Tesseract](https://github.com/tesseract-ocr/tesseract)

`yum install tesseract`

创建并进入虚拟环境

`python3 -m venv venv`

`source venv/bin/activate`

安装模块

`pip install -r requirements.txt`

## 配置

`cp config.ini.example config.ini`

`vim config.ini`

`startDate` 为本学期第一周周一的日期。

`url` 为本校的教务系统地址，默认为「西北工业大学明德学院」的教务系统，理论上支持所有采用 `1.5_0` 版「URP 综合教务系统」的学校，但未经实验，如有需要请修改相关信息自行测试。

`time` 中的上课时间，如有变动可修改对应时间。

## 运行

`pip install gunicorn`

`gunicorn -w 4 run:app`
