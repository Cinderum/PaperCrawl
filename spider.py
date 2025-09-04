import requests
import bs4
import os
import datetime
import time
import re
import sqlite3

def fetchUrl(url): #访问 url 的网页，获取网页内容并返回
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
    }
    
    r = requests.get(url,headers=headers)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text

def getPageList(year, month, day): #获取当天报纸的各版面的链接列表
    url = 'http://paper.people.com.cn/rmrb/pc/layout/' + year + month + '/' + day + '/node_01.html'
    # print(url)
    html = fetchUrl(url)
    bsobj = bs4.BeautifulSoup(html,'html.parser')
    temp = bsobj.find('div', attrs = {'id': 'pageList'})
    if temp:
        pageList = temp.ul.find_all('div', attrs = {'class': 'right_title-name'})
    else:
        pageList = bsobj.find('div', attrs = {'class': 'swiper-container'}).find_all('div', attrs = {'class': 'swiper-slide'})
    linkList = []
    
    for page in pageList:
        link = page.a["href"]
        url = 'http://paper.people.com.cn/rmrb/pc/layout/' + year + month + '/' + day + '/' + link
        linkList.append(url)
    
    return linkList

def getTitleList(year, month, day, pageUrl): # 获取报纸某一版面的文章链接列表
    html = fetchUrl(pageUrl)
    bsobj = bs4.BeautifulSoup(html,'html.parser')
    temp = bsobj.find('div', attrs = {'id': 'titleList'})
    if temp:
        titleList = temp.ul.find_all('li')
    else:
        titleList = bsobj.find('ul', attrs = {'class': 'news-list'}).find_all('li')
    linkList = []
    
    for title in titleList:
        tempList = title.find_all('a')
        for temp in tempList:
            link = temp["href"]
            link = link.replace("../", "", 3)
            if '/content_' in link:
                url = 'http://paper.people.com.cn/rmrb/pc/' + link
                linkList.append(url)
    
    return linkList

def getContent(html): # 解析 HTML 网页，获取新闻的文章内容
    bsobj = bs4.BeautifulSoup(html,'html.parser')
    
    # 获取文章 标题
    title = bsobj.h3.text + ' ' + bsobj.h1.text + ' ' + bsobj.h2.text
    #print(title)
    
    # 获取文章 内容
    pList = bsobj.find('div', attrs = {'id': 'ozoom'}).find_all('p')
    content = ''
    for p in pList:
        content += p.text.replace("　　", "\n　　")
    #print(content)
    
    # 返回结果标题+内容
    return title, content

def download_rmrb(year, month, day): # 爬取《人民日报》网站 某年 某月 某日 的新闻内容，并保存在 指定目录下
    pageList = getPageList(year, month, day)
    for page in pageList:
        titleList = getTitleList(year, month, day, page)
        for url in titleList:
            
            # 获取新闻文章内容
            html = fetchUrl(url)
            title, content = getContent(html)

            conn.execute("INSERT INTO texts (year, month, day, url, title, content) VALUES (?, ?, ?, ?, ?, ?)", (year, month, day, url, title, content))
            
            # 提交到数据库
            conn.commit()
            
def gen_dates(b_date, days):
    day = datetime.timedelta(days = 1)
    for i in range(days):
        yield b_date + day * i
        
        
def get_date_list(beginDate, endDate):
    """
    获取日期列表
    :param start: 开始日期
    :param end: 结束日期
    :return: 开始日期和结束日期之间的日期列表
    """
    start = datetime.datetime.strptime(beginDate, "%Y%m%d")
    end = datetime.datetime.strptime(endDate, "%Y%m%d")
    data = []
    for d in gen_dates(start, (end-start).days+1):
        data.append(d)

    return data

            
if __name__ == '__main__':
    # 输入起止日期，爬取之间的新闻
    beginDate = input('请输入开始日期:')
    endDate = input('请输入结束日期:')
    data = get_date_list(beginDate, endDate)

    # 连接到 SQLite 数据库
    conn = sqlite3.connect('data.db')
    #如果表格存在则删除
    conn.execute("DROP TABLE IF EXISTS texts")
    # 创建一个表格
    conn.execute('''CREATE TABLE texts (year NUMBER, month NUMBER, day NUMBER, url TEXT, title TEXT, content TEXT)''')
    
    for d in data:
        year = str(d.year)
        month = str(d.month) if d.month >=10 else '0' + str(d.month)
        day = str(d.day) if d.day >=10 else '0' + str(d.day)
        download_rmrb(year, month, day)
        print("爬取完成：" + year + month + day)

    # 查询数据
    # cursor = conn.execute("SELECT * FROM texts")
    # for row in cursor:
    #     print(row)

    # 关闭连接
    conn.close()
