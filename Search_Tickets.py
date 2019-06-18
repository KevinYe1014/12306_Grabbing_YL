
import requests
from docopt import docopt
from prettytable import PrettyTable
from time import sleep
import re
import time,datetime
from Tickests_Search.Login import login
from json import JSONDecodeError

class search():
    def __init__(self):
        self.session=login.session

    def get_station_code(self):
        url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9098'
        requests.packages.urllib3.disable_warnings()
        text = self.session.get(url, verify=False).text
        inf = text[:-2].split('@')[1:]

        stations = {}
        stations_research = {}
        for record in inf:
            rlist = record.split("|")
            stations[int(rlist[-1])] = {"name": rlist[1], "search": rlist[2], "fullname": rlist[3],
                                        "firstname": rlist[4]}
            stations_research[rlist[1]] = rlist[2]
        return stations_research

    def Price_Checi_Type(self,checi, checitype, pricedata):
        if checi == '' or checi == '-':
            return '-'
        elif pricedata=={}:
            return checi
        elif checitype not in pricedata.keys():
            return checi
        elif '/' in checi:
            return str(checi.split('/')[0])
        else:
            return '{0}/{1}'.format(checi, pricedata[checitype])

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
            if trainInfo[11] == 'Y' or True:

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

                trainDicts.append(trainDict.copy())  # 注意trainDict.copy()

        # self.prettyPrint(trains, queryData)  # 按照一定格式打印
        return trainDicts


    def decode(self,rows, stations_research, decode_str):
        result = []
        checi_type = []
        '''
        -g          高铁
        -d          动车
        -t          特快
        -k          快速
        -z          直达
        '''
        for char in decode_str:
            if char in 'gdtkz':
                checi_type.append(char)

        time_sleep_index=0

        for i in rows:
            list = i.split("|")
            checi = list[3]
            chufa = [k for k, v in stations_research.items() if v == list[6]][0]
            mudi = [k for k, v in stations_research.items() if v == list[7]][0]
            ftime = list[8]
            dtime = list[9]
            _time = list[10]

            sw = list[32] if list[25] == '' else list[25]
            yd = list[31]
            ed = list[30]

            rw = list[23]
            dw = list[33]
            yw = list[28]

            # rz=list[27]
            yz = list[29]
            wuzuo = list[26]

            if checi[0] in checi_type or len(checi_type) == 0:
                if time_sleep_index==3:
                    time.sleep(3)
                    time_sleep_index=0
                time_sleep_index+=1

                # region 票价信息
                train_no = list[2]
                from_station_no = list[16]
                to_station_no = list[17]
                seat_types = list[35]
                train_date = '{0}-{1}-{2}'.format(list[13][:4], list[13][4:6], list[13][6:])
                url = 'https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?train_no={0}&from_station_no={1}&to_station_no={2}&seat_types={3}&train_date={4}'. \
                    format(train_no, from_station_no, to_station_no, seat_types, train_date)
                sleep(0.1)

                try:
                    _pricedata = self.session.get(url)
                    _pricedata.encoding = 'utf-8'
                    pricedata = _pricedata.json()['data']
                except JSONDecodeError:
                    print('读取<{}>车次票价失败...'.format(checi))

                _sw = self.Price_Checi_Type(sw, 'A9', pricedata)
                _sw = self.Price_Checi_Type(_sw, 'P', pricedata)
                _yd = self.Price_Checi_Type(yd, 'M', pricedata)
                _ed = self.Price_Checi_Type(ed, 'O', pricedata)

                _rw = self.Price_Checi_Type(rw, 'A4', pricedata)
                _dw = self.Price_Checi_Type(dw, 'F', pricedata)
                _yw = self.Price_Checi_Type(yw, 'A3', pricedata)

                _yz = self.Price_Checi_Type(yz, 'A1', pricedata)
                _wuzuo = self.Price_Checi_Type(wuzuo, 'WZ', pricedata)
                pricedata={}

                result.append((checi, chufa, mudi, ftime, dtime, _time, _sw, _yd, _ed, _rw, _dw, _yw, _yz, _wuzuo))
        return result

    def get_color(self,_str, color_num):
        return "\033[{};".format(str(color_num)) + "0m" + _str + "\033[0m"

    def pretty_table(self,results):
        table = PrettyTable(
            ["车次", "出发站", "目的站", "发车时间", "到达时间", "历时", "商务座", "一等座", "二等座", "软卧", "动卧", "硬卧", "硬座", "无座"])
        color_num = 31
        train_count = 1
        for i in results:
            table.add_row([self.get_color(i[0], color_num), self.get_color(i[1], color_num), self.get_color(i[2], color_num),
                           self.get_color(i[3], color_num), self.get_color(i[4], color_num),
                           self.get_color(i[5], color_num), self.get_color(i[6], color_num), self.get_color(i[7], color_num),
                           self.get_color(i[8], color_num), self.get_color(i[9], color_num),
                           self.get_color(i[10], color_num), self.get_color(i[11], color_num), self.get_color(i[12], color_num),
                           self.get_color(i[13], color_num)])
            color_num += 1
            train_count += 1
            if color_num > 36:
                color_num = 31
        print(table)
        print("共查询到列车次数：{}".format(str(train_count - 1)))




    def _Train_Search(self):
        """command-line interface"""
        login().loging()

        print("===========================开始查询车票===========================")
        # arguments = docopt(__doc__)

        stations_research = self.get_station_code()

        # from_station = stations_research.get(arguments['<from>'])
        # to_station = stations_research.get(arguments['<to>'])
        # date = arguments['<date>']

        # from_station_name=input("请输入查询车(格式：北京)：")
        from_station_name='杭州'
        from_station=stations_research.get(from_station_name)
        # to_station_name=input("请输入目的站(格式：上海)：")
        to_station_name = '淮北'
        to_station=stations_research.get(to_station_name)
        # date=input("请输入出发时间(格式：2019-05-01)：")
        date = '2019-05-01'
        # print("列车类型说明：g：高铁；d：动车；t：特快；k：快车；z：直达车")
        decode_str=input("请输入查询列车类型(格式：g/gd，不输入代表所有类型)：")
        # decode_str =None


        queryData={'fromStation':from_station_name,
                   'toStation':to_station_name,
                   'trainDate':date,
                   'fromStationCode':from_station,
                   'toStationCode':to_station,
        }


        nowtime = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        nowtime = datetime.datetime.strptime(nowtime, "%Y-%m-%d")
        if from_station == None:
            print("请确认出发站：{}是否输入正确...".format(from_station))
        elif to_station == None:
            print("请确认目的站：{}是否输入正确...".format(to_station))
        elif len(re.findall('\d{4}-\d{2}-\d{2}', date)) == 0:
            print("请确认搜索日期：{}是否输入正确...".format(date))
        elif (datetime.datetime.strptime(date, "%Y-%m-%d") - nowtime).days < 0:
            print("请确认搜索日期是否小于今日日期...")
        elif (datetime.datetime.strptime(date, "%Y-%m-%d") - nowtime).days > 29:
            print("只能查询今日及后面30日以内...")
        else:
            url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={0}&leftTicketDTO.from_station={1}&leftTicketDTO.to_station={2}&purpose_codes=ADULT'.format(
                date, from_station, to_station)
            res=self.session.get(url, verify=False).json()
            trainDicts=self.getTrainInfo(res)
            rows=res['data']['result']
            # rows = requests.get(url, verify=False).json()['data']['result']
            if len(rows) == 0:
                print("没有从{0}到{1}的列车，请考虑换乘线路...".format(from_station, to_station))
            else:
                results = self.decode(rows, stations_research, decode_str)
                if len(results) == 0:
                    print("从{0}到{1}没有你需要查询的列车类型，请选择其他类型列车...".format(from_station, to_station))
                else:
                    self.pretty_table(results)
            return queryData,trainDicts



if __name__=='__main__':
    _search=search()
    queryData,trainDicts=_search._Train_Search()
    print(queryData)
    print(trainDicts)


