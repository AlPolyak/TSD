import json
from pelicandb import Pelican,DBSession,feed
import os
from pathlib import Path
import os

#from java import jclass
import uuid
import requests
from requests import post
from requests.auth import HTTPBasicAuth

#PELICAN
dbp = Pelican("samples_db1",path=os.path.dirname(Path(__file__).parent))
Settings=dbp["settings"]
Docs=dbp["docs"]

# запись константы
def setconst(name,value):
    Settings.insert({"value":value,"_id":name},upsert=True)
    return

# Чтение константы
def getconst(name):
    res=Settings.get(name)
    if res==None:
        return ""
    else:
        return str(res["value"])

#https://api.github.com/repos/AlPolyak/TSD/contents/MY_TSD/TSD_GLOBAL.ui
# Функция запускается при старте программы ищет и устанавливает ID
def init_on_start(hashMap,_files=None,_data=None): 
    try:
        _idtsd = getconst("idtsd")
        if _idtsd=="":
            _idtsd=str(uuid.uuid4())
            setconst("idtsd",_idtsd)
        hashMap.put("_idtsd",_idtsd)
        
        _nametsd = getconst("nametsd")
        if _nametsd=="":
            _nametsd="ТСД 1"
            setconst("nametsd",_nametsd)
        hashMap.put("_nametsd",_nametsd)

        hashMap.put("_IP",getconst("IP"))
        hashMap.put("_login1c",getconst("login1c"))
        hashMap.put("_password1c",getconst("password1c"))
        hashMap.put("_status_connect","Offline")
        hashMap.put("_was_connect","false")
        hashMap.put("_bool_connect","false")
        hashMap.put("Номенклатура","")
        hashMap.put("_indicator","▄")
        hashMap.put("StartTimer","{\"handler\":[{\"event\": \"\",\"action\":\"run\",\"listener\":\"\",\"type\":\"python\",\"method\":\"testhttp\",\"postExecute\":\"\",\"alias\":\"\"}],\"period\":10000}")
        hashMap.put("StartTimers","")
    except Exception as er :
        ErrorMessage="Ошибка "+ str(er)
    return hashMap

# Функция запускается при вводе имени тсд
def set_name_tsd(hashMap,_files=None,_data=None):
    listener=hashMap.get("listener")
    if listener == "ntsd":
        ntsd=hashMap.get("ntsd")
        setconst("nametsd",ntsd)
        hashMap.put("_nametsd",ntsd)
    elif listener == "IP_field":
        IP=hashMap.get(listener)
        setconst("IP",IP)
        hashMap.put("_IP",IP)
    elif listener == "login1c_field":
        login1c=hashMap.get(listener)
        setconst("login1c",login1c)
        hashMap.put("_login1c",login1c)
    elif listener == "password1c_field":
        password1c=hashMap.get(listener)
        setconst("password1c",password1c)
        hashMap.put("_password1c",password1c)
    elif listener == "btn_back_set": 
        hashMap.put("BackScreen","")
    return hashMap

# Функция подключение к http сервису 1С
def connect(hashMap,_files=None,_data=None):
    try:
        hashMap.put("screenerr","Подключение")
        hashMap.put("func1C","Подключение")
        names_put=["_idtsd","_nametsd","DEVICE_MODEL"]
        names_get=["ТекстОшибки","toast"]
        hashMap=callfunc1C(hashMap,names_put,names_get) 
        noerr=hashMap.get("_bool_connect")
        if noerr=="true":
            texterr=hashMap.get("ТекстОшибки")
            if str(texterr) != "": #  при ошибке 1с выводим сообщение
                if  hashMap.get("_was_connect")=="false":
                    hashMap.put("_bool_connect","false") # считаем что не подключено пререзапускаем таймер
                    screenmessage(hashMap,"Ошибка подключения к 1С: "+texterr,"Ошибка в функции 1С")
            else: # все хорошо
                hashMap.put("_was_connect","true") 
    except Exception as er :
        screenmessage(hashMap,"Ошибка подключения к 1С: "+str(er),"Ошибка в функции PY")
    return hashMap

def setasync(hashMap,returnnames):
    hashMap.put("_StackAddMode","") 
    if returnnames==None or returnnames=="":
        return hashMap
    returnnames=returnnames.replace(" ", "") 
    hashMap.put("returnnames",returnnames)
    listnames=returnnames.split(",")
    for name in listnames:
        hashMap.put(name+"_async",hashMap.get(name)) 
    return hashMap

def useasync(hashMap):
    if hashMap.get("_StackAddMode")==None:
        return hashMap
    hashMap.remove("_StackAddMode")
    returnnames=hashMap.get("returnnames")
    if returnnames==None or returnnames=="":
        return hashMap
    listnames=returnnames.split(",")
    for name in listnames:
        hashMap.put(name,hashMap.get(name+"_async"))
        hashMap.remove(name+"_async")
    hashMap.remove("returnnames")
    return hashMap

# Функция выбор операции
def type_of_operation(hashMap,_files=None,_data=None):
    try:
        listener=hashMap.get("listener")
        if listener==None or listener=="":
             listener=hashMap.get("onClick")
        if listener=="finishtimer":
            return hashMap
        if listener in ["btn_get","btn_put","btn_inv"]:
            setconst("typeofoperation",listener)
            hashMap.put("_typeofoperation",listener)
            if listener=="btn_get":
                captionscr="Приемка"
            elif listener=="btn_put":
                captionscr="Отгрузка"
            elif listener=="btn_inv":
                captionscr="Инвент."
            else:
                captionscr=""
            hashMap.put("typeopstr",captionscr)     
            # Проверим соединение с 1С, если не было запустим подключение
            if hashMap.get("_was_connect")=="false":
                connect(hashMap,_files,_data)
            #В зависимости от выбранного типа операции получим docsource и docresult из базы ТСД
            md=Docs.get("listener")
            # если документ результат из базы ТСД пустой, то переходим к запросу списка документов
            # иначе переходим на экран сканирования, там возможно завершение документа
            if md != None:
                docresult=str(md["docresult"])
                hashMap.put("docresult",docresult) # документ результат
                hashMap.put("_docsource",str(md["docsource"])) # документ источник
                hashMap.put("cardsofproduct",str(md["cardsofproduct"])) # список карточек ТЧ документа источника
                if docresult!=None and docresult!="":
                    hashMap.put("ShowScreen","Сканирование")
                    return hashMap
            if hashMap.get("_bool_connect")=="false":
                hashMap.put("screenerr","Выбор операции")
                hashMap=screenmessage(hashMap,"Для дальнейшей работы тебуется подключение к базе 1С","Ошибка нет связи с 1С")
            else:
                hashMap=getlistdoc(hashMap,None,None)   
                hashMap.put("ShowScreen","Выбор документа")
        elif listener=="btn_set":
            setconst("typeofoperation","")
            hashMap.put("_typeofoperation","")
            hashMap.put("ShowScreen","Настройки")
        else:
            hashMap.put("toast","else")
            setconst("typeofoperation","")
            hashMap.put("_typeofoperation","")
    except Exception as er :
        hashMap=screenmessage(hashMap,"Ошибка при выборе операции: "+str(er),"Ошибка в функции PY")
    return hashMap

# Функция получить список документов 1С
def getlistdoc(hashMap,_files=None,_data=None):
    _typeofoperation=hashMap.get("_typeofoperation")
    hashMap.put("screenerr","Выбор операции")
    hashMap.put("func1C","ПолучитьСписок")
    names_put=["_idtsd","_typeofoperation","_ТСД_Настройки"]
    names_get=["ТекстОшибки","ShowScreen","toast","_ТСД_Настройки","cards","docresult"]
    hashMap=callfunc1C(hashMap,names_put,names_get) 
    noerr=hashMap.get("_bool_connect")
    if noerr=="true":
        texterr=hashMap.get("ТекстОшибки")
        if str(texterr) != "":
            screenmessage(hashMap,"Ошибка при получении списка документов: "+texterr,"Ошибка в функции 1С")
        else:
            # запишем документ результат в базу ТСД
            docresult=str(hashMap.get("docresult"))
            if docresult != "":
                # значит не по документу
                hashMap.put("_docsource","") # не по документу
                Docs.insert({"docsource":"",
                             "docresult":docresult,
                             "cardsofproduct":"",
                             "_id":_typeofoperation}, upsert=True)
                # признак документ результат изменен и не записан в 1с
                hashMap.put("Изменен","нет")
    return hashMap

# Функция получить выбранный документ 1С
def selecteddoc(hashMap,_files=None,_data=None):
    try:
        hashMap.put("screenerr","Выбор документа")
        hashMap.put("func1C","ВыбранДокумент")
        names_put=["_idtsd","_typeofoperation","_ТСД_Настройки","selected_card_key"]
        names_get=["ТекстОшибки","ShowScreen","toast","_ТСД_Настройки","cardsofproduct","docresult","_docsource"]
        hashMap=callfunc1C(hashMap,names_put,names_get) 
        noerr=hashMap.get("_bool_connect")
        if noerr=="true":
            texterr=hashMap.get("ТекстОшибки")
            if str(texterr) != "":
                screenmessage(hashMap,"Ошибка выбора документа: "+texterr,"Ошибка в функции 1С")
            else:
                # запишем документы в базу ТСД
                docsource=str(hashMap.get("_docsource"))
                docresult=str(hashMap.get("docresult"))
                cardsofproduct=str(hashMap.get("cardsofproduct"))
                _typeofoperation=hashMap.get("_typeofoperation")
                if docresult != "":
                    # если выбран документ, то в 1С обязательно создается документ результат
                    Docs.insert({"docsource":docsource,
                                 "docresult":docresult,
                                 "cardsofproduct":cardsofproduct,
                                 "_id":_typeofoperation}, upsert=True)  
                    # признак документ результат изменен и не записан в 1с
                    hashMap.put("Изменен","нет")
                    hashMap.put("namedoc",json.loads(docsource)["namedoc"])
                    # ("ShowScreen","Сканирование") устанавливается в 1С
                else:
                    hashMap=screenmessage(hashMap,"Ошибка выбора документа: не получен документ результат из 1С","Ошибка в функции 1С")
    except Exception as er :
        hashMap=screenmessage(hashMap,"Ошибка при выборе документа, "+ str(er))     
    return hashMap

# Функция при сканировании
#В зависимости от режима ПоДокументу ищем в документе или в базе 
def Scanning(hashMap,_files=None,_data=None):
    try:
        barcode=hashMap.get("barcode")
        settings=json.loads(hashMap.get("_ТСД_Настройки"))
        if settings["ЗаменятьКоличество"]=="true":
            modeqtty="Режим ""Замена"""
        else:
            modeqtty="Режим ""Добавление"""
        if settings["ПоДокументу"]=="true":
            # надо попытаться найти шк в табличной части _docsource
            strdoc=str(hashMap.get("_docsource"))
            if strdoc=="":
                hashMap=screenmessage(hashMap,"Ошибка : не найден документ источник","Ошибка в функции сканирование")    
                return hashMap
            _docsource=json.loads(strdoc) 
            namedoc=_docsource["namedoc"]
            stocks=_docsource["stocks"]
            if stocks==None:
                hashMap=screenmessage(hashMap,"Ошибка : не найдена табличная часть документа источника","Ошибка в функции сканирование")    
                return hashMap
            # (Массив структур) *key;*Номенклатура;*ЕдиницаИзмерения;*prodid;*characid;
            # *typeunit;*unitid;*Количество;*Факт;*Цена;*Сумма;*СуммаФакт;*barcodes(Массив);
            for prod in stocks:
                if barcode in prod["barcodes"]:
                    # нашли строку в тч документа, передадим ее в процедуру ввода количества
                    hashMap.put("_curprod",json.dumps(prod,ensure_ascii=False))
                    if settings["ВводКоличества"]=="true":
                        # инициализируем количество из строки 
                        hashMap.put("nameinputqtty",prod["Номенклатура"])
                        ЕдиницаИзмерения=prod["ЕдиницаИзмерения"]
                        hashMap.put("unit",ЕдиницаИзмерения)
                        hashMap.put("namedoc",namedoc)
                        hashMap.put("qttydoc",str(prod["Факт"])+" "+ЕдиницаИзмерения)
                        hashMap.put("qtty","1")
                        hashMap.put("modeqtty",modeqtty)
                        hashMap.put("ShowScreen","Ввод количества")
                        return hashMap
                    else:
                        # просто добавим 1
                        plus1(hashMap,prod,1,settings,False)
                        hashMap.put("toast","Кол. +1 " + stocks[Номенклатура])
                        return hashMap
            else:
                hashMap.put("toast","Номенклатура со ШК:"+barcode+" в документе не найдена")
        if settings["ДобавлятьСтроки"]=="true":
            # не нашли, ищем в базе 
            hashMap.put("func1C","ПоискНоменклатуры")
            names_get=["Номенклатура"]
            names_put=["barcode"]
            hashMap=callfunc1C(hashMap,names_put,names_get) 
            noerr=hashMap.get("_bool_connect")
            if noerr=="true":
                texterr=hashMap.get("ТекстОшибки")
                if str(texterr) != "":
                    hashMap=screenmessage(hashMap,"Ошибка поиска Номенклатуры: "+texterr,"Ошибка в функции 1С")
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
                                hashMap.put("nameinputqtty",prod["Номенклатура"])
                                ЕдиницаИзмерения=prod["ЕдиницаИзмерения"]
                                hashMap.put("unit",ЕдиницаИзмерения)
                                hashMap.put("namedoc",namedoc)
                                hashMap.put("qttydoc",str(prod["Количество"])+" "+ЕдиницаИзмерения)
                                hashMap.put("qtty","1")       
                                hashMap.put("modeqtty",modeqtty)
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
    except Exception as er :
        hashMap=screenmessage(hashMap,"Ошибка при сканировании, "+ str(er)) 
    return hashMap

# Функция вызов функции http сервиса 1С
def callfunc1C(hashMap,names_put,names_get,showerr=True, httptimeout=100):
    _bool_connect=hashMap.get("_bool_connect")
    _status_connect="<font color=""red"">Offline</font>"
    _bool_connectnew="false"
    try:
        ErrorMessage = ""
        hashMap.put("ТекстОшибки","")
        func1C=hashMap.get("func1C")   
        if not func1C:
            hashMap.put("ТекстОшибки","Не задана функция http сервиса")
            return hashMap
        IP = getconst("IP")
        if IP == None :
            hashMap.put("ТекстОшибки","Не задан IP http сервиса")
            return hashMap
        url = "http://"+IP+"/UNF/hs/simpleuiTSD/set_input_direct/"+func1C
        url = url.encode('UTF-8').decode() 
        login1c = getconst("login1c")
        if login1c == None :
            hashMap.put("ТекстОшибки","Не задан Login http сервиса");
            return hashMap
        password1c = getconst("password1c")
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
                    _status_connect="<font color=""#006400"">Online</font>"
                    _bool_connectnew="true"
                except Exception as er :
                    ErrorMessage="Ошибка при получении результата HTTP запроса:"+ret.text +' '+ str(er)
            elif ret.status_code == 401 :
                ErrorMessage="Не корректный логин или пароль"
            else : 
                ErrorMessage="Ошибка подключения к http сервису 1С: "+str(ret.status_code)
        except Exception as er : # таймаут
            ErrorMessage="Ошибка подключения к http сервису 1С при выполнении функции: "+func1C+", "+ str(er)  
    except Exception as er :
        ErrorMessage="Ошибка подключения к http сервису 1С при выполнении функции: "+func1C+", "+ str(er)
    if ErrorMessage != "": 
        if showerr==True:
            hashMap.put("ErrorMessage",ErrorMessage) 
    _was_connect = hashMap.get("_was_connect")
    if _bool_connect != _bool_connectnew or _was_connect == "false":
        hashMap.put("_status_connect",_status_connect)
        hashMap.put("_bool_connect",_bool_connectnew)
    return hashMap

def screenmessage(hashMap,mess,cap_mess=None):
    hashMap.put("_message",str(mess))
    if cap_mess==None:
        cap_mess="" 
    screenerr=hashMap.get("screenerr")
    if screenerr=="" or screenerr==None:
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
        savein1c(hashMap,showerr)
       # if settings["ПоДокументу"]=="true":
            # сформируем новый список строк документа источника с учетом введенного количествa
            # переформируем cardsofproduct
            
    except Exception as er :
        hashMap=screenmessage(hashMap,"Ошибка в функции добавления количества:"+str(er))  
    hashMap.put("ShowScreen","Сканирование")
    return hashMap

def savein1c(hashMap,showerr=True):
    # запишем документ результат в базу ТСД
    docresult=str(hashMap.get("docresult"))
    docsource=str(hashMap.get("_docsource"))
    _typeofoperation=hashMap.get("_typeofoperation")
    if docresult != "":
        Docs.insert({"docsource":docsource, "docresult":docresult, "_id":_typeofoperation}, upsert=True) 
    # требуется онлайн
    hashMap.put("func1C","СохранитьДокумент")
    names_put=["_idtsd","docresult","listener","_typeofoperation","_ТСД_Настройки"]
    names_get=["ТекстОшибки"]
    hashMap=callfunc1C(hashMap,names_put,names_get) 
    noerr=hashMap.get("_bool_connect")
    if noerr=="true":
        # нет ошибки соединения, проверим ошибку 1С
        texterr=hashMap.get("ТекстОшибки")
        if str(texterr) != "":
            # ошибка записи в 1С 
            if showerr:               
                screenmessage(hashMap,"Ошибка при сохранении документа в 1С: "+texterr,"Ошибка в функции 1С")
            return False      
        else:
            # все хорошо
            hashMap.put("Изменен","нет")
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
    names_get=["ТекстОшибки","toast"]
    hashMap=callfunc1C(hashMap,names_put,names_get) 
    noerr=hashMap.get("_bool_connect")
    if noerr=="true":
        # нет ошибки соединения, проверим ошибку 1С
        texterr=hashMap.get("ТекстОшибки")
        if str(texterr) != "":
            # ошибка в 1С        
            hashMap=screenmessage(hashMap,"Ошибка при закрытии документа в 1С: "+texterr,"Ошибка в функции 1С")
        else:
            # все хорошо
            # удалим из тсд
            Docs.insert({"docsource":"", "docresult":"", "_id":_typeofoperation}, upsert=True) 
            hashMap.put("docresult","")
            hashMap.put("_docsource","")
            hashMap.put("toast","Документ закрыт в 1С")
            hashMap.put("Изменен","нет")
    # ошибка соединения http      
    return hashMap
    
# показ на экране документа результата
def showdoc(hashMap,_files=None,_data=None):
    typeopstr=hashMap.get("typeopstr")
    hashMap.put("SetTitle",typeopstr+" [Документ результат]")
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

def showhashmap(hashMap,v=False):
    l  = []
    it = hashMap.entrySet().iterator()
    while it.hasNext(): 
        pair = it.next()
        if v:
            l.append("<font color=""#006400"">"+pair.getKey()+"</font>"+":"+str(pair.getValue())+"<br>")
        else:
            l.append(pair.getKey()+"<br>")
    hashMapstr=';'.join(l)
    hashMap.put("screenerr",hashMap.get("current_screen_name"))
    hashMap=screenmessage(hashMap,json.dumps(hashMapstr,ensure_ascii=False).encode('utf8').decode(),"")    

def testhttp(hashMap,_files=None,_data=None):
    if  hashMap.get("_was_connect")=="false":
        connect(hashMap,_files,_data)   
        returnnames="_bool_connect,_was_connect,ТекстОшибки,_status_connect,_indicator,toast"
    else:
        hashMap.put("func1C","ТестСвязи")
        # восстановим из базы ТСД _idtsd
        hashMap.put("_idtsd",getconst("idtsd"))       
        names_put=["_idtsd"]
        names_get=["ТекстОшибки"]
        hashMap=callfunc1C(hashMap,names_put,names_get,False,10) 
        returnnames="_bool_connect,_was_connect,_status_connect,ТекстОшибки,_indicator,toast,NoRefresh"
    if hashMap.get("_bool_connect")=="false":
        ind="<font color=""Red"">█</font>"
    else:
        ind=hashMap.get("_indicator")
        if ind=="<font color=""#009688"">▄</font>":
            ind="<font color=""#1DE9B6"">▀</font>"
        else:
            ind="<font color=""#009688"">▄</font>"
    hashMap.put("_indicator",ind) 
    hashMap.put("NoRefresh","")
    hashMap=setasync(hashMap, returnnames)
    hashMap.remove("toast")
    hashMap.put("SendIntent","finishtimer")
    return hashMap     

def posttimer(hashMap,_files=None,_data=None):
    hashMap=useasync(hashMap)
    #if hashMap.get("current_screen_name")=="Ввод количества":
    hashMap.put("NoRefresh","")
    hashMap.remove("RefreshScreen")
    #hashMap.put("toast",hashMap.get("current_screen_name"))
    #showhashmap(hashMap,True)
    return hashMap     
