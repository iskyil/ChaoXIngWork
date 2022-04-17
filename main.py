import json
import requests
import re
import base64
from lxml import etree
from requests.sessions import session

global currClass
currClass = 0


class Work(object):
    def __init__(self):
        self.qkey = 'q-key'
        self.username = '188888888'
        self.password = '18888888'
        self.session = requests.session()
        self.headers = {
            'User-Agent':  "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
            'Referer': 'http://mooc1-1.chaoxing.com/'
        }
        self.blacklist = ['2020级跨文化交际','2021级跨文化交际','2022级跨文化交际']

    def Qsend(self, msg: str):
        data = {
            'msg': msg,
            'qkey': self.qkey,
            'type': 'text'
        }
        res = (requests.post('https://api.skyil.cn/send', data=data).text)

        print(res)
        res = json.loads(res)
        if res['code'] == 0:
            print('推送成功')
        else:
            print('推送失败')

    def login(self):
        url = 'http://passport2.chaoxing.com/fanyalogin'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Referer': r'http://passport2.chaoxing.com/login?fid=&newversion=true&refer=http%3A%2F%2Fi.chaoxing.com'
        }

        data = {
            'fid': -1,
            'uname': self.username,
            'password': base64.b64encode(self.password.encode()).decode(),
            'refer': r'http%253A%252F%252Fi.chaoxing.com',
            't': True,
            'forbidotherlogin': 0
        }
        self.session.post(url, headers=headers, data=data)

    def getclass(self):
        self.login()
        url = 'http://mooc1-2.chaoxing.com/visit/courses'
        headers = {
            'User-Agent':  "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
            'Referer': r'http://i.chaoxing.com/'
        }
        res = self.session.get(url, headers=headers)

        if res.status_code == 200:
            class_HTML = etree.HTML(res.text)
            i = 0
            global course_dict
            course_dict = {}

            for class_item in class_HTML.xpath("/html/body/div/div[2]/div[3]/ul/li[@class='courseItem curFile']"):
                try:
                    class_item_name = class_item.xpath(
                        "./div[2]/h3/a/@title")[0]
                    if(class_item.xpath("./div[2]/p/@style")[0] != 'color:#0099ff'):
                        # 等待开课的课程由于尚未对应链接，所有缺少a标签。
                        i += 1
                        course_dict[i] = [class_item_name, "https://mooc1-1.chaoxing.com{}".format(
                            class_item.xpath("./div[1]/a[1]/@href")[0]) + '&ismooc2=1']
                except:
                    pass
        else:
            return 0

    def get_work_url(self, url):
        try:
            course_url = self.session.get(
                url, headers=self.headers, stream=True).url
            course_data = self.session.get(
                course_url, headers=self.headers).text
            # 获取 work enc
            course_html = etree.HTML(course_data)
            enc = (course_html.xpath(
                "//*[@id='workEnc']/@value")[0])
            # 获取 work url
            list_url = course_url.replace('https://mooc2-ans.chaoxing.com/mycourse/stu?',
                                          'https://mooc1.chaoxing.com/mooc2/work/list?').replace('courseid', 'courseId').replace('clazzid', 'classId')
            list_url = list_url.split("enc=")[0] + 'enc=' + enc
            work_data = self.session.get(list_url, headers=self.headers)
            work_html = etree.HTML(work_data.text)
            workDetail = work_html.xpath(
                '/html/body/div/div/div/div[2]/div[2]/ul/li')
            return workDetail
        except:
            print("获取work_url失败")

    def check_work(self, url: str):
        workDetail = self.get_work_url(url)
        # 检测是否有作业未完成
        if workDetail:
            name = course_dict[currClass][0]
            print(name)
            for workID in workDetail:
                statu = (workID.xpath(
                    "./div[2]/p[@class='status fl']/text()")[0])
                work = (workID.xpath(
                    "./div[2]/p[@class='overHidden2 fl']/text()")[0])
                if(statu == '未交'):
                    if workID.xpath("./div[@class='time notOver']"):
                        # workid = re.search(r'workId=(\d*)&',workID.xpath("@data")[0]).group(1)
                        time = (workID.xpath(
                            "./div[@class='time notOver']/text()")[1]).replace('\n', '').replace('\r', '').replace(' ', '')
                        print(name+work+time)
                        hour = re.match(r'剩余(\d*)小时', time).group(1)
                        for num in 48, 24, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0:
                            if int(hour) == num:
                                self.Qsend(name + ' ' + work + ' ' + time)
                                break


if __name__ == '__main__':
    run = Work()
    result = run.getclass()
    if result != 0:
        for currClass in course_dict:
            flag = 0
            for black_course in Work().blacklist:
                if course_dict[currClass][0] == black_course:
                    flag = 1
                    break
            if flag != 1:
                run.check_work(course_dict[currClass][1])
    else:
        print('出错了')
