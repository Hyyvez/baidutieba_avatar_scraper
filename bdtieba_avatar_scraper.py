#-*-coding:utf8-*-
from lxml import etree
from fake_useragent import UserAgent
import requests
import re
import time
import random
from runTime import Get_time 
from timeNow import timeNow
import copy
from bs4 import BeautifulSoup



tieba_link = "https://tieba.baidu.com/f?ie=utf-8&kw=%E4%B8%AD%E5%9B%BD%E4%BA%BA%E5%8F%A3" #吧主页链接
#postlink = 'https://tieba.baidu.com/p/7823990986'
#begin = 1       #帖子内开始页数
#end = -1        #帖子内结束页数
save_path = 'raws'      #保存文件夹路径名称，当前py文件的相对路径
genders_filter = "-1"         #性别筛选，"-1"为不筛选
start_page = 69           #吧的下载开始页数
end_page = 499              #吧的结束页数
breakpoint_flag = 0     # 1 = 从断点继续下载 # 0 = 默认下载

ua = UserAgent()
headers = {'User-Agent':ua.opera}# fake UserAgent
fetch_profilepic_interval = 5    #头像下载平均间隔（单位：秒）         5
fetch_gender_interval = 3     #（性别获取）用户信息页获取平均间隔（单位：秒）         4
fetch_generalurl_interval = 7   # 通常网页获取平均间隔（单位：秒） w      7.5
breakpoint_loadpath = 'E:/untitled/breakpoint.txt' #断点加载文件位置

def Url2Html(url):
    headers = {'User-Agent':str(UserAgent().chrome)}# fake UserAgent
    html = requests.get(url,headers = headers)
    time.sleep(fetch_generalurl_interval*(random.random()+0.5))
    html = re.sub(r'charset=(/w*)', 'charset=UTF-8', html.text)
    return html

def GetSinglePageImgLink(url,genders_filter): 
    links = []
    inpost_html = Url2Html(url)
    #print(inpost_html)
    inpost_htmlcopy = copy.deepcopy(inpost_html)#如果在其他方法获取max_pagn的话，又需要request一次帖子，所有在这里复制一份
    maxpageandremain = inpost_htmlcopy.split('共<span class="red">')[1]# 'max-page="' 后面的数字"x"即总页数，截取它的数字直到在数字开头的位置开始找到"即为总页数
    global max_pagn 
    max_pagn = int(maxpageandremain[0:(maxpageandremain.find("<"))])#将max_pagn传到全局变量
    if not max_pagn:# 页面异常（404或被反爬虫）-->找不到max_pagn --> max_pagn = 1
        max_pagn = 1
    soup = BeautifulSoup(inpost_html, 'lxml')
    for user in soup.find_all(attrs={"class" : "icon_relative j_user_card"}): 
        #print(user)
        src = user.find('img')
        #print(src)
        #print(src.attrs['src'])
        if src.attrs['src'] != '//tb2.bdstatic.com/tb/static-pb/img/head_80.jpg':
            links.append(src.attrs['src'])
        else:
            links.append(src.attrs['data-tb-lazyload'])
    #print('unfiltered_links:',links)

    
    if not links:
        if "贴吧404" in inpost_htmlcopy:
            print("该贴不存在")
            return links
        if "本楼包含部分广告等违规内容的回复" in inpost_htmlcopy:
            print("本楼包含部分广告等违规内容的回复，已经被屏蔽，暂不可见。")#返回空links
            return links
        else:
            print("list为none，" + "已被反爬虫")
            print(timeNow())
             #testing
            time.sleep(900)
            SpecificBaMultiPage(tieba_link,save_path,genders_filter,start_page,end_page,1)
            return links
            
    links = list(set(links)) # 去掉一页中的重复图片地址
    links = Httpadder(links) #将没有http:的地址加上http:

    if genders_filter != ("-1"):
        genders_filter_rel = GendersFilter(genders_filter,links)
        if not genders_filter_rel:
            print("该页都不符合性别筛选") 
        #print('filtered_links:',links)
        return genders_filter_rel

    return links

# 筛选性别 返回一个经过性别筛选的头像网址list
def GendersFilter(gender,profilepiclist):
    Gendersfiltering = copy.deepcopy(profilepiclist)
    i = 0
    print("获取用户性别中")
            
    while i < len(Gendersfiltering):   
        UserInfoSite = requests.get(Userid2GetUserInfoSite(Gendersfiltering)[i],headers = headers)
        time.sleep(fetch_gender_interval*(random.random()+0.5))
        UserInfoSite = re.sub(r'charset=(/w*)', 'charset=UTF-8', UserInfoSite.text)
        #print(UserInfoSite)
        sexandremain = (UserInfoSite).partition('"sex":"')[2]
        if gender != sexandremain[0 : (sexandremain.find('"'))]:
            del Gendersfiltering[i]
        else:
            i += 1    

    Gendersfilter = Gendersfiltering
    return Gendersfilter

# 将头像图片地址转换为userid地址，profilepiclist contains userid
def Userid2GetUserInfoSite(profilepic):   
    sitelist = copy.deepcopy(profilepic)
    i=0
    while i < len(sitelist):
        sitelist[i] = "https://tieba.baidu.com/home/get/panel?ie=utf-8&id=" + (str(sitelist[i]).partition("item/")[2]) #tb为userid开头
        i += 1
    #print(sitelist)
    return sitelist 

'''将没有http:的地址加上http:'''
def Httpadder(links):
    if links != None:
        newlist4withouthttps = []
        if str(links[0])[0:4] != "http":
            for link in links:  
                newlist4withouthttps.append("https:" + str(link)) 
            return newlist4withouthttps
        else :
            return links

@Get_time# 下载一个帖子指定页数的头像
def Multidownloader_pagn(url,inpost_page_begin,inpost_page_end,save_path,gender):
    
    current_inpostpagn = inpost_page_begin
    while current_inpostpagn <= inpost_page_end or inpost_page_end == -1:
        urlwith_pagnindex = (url + '?pn=' + str(current_inpostpagn))
        print ("开始{0}第{1}页的下载:{2}".format(url,current_inpostpagn,urlwith_pagnindex))
        try:
            buffer_list = GetSinglePageImgLink(urlwith_pagnindex,gender)
        except:
            print("GetSinglePageImgLink获取links异常")
            buffer_list = []
            pass
            #当inpost_page_end设置为-1时，下载该帖子的所有页数
        if inpost_page_end == -1:
            if max_pagn > 200 :  # 发现在自动爬取所有吧里帖子时，如果一个帖子有非常多页数，极有可能是几个用户刷贴的水楼，所以在这排除掉只下载一页。在帖子被删除是，会获取不到max_pagn，在这里排除掉
                inpost_page_end = 1
            else:
                inpost_page_end = max_pagn

        print('下载该页所有符合筛选的图片中',buffer_list)
        i = 0
        for each_link in buffer_list:  
            graphic = requests.get(each_link)
            time.sleep(fetch_profilepic_interval*(random.random()+0.5))
            with open(save_path + '/' + "img{0}.jpeg".format(buffer_list[i][-9:]),"wb") as code:
                code.write(graphic.content)
            i = i + 1
        print ("已下载第" + str(current_inpostpagn) + "页，该帖共需要下载{0}".format(inpost_page_end)+"页")
        current_inpostpagn = current_inpostpagn + 1
    print ("已完成" + url + "的下载，下载了" + str(inpost_page_end-(inpost_page_begin-1)) + "页")
            

def TiebaLinkFetcher(tieba_link):
    postslist = []
    ba_html = Url2Html(tieba_link)
    #去掉 threadlist_lz clearfix 字符串在要寻找的threadlist_title pull_left j_th_tit class的前面，去掉它与它以上的html代码，html过长会导致想要的class搜索不到
    #print(ba_html)
    ba_html = ba_html.partition("threadlist_lz clearfix")[2]
     # lxml：html解析库（把HTML代码转化成Python对象）
    soup = BeautifulSoup(ba_html, 'lxml')
    #print(soup)
    for post in soup.find_all(attrs={"class" : "threadlist_title pull_left j_th_tit"}):
        linksuffix = post.a
        postslist.append("https://tieba.baidu.com"+ (linksuffix.attrs['href']))
        
    #print('该页贴吧的50个网页链接:',postslist)
    if not postslist:
            print("list为none，" + "已被反爬虫")
            print(timeNow())
             #testing
            time.sleep(900)
            SpecificBaMultiPage(tieba_link,save_path,genders_filter,start_page,end_page,1)
    return postslist 

#下载整个贴吧里帖子的头像
@Get_time
def SpecificBaMultiPage(tieba_link,save_path,gender,start_page,end_page,breakpoint_flag):
    inpost_page_begin = 1 # 下载帖子的开始页数
    inpost_page_end = -1    # 下载帖子的结束页数，-1为下载全部
    downloaded_posts_count = 0 # 此次运行方法下载的帖子总数
    tieba_link = tieba_link
    post_index = 1 
    
    

    current_page = start_page
    try:
        if breakpoint_flag == 1: #如果从断点继续下载
            tieba_linkwith_pagnindex = tieba_link + str((current_page-1)*50) # 0为第一页，50第二页，所以current_page-1
            postslist = TiebaLinkFetcher(tieba_linkwith_pagnindex)#获取该页所有帖子的list 为了让能从breakpoint开始
            print("从文件加载断点继续下载")
            with open(breakpoint_loadpath, 'r', encoding="utf-8") as f:
                breakpoint = [line.strip() for line in f]
            #print(breakpoint)
            current_page = breakpoint[0]  # 转换为int
            current_page = int(current_page) 
            del postslist[0:int(breakpoint[1])+1]
            breakpoint_flag = 2

        while current_page <= end_page:
            tieba_linkwith_pagnindex = tieba_link + str((current_page-1)*50) # 0为第一页，50第二页，所以current_page-1
            if breakpoint_flag == 0: # 上面以及从断点获取过了，这里加判断是为了第一次不运行，然后一直允许运行不覆盖掉从断点开始的列表
                postslist = TiebaLinkFetcher(tieba_linkwith_pagnindex)#获取该页所有帖子的list
            breakpoint_flag = 0
            print("当前为第{0}页{1}所有帖子:{2}".format(current_page,tieba_linkwith_pagnindex,postslist))
            for postlink in postslist:
                #print(postlink)
                Multidownloader_pagn(postlink,inpost_page_begin,inpost_page_end,save_path,gender)
                downloaded_posts_count = downloaded_posts_count + 1
                post_index = post_index + 1
                
                write_breakpoint = open(breakpoint_loadpath, "w")
                write_breakpoint.write(str(current_page)+'\n'+str(post_index-1)+'\n'+timeNow())

            current_page = current_page + 1
            post_index = 1
    except:
        print("遇到异常，已停止运行。")
        print("共下载{0}个帖子,遇到异常的帖子为第{1}页的第{2}个贴子:{3}".format(downloaded_posts_count,current_page,post_index,postslist[post_index]))

        print(timeNow())
        #testing
        time.sleep(900)
        SpecificBaMultiPage(tieba_link,save_path,genders_filter,start_page,end_page,breakpoint_flag = 1)
        


SpecificBaMultiPage(tieba_link,save_path,genders_filter,start_page,end_page,breakpoint_flag)

#TiebaLinkFetcher(tieba_link)
#Multidownloader_pagn(postlink,begin,end,save_path,genders_filter)
#GetSinglePageImgLink(postlink,genders_filter)
