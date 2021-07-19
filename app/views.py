from django.shortcuts import render,redirect
from django.http import HttpResponse
import pymysql
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from sklearn.cluster import KMeans
from sklearn import metrics
import numpy as np

# Create your views here.


def connect():
    try:
        db = pymysql.connect('rm-2vcph5luf4v959b2v2o.mysql.cn-chengdu.rds.aliyuncs.com', 'cqucs_stu2', 'cqucqu123',
                             'two_hand', autocommit=True)
        print('连接成功')
    except:
        print('连接失败')

    return db, db.cursor()


def disconnect(db, cursor):
    cursor.close()
    db.close()


def select(cur, sql, args=None):
    cur.execute(sql, args)



def rate_rank():
    sql8 = """SELECT Brand, avg_rate FROM
                (SELECT Brand, time, avg(rate) as avg_rate FROM cr
                WHERE Brand = %s
                GROUP BY time ORDER BY avg_rate DESC 
                ) as a LIMIT 5"""
    brand = [['别克'], ['大众'], ['奔驰'], ['宝马'], ['奥迪'], ['福特'], ['雪佛兰'], ['保时捷'], ['马自达'], ['荣威']]
    list_temp = []
    db, cursor = connect()
    for B in brand:
        select(cursor, sql8, B[0])
        data1 = cursor.fetchall()

        for item in data1:
            list_temp.append(list(item))

    list_table = []
    for i in range(len(brand)):
        rate = [x[1] for x in list_temp[i * 5:i * 5 + 5]]
        list_table.append(brand[i])
        for j in rate:
            list_table[i].append(round(j, 4))
        avg_rate = sum(rate) / 5
        list_table[i].append(round(avg_rate, 4))
    sorted_table = sorted(list_table, key=lambda a: a[6], reverse=True)
    disconnect(db, cursor)

    return sorted_table


def avg_price():
    brand = [['别克'], ['大众'], ['奔驰'], ['宝马'], ['奥迪'], ['福特'], ['雪佛兰'], ['保时捷'], ['马自达'], ['荣威']]
    sql9 = """SELECT Brand, avg(Sec_price) as avg_price FROM cr WHERE Brand = %s"""
    sql10 = """select Sec_price from cr where Brand = %s"""
    list_avg = []
    db, cursor = connect()
    for B in brand:
        list_temp = []
        select(cursor, sql10, B[0])
        data1 = cursor.fetchall()
        for item in data1:
            list_temp.append(float(item[0]))
        avg = sum(list_temp)/len(list_temp)
        list_avg.append(round(avg, 4))

    brand_name = [x[0] for x in brand]
    disconnect(db, cursor)
    return brand_name, list_avg


def salerate():#销量前10车辆的销售数所占比例,输出:(品牌,销售数量)
    # connect with the database
    db, cursor = connect()
    reslist = []
    sql = """
        select Brand,count(Brand) as cb from cr group by Brand order by cb DESC limit 10
        """
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        for row in results:
            id=row[0]
            num=int(row[1])
            reslist.append((id,num))
    except Exception as e:
        raise e
    finally:
        pass
    # 关闭数据库连接
    disconnect(db, cursor)
    name = [x[0] for x in reslist]
    price = [x[1] for x in reslist]
    return name, price


def index(request):
    table = rate_rank()
    context = dict()
    context['table'] = table
    context['title'] = ['品牌', '1年保值率', '2年保值率', '3年保值率', '4年保值率', '5年保值率', '平均保值率']
    brand, avg_p = avg_price()
    context['brand'] = brand
    context['avg_price'] = avg_p
    _, num = salerate()
    context['car_num'] = num
    class_center, class_num = cluster()
    context['class1'] = class_center[0]
    context['class2'] = class_center[1]
    context['class3'] = class_center[2]
    context['class4'] = class_center[3]
    context['class_num1'] = class_num[0]
    context['class_num2'] = class_num[1]
    context['class_num3'] = class_num[2]
    context['class_num4'] = class_num[3]
    return render(request,'index.html', context)

def cluster():
    sql12 = """select Brand, Km, Sec_price, New_price, time, rate 
                    from cr where Brand = %s"""
    brand = [['别克'], ['大众'], ['奔驰'], ['宝马'], ['奥迪'], ['福特'], ['雪佛兰'], ['保时捷'], ['马自达'], ['荣威']]
    list_temp = []  # 每一型号的车的特征组成的list，不包括品牌名
    list_item = []  # 每一型号的车的特征组成的list，包括品牌名
    db, cursor = connect()
    for B in brand:
        select(cursor, sql12, B[0])
        data1 = cursor.fetchall()
        for item in data1:
            list_num = []
            # print(item)
            list_item.append(item)
            for i in range(1, 6):
                list_num.append(float(item[i]))
            list_temp.append(list_num)
            # print(list_num)
    list_temp = np.array(list_temp)
    list_item = np.array(list_item)
    # 聚合4类时效果最佳
    kmeans = KMeans(n_clusters=4)
    kmeans.fit(list_temp)
    y_pred = kmeans.fit_predict(list_temp)
    # sc评估标准
    sc = metrics.silhouette_score(list_temp, y_pred)
    # ch评估标准
    ch = metrics.calinski_harabasz_score(list_temp, y_pred)
    # sse误差函数
    sse = kmeans.inertia_
    list_center = []
    for class_ in kmeans.cluster_centers_:
        temp = []
        for i in range(5):
            if i == 3:
                temp.append(round(class_[i], 0))
            else:
                temp.append(round(class_[i], 3))
        list_center.append(temp)
    class_1, class_2, class_3, class_4 = 0, 0, 0, 0
    for i in range(len(y_pred)):
        if y_pred[i] == 0:
            class_1 += 1
        elif y_pred[i] == 1:
            class_2 += 1
        elif y_pred[i] == 2:
            class_3 += 1
        elif y_pred[i] == 3:
            class_4 += 1
    print('class number: {}, {}, {}, {}'.format(class_1, class_2, class_3, class_4))
    class_num = [class_1, class_2, class_3, class_4]
    return list_center, class_num


def draw(request):
    return render(request, 'draw.html')



def gotoindex(request):
    return redirect('/app/index/')

def connect2():
    try:
        db = pymysql.connect('rm-2vcph5luf4v959b2v2o.mysql.cn-chengdu.rds.aliyuncs.com', 'cqucs_stu2', 'cqucqu123',
                             'two_hand', autocommit=True)
        print('connection succeeded')
    except:
        print('连接失败')

    return db.cursor()


def details(request): #传入要查询的品牌名字
    brand="宝马"#默认值是宝马车型的数据
    if request.method=="POST":
        brand=request.POST.get('brandname')
        return render(request,'details.html',locals())
    return render(request,'details.html',locals())

def price_distribution(brand):  # 图1(柱状)
    cursor = connect2()
    sql = """
    select Sec_price from cr where Brand = '{0}'
    """.format(brand)

    try:
        cursor.execute(sql)
        results = cursor.fetchall()

        price_section = [0] * 12
        for row in results:
            temp = int(row[0] / 10)
            if (temp >= 10):
                price_section[10] += 1
            else:
                price_section[temp] += 1

    except Exception as e:
        raise e
    finally:
        pass
    cursor.close()
    # conn.close()

    # print(price_section)
    return price_section


def Brand_rate(brand):  # 图2()
    cursor = connect2()
    sql7 = """SELECT Brand, time, avg(rate) as avg_rate FROM cr
                    WHERE Brand = %s
                    GROUP BY time ORDER BY time DESC """
    cursor.execute(sql7, brand)
    data1 = cursor.fetchall()
    list_temp = []
    for item in data1:
        list_temp.append(list(item))
    time = [x[1] for x in list_temp]
    rate = [x[2] for x in list_temp]
    rate[-1] = 1
    cursor.close()
    time.reverse()
    rate.reverse()
    return time, rate


def nummanufacture(brand):  # 图3(柱状)
    # 各出厂年份的车辆售出数 :brand:车辆品牌，输出：(年份,数量)
    # connect with the database
    cursor = connect2()
    reslist = []
    amount_eachyear = []
    for i in range(2000, 2018):
        sql = """
        SELECT count(*) FROM cr where Name like '%{0}款%' and Brand like '{1}';
        """.format(i, brand)

        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            for row in results:
                id = row[0]
                amount_eachyear.append(id)
            reslist.append((i, id))  # year,num
        except Exception as e:
            raise e
        finally:
            pass
    cursor.close()

    # print(amount_eachyear)

    # 返回一个长度为17的列表
    return amount_eachyear


def num_categorized_by_year(brand):  # 图4(饼状)同一品牌不同车龄的车辆数（可化为饼图，自动转化为所占百分比）,输入:brand：品牌，输出:(车龄，数量)
    # connect with the database
    cursor = connect2()
    reslist = []
    sql = """
        SELECT SL,count(SL)  as 'total_num' from(SELECT Brand,left(Boarding_time,4) AS 'SL' FROM cr where Brand like '{0}') AS A GROUP BY SL  ORDER BY SL ASC

        """.format(brand)

    try:
        cursor.execute(sql)
        results = cursor.fetchall()

        for row in results:
            id = 2017 - int(row[0])  # id是车龄吧?
            reslist.append((id, int(row[1])))  # year,num
    except:
        print("出错了")

    cursor.close()  # 关闭数据库连接

    num_age = []
    reslist.reverse()

    for i in range(10):
        num_age.append(reslist[i][1])
    return num_age

# index 页面跳转
@csrf_exempt
def draw_all(request):
    if request.method=="POST":
        brand=request.POST.get('brandname','奥迪')
        resp = redirect('/app/details/')
        # cookie不支持有中文的utf-8编码，先处理为latin-1可编码的形式
        resp.set_cookie('brand', brand.encode('utf-8').decode('latin-1'), max_age=30)
        print(request.POST)
        print(brand)
        return resp
    else:
        # 得到的cookie先用latin-1解码，再用utf-8编回中文
        flg=request.COOKIES.get('flag')
        if not flg:
            false_msg = redirect('/app/login_wrong/')
            return false_msg
        else:
            flg = request.get_signed_cookie('flag', salt='asdfasdf')
            if flg=='1':
                brand = request.COOKIES.get('brand', '奥迪'.encode('utf-8').decode('latin-1')).encode('latin-1').decode(
                'utf-8')
                print(request.COOKIES.get('brand'))
            else:
                false_msg=redirect('/app/login_wrong/')
                return false_msg
    #print(brand)
    context = dict()
    #图1
    context['price_distribution'] = price_distribution(brand)
    #图2  context['xlabel']只是x轴的坐标
    context['xlabel2'],context['hedge_ratio'] = Brand_rate(brand)
    #图3
    context['mannufactured_year'] = nummanufacture(brand)
    #图4
    context['num_categorized_by_year'] = num_categorized_by_year(brand)
    context['brand']=brand
    # context['test'] = [900,800,700,600,500,400,300,200,100,0]
    return render(request, "details.html", context)


# detail 页面内更新
@csrf_exempt
def update_draw(request, resultType):
    brand = '奥迪'
    if request.method == "POST":
        brand = request.POST.get('brandname', '6')
        #print(request.POST)
    #print(brand)
    context = dict()
    # 图1
    context['price_distribution'] = price_distribution(brand)
    # 图2  context['xlabel']只是x轴的坐标
    context['xlabel2'], context['hedge_ratio'] = Brand_rate(brand)
    # 图3
    context['mannufactured_year'] = nummanufacture(brand)
    # 图4
    context['num_categorized_by_year'] = num_categorized_by_year(brand)
    context['brand'] = brand
    # context['test'] = [900,800,700,600,500,400,300,200,100,0]
    if request.method == "POST":
        #print(context['brand'])
        if resultType == "title":
            return render(request, "bigTitle.html", context)
        elif resultType == "tables":
            return render(request, "tables.html", context)
    else:
        return render(request, "details.html", context)

def login(request):
    return render(request,"login.html")

def register(request):
    return render(request,"register.html")

def login_action(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password =request.POST.get('password', '')
        if len(username)==0 or len(password)==0:
            return render(request,'login.html',{'error':'登陆失败:请输入用户名/密码'})
        else:
            db,cursor=connect()
            sql="""
            select count(*) from profile where id={0} and password={1}
            """.format(str(username),str(password))

            try:
                cursor.execute(sql)
                results=cursor.fetchall()
            except Exception as e:
                raise e

            if results[0][0]==1:
                res=redirect('/app/details/')
                    #设置加盐cookie,5分钟失效
                res.set_signed_cookie('flag','1',salt="asdfasdf",max_age=900)
                return res
                # return HttpResponse('login success!')
            else:
                return render(request,'login.html',{'error':'登陆失败:用户名或者密码有误'})
    else:
        return render(request,'login.html')

def login_wrong(request):
    return render(request,'login_wrong.html')

def reg_action(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        password2=request.POST.get('password2','')
        if password != password2:
            return render(request, 'register.html', {'error': '注册失败:两次密码输入不一致'})
        elif len(username)>12 or len(username)<=0 :
            return render(request,'register.html',{'error':'注册失败:用户名不符合规范'})
        elif len(password)<=0 or len(password2)<=0:
            return render(request,'register.html',{'error':'注册失败：您是否忘记输入密码/重复密码?'})
        else:
            db, cursor = connect()
            sql1 = """
            select count(*) from profile where id={0}
            """.format(str(username))

            sql2="""
            insert into profile values ({0},{1})
            """.format(username,password)


            try:
                cursor.execute(sql1)
                results = cursor.fetchall()
            except Exception as e:
                raise e

            if results[0][0] == 1:
                return render(request,'register.html',{'error':'注册失败:用户已经被注册'})
            else:
                try:
                    cursor.execute(sql2)
                    return render(request,'reg_success.html')
                except Exception as e:
                    raise e
    else:
        return render(request, 'register.html')

def reg_success(request):
    return render(request,'login.html') #之所以跳转到login.html而不是reg_success.html是为了防止直接访问reg_success.html而出现错误的“注册成功”信息

def loginindex(request):
    flg = request.COOKIES.get('flag')
    if not flg:
        return render(request,'index.html',{'status':'未登录'})
    else:
        return render(request,'index.html',{'status':'已登录'})