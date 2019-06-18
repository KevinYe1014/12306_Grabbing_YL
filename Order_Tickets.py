
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
            else:
                i+=1
                if i>=len(trainDicts):
                    print('车次<{0}>，车票类型<{1}>没有余票！'.format(trainIndex,trainTicketTypes[seatType]))

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
            if dict['data']['ifShowPassCode'] == 'Y':
                print('需要再次验证')
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
        else:
            print('<{}>订票失败,请稍后重试!'.format(passenger['passenger_name']))




if __name__=='__main__':
    bt=BookTicket()
    bt.booktickets()