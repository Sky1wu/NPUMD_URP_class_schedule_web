import requests
import random
import base64
from PIL import Image
from io import BytesIO
import base64
import pytesseract


def getCaptcha(session):
    for i in range(10):
        captcha_url = 'http://urp.npumd.cn/validateCodeAction.do'

        captcha_data = {
            'random': random.random()
        }

        response = session.get(captcha_url, params=captcha_data)

        im = Image.open(BytesIO(response.content))
        w, h = im.size
        im = im.resize((w*2, h*2))
        gray = im.convert('L')  # 灰度处理

        threshold = 150
        table = []
        for i in range(256):
            if i < threshold:
                table.append(0)
            else:
                table.append(1)
        out = gray.point(table, '1')

        code = pytesseract.image_to_string(out)

        code = filter(str.isalnum, code)
        code = ''.join(list(code))

        if len(code) == 4:
            break

    return code
