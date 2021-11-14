import base64
import configparser
import json
import re
import time

import requests
from lxml import etree
from requests.sessions import session

config=configparser.ConfigParser()
config.read("/root/python/chaoxing/config.ini")

global currClass
currClass = 0

def setConf(section:str,option:str,value:str):
    '''在指定section中添加变量和变量值'''
    try:
        config.add_section(section)
    except configparser.DuplicateSectionError:
        sss = ("Section already exists")
        # print(sss)
    config.set(section,option,value)
    config.write(open("/root/python/chaoxing/config.ini", "w"))


def login(username, password):
    url = 'http://passport2.chaoxing.com/fanyalogin'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Referer': r'http://passport2.chaoxing.com/login?fid=&newversion=true&refer=http%3A%2F%2Fi.chaoxing.com'
    }

    data = {
        'fid': -1,
        'uname': username,
        'password': base64.b64encode(password.encode()).decode(),
        'refer': r'http%253A%252F%252Fi.chaoxing.com',
        't': True,
        'forbidotherlogin': 0
    }
    global session
    session = requests.session()
    session.post(url, headers=headers, data=data)


def getClass():
    url = 'http://mooc1-2.chaoxing.com/visit/courses'
    headers = {
        'User-Agent':  "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        'Referer': r'http://i.chaoxing.com/'
    }
    res = session.get(url, headers=headers)

    if res.status_code == 200:
        class_HTML = etree.HTML(res.text)
        i = 0
        global course_dict
        course_dict = {}

        for class_item in class_HTML.xpath("/html/body/div/div[2]/div[3]/ul/li[@class='courseItem curFile']"):
            try:
                class_item_name = class_item.xpath("./div[2]/h3/a/@title")[0]
                if(class_item.xpath("./div[2]/p/@style")[0] != 'color:#0099ff'):
                    i += 1
                    course_dict[i] = [class_item_name, "https://mooc1-1.chaoxing.com{}".format(
                        class_item.xpath("./div[1]/a[1]/@href")[0]) + '&ismooc2=1']
            except:
                pass
    else:
        print("error:课程处理失败")

def Qsend(qq:int,msg:str):
    print(msg)
    data = {
        'msg': msg,
        'qq': qq,
        'type':'text'
    }
    res = (requests.post('https://api.skyil.cn/send', data=data).text)
    
    print(res)
    res = json.loads(res)
    if res['code'] == 0:
        print('推送成功')
    else:
        print('推送失败')


def getWork(url: str,qq:int):
    headers = {
        'User-Agent':  "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        'Referer': 'http://mooc1-1.chaoxing.com/'
    }
    course_url = session.get(url, headers=headers, stream=True).url
    course_data = session.get(course_url, headers=headers)
    # 获取 work enc
    course_html = etree.HTML(course_data.text)
    enc = (course_html.xpath(
        "//*[@id='workEnc']/@value")[0])
    # 获取 work url
    list_url = course_url.replace('https://mooc2-ans.chaoxing.com/mycourse/stu?', 'https://mooc1.chaoxing.com/mooc2/work/list?').replace('courseid', 'courseId').replace('clazzid', 'classId')
    list_url = list_url.split("enc=")[0] + 'enc=' +  enc
    work_data = session.get(list_url, headers=headers)
    work_html = etree.HTML(work_data.text)
    workDetail = work_html.xpath('/html/body/div/div/div/div[2]/div[2]/ul/li')
    # 检测是否有作业未完成
    if workDetail:
        name = course_dict[currClass][0]
        print(name)
        for workID in workDetail:
            statu = (workID.xpath("./div[2]/p[@class='status']/text()")[0])
            work = (workID.xpath("./div[2]/p[@class='overHidden2 fl']/text()")[0])
            if(statu == '未交'):
                if workID.xpath("./div[@class='time notOver']"):
                    workid = re.search(r'workId=(\d*)&',workID.xpath("@data")[0]).group(1)
                    time = (workID.xpath(
                        "./div[@class='time notOver']/text()")[1]).replace('\n', '').replace('\r', '').replace(' ','')
                    print(name+work+time)
                    hour = re.match(r'剩余(\d*)小时', time).group(1)
                    for num in 48,24,12,6,5,4,3,2,1,0:
                        if config.has_option(str(num), workid) == False and int(hour) <= num:
                            setConf(str(num),workid,'1')
                            Qsend(qq,name + ' ' + work + ' ' + time)
                            break


if __name__ == '__main__':
    print(time.asctime( time.localtime(time.time()) ))
    username = ''
    password = ''
    qq = ''

    login(username, password)
    getClass()

    for currClass in course_dict:
        getWork(course_dict[currClass][1],qq)
