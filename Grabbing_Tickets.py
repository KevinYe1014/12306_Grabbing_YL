import random
import os,re
import requests
from json import loads,JSONDecodeError
from PIL import Image
import numpy as np
from Tickests_Search.Search_Tickets import search
from Tickests_Search.Login import login
from urllib import parse
import time

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

yanzhengma_pic=r'c:/users/yelei/desktop'

class BookTicket():
    def __init__(self):
        self.headers=login().headers
        self.session=login.session

    def booktickets(self):
        queryData,trainDicts=search()._Train_Search()
        print("============================开始订票==============================")
        trainIndexes=[train['trainName'] for train in trainDicts]
        while True:
            trainIndex = input("请输入定票车次：").upper()
            if trainIndex in trainIndexes:
                break
            else:
                print("请输入查询结果中列车车次！")
        # 这个地方座位类型也是不是固定的，如硬卧有时候是3，有时是A3
        print("车票类型说明：WZ：无座；F：动卧；M：一等座；O：二等座；1：硬座；3：硬卧；4：软卧；6：高级软卧；9：商务座")
        trainTicketTypes={'WZ':'无座','F':'动卧','M':'一等座','O':'二等座','1':'硬座','3':'硬卧','4':'软卧','6':'高级软卧','9':'商务座'}
        ##抢票用的字典
        trainTicketDic={}
        while True:
            seatType = str(input("请输入车票类型(格式：1/M等)："))
            if seatType in trainTicketTypes.keys():
                break
            else:
                print("请输入车票类型中格式！")
        i=0
        for trainDict in trainDicts:
            if trainIndex==trainDict['trainName'] and (trainDict[seatType] == '有' or trainDict[seatType].isdigit()) :
                print('为您选择的车次：<{0}>,车票类型：<{1}>。正在订票中……'.format(trainIndex,trainTicketTypes[seatType]))
                self.submitOrderRequest(queryData,trainDict)
                self.getPassengerDTOs(seatType,trainDict)
            elif trainIndex==trainDict['trainName'] and  trainDict[seatType]=='无':
                isGrab=str(input('需要为您抢：车次<{0}>，车票类型<{1}>的车票吗？（是请输入1，否请输入0）：'.format(trainIndex,trainTicketTypes[seatType])))
                if isGrab=='1':
                    print("抢票和买票逻辑不一样，需要您先输入用户姓名！")
                    ##获取12306账户常用联系人名字
                    url='https://kyfw.12306.cn/otn/passengers/query'
                    passengersList=[]
                    pageindex=1
                    try:
                        while True:
                            data = {'pageIndex': str(pageindex), 'pageSize': '10'}
                            res = self.session.post(url=url, data=data)
                            passengers_info = res.json()
                            passengers = [passenger['passenger_name'] for passenger in passengers_info['data']['datas']]
                            passengersList.append(passengers)
                            if pageindex==1:
                                IndexTotal = passengers_info['data']['pageTotal']
                            if pageindex==IndexTotal:
                                break
                            pageindex+=1
                    except JSONDecodeError:
                        return "读取联系联系人失败！"
                    passengersList=[x for j in passengersList for x in j]
                    print("12306账号中常用联系人姓名如下：")
                    print(passengersList)
                    user_check = False
                    while not user_check:
                        usernames = str(input('请输入抢票乘客姓名，如果多个用英文,间隔：'))
                        if ',' in usernames:
                            usernames = usernames.split(',')
                        else:
                            usernames = [usernames]
                        for user in usernames:
                            if user in passengersList:
                                if user == usernames[len(usernames) - 1]:
                                    user_check = True
                                    break
                                else:
                                    continue
                            else:
                                print("请输入有效乘客姓名！")
                    print(":::   开始抢票   :::")
                    for usename in usernames:
                        print("开始为<{}>抢票...".format(usename))
                        grab_count=1
                        while True:
                            url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={0}&leftTicketDTO.from_station={1}&leftTicketDTO.to_station={2}&purpose_codes=ADULT'.format(
                                queryData['trainDate'], queryData['fromStationCode'], queryData['toStationCode'])
                            ##抢票间隔时间
                            time.sleep(4)
                            res = self.session.get(url, verify=False).json()
                            print("<{0}>第<{1}>次抢票...".format(usename,grab_count))
                            trainDicts = self.getTrainInfo(res)
                            rows = res['data']['result']
                            list=[]
                            for i in rows:
                                list = i.split("|")
                                if trainIndex == list[3]:
                                    trainTicketDic['9'] = list[32] if list[25] == '' else list[25]
                                    trainTicketDic['M'] = list[31]
                                    trainTicketDic['O'] = list[30]

                                    trainTicketDic['4'] = list[23]
                                    trainTicketDic['F'] = list[33]
                                    trainTicketDic['3'] = list[28]

                                    # rz=list[27]
                                    trainTicketDic['1'] = list[29]
                                    trainTicketDic['WZ'] = list[26]
                            grab_count+=1
                            if trainTicketDic[seatType]=='有':
                                trainDicts_new = self.getTrainInfo(res)
                                print("Congratulation：<{}>抢到车票了!".format(usename))
                                break
                        print('开始预定车票：车次<{0}>；车票类型<{1}>...'.format(trainIndex, trainTicketTypes[seatType]))
                        self.submitOrderRequest(queryData, trainDicts_new)
                        self.GrabgetPassengerDTOs(seatType, trainDicts_new,usename)

                else:
                    continue
            else:
                i+=1
                if i>=len(trainDicts):
                    print('车次<{0}>，车票类型<{1}>没有您要预定的车票！！'.format(trainIndex,trainTicketTypes[seatType]))


    def getTrainInfo(self, result):
        trainDict = {}  # 车次信息字典
        trainDicts = []  # 用于订票
        trains = []  # 用于在terminal里打印

        results = result['data']['result']
        maps = result['data']['map']

        for item in results:
            trainInfo = item.split('|')
            # for index, item in enumerate(trainInfo, 0):
            #     print('{}:\t{}'.format(index, item)
            if trainInfo[11] == 'Y':

                trainDict['secretStr'] = trainInfo[0]

                trainDict['trainNumber'] = trainInfo[2]  # 5l0000D35273

                trainDict['trainName'] = trainInfo[3]  # 车次名称，如D352

                trainDict['fromTelecode'] = trainInfo[6]  # 出发地电报码

                trainDict['toTelecode'] = trainInfo[7]  # 出发地电报码

                trainDict['fromStation'] = maps[trainInfo[6]]  # 上海

                trainDict['toStation'] = maps[trainInfo[7]]  # 成都

                trainDict['departTime'] = (trainInfo[8])  # 出发时间

                trainDict['arriveTime'] = (trainInfo[9])  # 到达时间

                trainDict['totalTime'] = (trainInfo[10])  # 总用时

                trainDict['leftTicket'] = trainInfo[12]  # 余票

                trainDict['trainDate'] = trainInfo[13]  # 20180822

                trainDict['trainLocation'] = trainInfo[15]  # H2

                # 以下顺序貌似也不是一直固定的，我遇到过代表硬座的几天后代表其他座位了
                trainDict['9'] = trainInfo[32]  # 商务座

                trainDict['M'] = trainInfo[31]  # 一等座

                trainDict['O'] = trainInfo[30]  # 二等座

                trainDict['6'] = trainInfo[21]  # 高级软卧

                trainDict['4'] = trainInfo[23]  # 软卧

                trainDict['F'] = trainInfo[33]  # 动卧

                trainDict['WZ'] = trainInfo[26]  # 无座

                trainDict['3'] = trainInfo[28]  # 硬卧

                trainDict['1'] = trainInfo[29]  # 硬座

                trainDict['otherSeat'] = trainInfo[22]  # 其他

                # 如果值为空，则将值修改为'--',有票则有字显示为绿色，无票红色显示
                for key in trainDict.keys():
                    if trainDict[key] == '':
                        trainDict[key] = '--'
                    if trainDict[key] == '有':
                        trainDict[key] ='有'
                    if trainDict[key] == '无':
                        trainDict[key] = '无'

                # train = [
                #     Color.magenta(trainDict['trainName']) + Color.green('[ID]') if trainInfo[18] == '1' else trainDict[
                #         'trainName'],
                #     Color.green(trainDict['fromStation']) + '\n' + Color.red(trainDict['toStation']),
                #     trainDict['departTime'] + '\n' + trainDict['arriveTime'],
                #     trainDict['totalTime'], trainDict[const.businessSeat], trainDict[const.firstClassSeat],
                #     trainDict[const.secondClassSeat], trainDict[const.advancedSoftBerth], trainDict[const.softBerth],
                #     trainDict[const.moveBerth], trainDict[const.hardBerth], trainDict[const.hardSeat],
                #     trainDict[const.noSeat],
                #     trainDict['otherSeat']]

                # 直接使用append方法将字典添加到列表中，如果需要更改字典中的数据，那么列表中的内容也会发生改变，这是因为dict在Python里是object，不属于primitive
                # type（即int、float、string、None、bool)。这意味着你一般操控的是一个指向object（对象）的指针，而非object本身。下面是改善方法：使用copy()
                # trains.append(train)
                trainDicts.append(trainDict.copy())  # 注意trainDict.copy()

        # self.prettyPrint(trains, queryData)  # 按照一定格式打印
        return trainDicts


    ##下面进行订单确认，date输入需要特定格式，所以进行时间格式的转化。
    def getTrainDate(self,dateStr):
        # 返回格式 Wed Aug 22 2018 00: 00:00 GMT + 0800 (China Standard Time)
        # 转换成时间数组
        timeArray = time.strptime(dateStr, "%Y%m%d")
        # 转换成时间戳
        timestamp = time.mktime(timeArray)
        # 转换成localtime
        timeLocal = time.localtime(timestamp)
        # 转换成新的时间格式
        GMT_FORMAT = '%a %b %d %Y %H:%M:%S GMT+0800 (China Standard Time)'
        timeStr = time.strftime(GMT_FORMAT, timeLocal)
        return timeStr

    def submitOrderRequest(self,queryData,trainDict):
        data = {
            'purpose_codes': 'ADULT',
            'query_from_station_name': queryData['fromStation'],
            'query_to_station_name': queryData['toStation'],
            'secretStr': parse.unquote(trainDict['secretStr']),
            'tour_flag': 'dc',
            'train_date': queryData['trainDate'],
            'undefined': ''
        }

        url='https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest'
        dict = self.session.post(url=url, data=data,headers=self.headers).json()
        if dict['status']:
            print('系统提交订单请求成功！')
        elif dict['messages']!=[]:
            if dict['messages'][0] == '车票信息已过期，请重新查询最新车票信息':
                print('车票信息已过期，请重新查询最新车票信息！')
        else:
            print("系统提交订单请求失败！")

    def initDC(self):
        # step 1: initDc
        data = {
            '_json_att': ''
        }
        url='https://kyfw.12306.cn/otn/confirmPassenger/initDc'
        res = self.session.post(url=url, data=data,headers=self.headers)
        try:
            repeatSubmitToken = re.findall(r"var globalRepeatSubmitToken = '(.*?)'", res.text)[0]
            keyCheckIsChange = re.findall(r"key_check_isChange':'(.*?)'", res.text)[0]
            return repeatSubmitToken,keyCheckIsChange
        except:
            print('获取Token参数失败，请检查是否有订单未支付！')
            return

    def getPassengers(self):
        repeatSubmitToken, keyCheckIsChange = self.initDC()
        data = {
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': repeatSubmitToken
        }
        url = 'https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs'
        res = self.session.post(url=url, data=data, headers=self.headers)
        passengers = res.json()['data']['normal_passengers']
        usernames = [passenger['passenger_name'] for passenger in passengers]
        usernameStr = '，'.join(usernames)
        print("12306账号中的乘客姓名有如下!")
        print(usernameStr)
        user_check = False
        while not user_check:
            username = str(input('请输入抢票乘客姓名，如果多个用英文,间隔：'))
            if ',' in username:
                username = username.split(',')
            else:
                username = [username]
            for user in username:
                if user in usernames:
                    if user == username[len(username) - 1]:
                        user_check = True
                        break
                    else:
                        continue
                else:
                    print("请输入有效乘客姓名！")
        return username

    def GrabgetPassengerDTOs(self, seatType, trainDict,username):
        repeatSubmitToken, keyCheckIsChange = self.initDC()
        self.checkOrderInfo(seatType, repeatSubmitToken, username)
        # step 4:获取队列
        self.getQueueCount(seatType, repeatSubmitToken, keyCheckIsChange, trainDict, username)




    def getPassengerDTOs(self, seatType, trainDict):
        # step 1: initDc
        repeatSubmitToken, keyCheckIsChange = self.initDC()

        # step2 : getPassengerDTOs

        data = {
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': repeatSubmitToken
        }
        url='https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs'
        res = self.session.post(url=url, data=data,headers=self.headers)
        passengers = res.json()['data']['normal_passengers']
        usernames=[passenger['passenger_name'] for passenger in passengers]
        usernameStr='，'.join(usernames)
        print("12306账号中的乘客姓名有如下")
        print(usernameStr)
        user_check = False
        while not user_check:
            username = str(input('请输入定票乘客姓名，如果多个用英文,间隔：'))
            if ',' in username:
                username = username.split(',')
            else:
                username = [username]
            for user in username:
                if user in usernames:
                    if user == username[len(username) - 1]:
                        user_check = True
                        break
                    else:
                        continue
                else:
                    print("请输入有效乘客姓名！")



        for passenger in passengers:
            if passenger['passenger_name'] in username:
                print("*** 正在给<{}>定票".format(passenger['passenger_name']))
                # step 3: Check order
                self.checkOrderInfo(seatType, repeatSubmitToken, passenger)
                # step 4:获取队列
                self.getQueueCount(seatType, repeatSubmitToken, keyCheckIsChange, trainDict, passenger)
                return
            else:
                print('无法购票')

    def GetBuyImage(self):
        url = 'https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=passenger&rand=randp&{}'.format(
            random.random())
        response = self.session.get(url=url, headers=self.headers,  verify=False)
        path = os.path.abspath('..')
        with open(os.path.join(yanzhengma_pic,'img2.jpg'), 'wb') as f:
            f.write(response.content)


    def checkOrderInfo(self, seatType, repeatSubmitToken, passenger):

        passengerTicketStr = '{},{},{},{},{},{},{},N'.format(seatType, passenger['passenger_flag'],
                                                             passenger['passenger_type'],
                                                             passenger['passenger_name'],
                                                             passenger['passenger_id_type_code'],
                                                             passenger['passenger_id_no'],
                                                             passenger['mobile_no'])

        oldPassengerStr = '{},{},{},1_'.format(passenger['passenger_name'], passenger['passenger_id_type_code'],
                                               passenger['passenger_id_no'])
        data = {
            '_json_att': '',
            'bed_level_order_num': '000000000000000000000000000000',
            'cancel_flag': '2',
            'oldPassengerStr': oldPassengerStr,
            'passengerTicketStr': passengerTicketStr,
            'randCode': '',
            'REPEAT_SUBMIT_TOKEN': repeatSubmitToken,
            'tour_flag': 'dc',
            'whatsSelect': '1'
        }
        url='https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo'

        res = self.session.post(url=url, data=data,headers=self.headers)
        dict = res.json()
        if dict['data']['submitStatus']:
            print('系统校验订单信息成功')
            ##下面条件一般是N 除非抢票，购票紧张时才会出现。虽然能取出验证码图片，但是目前不知道该怎么处理
            if dict['data']['ifShowPassCode'] == 'Y':
                print('需要再次验证码验证')
                return True
            if dict['data']['ifShowPassCode'] == 'N':
                return False
        else:
            print('系统校验订单信息失败')
            return False


    def getQueueCount(self, seatType, repeatSubmitToken, keyCheckIsChange, trainDict, passenger):

        data = {
            '_json_att': '',
            'fromStationTelecode': trainDict['fromTelecode'],
            'leftTicket': trainDict['leftTicket'],
            'purpose_codes': '00',
            'REPEAT_SUBMIT_TOKEN': repeatSubmitToken,
            'seatType': seatType,
            'stationTrainCode': trainDict['trainName'],
            'toStationTelecode': trainDict['toTelecode'],
            'train_date': self.getTrainDate(trainDict['trainDate']),
            'train_location': trainDict['trainLocation'],
            'train_no': trainDict['trainNumber'],
        }
        url='https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount'


        # res = self.session.post(url=url, data=data,headers=self.headers)
        while True:
            time.sleep(2)
            res = self.session.post(url=url, data=data, headers=self.headers)
            if res.json()['status']:
                print('系统获取队列信息成功')
                self.confirmSingleForQueue(seatType, repeatSubmitToken, keyCheckIsChange, passenger, trainDict)
                break
            else:
                print('系统获取队列信息失败,重新获取...')



    def SendMail(self,message):
        my_sender='2439745857@qq.com'
        my_pass='pzypjfblmmjdjba'
        my_receiver='2439745857@qq.com'

        subject='12306抢票成功通知'
        msg=MIMEText(message,'plain','utf-8')
        msg['Subject']=subject
        msg['From']=formataddr(['FromQQEmail',my_sender])
        msg['To']=formataddr(['ToQQEmail',my_receiver])
        try:
            server=smtplib.SMTP_SSL('smtp.qq.com','465')
            server.login(my_sender,my_pass)
            server.sendmail(my_sender,[my_receiver,],msg.as_string())
            print("邮件发送成功！")
        except:
            print("邮件发送失败！")
        finally:
            server.quit()



    def confirmSingleForQueue(self, seatType, repeatSubmitToken, keyCheckIsChange, passenger, trainDict):

        passengerTicketStr = '{},{},{},{},{},{},{},N'.format(seatType, passenger['passenger_flag'],
                                                             passenger['passenger_type'],
                                                             passenger['passenger_name'],
                                                             passenger['passenger_id_type_code'],
                                                             passenger['passenger_id_no'],
                                                             passenger['mobile_no'])
        oldPassengerStr = '{},{},{},1_'.format(passenger['passenger_name'], passenger['passenger_id_type_code'],
                                               passenger['passenger_id_no'])
        data = {
            'passengerTicketStr': passengerTicketStr,
            'oldPassengerStr': oldPassengerStr,
            'randCode': '',
            'purpose_codes': '00',
            'key_check_isChange': keyCheckIsChange,
            'leftTicketStr': trainDict['leftTicket'],
            'train_location': trainDict['trainLocation'],
            'choose_seats': '',
            'seatDetailType': '000',
            'whatsSelect': '1',
            'roomType': '00',
            'dwAll': 'N',
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': repeatSubmitToken,
        }

        url='https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue'

        res = login.session.post(url=url, data=data,headers=self.headers)
        if res.json()['data']['submitStatus'] == 'true':
            print('<{}>已完成订票，请前往12306进行支付'.format(passenger['passenger_name']))
            self.SendMail("抢票或订票成功啦，赶快前往12306网站登录支付！！！")
        else:
            print('<{}>订票失败,请稍后重试!'.format(passenger['passenger_name']))




if __name__=='__main__':
    bt=BookTicket()
    bt.booktickets()