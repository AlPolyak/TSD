from pysimplebase import SimpleBase
import json

#from ru.travelfood.simple_ui import NoSQL as noClass
from java import jclass
import uuid
import requests
from requests import post
from requests.auth import HTTPBasicAuth

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
db = noClass("dbtsd")

#https://api.github.com/repos/AlPolyak/TSD/contents/MY_TSD/TSD_GLOBAL.ui
# Функция запускается при старте программы ищет и устанавливает ID
def init_on_start(hashMap,_files=None,_data=None):
    result = db.get("idtsd")
    if not result:
        _idtsd=str(uuid.uuid4())
        db.put("idtsd",_idtsd,True)
        hashMap.put("_idtsd",_idtsd)
    else:
        hashMap.put("_idtsd",result)
    result = db.get("nametsd")
    if not result:
        _nametsd="ТСД 1"
        db.put("nametsd",_nametsd,True)
        hashMap.put("_nametsd",_nametsd)
    else:
        hashMap.put("_nametsd",result)
    hashMap.put("_IP",str(db.get("IP")))
    hashMap.put("_login1c",str(db.get("login1c")))
    hashMap.put("_password1c",str(db.get("password1c")))
    hashMap.put("_status_connect","Offline")
    return hashMap

# Функция запускается при вводе имени тсд
def set_name_tsd(hashMap,_files=None,_data=None):
    listener=hashMap.get("listener")
    if listener == "ntsd":
        ntsd=hashMap.get("ntsd")
        db.put("nametsd",ntsd,True)
        hashMap.put("_nametsd",ntsd)
    elif listener == "IP_field":
        IP=hashMap.get(listener)
        db.put("IP",IP,True)
        hashMap.put("_IP",IP)
    elif listener == "login1c_field":
        login1c=hashMap.get(listener)
        db.put("login1c",login1c,True)
        hashMap.put("_login1c",login1c)
    elif listener == "password1c_field":
        password1c=hashMap.get(listener)
        db.put("password1c",password1c,True)
        hashMap.put("_password1c",password1c)
    elif listener == "btn_back_set": 
        hashMap.put("BackScreen","")
    return hashMap

# Функция подключение к http сервису 1С
def connect(hashMap,_files=None,_data=None):
    hashMap.put("func1C","Подключение")
    names_put=["_idtsd","_nametsd"]
    names_get=["ТекстОшибки","ShowScreen"]
    newhashMap=callfunc1C(hashMap,names_put,names_get) 
    texterr=newhashMap.get("ТекстОшибки")
    if texterr=="":
        hashMap.put("ShowScreen",newhashMap.get("ShowScreen"))
    else:
        screenmessage(hashMap,texterr,"Ошибка соединения с 1С")
    return hashMap

# Функция выбор операции
def type_of_operation(hashMap,_files=None,_data=None):
    listener=hashMap.get("listener")
    if listener in ["btn_get","btn_put","btn_inv"]:
        db.put("typeofoperation",listener,True)
        hashMap.put("_typeofoperation",listener)
#        hashMap.put("noRefresh","");
#        hashMap.put("ShowScreen","Выбор документа")
    elif listener=="btn_ret":
        db.put("typeofoperation","",True)
        hashMap.put("_typeofoperation","")
        hashMap.put("BackScreen","")
    return hashMap

# Функция получить список документов 1С
def getlistdoc(hashMap,_files=None,_data=None):
    hashMap.put("func1C","ПолучитьСписок")
    names_put=["_idtsd","onClick","listener","_typeofoperation","_ТСД_Настройки"]
    names_get=["ТекстОшибки","ShowScreen","_ТСД_Настройки","cards","docresult"]
    newhashMap=callfunc1C(hashMap,names_put,names_get) 
    texterr=newhashMap.get("ТекстОшибки")
    if texterr!="":
        screenmessage(hashMap,texterr,"Ошибка соединения с 1С")
    else:
        # запишем документ результат в базу ТСД
        docresult=hashMap.get("docresult")
        if docresult != "":
            db.put("docresult",docresult,True)
    return hashMap

# Функция получить список строк выбранного документа 1С
def selecteddoc(hashMap,_files=None,_data=None):
    hashMap.put("func1C","ВыбранДокумент")
    names_put=["_idtsd","_typeofoperation","_ТСД_Настройки","selected_card_key"]
    names_get=["ТекстОшибки","ShowScreen","_ТСД_Настройки","cardsofproduct","docresult","_tabproducts"]
    newhashMap=callfunc1C(hashMap,names_put,names_get) 
    texterr=newhashMap.get("ТекстОшибки")
    if texterr!="":
        screenmessage(hashMap,texterr,"Ошибка соединения с 1С")
    return hashMap

# Функция при сканировании
#В зависимости от режима ПоДокументу ищем в документе или в базе 
def Scanning(hashMap,_files=None,_data=None):
    barcode=hashMap.get("barcode")
    _ТСД_Настройки=json.loads(hashMap.get("_ТСД_Настройки"))
    if _ТСД_Настройки["ПоДокументу"]=="true":
        # надо попытаться найти шк в табличной части _tabproducts
        _tabproducts=json.loads(hashMap.get("_tabproducts")) 
        # (Массив структур) *key;*Наименование;*Характеристика;*ЕдиницаИзмерения;
        # *Количество;*Факт;*Цена;*Сумма;*СуммаФакт;*barcodes(Массив);
        for prod in _tabproducts:
            namecol=prod["barcodes"]
            if barcode in prod[namecol]:
                hashMap.put("_curprod",json.dumps(prod,ensure_ascii=False))
                if _ТСД_Настройки["ВводКоличества"]=="true":
                    hashMap.put("ShowScreen","Ввод количества")
                    return hashMap
                else:
                    # просто добавим 1
                    plus1(hashMap,prod,1)
                    return hashMap
        else:
            hashMap.put("toast","Номенклатура со ШК:"+barcode+" в документе не найдена")
    if _ТСД_Настройки["ДобавлятьСтроки"]=="true":
        # не нашли, ищем в базе 
        hashMap.put("func1C","ПоискНоменклатуры")
        names_get=["Номенклатура"]
        names_put=["barcode"]
        newhashMap=callfunc1C(hashMap,names_put,names_get) 
        # получаем массив номенклатуры
        sprods=json.loads(newhashMap.get("Номенклатура"))
        if not sprods:
            hashMap=screenmessage(hashMap,"Не получена номенклатура по ШК:"+barcode) 
        else:
            retcode=sprods["КодЗавершения"] 
            hashMap=screenmessage(hashMap,retcode) 
            if retcode==0:
                prod=sprods["Номенклатура"][0]
                # Если найдена одна, то если есть настройка - ввод количества,
                # иначе добавление количества факт в накладную        
                hashMap.put("toast",prod["Номенклатура"])
                if _ТСД_Настройки["ВводКоличества"]=="true":
                    hashMap.put("ShowScreen","Ввод количества")
                    return hashMap
                else:
                    # просто добавим 1
                    plus1(hashMap,prod,1)
            elif retcode==3:
                # Если найдено несколько номенклатур, то показать выбор    
                hashMap.put("toast",sprods["ТекстОшибки"])
                hashMap=cardslist(hashMap,sprods["Номенклатура"])
                hashMap.put("ShowScreen","Выбор номенклатуры")
            else:
                hashMap.put("toast",sprods["ТекстОшибки"])
    return hashMap

# Функция вызов функции http сервиса 1С
def callfunc1C(hashMap,names_put,names_get):
    func1C=hashMap.get("func1C")     
    if not func1C:
        return hashMap
    noClass = jclass("ru.travelfood.simple_ui.NoSQL")
    db = noClass("dbtsd")
    IP = db.get("IP")
    if IP == None :
        hashMap.put("toast","Не задан IP http сервиса")
        return hashMap
    url = "http://"+IP+"/UNF/hs/simpleuiTSD/set_input_direct/"+func1C
    url = url.encode('UTF-8')
    login1c = db.get("login1c")
    if login1c == None :
        hashMap.put("toast","Не задан Login http сервиса")
        return hashMap
    password1c = str(db.get("password1c"))
    auth = HTTPBasicAuth(login1c.encode('UTF-8'), password1c.encode('UTF-8'))
    # подготовим параметры
    mp=[]
    names_put.append('_idtsd')
    for name in names_put:
        val=hashMap.get(name)
        if val != None:
            d={}
            d.update({"key":name,"value":val})
            mp.append(d)
    conv={'hashMap':mp} 
    _status_connect = "Offline"
    try:
        ret=post(url, json=conv, auth=auth, headers={'content-type': 'application/json; charset=utf-8'}, timeout=60)
        ret.encoding = 'UTF-8'
    except Exception as er :
        ErrorMessage="Ошибка подключения к http сервису 1С при выполнении функции: "+func1C+", "+ str(er)
    if ret.status_code == 200 :
        try:
            fullresp = json.loads(ret.text)
            newhashMap=fullresp['hashmap']
            for el in newhashMap:
                name=el["key"]
                if name in names_get:
                    hashMap.put(name,el["value"])
            ErrorMessage=fullresp['ErrorMessage']
            if ErrorMessage == '' :
                _status_connect = "Online"                              
        except Exception as er :
            ErrorMessage="Ошибка при получении результата HTTP запроса:"+ret.text +' '+ str(er)
    elif ret.status_code == 401 :
        ErrorMessage="Не корректный логин или пароль"
    else : 
        ErrorMessage="Ошибка подключения к http сервису 1С: "+str(ret.status_code)
    hashMap.put("ErrorMessage",ErrorMessage) 
    if ErrorMessage != "":
        hashMap=screenmessage(hashMap,ErrorMessage)       
    if _status_connect=="Online":
        color="<font color = ""#006400"">"
    else:
        color="<font color = ""red"">"
    hashMap.put("_status_connect",color+_status_connect+"</font>")
#    hashMap.put("RefreshScreen","")
    return hashMap

def screenmessage(hashMap,mess,cap_mess=None):
    hashMap.put("_message",str(mess))
    if cap_mess==None:
        cap_mess=""    
    hashMap.put("_cap_message",str(cap_mess))
    hashMap.put("ShowScreen","Сообщение")
    return hashMap

def cardslist(hashMap,object1):
    j = { "customcards":{
            "options":{
            "search_enabled":True,
            "save_position":True
            },
        "layout": {
        "type": "LinearLayout",
        "orientation": "vertical",
        "height": "match_parent",
        "width": "match_parent",
        "weight": "1",
        "Elements": [
        {
            "type": "TextView",
            "show_by_condition": "",
            "Value": "@string1",
            "TextSize": "20",
            "NoRefresh": False,
            "document_type": "",
            "mask": "",
            "Variable": ""
        },
        {
            "type": "TextView",
            "show_by_condition": "",
            "Value": "@string2",
            "TextSize": "20",
            "NoRefresh": False,
            "document_type": "",
            "mask": "",
            "Variable": ""
        },
        {
        "type": "TextView",
        "show_by_condition": "false",
        "Value": "@val",
        "NoRefresh": False,
        "document_type": "",
        "mask": "",
        "Variable": "",
        "TextSize": "16",
        "TextColor": "#DB7093",
        "TextBold": True,
        "TextItalic": False,
        "BackgroundColor": "",
        "width": "match_parent",
        "height": "wrap_content",
        }
        ]
        }
        }
    }

    j["customcards"]["cardsdata"]=[]
    i=0
    for prod in object1:
        c =  {
        "key": str(i),
        "string1": prod["Номенклатура"]+" "+prod["Характеристика"].rstrip(),
        "string2": prod["ЕдиницаИзмерения"],
        "val":  prod["Количество"]
        }
        i=i+1  
        j["customcards"]["cardsdata"].append(c)
    hashMap.put("cards_prod",json.dumps(j,ensure_ascii=False).encode('utf8').decode())
    return hashMap

# Ввод количества
def iputqtty(hashMap):
    _ТСД_Настройки=json.loads(hashMap.get("_ТСД_Настройки"))
    if _ТСД_Настройки["ВводКоличества"]=="true":   
        hashMap.put("ShowScreen","Ввод  количества")
    else:
        #  просто добавим количество
        prod=json.loads(hashMap.get("_curprod"))
        plus1(hashMap,prod,qnt)
    return hashMap

def plus1(hashMap,prod,qnt):
    # получим по prod ключи номенклатуры
    # поищем в документе результате эту номенклатуру
    # если нашли, добавим или заменим в зависимости от настройки qnt
    # если нет добавим строку
    return hashMap
    
