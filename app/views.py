#!/usr/bin/python
# -*- coding: UTF-8 -*-
from flask import Flask,render_template,jsonify,request,g, url_for,abort
from flask_cors import CORS
from app import app
from models import *
import hashlib
import json
import os
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from .store_info import store_info
from .user_info import user_info
from .order_info import order_info

# extensions
auth = HTTPBasicAuth()

app.register_blueprint(store_info)
app.register_blueprint(user_info)
app.register_blueprint(order_info)


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})
@app.route('/api/users/<username>')
def get_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(400)
    return jsonify({'username': user.username})
@app.route('/api/resource')
@auth.login_required
def get_resource():
    return jsonify({ 'data': 'Hello, %s!' % g.user.username })


@app.route("/")
def home():
    '''
    页面之间的跳转交给前端路由负责，后端不用再写大量的路由
    '餐馆信息 : /index 注册信息 : /sign_up 订单详情 : /user/<userID>/orders/<orderID> 登陆信息 : /login 单个店铺点单信息 : host/index/store_name'
    '''
    return render_template('index.html')

@app.route("/search")
def search():
    '''
    SZQ
    返回搜索店铺分类属性下的所有店铺
    带参数传入/search?type=dessert
    '''
    type = request.args.get('type')
    path = 'json_test/' + type + '.json'
    try:
        print path
        json_fd = open(path, 'r')
    except IOError:
        return jsonify({'status_code': '401', 'error_message': '404 Not Found'})
        # return "{'status_code':'401','error_message':'404 Not Found'}"
    json_store = json.load(json_fd)
    # json_store_str = json.dumps(json_store, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
    return jsonify(json_store)

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    SZQ
    登陆api
    '''
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if verify_password(username, password):
            # 号码以及密码验证通过
            pass
        else:
            # 手机号或者密码错误
            error = jsonify({'status_code':'401','error_message':'Unauthorized'})
            return error
        token = g.user.generate_auth_token(600)
        status_code = "201"
        user_data = {
            'status_code': status_code,
            'token': token.decode('ascii'),
            'duration': 600,
            "user": {
                "ID": '15331533',
                "username": username,
                "name": 'test_c1',
                "avar": '/static/images/user_img/test_user_1.png',
                "message": '',
                "orderList": ['']
            }
        }
        json_user_data = jsonify(user_data)
        return json_user_data

def valid_sign_up(username, password):
    if username is None or password is None:
        return False
    if User.query.filter_by(username=username).first() is not None:
        return False
    return True
def valid_login(username, password):
    '''
        SZQ
        在数据库中查找手机号，不存在则非法，返回无此号码失败信息
        如果存在手机号，但密码错误，返回密码错误失败信息
        如果存在该手机号码并且密码正确则返回成功信息
        '''
    # 查找数据库,手机号无效
    # if User.query.get(mobile) is not None:
    #     return False
    # 查找数据库,手机号对应密码错误
    # if User.query.get(password) is not equal to password:
    #     return False
    if username is None or password is None:
        return False
    if User.query.filter_by(username=username).first() is not None:
        return True
    return False


@app.route('/index/<storeID>', methods=['GET', 'POST'])
def store_info(storeID):
    '''
    SZQ
    获取单个电铺点单信息，返回定义的json化数据
    '''
    store_list = ['110', '111']
    storeID_exist = True
    for id_index in store_list:
        print id_index
        if (storeID == id_index):
            storeID_exist = True
            break
        else:
            storeID_exist = False

    if (storeID_exist):
        print storeID
        path = './json_test/' + storeID + '.json'
        try:
            print path
            json_fd = open(path, 'r')
        except IOError:
            print "fault"
            return jsonify({'status_code':'401','error_message':'OrderData File Not Found'})
    else:
        return jsonify({'status_code':'401','error_message':'StoreID Not Exist'})

    json_fd_dict = json.load(json_fd)
    # 使用flask中定义返回的json而不是content：html.text
    # json_fd_str = json.dumps(json_fd_dict, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
    json_fd_data = jsonify(json_fd_dict)
    return json_fd_data


@app.route('/user/<userID>/orders', methods=['GET', 'POST'])
def order_info_brief(userID):
    '''
    SZQ
    订单详情api
    用户身份和订单信息确认后输出订单详细信息,失败返回（401）
    '''
    token = request.headers['accesstoken']
    user = User.verify_auth_token(token)
    if not user:
        return jsonify({'status_code': '401', 'error_message': 'Unauthorized'})
    if request.method == 'GET':
        path = './json_test/' + userID + '_brief_order.json'
        try:
            print path
            json_od = open(path, 'r')
        except IOError:
            print "fault"
            return jsonify({'status_code': '401', 'error_message': 'OrderData File Not Found'})
        json_od_dict = json.load(json_od)
        json_order_data = jsonify(json_od_dict)
        return json_order_data
    if request.method == 'POST':
        path = './json_test/' + userID + '_brief_order.json'
        new_order = request.get_data()
        json_od = open(path, 'r')
        print new_order
        new_order = jsonify(new_order)

        return new_order


# @app.route('/user/<userID>/orders/<orderID>', methods=['GET', 'POST'])
# def order_info_detail(userID, orderID):
#     '''
#     SXT
#     订单详情api
#     用户身份和订单信息确认后输出订单详细信息,失败返回（401）
#     '''
#     if request.method == 'GET':
#         token = request.headers['accesstoken']
#         user = User.verify_auth_token(token)
#         if not user:
#             return jsonify({'status_code': '401', 'error_message': 'Unauthorized'})
#         else:
#             path = './json_test/' + userID + '_detail_' + orderID + '_order.json'
#             try:
#                 print path
#                 json_od = open(path, 'r')
#             except IOError:
#                 print "fault"
#                 return jsonify({'status_code': '401', 'error_message': 'OrderData File Not Found'})
#             json_od_dict = json.load(json_od)
#             json_order_data = jsonify(json_od_dict)
#             return json_order_data

@app.route('/test', methods=['GET', 'POST'])
def test():
    ''' 这个API用来测试跨域 '''
    return 'success'



# @app.route('/user/<userID>/orders/<orderID>', methods=['GET', 'POST'])
# def order_info_detail(userID, orderID):
#     '''
#     SXT
#     订单详情api
#     用户身份和订单信息确认后输出订单详细信息,失败返回（401）
#     '''
#     if request.method == 'GET':
#         status_code = '201'
#         order_hash = hashlib.md5(orderID)
#         order_detail = {
#             'status_code': status_code,
#             'storeName': 'test_srore_name',
#             'foodList': [''],
#             'mealFee': '123',
#             'ServiceFee': '123',
#             'totalFee': '123',
#             'Offer': '123',
#             'paymentMethod': '1',
#             'Date': '2017-01-08 17:05:24',
#             'orderNumber': order_hash.hexdigest()
#         }
#         # json_order_data = json.dumps(order_detail, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
#         json_order_data = jsonify(order_detail)
#         return json_order_data