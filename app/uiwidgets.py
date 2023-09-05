from PyQt5 import QtCore, QtGui, QtWidgets

class Compose_Ui(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(574, 516)
        Dialog.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.recepients = QtWidgets.QLineEdit(Dialog)
        self.recepients.setObjectName("recepients")
        self.verticalLayout.addWidget(self.recepients)
        self.subject = QtWidgets.QLineEdit(Dialog)
        self.subject.setObjectName("subject")
        self.verticalLayout.addWidget(self.subject)
        self.text = QtWidgets.QTextEdit(Dialog)
        self.text.setObjectName("text")
        self.verticalLayout.addWidget(self.text)
        self.atbtns = QtWidgets.QWidget(Dialog)
        self.atbtns.setObjectName("atbtns")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.atbtns)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.atbtns)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.rmBtn = QtWidgets.QPushButton(self.atbtns)
        self.rmBtn.setObjectName("rmBtn")
        self.horizontalLayout.addWidget(self.rmBtn)
        self.addBtn = QtWidgets.QPushButton(self.atbtns)
        self.addBtn.setObjectName("addBtn")
        self.horizontalLayout.addWidget(self.addBtn)
        self.verticalLayout.addWidget(self.atbtns)
        self.attchs = QtWidgets.QListWidget(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.attchs.sizePolicy().hasHeightForWidth())
        self.attchs.setSizePolicy(sizePolicy)
        self.attchs.setMaximumSize(QtCore.QSize(16777215, 100))
        self.attchs.setObjectName("attchs")
        self.verticalLayout.addWidget(self.attchs)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Reset)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.rejected.connect(Dialog.reject)
        self.buttonBox.accepted.connect(Dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Compose"))
        self.recepients.setPlaceholderText(_translate("Dialog", "To"))
        self.subject.setPlaceholderText(_translate("Dialog", "Subject"))
        self.label.setText(_translate("Dialog", "Attachments"))
        self.rmBtn.setText(_translate("Dialog", "-"))
        self.addBtn.setText(_translate("Dialog", "+"))


class Read_Ui(object):
    def setupUi(self, Widget):
        Widget.setObjectName("Widget")
        Widget.resize(574, 516)
        Widget.setWindowTitle("")
        Widget.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.verticalLayout = QtWidgets.QVBoxLayout(Widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.header = QtWidgets.QTextEdit(Widget)
        self.header.setMaximumSize(QtCore.QSize(16777215, 139))
        self.header.setObjectName("header")
        self.verticalLayout.addWidget(self.header)
        self.body = QtWidgets.QTextBrowser(Widget)
        self.body.setOpenExternalLinks(True)
        self.body.setObjectName("body")
        self.verticalLayout.addWidget(self.body)
        self.atbtns = QtWidgets.QWidget(Widget)
        self.atbtns.setObjectName("atbtns")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.atbtns)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.atbtns)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.verticalLayout.addWidget(self.atbtns)
        self.attchs = QtWidgets.QListWidget(Widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.attchs.sizePolicy().hasHeightForWidth())
        self.attchs.setSizePolicy(sizePolicy)
        self.attchs.setMaximumSize(QtCore.QSize(16777215, 100))
        self.attchs.setObjectName("attchs")
        self.verticalLayout.addWidget(self.attchs)

        self.retranslateUi(Widget)
        QtCore.QMetaObject.connectSlotsByName(Widget)

    def retranslateUi(self, Widget):
        _translate = QtCore.QCoreApplication.translate
        self.label.setText(_translate("Widget", "Attachments"))


class Auth_Ui(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(382, 298)
        Dialog.setMaximumSize(QtCore.QSize(382, 298))
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.email = QtWidgets.QLineEdit(Dialog)
        self.email.setInputMethodHints(QtCore.Qt.ImhEmailCharactersOnly)
        self.email.setObjectName("email")
        self.verticalLayout.addWidget(self.email)
        self.pass_ = QtWidgets.QLineEdit(Dialog)
        self.pass_.setInputMethodHints(QtCore.Qt.ImhHiddenText|QtCore.Qt.ImhNoAutoUppercase|QtCore.Qt.ImhNoPredictiveText|QtCore.Qt.ImhSensitiveData)
        self.pass_.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pass_.setObjectName("pass_")
        self.verticalLayout.addWidget(self.pass_)
        self.widget = QtWidgets.QWidget(Dialog)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.imaphost = QtWidgets.QLineEdit(self.widget)
        self.imaphost.setObjectName("imaphost")
        self.horizontalLayout.addWidget(self.imaphost)
        self.imapport = QtWidgets.QSpinBox(self.widget)
        self.imapport.setMinimum(1)
        self.imapport.setMaximum(65535)
        self.imapport.setProperty("value", 993)
        self.imapport.setObjectName("imapport")
        self.horizontalLayout.addWidget(self.imapport)
        self.verticalLayout.addWidget(self.widget)
        self.widget_2 = QtWidgets.QWidget(Dialog)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pophost = QtWidgets.QLineEdit(self.widget_2)
        self.pophost.setObjectName("pophost")
        self.horizontalLayout_2.addWidget(self.pophost)
        self.popport = QtWidgets.QSpinBox(self.widget_2)
        self.popport.setMinimum(1)
        self.popport.setMaximum(65535)
        self.popport.setProperty("value", 995)
        self.popport.setObjectName("popport")
        self.horizontalLayout_2.addWidget(self.popport)
        self.verticalLayout.addWidget(self.widget_2)
        self.widget_3 = QtWidgets.QWidget(Dialog)
        self.widget_3.setMaximumSize(QtCore.QSize(382, 64))
        self.widget_3.setObjectName("widget_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.widget_3)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.smtphost = QtWidgets.QLineEdit(self.widget_3)
        self.smtphost.setObjectName("smtphost")
        self.horizontalLayout_3.addWidget(self.smtphost)
        self.smtpport = QtWidgets.QSpinBox(self.widget_3)
        self.smtpport.setMinimum(1)
        self.smtpport.setMaximum(65535)
        self.smtpport.setProperty("value", 587)
        self.smtpport.setObjectName("smtpport")
        self.horizontalLayout_3.addWidget(self.smtpport)
        self.verticalLayout.addWidget(self.widget_3)
        self.btn = QtWidgets.QPushButton(Dialog)
        self.btn.setObjectName("btn")
        self.verticalLayout.addWidget(self.btn)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Settings"))
        self.email.setPlaceholderText(_translate("Dialog", "email"))
        self.pass_.setPlaceholderText(_translate("Dialog", "pass"))
        self.imaphost.setPlaceholderText(_translate("Dialog", "imap server"))
        self.pophost.setPlaceholderText(_translate("Dialog", "pop3 server"))
        self.smtphost.setPlaceholderText(_translate("Dialog", "smtp server"))
        self.btn.setText(_translate("Dialog", "OK"))