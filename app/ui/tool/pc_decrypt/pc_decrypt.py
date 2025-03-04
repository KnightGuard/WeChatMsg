import json
import os.path
import time
import traceback

from PyQt5.QtCore import pyqtSignal, QThread, QUrl, QFile, QIODevice, QTextStream
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget, QMessageBox, QFileDialog

from app.DataBase import msg_db, misc_db
from app.DataBase.merge import merge_databases, merge_MediaMSG_databases
from app.decrypt import get_wx_info, decrypt
from app.log import logger
from app.util import path
from . import decryptUi


class DecryptControl(QWidget, decryptUi.Ui_Dialog):
    DecryptSignal = pyqtSignal(bool)
    get_wxidSignal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(DecryptControl, self).__init__(parent)
        self.setupUi(self)

        self.pushButton_3.clicked.connect(self.decrypt)
        self.btn_getinfo.clicked.connect(self.get_info)
        self.btn_db_dir.clicked.connect(self.select_db_dir)
        self.lineEdit.returnPressed.connect(self.set_wxid)
        self.lineEdit.textChanged.connect(self.set_wxid_)
        self.btn_help.clicked.connect(self.show_help)
        self.label_tip.setVisible(False)
        self.info = {}
        self.lineEdit.setFocus()
        self.ready = False
        self.wx_dir = None

    def show_help(self):
        # 定义网页链接
        url = QUrl("https://blog.lc044.love/post/4")
        # 使用QDesktopServices打开网页
        QDesktopServices.openUrl(url)

    # @log
    def get_info(self):
        try:
            file = QFile(':/data/version_list.json')
            if file.open(QIODevice.ReadOnly | QIODevice.Text):
                stream = QTextStream(file)
                content = stream.readAll()
                file.close()
                VERSION_LIST = json.loads(content)
            else:
                return
            result = get_wx_info.get_info(VERSION_LIST)
            print(result)
            if result == -1:
                QMessageBox.critical(self, "错误", "请登录微信")
            elif result == -2:
                QMessageBox.critical(self, "错误", "微信版本不匹配\n请更新微信版本为:3.9.8.15")
            elif result == -3:
                QMessageBox.critical(self, "错误", "WeChat WeChatWin.dll Not Found")
            else:
                self.ready = True
                self.info = result[0]
                self.label_key.setText(self.info['key'])
                self.lineEdit.setText(self.info['wxid'])
                self.label_name.setText(self.info['name'])
                self.label_phone.setText(self.info['mobile'])
                self.label_pid.setText(str(self.info['pid']))
                self.label_version.setText(self.info['version'])
                self.lineEdit.setFocus()
                self.checkBox.setChecked(True)
                self.get_wxidSignal.emit(self.info['wxid'])
                directory = os.path.join(path.wx_path(), self.info['wxid'])
                if os.path.exists(directory):
                    self.label_db_dir.setText(directory)
                    self.wx_dir = directory
                    self.checkBox_2.setChecked(True)
                    self.ready = True
                if self.ready:
                    self.label_ready.setText('已就绪')
                if self.wx_dir and os.path.exists(os.path.join(self.wx_dir)):
                    self.label_ready.setText('已就绪')
        except Exception as e:
            QMessageBox.critical(self, "未知错误", "请收集报错信息，发起issue解决问题")
            logger.error(traceback.format_exc())

    def set_wxid_(self):
        self.info['wxid'] = self.lineEdit.text()

    def set_wxid(self):
        self.info['wxid'] = self.lineEdit.text()
        QMessageBox.information(self, "ok", f"wxid修改成功{self.info['wxid']}")

    def select_db_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "选取微信文件保存目录——能看到Msg文件夹",
            path.wx_path()
        )  # 起始路径
        db_dir = os.path.join(directory, 'Msg')
        if not os.path.exists(db_dir):
            QMessageBox.critical(self, "错误", "文件夹选择错误\n一般以wxid_xxx结尾")
            return

        self.label_db_dir.setText(directory)
        self.wx_dir = directory
        self.checkBox_2.setChecked(True)
        if self.ready:
            self.label_ready.setText('已就绪')

    def decrypt(self):
        if not self.ready:
            QMessageBox.critical(self, "错误", "请先获取密钥")
            return
        if not self.wx_dir:
            QMessageBox.critical(self, "错误", "请先选择微信安装路径")
            return
        if self.lineEdit.text() == 'None':
            QMessageBox.critical(self, "错误", "请填入wxid")
            return
        db_dir = os.path.join(self.wx_dir, 'Msg')
        if self.ready:
            if not os.path.exists(db_dir):
                QMessageBox.critical(self, "错误", "文件夹选择错误\n一般以wxid_xxx结尾")
                return
        if self.info.get('key') == 'none':
            QMessageBox.critical(self, "错误", "密钥错误\n请检查微信版本是否为最新和微信路径是否正确")
        self.label_tip.setVisible(True)
        self.label_tip.setText('点我之后没有反应那就多等儿吧,不要再点了')
        self.thread2 = DecryptThread(db_dir, self.info['key'])
        self.thread2.maxNumSignal.connect(self.setProgressBarMaxNum)
        self.thread2.signal.connect(self.progressBar_view)
        self.thread2.okSignal.connect(self.btnExitClicked)
        self.thread2.errorSignal.connect(
            lambda x: QMessageBox.critical(self, "错误", "密钥错误\n请检查微信版本是否为最新和微信路径是否正确")
        )
        self.thread2.start()

    def btnEnterClicked(self):
        # print("enter clicked")
        # 中间可以添加处理逻辑
        # QMessageBox.about(self, "解密成功", "数据库文件存储在app/DataBase/Msg文件夹下")

        self.DecryptSignal.emit(True)
        # self.close()

    def setProgressBarMaxNum(self, max_val):
        self.progressBar.setRange(0, max_val)

    def progressBar_view(self, value):
        """
        进度条显示
        :param value: 进度0-100
        :return: None
        """
        self.progressBar.setProperty('value', value)
        #     self.btnExitClicked()
        #     data.init_database()

    def btnExitClicked(self):
        # print("Exit clicked")
        dic = {
            'wxid': self.info['wxid'],
            'wx_dir': self.wx_dir,
            'name': self.info['name'],
            'mobile': self.info['mobile']
        }
        try:
            os.makedirs('./app/data', exist_ok=True)
            with open('./app/data/info.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(dic))
        except:
            with open('./info.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(dic))
        # 目标数据库文件
        target_database = "app/DataBase/Msg/MSG.db"
        # 源数据库文件列表
        source_databases = [f"app/DataBase/Msg/MSG{i}.db" for i in range(1, 200)]
        import shutil
        shutil.copy2("app/DataBase/Msg/MSG0.db", target_database)  # 使用一个数据库文件作为模板
        # 合并数据库
        try:
            merge_databases(source_databases, target_database)
        except FileNotFoundError:
            QMessageBox.critical(self, "错误", "数据库不存在\n请检查微信版本是否为最新")

        # 音频数据库文件
        target_database = "app/DataBase/Msg/MediaMSG.db"
        # 源数据库文件列表
        source_databases = [f"app/DataBase/Msg/MediaMSG{i}.db" for i in range(1, 200)]
        shutil.copy2("app/DataBase/Msg/MediaMSG0.db", target_database)  # 使用一个数据库文件作为模板
        # 合并数据库
        try:
            merge_MediaMSG_databases(source_databases, target_database)
        except FileNotFoundError:
            QMessageBox.critical(self, "错误", "数据库不存在\n请检查微信版本是否为最新")
        
        self.DecryptSignal.emit(True)
        self.close()


class DecryptThread(QThread):
    signal = pyqtSignal(str)
    maxNumSignal = pyqtSignal(int)
    okSignal = pyqtSignal(str)
    errorSignal = pyqtSignal(bool)

    def __init__(self, db_path, key):
        super(DecryptThread, self).__init__()
        self.db_path = db_path
        self.key = key
        self.textBrowser = None

    def __del__(self):
        pass

    def run(self):
        misc_db.close()
        msg_db.close()
        # micro_msg_db.close()
        # hard_link_db.close()
        output_dir = 'app/DataBase/Msg'
        os.makedirs(output_dir, exist_ok=True)
        tasks = []
        if os.path.exists(self.db_path):
            for root, dirs, files in os.walk(self.db_path):
                for file in files:
                    if '.db' == file[-3:]:
                        if 'xInfo.db' == file:
                            continue
                        inpath = os.path.join(root, file)
                        # print(inpath)
                        output_path = os.path.join(output_dir, file)
                        tasks.append([self.key, inpath, output_path])
        self.maxNumSignal.emit(len(tasks))
        for i, task in enumerate(tasks):
            if decrypt.decrypt(*task) == -1:
                self.errorSignal.emit(True)
            self.signal.emit(str(i))
        # print(self.db_path)
        self.okSignal.emit('ok')
        # self.signal.emit('100')


class MyThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self):
        super(MyThread, self).__init__()

    def __del__(self):
        pass

    def run(self):
        for i in range(100):
            self.signal.emit(str(i))
            time.sleep(0.1)
