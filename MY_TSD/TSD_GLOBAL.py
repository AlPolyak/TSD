from pysimplebase import SimpleBase
import json
from pelicandb import Pelican,DBSession,feed
import os
from pathlib import Path
import os

#from ru.travelfood.simple_ui import NoSQL as noClass
from java import jclass
import uuid
import requests
from requests import post
from requests.auth import HTTPBasicAuth

noClass = jclass("ru.travelfood.simple_ui.NoSQL")
db = noClass("dbtsd")
#PELICAN
dbp = Pelican("samples_db1",path=os.path.dirname(Path(__file__).parent))

#https://api.github.com/repos/AlPolyak/TSD/contents/MY_TSD/TSD_GLOBAL.ui
# Функция запускается при старте программы ищет и устанавливает ID
def init_on_start(hashMap,_files=None,_data=None):
    #PELICAN
   # dbp["settings"].insert({"value":db.get("idtsd"),"_id":"idtsd"},upsert=True)
   # dbp["settings"].insert({"value":db.get("nametsd"),"_id":"nametsd"},upsert=True)
   # dbp["settings"].insert({"value":db.get("IP"),"_id":"IP"},upsert=True)
   # dbp["settings"].insert({"value":db.get("login1c"),"_id":"login1c"},upsert=True)
   # dbp["settings"].insert({"value":db.get("password1c"),"_id":"password1c"},upsert=True)
    
    result = dbp.get("idtsd")
    if not result:
        _idtsd=str(uuid.uuid4())
        dbp["settings"].insert({"value":_idtsd,"_id":"idtsd"},upsert=True)
        hashMap.put("_idtsd",_idtsd)
    else:
        hashMap.put("_idtsd",result["value"])
    result = dbp["settings"].get("nametsd")
    if not result:
        _nametsd="ТСД 1"
        dbp["settings"].insert({"value":_nametsd,"_id":"nametsd"},upsert=True)
        hashMap.put("_nametsd",_nametsd)
    else:
        hashMap.put("_nametsd",result["value"])
    hashMap.put("_IP",str(dbp["settings"].get("IP")["value"]))
    hashMap.put("_login1c",str(dbp["settings"].get("login1c")["value"]))
    hashMap.put("_password1c",str(dbp["settings"].get("password1c")["value"]))
    hashMap.put("_status_connect","Offline")
    return hashMap

# Функция запускается при вводе имени тсд
def set_name_tsd(hashMap,_files=None,_data=None):
    listener=hashMap.get("listener")
    if listener == "ntsd":
        ntsd=hashMap.get("ntsd")
        dbp["settings"].insert({"value":ntsd,"_id":"nametsd"},upsert=True)
        hashMap.put("_nametsd",ntsd)
    elif listener == "IP_field":
        IP=hashMap.get(listener)
        dbp["settings"].insert({"value":IP,"_id":"IP"},upsert=True)
        hashMap.put("_IP",IP)
    elif listener == "login1c_field":
        login1c=hashMap.get(listener)
        dbp["settings"].insert({"value":login1c,"_id":"login1c"},upsert=True)
        hashMap.put("_login1c",login1c)
    elif listener == "password1c_field":
        password1c=hashMap.get(listener)
        dbp["settings"].insert({"value":password1c,"_id":"password1c"},upsert=True)
        hashMap.put("_password1c",password1c)
    elif listener == "btn_back_set": 
        hashMap.put("BackScreen","")
    return hashMap

# Функция подключение к http сервису 1С
def connect(hashMap,_files=None,_data=None):
    hashMap.put("func1C","Подключение")
    names_put=["_idtsd","_nametsd","DEVICE_MODEL"]
    names_get=["ТекстОшибки","ShowScreen"]
    hashMap=callfunc1C(hashMap,names_put,names_get) 
    err=hashMap.get("errhttp")
    if err=="False":
        texterr=hashMap.get("ТекстОшибки")
        if str(texterr) != "":
            screenmessage(hashMap,"Ошибка connect: "+texterr,"Ошибка в функции 1С")
        hashMap.put("StartTimer","{\"handler\":[{\"event\": \"\",\"action\":\"run\",\"listener\":\"\",\"type\":\"python\",\"method\":\"testhttp\",\"postExecute\":\"\",\"alias\":\"\"}],\"period\":15000}")
        hashMap.put("StartTimers","")
    return hashMap

# Функция выбор операции
def type_of_operation(hashMap,_files=None,_data=None):
    listener=hashMap.get("listener")
    if listener in ["btn_get","btn_put","btn_inv"]:
        db.put("typeofoperation",listener,True)
        hashMap.put("_typeofoperation",listener)
    elif listener=="btn_ret":
        db.put("typeofoperation","",True)
        hashMap.put("_typeofoperation","")
        hashMap.put("ShowScreen","Подключение")
    else:
        hashMap.put("_typeofoperation","")
    return hashMap

# Функция получить список документов 1С
def getlistdoc(hashMap,_files=None,_data=None):
    if hashMap.get("_typeofoperation")=="":
        return hashMap
    hashMap.put("screenerr","Выбор операции")
    hashMap.put("func1C","ПолучитьСписок")
    names_put=["_idtsd","onClick","listener","_typeofoperation","_ТСД_Настройки"]
    names_get=["ТекстОшибки","ShowScreen","_ТСД_Настройки","cards","docresult"]
    hashMap=callfunc1C(hashMap,names_put,names_get) 
    err=hashMap.get("errhttp")
    if err=="False":
        texterr=hashMap.get("ТекстОшибки")
        if str(texterr) != "":
            screenmessage(hashMap,"Ошибка getlistdoc: "+texterr,"Ошибка в функции 1С")
        else:
            # запишем документ результат в базу ТСД
            docresult=hashMap.get("docresult")
            if docresult != "":
                db.put("docresult",docresult,True)
                # признак документ результат изменен и не записан в 1с
                hashMap.put("Изменен","нет")
    return hashMap

# Функция получить список строк выбранного документа 1С
def selecteddoc(hashMap,_files=None,_data=None):
    hashMap.put("screenerr","Выбор документа")
    hashMap.put("func1C","ВыбранДокумент")
    names_put=["_idtsd","_typeofoperation","_ТСД_Настройки","selected_card_key"]
    names_get=["ТекстОшибки","ShowScreen","_ТСД_Настройки","cardsofproduct","docresult","_tabproducts"]
    hashMap=callfunc1C(hashMap,names_put,names_get) 
    err=hashMap.get("errhttp")
    if err=="False":
        texterr=hashMap.get("ТекстОшибки")
        if str(texterr) != "":
            screenmessage(hashMap,"Ошибка selecteddoc: "+texterr,"Ошибка в функции 1С")
        else:
            # запишем документ результат в базу ТСД
            docresult=hashMap.get("docresult")
            if docresult != "":
                db.put("docresult",docresult,True)   
                # признак документ результат изменен и не записан в 1с
                hashMap.put("Изменен","нет")
    return hashMap

# Функция при сканировании
#В зависимости от режима ПоДокументу ищем в документе или в базе 
def Scanning(hashMap,_files=None,_data=None):
    barcode=hashMap.get("barcode")
    settings=json.loads(hashMap.get("_ТСД_Настройки"))
    if settings["ПоДокументу"]=="true":
        # надо попытаться найти шк в табличной части _tabproducts
        _tabproducts=json.loads(hashMap.get("_tabproducts")) 
        # (Массив структур) *key;*Номенклатура;*ЕдиницаИзмерения;*prodid;*characid;
        # *typeunit;*unitid;*Количество;*Факт;*Цена;*Сумма;*СуммаФакт;*barcodes(Массив);
        for prod in _tabproducts:
            namecol=prod["barcodes"]
            if barcode in prod[namecol]:
                # нашли строку в тч документа, передадим ее в процедуру ввода количества
                hashMap.put("_curprod",json.dumps(prod,ensure_ascii=False))
                if settings["ВводКоличества"]=="true":
                    hashMap.put("ShowScreen","Ввод количества")
                    return hashMap
                else:
                    # просто добавим 1
                    plus1(hashMap,prod,1,settings,False)
                    hashMap.put("toast","Кол. +1 " + _tabproducts[Номенклатура])
                    return hashMap
        else:
            hashMap.put("toast","Номенклатура со ШК:"+barcode+" в документе не найдена")
    if settings["ДобавлятьСтроки"]=="true":
        # не нашли, ищем в базе 
        hashMap.put("func1C","ПоискНоменклатуры")
        names_get=["Номенклатура"]
        names_put=["barcode"]
        hashMap=callfunc1C(hashMap,names_put,names_get) 
        err=hashMap.get("errhttp")
        if err=="False":
            texterr=hashMap.get("ТекстОшибки")
            if str(texterr) != "":
                screenmessage(hashMap,"Ошибка ПоискНоменклатуры: "+texterr,"Ошибка в функции 1С")
            else:
                # получаем массив номенклатуры
                sprods=json.loads(hashMap.get("Номенклатура"))
                if not sprods:
                    hashMap=screenmessage(hashMap,"Не получена номенклатура по ШК:"+barcode) 
                else:
                    retcode=sprods["КодЗавершения"] 
                    if retcode==0:
                        prod=sprods["Номенклатура"][0]
                        # Если найдена одна, то если есть настройка - ввод количества,
                        # иначе добавление количества факт в накладную        
                        if settings["ВводКоличества"]=="true":
                            hashMap.put("ShowScreen","Ввод количества")
                            return hashMap
                        else:
                            # просто добавим 1
                            plus1(hashMap,prod,1,settings,False)
                            hashMap.put("toast","Кол. +1 " + prod["Номенклатура"])
                    elif retcode==3:
                        # Если найдено несколько номенклатур, то показать выбор    
                        hashMap.put("toast",sprods["ТекстОшибки"])
                        hashMap=cardslist(hashMap,sprods["Номенклатура"])
                        hashMap.put("ShowScreen","Выбор номенклатуры")
                    else:
                        hashMap.put("toast",sprods["ТекстОшибки"])
    return hashMap

# Функция вызов функции http сервиса 1С
def callfunc1C(hashMap,names_put,names_get,showerr=True, httptimeout=100):
    hashMap.put("_status_connect","<font color=""red"">Offline</font>")
    try:
        ErrorMessage = ""
        hashMap.put("ТекстОшибки","")
        hashMap.put("errhttp","False")
        func1C=hashMap.get("func1C")   
        if not func1C:
            hashMap.put("errhttp","True")
            hashMap.put("ТекстОшибки","Не задана функция http сервиса")
            return hashMap
        noClass = jclass("ru.travelfood.simple_ui.NoSQL")
        db = noClass("dbtsd")
        IP = db.get("IP")
        if IP == None :
            hashMap.put("errhttp","True")
            hashMap.put("ТекстОшибки","Не задан IP http сервиса")
            return hashMap
        url = "http://"+IP+"/UNF/hs/simpleuiTSD/set_input_direct/"+func1C
        url = url.encode('UTF-8').decode() 
        login1c = db.get("login1c")
        if login1c == None :
            hashMap.put("errhttp","True")
            hashMap.put("ТекстОшибки","Не задан Login http сервиса");
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
        try:
            ret=post(url, json=conv, auth=auth, headers={'content-type': 'application/json; charset=utf-8'}, timeout=httptimeout)
            ret.encoding = 'UTF-8'
            if ret.status_code == 200 :
                try:
                    fullresp = json.loads(ret.text)
                    newhashMap=fullresp['hashmap']
                    for el in newhashMap:
                        name=el["key"]
                        if name in names_get:
                            hashMap.put(name,el["value"])
                    hashMap.put("_status_connect","<font color=""#006400"">Online</font>")
                except Exception as er :
                    ErrorMessage="Ошибка при получении результата HTTP запроса:"+ret.text +' '+ str(er)
            elif ret.status_code == 401 :
                ErrorMessage="Не корректный логин или пароль"
            else : 
                ErrorMessage="Ошибка подключения к http сервису 1С: "+str(ret.status_code)
        except Exception as er :
            ErrorMessage="Ошибка подключения к http сервису 1С при выполнении функции: "+func1C+", "+ str(er)  
    except Exception as er :
        ErrorMessage="Ошибка подключения к http сервису 1С при выполнении функции: "+func1C+", "+ str(er)
    hashMap.put("ErrorMessage",ErrorMessage) 
    if ErrorMessage != "":
        hashMap.put("errhttp","True") 
        if showerr:
            hashMap=screenmessage(hashMap,"Ошибка в функции callfunc1C:"+ErrorMessage)       
    return hashMap

def screenmessage(hashMap,mess,cap_mess=None):
    hashMap.put("_message",str(mess))
    if cap_mess==None:
        cap_mess="" 
    if hashMap.get("screenerr")=="" or hashMap.get("screenerr")==None:
        hashMap.put("screenerr",parent_screen)
    hashMap.put("_cap_message",str(cap_mess))
    hashMap.put("ShowScreen","Сообщение")
    return hashMap

def cardslist(hashMap,object1):
    j = {
        "customcards": {
            "options": {
                "search_enabled": True,
                "save_position": True
            },
            "layout": {
                "type": "LinearLayout",
                "orientation": "vertical",
                "height": "match_parent",
                "width": "match_parent",
                "weight": "0",
                "Elements": [
                {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "@Номенклатура",
                        "TextSize": "20",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": ""
                    },
                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "@ЕдиницаИзмерения",
                        "TextSize": "20",
                        "NoRefresh": False,
                        "document_type": "",
                        "mask": "",
                        "Variable": ""
                    },
                    {
                        "type": "TextView",
                        "show_by_condition": "",
                        "Value": "@Количество",
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
                        "height": "wrap_content"
                    }
                ]
            }
        }
    }
    
    j["customcards"]["cardsdata"]=[]
    for prod in object1:
        c =  {
        "key": str(object1.index(prod)),
        "Номенклатура": prod["Номенклатура"],
        "ЕдиницаИзмерения": prod["ЕдиницаИзмерения"],
        "prodid":  prod["prodid"],
        "characid":  prod["characid"],
        "unitid":  prod["unitid"],
        "typeunit":  prod["typeunit"],    
        "Количество":  prod["Количество"],
        "barcode":  prod["barcode"]            
        } 
        j["customcards"]["cardsdata"].append(c)
    hashMap.put("cards_prod",json.dumps(j,ensure_ascii=False).encode('utf8').decode())
    return hashMap

# Ввод количества
def inputqtty(hashMap,_files=None,_data=None):
    cards_prod=json.loads(hashMap.get("cards_prod"))
    selected_card_key=hashMap.get("selected_card_key")
    prod=cards_prod["customcards"]["cardsdata"][int(selected_card_key)]
    hashMap.put("qtty",prod["Количество"])
    hashMap.put("_curprod",json.dumps(prod,ensure_ascii=False))
    settings=json.loads(hashMap.get("_ТСД_Настройки"))
    # надо достать Факт из док результата по id номенклатуры Характеристике и Ед изм
    
    if settings["ВводКоличества"]=="true":   
        hashMap.put("ShowScreen","Ввод количества")
    else:
        #  просто добавим количество
        #screenmessage(hashMap,json.dumps(prod,ensure_ascii=False)) 
        plus1(hashMap,prod,prod["Количество"],_ТСД_Настройки) # Количество из ШК
    return hashMap

# добавление количества в документ после диалога ввода количества
def plus2(hashMap,_files=None,_data=None):
    qtty=hashMap.get("qtty")
    prod=json.loads(hashMap.get("_curprod"))
    settings=json.loads(hashMap.get("_ТСД_Настройки"))
    plus1(hashMap, prod, qtty, settings)
    return hashMap
    
def plus1(hashMap,prod,qnt,settings,showerr=True):
    try:
        # получим по prod ключи номенклатуры
        prodid=prod["prodid"]  
        characid=prod["characid"] 
        unitid=prod["unitid"]
        typeunit=prod["typeunit"]
        # поищем в документе результате эту номенклатуру
        docresult=json.loads(hashMap.get("docresult"))
        stocks=docresult["stocks"]
        yes=False
        for line in stocks:
            if line["prodid"]==prodid and line["characid"]==characid and line["unitid"]==unitid and line["typeunit"]==typeunit:
                # если нашли, добавим или заменим в зависимости от настройки qnt
                yes=True
                if settings["ЗаменятьКоличество"]=="true":
                    line["Факт"]=float(qnt)
                else:
                    line["Факт"]=line["Факт"]+float(qnt)
                break
        if yes == False:
            # если нет добавим строку 
            newline={
                     "Номенклатура":prod["Номенклатура"],
                     "prodid":prod["prodid"], 
                     "characid":prod["characid"], 
                     "ЕдиницаИзмерения":prod["ЕдиницаИзмерения"], 
                     "unitid":prod["unitid"], 
                     "typeunit":prod["typeunit"], 
                     "Факт":float(qnt), 
                     "key":str(uuid.uuid4()), 
                     "barcode":prod["barcode"]
            } 
            stocks.append(newline)  
        # признак документ результат изменен и не записан в 1с
        hashMap.put("Изменен","да")
        hashMap.put("docresult",json.dumps(docresult,ensure_ascii=False))
        # попробуем сохранить в 1с
        ok=savein1c(hashMap,showerr)
        if ok:
            hashMap.put("Изменен","нет")
    except Exception as er :
        hashMap=screenmessage(hashMap,"Ошибка в функции plus1:"+str(er))  
    hashMap.put("ShowScreen","Сканирование")
    return hashMap

def savein1c(hashMap,showerr=True):
    # запишем документ результат в базу ТСД
    docresult=hashMap.get("docresult")
    if docresult != "":
        db.put("docresult",docresult,True) 
    # требуется онлайн
    hashMap.put("func1C","СохранитьДокумент")
    names_put=["_idtsd","docresult","listener","_typeofoperation","_ТСД_Настройки"]
    names_get=["ТекстОшибки"]
    hashMap=callfunc1C(hashMap,names_put,names_get) 
    err=hashMap.get("errhttp")
    if err=="False":
        # нет ошибки соединения, проверим ошибку 1С
        texterr=hashMap.get("ТекстОшибки")
        if str(texterr) != "":
            # ошибка записи в 1С 
            if showerr:               
                screenmessage(hashMap,"Ошибка СохранитьДокумент: "+texterr,"Ошибка в функции 1С")
            return False      
        else:
            # все хорошо
            return True 
    # ошибка соединения http
    return False     

def savedoc(hashMap,_files=None,_data=None):
    if savein1c(hashMap,True):
        hashMap.put("toast","Документ записан в 1С")
    return hashMap   

def closedoc(hashMap,_files=None,_data=None):
    hashMap.put("screenerr","Сканирование")
    if hashMap.get("Изменен")=="да":
        if not savein1c(hashMap):
            return hashMap
    # попробуем закрыть документ в 1С
    hashMap.put("func1C","ЗакрытьДокумент")
    names_put=["_idtsd","docresult","_typeofoperation","Изменен"]
    names_get=["ТекстОшибки"]
    hashMap=callfunc1C(hashMap,names_put,names_get) 
    err=hashMap.get("errhttp")
    if err=="False":
        # нет ошибки соединения, проверим ошибку 1С
        texterr=hashMap.get("ТекстОшибки")
        if str(texterr) != "":
            # ошибка в 1С        
            screenmessage(hashMap,"Ошибка ЗакрытьДокумент: "+texterr,"Ошибка в функции 1С")
        else:
            # все хорошо
            hashMap.put("toast","Документ закрыт в 1С")
    # ошибка соединения http      
    return hashMap
    
# показ на экране документа результата
def showdoc(hashMap,_files=None,_data=None):
    docresult=json.loads(hashMap.get("docresult"))
    j = { "customcards":         {
        "options":{
          "search_enabled":True,
          "save_position":True
        },

        "layout": {
        "type": "LinearLayout",
        "orientation": "vertical",
        "height": "match_parent",
        "width": "match_parent",
        "weight": "0",
        "Elements": [
            {
                "type": "TextView",
                "show_by_condition": "",
                "Value": "@Номенклатура",
                "NoRefresh": False,
                "document_type": "",
                "mask": "",
                "Variable": ""
            },
            {
                "type": "TextView",
                "show_by_condition": "",
                "Value": "@barcode",
                "NoRefresh": False,
                "document_type": "",
                "mask": "",
                "Variable": ""
            },
            {
            "type": "TextView",
            "show_by_condition": "",
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
            "weight": 2
            }
            ]
         }
       }
     }
    j["customcards"]["cardsdata"]=[]
    stocks=docresult["stocks"]
    for line in stocks:
        c =  {
        "key": str(line["key"]),
        "val": str(line["Факт"])+" "+line["ЕдиницаИзмерения"],
        "Номенклатура": line["Номенклатура"],
        "barcode": line["barcode"]
            }
        j["customcards"]["cardsdata"].append(c)
    hashMap.put("list_doc",json.dumps(j,ensure_ascii=False).encode('utf8').decode())
    namedoc=docresult["type"]+" №"+docresult["Номер"]+" от "+docresult["Дата"]
    hashMap.put("namedoc",namedoc)
    hashMap.put("ShowScreen","Документ результат")    
    return hashMap    

def testhttp(hashMap,_files=None,_data=None):
    hashMap.put("func1C","ТестСвязи")
    names_put=["_idtsd"]
    names_get=["ТекстОшибки"]
    hashMap=callfunc1C(hashMap,names_put,names_get,False,10) 
    hashMap.put("RefreshScreen","")
    return hashMap     
    
