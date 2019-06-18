import smtplib
from email.mime.text import MIMEText
from email.header import  Header

# sender='3099238642@qq.com'
# receivers=['2439745857@qq.com']
#
# message=MIMEText('邮件测试','plain','utf-8')
# message['From']=Header('Me','utf-8')
# message['To']=Header('You','utf-8')
# subject='dudududududu........................'
# message['Subject']=Header(subject,'utf-8')
#
# try:
#     smtObj=smtplib.SMTP('localhost')
#     smtObj.sendmail(sender,receivers,message.as_string())
#     print('OK')
# except smtplib.SMTPException:
#     print('Error')


# !/usr/bin/python
# -*- coding: UTF-8 -*-

# import smtplib
# from email.mime.text import MIMEText
# from email.utils import formataddr
#



# my_sender = '2439745857@qq.com'  # 发件人邮箱账号
# my_pass = 'pzypjyfblmmjdjba'  # 发件人邮箱密码
# my_user = '3099238642@qq.com'  # 收件人邮箱账号，我这边发送给自己
#
#
# def mail():
#     ret = True
#     try:
#         msg = MIMEText('填写邮件内容', 'plain', 'utf-8')
#         msg['From'] = formataddr(["FromRunoob", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
#         msg['To'] = formataddr(["FK", my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
#         msg['Subject'] = "菜鸟教程发送邮件测试"  # 邮件的主题，也可以说是标题
#
#         server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是25
#         server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
#         server.sendmail(my_sender, [my_user, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
#         server.quit()  # 关闭连接
#     except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
#         ret = False
#     return ret
#
#
# ret = mail()
# if ret:
#     print("邮件发送成功")
# else:
#     print("邮件发送失败")


# coding: utf-8

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
from email.utils import formataddr

my_sender='2439745857@qq.com'
my_pass='pzypjyfblmmjdjba'
my_receiver='2439745857@qq.com'

def mail():
    ret=True
    try:
        subject='Python Email Test'
        msg=MIMEMultipart('alternative')
        msg['Subject']=subject
        msg['From']=formataddr(['From110',my_sender])
        msg['To']=formataddr(['To110',my_receiver])


        ##构造文字内容
        text='你好!\nHow are you\nHere is link you wanted\nhttps://www.baidu.com'
        text_plain=MIMEText(text,'plain','utf-8')
        # msg.attach(text_plain)



        ##构造html
        html ="""
        <p>Python 邮件发送测试...</p>
        <p><a href="http://www.runoob.com">菜鸟教程链接</a></p>
        <p>图片演示：</p>
        <p><img src="cid:image"></p>
        """
        text_html=MIMEText(html,'html','utf-8')
        text_html['Content-Disposition']='attachment;filename="texthtml.html"'
        msg.attach(text_html)

        ##构造图片
        sendimagefile = open(r'c:/users/yelei/desktop/img.jpg', 'rb')
        image = MIMEImage(sendimagefile.read())
        sendimagefile.close()

        image.add_header('Conten-ID', '<image>')
        # image['Content-Disposition']='attachment;filename="testimage.jpg"'
        msg.attach(image)

        ##构造附件
        sendfile=open(r'c:/users/yelei/desktop/非标准温度间隔0403.xls','rb').read()
        text_att=MIMEText(sendfile,'base64','utf-8')
        text_att['Content-Type']='application/octet-stream'
        text_att.add_header('Content-Disposition','attachment',filename='aaa.txt')
        msg.attach(text_att)

        server=smtplib.SMTP_SSL('SMTP.qq.com','465')
        server.login(my_sender,my_pass)
        server.sendmail(my_sender,[my_receiver,],msg.as_string())
        server.quit()
    except Exception:
        ret=False
    return ret

ret=mail()
if ret:
    print("OKAY")
else:
    print('FAIL')








# # 设置smtplib所需的参数
# # 下面的发件人，收件人是用于邮件传输的。
# smtpserver = 'smtp.qq.com'
# # username = '2439745857@qq.com'
# password = 'pzypjyfblmmjdjba'
# sender =  '2439745857@qq.com'
# # receiver='XXX@126.com'
# # 收件人为多个收件人
# receiver = '3099238642@qq.com'
#
# subject = 'Python email test'
# # 通过Header对象编码的文本，包含utf-8编码信息和Base64编码信息。以下中文名测试ok
# # subject = '中文标题'
# # subject=Header(subject, 'utf-8').encode()
#
# # 构造邮件对象MIMEMultipart对象
# # 下面的主题，发件人，收件人，日期是显示在邮件页面上的。
# msg = MIMEMultipart('mixed')
# msg['Subject'] = subject
# msg['From'] = 'XXX@163.com <XXX@163.com>'
# # msg['To'] = 'XXX@126.com'
# # 收件人为多个收件人,通过join将列表转换为以;为间隔的字符串
# msg['To'] = ";".join(receiver)
# # msg['Date']='2012-3-16'
#
# # 构造文字内容
# text = "Hi!\nHow are you?\nHere is the link you wanted:\nhttp://www.baidu.com"
# text_plain = MIMEText(text, 'plain', 'utf-8')
# msg.attach(text_plain)
#
# # 构造图片链接
# sendimagefile = open(r'D:\pythontest\testimage.png', 'rb').read()
# image = MIMEImage(sendimagefile)
# image.add_header('Content-ID', '<image1>')
# image["Content-Disposition"] = 'attachment; filename="testimage.png"'
# msg.attach(image)
#
# # 构造html
# # 发送正文中的图片:由于包含未被许可的信息，网易邮箱定义为垃圾邮件，报554 DT:SPM ：<p><img src="cid:image1"></p>
# html = """
# <html>
#   <head></head>
#   <body>
#     <p>Hi!<br>
#        How are you?<br>
#        Here is the <a href="http://www.baidu.com">link</a> you wanted.<br>
#     </p>
#   </body>
# </html>
# """
# text_html = MIMEText(html, 'html', 'utf-8')
# text_html["Content-Disposition"] = 'attachment; filename="texthtml.html"'
# msg.attach(text_html)
#
# # 构造附件
# sendfile = open(r'D:\pythontest\1111.txt', 'rb').read()
# text_att = MIMEText(sendfile, 'base64', 'utf-8')
# text_att["Content-Type"] = 'application/octet-stream'
# # 以下附件可以重命名成aaa.txt
# # text_att["Content-Disposition"] = 'attachment; filename="aaa.txt"'
# # 另一种实现方式
# text_att.add_header('Content-Disposition', 'attachment', filename='aaa.txt')
# # 以下中文测试不ok
# # text_att["Content-Disposition"] = u'attachment; filename="中文附件.txt"'.decode('utf-8')
# msg.attach(text_att)
#
# # 发送邮件
# smtp = smtplib.SMTP()
# smtp.connect('smtp.163.com')
# # 我们用set_debuglevel(1)就可以打印出和SMTP服务器交互的所有信息。
# # smtp.set_debuglevel(1)
# smtp.login(sender, password)
# smtp.sendmail(sender, receiver, msg.as_string())
# smtp.quit()