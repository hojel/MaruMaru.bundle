# -*- coding: utf-8 -*-

PLUGIN_PREFIX   = "/photos/MaruMaru"
PLUGIN_TITLE    = "MaruMaru"

ROOT_URL        = "http://marumaru.in"
RECENT_URL      = ROOT_URL+"/?c=1/44"
CATE_URL        = ROOT_URL+"/?c=1/%d"
GENRE_URL       = ROOT_URL+"/?r=home&m=bbs&bid=manga&where=tag&keyword=G%3A"
MANGA_URL       = ROOT_URL+"/b/manga/%d"

RE_THUMB        = Regex("background-image:url\((.*)\)")
RE_ARCHIVE      = Regex("/archives/(\d+)")
RE_IMGURL       = Regex('data-src="(.*?)"')

ART             = "art-default.jpg"
ICON            = "icon-default.png"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    'Cookie': '__cfduid=0'
}

GENRES = [
    u"17", u"SF", u"TS", u"개그", u"드라마",
    u"러브코미디", u"먹방", u"백합", u"붕탁", u"순정",
    u"스릴러", u"스포츠", u"시대", u"액션", u"일상+치유",
    u"추리", u"판타지", u"학원", u"호러"
]

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE, ICON, ART)
  Plugin.AddViewGroup("ImageStream", viewMode="Pictures", mediaType="items")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")

  #ObjectContainer.art       = R(ART)
  ObjectContainer.title1     = PLUGIN_TITLE
  ObjectContainer.view_group = "InfoList"
  DirectoryObject.thumb      = R(ICON)

  HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
def MainMenu():
  oc = ObjectContainer(view_group = "List")
  oc.add(DirectoryObject(key=Callback(RecentPage), title=u"업데이트"))
  oc.add(DirectoryObject(key=Callback(CategoryMenu), title=u"카테고리"))
  oc.add(DirectoryObject(key=Callback(GenreMenu), title=u"장르"))
  #oc.add(PrefsObject(title=u"설정"))
  return oc

@route(PLUGIN_PREFIX+'/category')
def CategoryMenu():
  oc = ObjectContainer(title1=u"Category", view_group = "List")
  oc.add(DirectoryObject(key=Callback(CategoryPage, cid=28), title=u"주간"))
  oc.add(DirectoryObject(key=Callback(CategoryPage, cid=29), title=u"격주"))
  oc.add(DirectoryObject(key=Callback(CategoryPage, cid=30), title=u"월간"))
  oc.add(DirectoryObject(key=Callback(CategoryPage, cid=31), title=u"격월/비정기"))
  oc.add(DirectoryObject(key=Callback(CategoryPage, cid=32), title=u"단행본"))
  oc.add(DirectoryObject(key=Callback(CategoryPage, cid=33), title=u"완결"))
  #oc.add(DirectoryObject(key=Callback(CategoryPage, cid=34), title=u"붕탁"))
  #oc.add(DirectoryObject(key=Callback(CategoryPage, cid=35), title=u"와이!"))
  #oc.add(DirectoryObject(key=Callback(CategoryPage, cid=39), title=u"붕탁 완결"))
  return oc

@route(PLUGIN_PREFIX+'/genre')
def GenreMenu():
  oc = ObjectContainer(title1=u"Genre", view_group = "List")
  for name in GENRES:
    oc.add(DirectoryObject(key=Callback(GenrePage, keyword=name), title=name))
  return oc

####################################################################################################
@route(PLUGIN_PREFIX+'/recent/{page}')
def RecentPage(page='1'):
  oc = ObjectContainer(title1='#'+page, view_group = "List")
  url = RECENT_URL
  url += '&p='+page
  try:
    html = HTML.ElementFromURL(url, timeout=10.0)
  except:
    raise Ex.MediaNotAvailable
  # body
  for node in html.xpath("//a[contains(@class,'subj') and (contains(@href,'uid=') or contains(@href,'/b/mangaup/'))]"):
    url = node.get('href')
    if not url.startswith('http'):
      url = ROOT_URL + url
    title = node.xpath(".//div[@cid]")[0].text.strip()
    Log.Debug(title)
    stxt = node.xpath(".//div[contains(@class,'image-thumb')]")[0].get('style')
    thumb = ROOT_URL + RE_THUMB.search(stxt).group(1)

    oc.add(DirectoryObject(key=Callback(MangaPageWithUrl, url=url), title=title, thumb=thumb))
  # navigation
  nextpg = html.xpath("//div[@class='pagebox01']//span[@class='selected']/following-sibling::a[@class='notselected']")
  if nextpg:
    Log.Debug(nextpg[0].get('href'))
    oc.add(NextPageObject(key=Callback(RecentPage, page=nextpg[0].text), title="Next Page"))
  return oc

@route(PLUGIN_PREFIX+'/listpage')
def ListPage(url, page='1'):
  oc = ObjectContainer(title2='#'+page, view_group = "InfoList")
  page_url = url
  url += '&p='+page
  try:
    html = HTML.ElementFromURL(url, timeout=10.0)
  except:
    raise Ex.MediaNotAvailable
  # body
  for node in html.xpath("//div[@class='sbjx']/a"):
    url = node.get('href')
    if not url.startswith('http'):
      url = ROOT_URL + url
    title = u' '.join(node.xpath('.//text()'))
    thumb = node.xpath("../preceding-sibling::div//img")[0].get('src')

    # various URL cases
    match = RE_ARCHIVE.search(url)
    if match:
      #oc.add( PhotoAlbumObject(url=url, title=title, thumb=thumb) )
      oc.add(PhotoAlbumObject(
            key=Callback(GetPhotoAlbum, url=url, title=title),
            rating_key=url,
            title=title,
            source_title=PLUGIN_TITLE,
            thumb=thumb
            ))
      continue
    oc.add(DirectoryObject(key=Callback(MangaPageWithUrl, url=url), title=title, thumb=thumb))
  # navigation
  nextpg = html.xpath("//div[@class='pagebox01']//span[@class='selected']/following-sibling::a[@class='notselected']")
  if nextpg:
    Log.Debug(nextpg[0].get('href'))
    oc.add(NextPageObject(key=Callback(ListPage, url=page_url, page=nextpg[0].text), title="Next Page"))
  return oc

@route(PLUGIN_PREFIX+'/category/{cid}')
def CategoryPage(cid, page='1'):
  url = CATE_URL % int(cid)
  url += "&sort=%s" % Prefs['sort_type']
  return ListPage(url, page=page)

@route(PLUGIN_PREFIX+'/genre/{keyword}')
def GenrePage(keyword, page='1'):
  url = GENRE_URL + keyword
  url += "&sort=%s" % Prefs['sort_type']
  return ListPage(url, page=page)


####################################################################################################
@route(PLUGIN_PREFIX+'/manga')
def MangaPageWithUrl(url):
  try:
    html = HTML.ElementFromURL(url, timeout=10.0)
  except:
    raise Ex.MediaNotAvailable
  title = html.xpath("//meta[@property='og:title']")[0].get('content')
  oc = ObjectContainer(title2=title, view_group = "List")
  content = html.xpath("//div[@id='vContent']")[0]
  # episodes
  for node in content.xpath(".//a[contains(@href,'/archives/')]"):
    title = ' '.join(node.xpath('.//text()'))
    url = node.get('href')
    if not url.startswith('http'):
      url = ROOT_URL + url
    #oc.add( PhotoAlbumObject(url=url, title=title, thumb=None) )
    oc.add(PhotoAlbumObject(
            key=Callback(GetPhotoAlbum, url=url, title=title),
            rating_key=url,
            title=title,
            source_title=PLUGIN_TITLE,
            thumb=None
            ))
  # jump to manga main page
  for node in content.xpath(".//a[contains(@style,'color: rgb')]"):
    url = node.get('href')
    if not url.startswith('http'):
      url = ROOT_URL + url
    Log.Debug("Manga Top: "+url)
    title = node.text
    oc.add(DirectoryObject(key=Callback(MangaPageWithUrl, url=url), title=title, thumb=None))
  return oc

@route(PLUGIN_PREFIX+'/manga/{id}')
def MangaPage(id):
  url = MANGA_URL % int(id)
  return MangaPageWithUrl(url)

####################################################################################################
@route(PLUGIN_PREFIX + '/get/photoablum')
def GetPhotoAlbum(url, title):
    oc = ObjectContainer(title2=title.decode('utf-8'))

    url = url.replace("blog.yuncomics", "www.yuncomics")
    url = url.replace("shencomics", "yuncomics")
    page = HTTP.Request(url).content

    imgs = RE_IMGURL.findall(page)

    # sucuri
    if len(imgs) == 0:
        HEADERS['Cookie'] = get_sucuri_cookie(page)
        page = HTTP.Request(url, {'method':'GET'}, headers=HEADERS).content
        imgs = RE_IMGURL.findall(page)

    for idx, img_url in enumerate(imgs):
        Log.Debug(img_url)
        oc.add(
            PhotoObject(
                key = img_url,
                rating_key = img_url,
                title = str(idx+1),
                thumb = img_url,
                items = [MediaObject(parts=[PartObject(key=img_url)])]
            ))

    return oc

def get_sucuri_cookie(html):
    match = Regex("S\s*=\s*'([^']+)").search(html)
    if not match:
        return ""
    Log.Info("sucuri found")

    import base64
    import js2py
    s = base64.b64decode(match.group(1))
    Log.Debug(s)
    s = s.replace(";document.cookie", ";cookie")
    s = s.replace("; location.reload();", "")
    cookie = js2py.eval_js(s)
    Log.Debug(cookie)
    return cookie