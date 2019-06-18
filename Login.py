
import random
import os,time
import requests
from json import loads,JSONDecodeError
import cv2
from PIL import Image
import numpy as np

yanzhengma_pic=r'c:/users/yelei/desktop'

def cv_imread(file_path):
    cv_img=cv2.imdecode(np.fromfile(file_path,dtype=np.uint8),1)
    return cv_img
def cv_imwrite(filename,src):
    cv2.imencode('.jpg',src)[1].tofile(filename)

class login():
    session=requests.session()
    def __init__(self):
        self.account='nanhuaqiushui123'
        self.password='xiaoye66'

        self.session=login.session

        self.headers = {
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://kyfw.12306.cn',
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://kyfw.12306.cn/otn/login/init',
        }

    ## 获取验证码
    def get_img(self):
        url = "https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand&{}".format \
            (random.random())
        response = self.session.get(url=url, headers=self.headers)
        # path = os.path.abspath('..')
        with open(os.path.join(yanzhengma_pic, "img.jpg"), 'wb') as f:
            f.write(response.content)
        # img=cv_imread(os.path.join(yanzhengma_pic, "img.jpg"))
        # cv2.imshow('img',img)
        # cv2.waitKey(0)
        img=Image.open(os.path.join(yanzhengma_pic, "img.jpg"))
        img.show()
        img.close()



    ##验证码逻辑
    def verify(self, clickList,login_answer):
        url = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
        code = ['45,45', '125,45', '180,45', '255,45', '45,120', '120,120', '180,120', '255,120']
        verifyList = []
        for a in clickList:
            verifyList.append(code[int(a)])
        codeList = ','.join(verifyList)
        data = {
            'answer': codeList,
            'rand': 'sjrand',
            'login_site': 'E',

        }
        login_answer[0]=codeList
        response = self.session.post(url=url, data=data, headers=self.headers)
        try:
            dic = loads(response.content.decode())
        except:
            return "NetWorkError"
        resultCode = dic['result_code']
        resultMsg = dic['result_message']
        self.verifyInfo = resultMsg
        print(resultMsg)
        return resultCode

        # if str(resultCode) == "4":



    ##登录逻辑  上面验证码返回是4  才可以走登录逻辑
    def loging(self):
        print('==========================开始登陆12306账号=========================')
        url="https://kyfw.12306.cn/otn/login/init"
        self.session.get(url=url,headers=self.headers)
        ##验证码验证正确才能登陆
        check=False
        login_answer=[0]
        while not check:
            self.get_img()
            yanzhengma_code = input("请输入验证码（多个请用英文字符','间隔）：")
            yanzhengma_code_list = yanzhengma_code.split(',')
            return_code=self.verify(yanzhengma_code_list,login_answer)
            if return_code=='4':
                break

        url = 'https://kyfw.12306.cn/passport/web/login' ##answer必须要
        data = {
            'username': self.account,
            'password': self.password,
            'appid': 'otn',
            'answer':login_answer[0],
        }
        time.sleep(2)
        login_check=False
        while not login_check:
            response = self.session.post(url=url, data=data, headers=self.headers)
            try:
                dic = loads(response.content)
                login_check=True
            except JSONDecodeError:
                login_check=False


        resultCode = dic['result_code']
        resultMsg = dic['result_message']
        self.loginInfo = resultMsg
        ##登录三部曲 第二步和第三步都是影藏的
        if resultCode == 0:
            uamtk_url = 'https://kyfw.12306.cn/passport/web/auth/uamtk'
            form_data = {'appid': 'otn'}
            uamtk_response = self.session.post(uamtk_url, data=form_data)
            if uamtk_response.json()["result_code"] == 0:
                uamauthclient_url = 'https://kyfw.12306.cn/otn/uamauthclient'
                form_data = {'tk': uamtk_response.json()["newapptk"]}
                uamauthclient_response = self.session.post(uamauthclient_url, data=form_data)
                # print(uamauthclient_response.json())
            else:
                print("权限token获取失败")
            print(resultMsg)
        else:
            print(resultMsg)

if __name__=='__main__':
    t_b=login()
    t_b.loging()

