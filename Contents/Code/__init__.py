# -*- coding: utf-8 -*-
import re,urllib2,base64
import calendar
from datetime import *
import time
#, translit, urllib
# Kartina TV Plugin
# by Alex Titoff
# http://rozdol.com/
# rozdol@gmail.com
VERSION						= 2.3
####################################################################################################
# v2.3 - April 6, 2011
# > HQ logos of channels added (thnx Alex1808)
#
# v2.2 - April 5, 2011
# > Fixed Posters display for VOD
#
# v2.1 - April 3, 2011
# > Added Favorites
# > Added VOD
#
# v2.0 - April 2, 2011
# > Framework V.2 used (Complete rewrite)
# > XML changed to JSON 
# > Authentication procedure changed
# > Version update check
#
# v0.3 - February 03, 2011
# > Fixed archieve checking
# > Replace quotes
# > Added Movies
#
# v0.2 - January 22, 2011
# > Changed default icon
#
# v0.1 - January 20, 2011
# > Initial release
#
###################################################################################################

VIDEO_PREFIX				= "/video/kartinatv2"
NAME						= 'KartinaTV2'
ART							= 'art-default.jpg'
ICON						= 'icon-default.png'
PREFS						= 'icon-prefs.png'
API_URL						= 'http://iptv.kartina.tv/api/json/'
BASE_URL					= 'http://iptv.kartina.tv/api/json/'
USER_AGENT					= 'User-Agent','PLEX KartinaTV plugin (Macintosh; U; Intel Mac OS X 10.6; ru; rv:1.9.2.13) Author/Alex_Titov'
LOGGEDIN					= False
SID							= ''
title1						= NAME
title2						= ''
SORT_NAMES 					= ['По эфиру', 'По году', 'Но названию', 'По рейтингу']
SORT_VALUES 				= ['on_air','production_year','name','mark_total']
DIR_NAMES 					= ['По убыванию', 'По возрастанию']
DIR_VALUES 					= ['desc','asc'] 
UPDATECHECK_URL            = 'http://www.rozdol.com/versioncheck.php?module=kartinatv&v='+ str(VERSION)+'&info=' 
#Dict['sessionid']=""
####################################################################################################

def Start():


	Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, NAME, ICON, ART)

	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	MediaContainer.title1 = title1
	MediaContainer.title2 = title2
	MediaContainer.viewGroup = "List"
	MediaContainer.art = R(ART)
	DirectoryItem.thumb = R(ICON)
	VideoItem.thumb = R(ICON)
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent']=USER_AGENT #'Mozilla/5.0 [Macintosh; U; Intel Mac OS X 10.6; ru; rv:1.9.2.13] Gecko/20101203 Firefox/3.6.13 GTB7.1'
	HTTP.Headers['Accept']='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
	HTTP.Headers['Accept-Encoding']='gzip,deflate,sdch'
	HTTP.Headers['Accept-Language']='ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3'
	HTTP.Headers['Accept-Charset']='windows-1251,utf-8;q=0.7,*;q=0.7'
	HTTP.Headers['Keep-Alive']='115'
	HTTP.Headers['Referer']='http://kartina.tv/'
	#LOGGEDIN = Login()
	
####################################################################################################
	
def ValidatePrefs():
	global LOGGEDIN, SID
	u = Prefs['username']
	p = Prefs['password']
	if( u and p ):
		LOGGEDIN = Login()
		if LOGGEDIN == False:
			return MessageContainer(
				"Ошибка",
				"Отказ в доступе"
			)
	else:
		return MessageContainer(
			"Ошибка",
			"Веедите имя и пароль"
		)

####################################################################################################

def MainMenu():
	global LOGGEDIN, SID
	httpCookies=HTTP.GetCookiesForURL(BASE_URL)
	SID=Dict['sessionid']
	url=API_URL +'channel_list&MWARE_SSID='+str(SID)
	Log(" --> SSID='%s'" % (SID))
	msg=""
	dir = MediaContainer(viewGroup="List", noCache=True, httpCookies=httpCookies)	
	if Prefs['updates'] == True and CheckForUpdate() != None:
		newver=CheckForUpdate()
		dir.Append(Function(DirectoryItem(UpdateAvailable, title='Доступна новая версия '+str(newver), thumb=R('warning.png'))))
	if SID != "":
		msg=""
		dir.Append(Function(DirectoryItem(Channels, title='Телевидение', thumb=R('tv-icon.png')), link='channel_list', id=0))
		dir.Append(Function(DirectoryItem(Favorites, title='Избранное', thumb=R('Favorites.png'))))
		dir.Append(Function(DirectoryItem(MovieMenu, title='Видеотека', thumb=R('movies.png'))))
		dir.Append(Function(DirectoryItem(Logout, title='Прервать сессию', thumb=R('exit.png'))))
	else:
		dir.Append(Function(DirectoryItem(DoLogin, title='Новая сессия', thumb=R('start2.png'))))
	dir.Append(PrefsItem('Настройки '+msg, thumb=R('settings.png')))
	dir.Append(Function(DirectoryItem(About, title='О плагине', thumb=R('info.png'))))
	#dir.Append(Function(DirectoryItem(Test, title='TEST', thumb=R('warning.png'))))
	
	return dir

####################################################################################################

def MovieMenu(sender):
	dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL(BASE_URL),title2='Видеотека')
	dir.Append(Function(DirectoryItem(ListMovies, title='Последние', summary='отсортированы по дате добавления в обратном порядке', thumb=R('movies.png')),type='last', page=1, query='', genre='', nums=Prefs['itemsperpage']))
	dir.Append(Function(DirectoryItem(ListMovies, title='Лучшие', summary='отсортированы согласно рейтинга по просмотрам', thumb=R('movies.png')),type='best', page=1, query='', genre='', nums=Prefs['itemsperpage']))
	dir.Append(Function(InputDirectoryItem(Search, title='Поиск', prompt=L('SEARCHPROMT'), thumb=R('search.png'))))
	return dir
def ListMovies(sender,type, page, query, genre, nums):
	nextpage=page+1
	dir = MediaContainer(viewGroup="InfoList", title='Movies', noCache=True)
	title='ok'
	idf=1
	summary='summary'	
	url=API_URL + 'vod_list?&type='+type+'&page='+str(page)+'&query='+query+'&genre='+genre+'&nums='+str(nums)+'&MWARE_SSID='+Dict['sessionid']
	Log("------> URL='%s'" % (url))
	dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL(BASE_URL),title2='Видеотека')
	obj = JSON.ObjectFromURL(url)
	if obj.has_key('error'):
		msg=obj["error"]["message"]
		Dict['sessionid']=""
		return MessageContainer("Ошибка", msg)
	else:
		msg=""
		for items in obj["rows"]:
			title = items["name"]
			subtitle = items["genre_str"]
			summary = items["description"]
			poster = 'http://iptv.kartina.tv'+items["poster"]
			rating = items["rate_kinopoisk"]
			summary=summary.replace('&quot;','"')
			id = items["id"]
			Log("------> Movie ID=%s, POSTER=%s" % (id,poster))
			thumb=Function(Thumb, url=poster)
			dir.Append(Function(DirectoryItem(ListSeries, title=title, summary=summary, rating=rating, infoLabel='', thumb=thumb), id=id))
		dir.Append(Function(DirectoryItem(ListMovies, title='Next'),type=type, page=nextpage, query=query, genre=genre, nums=nums))
		return dir
	
####################################################################################################

def ListSeries(sender,id):

	dir = MediaContainer(viewGroup="InfoList", title='Series', noCache=True)
	url=API_URL + 'vod_info?id='+id+'&MWARE_SSID='+Dict['sessionid']
	Log("------> URL='%s'" % (url))
	title='ok'
	summary='summary'
	dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL(BASE_URL),title2='Серии')
	obj = JSON.ObjectFromURL(url)
	if obj.has_key('error'):
		msg=obj["error"]["message"]
		Dict['sessionid']=""
		return MessageContainer("Ошибка", msg)
	else:
		msg=""
		st=JSON.StringFromObject(obj)
		Log("------> OBJ='%s'" % (st))
		for items in obj["film"]["videos"]:
			st=JSON.StringFromObject(items)
			Log("------> OBJ='%s'" % (st))
			title=items["title"]
			if len(title)==0:
				title="Смотреть"
			title='▶ '+title
			id =  items["id"]
			dir.Append(Function(VideoItem(PlayMovie, title=title), id=id))
		return dir

####################################################################################################

def PlayMovie(sender, id):
	Log("------> ID='%s'" % (id))
	xp='//url'
	url=API_URL+'vod_geturl?fileid='+id+'&MWARE_SSID='+Dict['sessionid']
	obj = JSON.ObjectFromURL(url)
	if obj.has_key('error'):
		msg=obj["error"]["message"]
		Dict['sessionid']=""
		return MessageContainer("Ошибка", msg)
	else:
		msg=""
		murl=obj["url"]		
		#strn=JSON.StringFromObject(obj)
		Log("------> Orig STREAM URL '%s'" % (murl))
		murl=murl[0:murl.find(" :")]
		murl=murl.replace('http/ts://','http://')
		Log("------> Clean STREAM URL '%s'" % (murl))
		HTTP.SetHeader('User-Agent', 'vlc/1.1.0 LibVLC/1.1.0')
		HTTP.SetHeader('Icy-MetaData', '1')
		return Redirect(VideoItem( murl, title='' ))
	
#########################################################

def Channels(sender,link,id=0):
	url=API_URL + link +'&MWARE_SSID='+Dict['sessionid']
	Log("------> URL='%s'" % (url))
	dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL(BASE_URL),title2='Каналы')
	obj = JSON.ObjectFromURL(url)
	if obj.has_key('error'):
		msg=obj["error"]["message"]
		Dict['sessionid']=""
		return MessageContainer("Ошибка", msg)
	else:
		msg=""
	if id==0:						
		for group in obj["groups"]:
			name=group["name"]
			gid=group["id"]				
			dir.Append(Function(DirectoryItem(Channels, title=name,thumb=R('group_'+str(gid)+'.png')), link='channel_list', id=gid))
	else:
		for group in obj["groups"]:
			if group["id"]==id:
				for chan in group["channels"]:
					cid=chan["id"]	
					name=chan["name"]
					poster = 'http://iptv.kartina.tv'+chan["icon"]
					Log("------> Channel ID=%s, POSTER=%s" % (cid,poster))
					#thumb='http://iptv.kartina.tv/img/ico/24/'+str(cid)+'.gif'			
					#dir.Append(Function(DirectoryItem(EPG, title=name, summary=name, thumb=R('art-default.jpg')), id=cid, page=1))
					dir.Append(Function(DirectoryItem(ListDays, title=name, title2=name,thumb=R('channel_'+str(cid)+'.png')), id=cid,channelname=name))
	return dir

####################################################################################################

def Favorites(sender):
	url=API_URL  +'favorites&MWARE_SSID='+Dict['sessionid']
	Log("------> URL='%s'" % (url))
	dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL(BASE_URL),title2='Каналы')
	obj = JSON.ObjectFromURL(url)
	if obj.has_key('error'):
		msg=obj["error"]["message"]
		Dict['sessionid']=""
		return MessageContainer("Ошибка", msg)
	else:
		msg=""
	if id==0:						
		for group in obj["groups"]:
			name=group["name"]
			gid=group["id"]				
			dir.Append(Function(DirectoryItem(Channels, title=name), link='channel_list', id=gid))
	else:
		for items in obj["favorites"]:
			cid=items["channel_id"]	
			name='Ячейка № '+str(items["place"])
			thumb='http://iptv.kartina.tv/img/ico/24/'+str(cid)+'.gif'			
			dir.Append(Function(DirectoryItem(ListDays, title=name, title2=name,thumb=Function(Thumb, url=thumb)), id=cid,channelname=name))
	return dir

####################################################################################################

def ListDays(sender,id='',channelname=''):
		dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL(BASE_URL),title2=channelname)
		now=time.time()
		ts=int(Prefs['liveshift'])
		Log("------> TS='%s'" % (Prefs['liveshift']))
		url=API_URL+'account&MWARE_SSID='+Dict['sessionid']	
		obj = JSON.ObjectFromURL(url)
		servertime=int(obj["servertime"])-ts*60
		nowday=datetime.fromtimestamp(now).strftime("%d%m%y")
		have_archive = 1 #Temoprary fix
		if have_archive == 0:
			subtitle = "No archive"
			dir.viewGroup = 'InfoList'
		else:
			subtitle = "Play Live"
			dir.viewGroup = 'List'
		dir.Append(Function(VideoItem(PlayChannel, title='▶ Прямой эфир', subtitle=subtitle, summary=''), id=id,gmt=servertime))
		if have_archive > 0:			
			today=time.time()
			for n in range(0, 30):
				theday=today-n*24*3600
				timestamp = datetime.fromtimestamp(theday)
				da=timestamp.strftime("%d%m%y")
				title=timestamp.strftime("%A (%d.%m)")
				#Log("------> Loop n='%s, %s, %s'" % (da,theday,Weekday[datetime.date.weekday(theday)]))
				dir.Append(Function(DirectoryItem(ShowEPG, title=title, subtitle='', summary=''), id=id, nowday=da,channelname=channelname))
		return dir

####################################################################################################

def ShowEPG(sender, id, nowday,channelname=''):
	dir = MediaContainer(viewGroup='InfoList', httpCookies=HTTP.GetCookiesForURL(BASE_URL),title2=channelname)
	ts = int(Prefs['timeshift'])
	now=time.time()
	if nowday == '':
		nowday=datetime.fromtimestamp(now).strftime("%d%m%y")
	Log("------> Nowday = %s " % (nowday))
	prevday=int(nowday)-1
	nextday=int(nowday)+1
	#/epg?cid=<идентификатор канала>&day=<дата формата DDMMYY>
	url=API_URL + 'epg?cid='+ str(id) +'&day='+ str(nowday) +'&MWARE_SSID='+Dict['sessionid']
	Log("------> URL = %s " % (url))
	obj = JSON.ObjectFromURL(url)
	if obj.has_key('error'):
		msg=obj["error"]["message"]
		Dict['sessionid']=""
		return MessageContainer("Ошибка", msg)
	else:
		msg=""
		i=0
		items=len(obj["epg"])
		for epg in obj["epg"]:
			i=i+1
			progname=epg["progname"]
			gmt=epg["ut_start"]
			start=epg["t_start"]
			gmt=int(epg["ut_start"])+ts*60*60
			if i<items:
				gmtnext=int(obj["epg"][i]["ut_start"])+ts*60*60
			else:
				gmtnext=int(obj["epg"][items-1]["ut_start"])+ts*60*60
			duration=int(( gmtnext - gmt ) * 1000)
			prevtime = gmt
			timestamp = datetime.fromtimestamp(gmt)
			timestampnext = datetime.fromtimestamp(gmtnext)
			gmtstr = timestamp.strftime("%H:%M:%S")
			gmtnextstr = timestampnext.strftime("%H:%M:%S")
			subtitle = gmtstr+" - "+gmtnextstr
			
			if progname.rfind("\n-")>0:
				res=progname.split("\n-")
				name=res[0]
				summary=res[1]
			else:
				if progname.rfind("\n")>0:
					res=progname.split("\n")
					name=res[0]
					summary=res[1]
				else:
					name=progname
					summary=''
			if now <= gmt:
				name = "✖ %s" % name
				#dir.Append(DirectoryItem(ShowMessage, title=name, subtitle=subtitle, summary=summary, duration=duration), title="Иформация", message="Передача пока не доступна"))
				dir.Append(Function(DirectoryItem(ShowMessage, title=name, subtitle=subtitle, summary=summary, duration=duration), title="Иформация", message="Передача пока не доступна"))
			else:
				name = "▶ %s" % name
				dir.Append(Function(VideoItem(PlayChannel, title=name, subtitle=subtitle, summary=summary, duration=duration), id=id,gmt=gmt))
		return dir
	
####################################################################################################

def PlayChannel(sender, id, gmt):
	Log("------> ID='%s'" % (id))
	url=API_URL+'get_url?cid='+str(id)+'&gmt='+str(gmt)+'&protect_code='+Prefs['password'] +'&MWARE_SSID='+Dict['sessionid']	
	Log("------> QRY_URL '%s'" % (url))
	obj = JSON.ObjectFromURL(url)
	if obj.has_key('error'):
		msg=obj["error"]["message"]
		Dict['sessionid']=""
		return MessageContainer("Ошибка", msg)
	else:
		msg=""
		murl=obj["url"]		
		#strn=JSON.StringFromObject(obj)
		Log("------> Orig STREAM URL '%s'" % (murl))
		murl=murl[0:murl.find(" :")]
		murl=murl.replace('http/ts://','http://')
		Log("------> Clean STREAM URL '%s'" % (murl))
		HTTP.SetHeader('User-Agent', 'vlc/1.1.0 LibVLC/1.1.0')
		HTTP.SetHeader('Icy-MetaData', '1')
		return Redirect(VideoItem( murl, title='' ))
	
####################################################################################################

def PlayMedia(sender,url):	
	Log("----> URL='%s'" % (url))
	obj=JSON.ObjectFromURL(url)
	st=JSON.StringFromObject(obj)
	Log("----> OBJ='%s'" % (st))
	if obj.has_key('status'):
		if obj['status']=='ok':
			vurl=obj['url']
			title=obj['msg']
			Log("----> play from '%s'" % (vurl))
			#return Redirect(VideoItem(key=vurl, title=title ))
			return Redirect(vurl)
		else:
			title=obj['msg']
			MessageContainer("Error",title)
	else:
		return MessageContainer("Error","Some Error")
		
####################################################################################################
	
def ShowMessage(sender, title, message):
	return MessageContainer(title, message)

####################################################################################################
def Search(sender, query):
	query = re.sub (r' ', r'+', query)
	#if Prefs['cyrillic'] == True:
	#	return Categories('Result', link='media/search.json?q=' + translit.detranslify(query).encode("utf-8"), page=1)
	#else:
	#	#return Categories('Result', link='media/search.json?q=' + query.encode("utf-8"), page=1)
	return ListMovies('Result',type='text', page=1, query=query.encode("utf-8"), genre='', nums=Prefs['itemsperpage'])
		
	
####################################################################################################
def Logout(sender):
	url=API_URL + 'logout' +'&MWARE_SSID='+Dict['sessionid']
	Log("----> LOG Out: '%s'" % (url))
	obj = JSON.ObjectFromURL(url, encoding='utf-8', cacheTime=1)
	#strn=JSON.StringFromObject(item)
	#strn=unicode(strn).decode('unicode_escape')
	Log("----> LOG Out: '%s'" % (obj))
	Dict['sessionid']=""
	return True

####################################################################################################
def DoLogin(sender):
	u = Prefs['username']
	p = Prefs['password']
	if( u and p ):
		LOGGEDIN = Login()
		if LOGGEDIN == False:
			return MessageContainer(
				"Ошибка",
				"Отказ в доступе"
			)
	else:
		return MessageContainer(
			"Ошибка",
			"Веедите имя и пароль"
		)

####################################################################################################	
def Login():
	global LOGGEDIN, SID
	if LOGGEDIN == True:
		return True
	elif not Prefs['username'] and not Prefs['password']:
		return False
	else:
		url = API_URL+'login?login='+str(Prefs['username'])+'&pass='+str(Prefs['password'])+'&device=apple'		
		try:
			obj = JSON.ObjectFromURL(url, encoding='utf-8', cacheTime=1)
			strn=JSON.StringFromObject(obj)
			Log(" --> OBJ='%s'" % (strn))
		except:
			obj=[]
			Log("----> Someting Bad'%s'" % (url))
			LOGGEDIN = False
			return False	
		SID = obj['sid']
		if len(SID) > 0:
			LOGGEDIN = True
			Log(" --> Login successful! %s SSID='%s'" % (LOGGEDIN,SID))
			Dict['sessionid']=SID
			return True
		else:
			LOGGEDIN = False
			Dict['sessionid']=""
			Log(' --> Username/password incorrect!')
			return False
			#MessageContainer("Ошибка","Отказано в доступе")

####################################################################################################

def Thumb(url):
	if url=='':
		return Redirect(R(ICON))
	else:
		try:
			data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
			return DataObject(data, 'image/jpeg')
		except:
			return Redirect(R(ICON))
  
#################################################################################################### 

def Summary(id):
	url=API_URL +"media/details/"+str(id)+".json"
	obj=JSON.ObjectFromURL(url)
	summary=obj['media']['description']
	return summary
  
#################################################################################################### 

def About(sender):
	return MessageContainer(NAME+' (Версия ' + str(VERSION) + ')', 'Автор: Александр Титов\nwww.rozdol.com')

####################################################################################################

def CheckForUpdate():
	Log(' --> Checking for Update...')
	update = JSON.ObjectFromURL(UPDATECHECK_URL, cacheTime=1)
	if update['version'] != None and update['url'] != None:
		Log(' --> Still checking... (%s / %s)' % (update['version'],VERSION))
		if float(update['version']) > VERSION:
			Log(' --> New Version found!')
			return update['version']
		else:
			Log(' --> No New Version')
			return None

#################################################################################################### 

def Test(sender):
	title="Servertime"
	url=API_URL+'account&MWARE_SSID='+Dict['sessionid']	
	obj = JSON.ObjectFromURL(url)
	text=obj["servertime"]
	return MessageContainer(title, text)

####################################################################################################

def UpdateAvailable(sender):
	return MessageContainer('Доступна новая версия', 'Новая версия плагина на\nhttp://www.rozdol.com')

####################################################################################################