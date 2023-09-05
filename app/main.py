#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import (QMainWindow, QDialog, QFileDialog, QDialogButtonBox, 
	QLabel, QMessageBox, QWidget, QListWidget, QPushButton, QComboBox, QSpinBox, 
	QDesktopWidget, QVBoxLayout, QHBoxLayout, QApplication, QMenuBar, QTableView,
	QTableWidgetItem)
from PyQt5 import QtCore
from PyQt5 import uic
from uiwidgets import *
from imaplib import IMAP4_SSL
from poplib import POP3_SSL
import mailparser
from smtplib import SMTP_SSL, SMTP
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils as eutils
import os
from datetime import datetime
import subprocess
from htmlwidget import myEditor
from db import *
from mail_utils import (
	send_mail, sign_and_enc, dec_and_ver,
	saveAsDraft,
	sign_mail, verify_mail
)
from cipher_utils import (
    RSACipher, DSACipher
)
import shutil
from random import seed
from random import randint
from base64 import b64encode
from email import message_from_bytes
import traceback
import functools

class LoadingWindow(QDialog):
	def __init__(self, parent, thread, text="LOADING..."):
		super().__init__(parent)
		self.resize(200,37)
		self.setMinimumSize(QtCore.QSize(200, 37))
		lout = QVBoxLayout()
		self.label = QLabel(self)
		lout.addWidget(self.label)
		self.setLayout(lout)
		self.setWindowTitle('')
		self.label.setText(text)
		self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowTitleHint)
		self.thread=thread
		self.thread.finished.connect(self.close)
		self.thread.w = parent
		self.thread.start()


def default_error_handler(f):
	@functools.wraps(f)
	def wrapper(self, *args):
		try:
			return f(self)
		except Exception as e:
			traceback.print_exc()
			QMessageBox.critical(self, 'Error', str(e))
	return wrapper


class GenericThread(QtCore.QThread):
	def __init__(self, func):
		super().__init__()
		self.w = None
		self.func = func

	def run(self):
		return self.func()


class AddAccountDialog(QDialog):
	def __init__(self, parent):
		super().__init__(parent)
		uic.loadUi('addaccount.ui', self)
		self.addB.clicked.connect(self.add)

	def add(self):
		try:
			User.insert(email=self.email.text(),
			 passw=self.passw.text(),
			 smtphost=self.smtphost.text(),
			 smtpport=self.smtpport.value(),
			 imaphost=self.imaphost.text(),
			 imapport=self.imapport.value()).execute()
			self.accept()
		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))
			#QMessageBox.critical(self, 'Error', "Invalid data.")


class AccountsWindow(QDialog):
	def __init__(self, parent):
		super().__init__(parent)
		uic.loadUi('accounts.ui', self)
		self.addB.clicked.connect(self.add)
		self.delB.clicked.connect(self.remove)
		self.saveB.clicked.connect(self.save)
		self.accounts.itemClicked.connect(self.showDetails)
		self.curId = None
		self.loadList()
		self.show()

	def loadList(self):
		self.accounts.clear()
		for u in User.select().order_by('email').iterator():
			self.accounts.addItem(u.email)
		if self.accounts.count() > 0:
			self.widget_3.setDisabled(False)
			self.accounts.setCurrentRow(0)
			self.showDetails(self.accounts.currentItem())
		else:
			self.widget_3.setDisabled(True)

	def showDetails(self, item):
		if item:
			u = User.get_or_none(email=item.text())
			if u:
				self.curId = u.id
				self.email.setText(u.email)
				self.passw.setText(u.passw)
				self.smtphost.setText(u.smtphost)
				self.smtpport.setValue(u.smtpport)
				self.imaphost.setText(u.imaphost)
				self.imapport.setValue(u.imapport)

	def add(self):
		d = AddAccountDialog(self)
		r = d.exec_()
		if r:
			self.loadList()

	def save(self):
		u = User.get_or_none(id=self.curId)
		if u:
			u.email = self.email.text()
			u.passw = self.passw.text()
			u.smtphost = self.smtphost.text()
			u.smtpport = self.smtpport.value()
			u.imaphost = self.imaphost.text()
			u.imapport = self.imapport.value()
			try:
				u.save()
				self.loadList()
			except Exception as e:
				QMessageBox.critical(self, 'Error', str(e))

	def remove(self):
		User.delete().where(User.id==self.curId).execute()
		self.loadList()


class AddContactDialog(QDialog):
	def __init__(self, parent, ac):
		super().__init__(parent)
		self.ac = ac
		uic.loadUi('addcontact.ui', self)
		self.addB.clicked.connect(self.add)

	def add(self):
		try:
			rprk, rpbk = RSACipher().generate()
			dprk, dpbk = DSACipher().generate()
			Contact.insert(email=self.email.text(),
			 account=self.ac,
			 my_enc_pr_key=rprk.exportKey(),
			 my_enc_pub_key=rpbk.exportKey(),
			 my_sgn_pr_key=dprk.exportKey(),
				my_sgn_pub_key=dpbk.exportKey()).execute()
			self.accept()
		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))


class ContactsWindow(QDialog):
	def __init__(self, parent, ac):
		super().__init__(parent)
		uic.loadUi('contacts.ui', self)
		self.ac = User.get(email=ac).id
		self.addB.clicked.connect(self.add)
		self.delB.clicked.connect(self.remove)
		self.saveB.clicked.connect(self.save)
		self.contacts.itemClicked.connect(self.showDetails)
		self.curId = None
		self.loadList()
		self.crsaiB.clicked.connect(self.import_contact_enc_key)
		self.cdsaiB.clicked.connect(self.import_contact_sgn_key)
		self.crsaeB.clicked.connect(self.export_contact_enc_key)
		self.cdsaeB.clicked.connect(self.export_contact_sgn_key)
		self.genrsaB.clicked.connect(self.generate_enc_keys)
		self.gendsaB.clicked.connect(self.generate_sgn_keys)
		self.srsaB.clicked.connect(self.send_enc_key)
		self.sdsaB.clicked.connect(self.send_sgn_key)
		self.mrsapriB.clicked.connect(self.import_enc_pr_key)
		self.mrsapuiB.clicked.connect(self.import_enc_pub_key)
		self.mdsapriB.clicked.connect(self.import_sgn_pr_key)
		self.mdsapuiB.clicked.connect(self.import_sgn_pub_key)
		self.mrsapreB.clicked.connect(self.export_enc_pr_key)
		self.mrsapueB.clicked.connect(self.export_enc_pub_key)
		self.mdsapreB.clicked.connect(self.export_sgn_pr_key)
		self.mdsapueB.clicked.connect(self.export_sgn_pub_key)
		self.show()

	def loadList(self):
		self.contacts.clear()
		for u in Contact.select().where(Contact.account==self.ac).order_by('email').iterator():
			self.contacts.addItem(u.email)
		if self.contacts.count() > 0:
			self.widget_2.setDisabled(False)
			self.contacts.setCurrentRow(0)
			self.showDetails(self.contacts.currentItem())
		else:
			self.widget_2.setDisabled(True)

	def showDetails(self, item):
		if item:
			u = Contact.get_or_none(email=item.text(), account=self.ac)
			if u:
				self.curId = u.id
				self.email.setText(u.email)

	def add(self):
		d = AddContactDialog(self, self.ac)
		r = d.exec_()
		if r:
			self.loadList()

	def save(self):
		u = Contact.get_or_none(id=self.curId)
		if u:
			u.email = self.email.text()
			try:
				u.save()
				self.loadList()
			except Exception as e:
				QMessageBox.critical(self, 'Error', str(e))

	def remove(self):
		Contact.delete().where(Contact.id==self.curId).execute()
		self.loadList()

	def import_contact_enc_key(self):
		fname, _ = QFileDialog.getOpenFileName(self, 'Choose public key', os.getcwd())
		if not fname:
			return
		try:
			with open(fname, 'rb') as f:
				Contact.update(pub_enc_key=f.read()).where(Contact.id==self.curId).execute()
			QMessageBox.information(self, 'Info', 'Imported.')
		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))

	def import_contact_sgn_key(self):
		fname, _ = QFileDialog.getOpenFileName(self, 'Choose public key', os.getcwd())
		if not fname:
			return
		try:
			with open(fname, 'rb') as f:
				Contact.update(pub_sgn_key=f.read()).where(Contact.id==self.curId).execute()
			QMessageBox.information(self, 'Info', 'Imported.')
		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))

	def export_contact_enc_key(self):
		fname, _ = QFileDialog.getSaveFileName(self, 'Save public key', os.getcwd(),"Keys (*.puk)")
		if not fname:
			return
		else:
			try:
				c = [x for x in Contact.select(Contact.pub_enc_key).where(Contact.id==self.curId).limit(1).iterator()]
				if c:
					c = c[0]
					if c.pub_enc_key:
						with open(fname, 'wb') as f:
							f.write(c.pub_enc_key)
						QMessageBox.information(self, 'Info', 'Exported.')
					else:
						QMessageBox.information(self, 'Info', 'There is no key.')
			except Exception as e:
				QMessageBox.critical(self, 'Error', str(e))	

	def export_contact_sgn_key(self):
		fname, _ = QFileDialog.getSaveFileName(self, 'Save public key', os.getcwd(),"Keys (*.puk)")
		if not fname:
			return
		else:
			try:
				c = [x for x in Contact.select(Contact.pub_sgn_key).where(Contact.id==self.curId).limit(1).iterator()]
				if c:
					c = c[0]
					if c.pub_sgn_key:
						with open(fname, 'wb') as f:
							f.write(c.pub_sgn_key)
						QMessageBox.information(self, 'Info', 'Exported.')
					else:
						QMessageBox.information(self, 'Info', 'There is no key.')
			except Exception as e:
				QMessageBox.critical(self, 'Error', str(e))	

	def generate_enc_keys(self):
		prk, pbk = RSACipher().generate()
		Contact.update(my_enc_pub_key=pbk.exportKey(), 
			my_enc_pr_key=prk.exportKey()).where(Contact.id==self.curId).execute()
		QMessageBox.information(self, 'Info', 'Generated')

	def generate_sgn_keys(self):
		prk, pbk = DSACipher().generate()
		Contact.update(my_sgn_pub_key=pbk.exportKey(), 
			my_sgn_pr_key=prk.exportKey()).where(Contact.id==self.curId).execute()
		QMessageBox.information(self, 'Info', 'Generated')

	def send_enc_key(self):
		try:
			ac = User.get(id=self.ac)
			c = Contact.get(id=self.curId)
			msg = MIMEMultipart()
			msg['From']=ac.email
			msg["To"] = c.email
			msg["Subject"] = "PyQt Email Client Enc Key"
			
			part = MIMEBase("application", "octet-stream")
			part.set_payload(c.my_enc_pub_key)
			encoders.encode_base64(part)
			part.add_header(
					"Content-Disposition",
					"attachment", filename="key"
				)
			msg.attach(part)
			send_mail(ac.smtphost, ac.smtpport, ac.email, ac.passw, msg)
			QMessageBox.information(self,'Info','Sent.')

		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))

	def send_sgn_key(self):
		try:
			ac = User.get(id=self.ac)
			c = Contact.get(id=self.curId)
			msg = MIMEMultipart()
			msg['From']=ac.email
			msg["To"] = c.email
			msg["Subject"] = "PyQt Email Client Sign Key"
			
			part = MIMEBase("application", "octet-stream")
			part.set_payload(c.my_sgn_pub_key)
			encoders.encode_base64(part)
			part.add_header(
					"Content-Disposition",
					"attachment", filename="key"
				)
			msg.attach(part)
			send_mail(ac.smtphost, ac.smtpport, ac.email, ac.passw, msg)
			QMessageBox.information(self,'Info','Sent.')

		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))

	def import_enc_pub_key(self):
		fname, _ = QFileDialog.getOpenFileName(self, 'Choose public key', os.getcwd())
		if not fname:
			return
		try:
			with open(fname, 'rb') as f:
				Contact.update(my_enc_pub_key=f.read()).where(Contact.id==self.curId).execute()
			QMessageBox.information(self, 'Info', 'Imported.')
		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))

	def import_enc_pr_key(self):
		fname, _ = QFileDialog.getOpenFileName(self, 'Choose private key', os.getcwd())
		if not fname:
			return
		try:
			with open(fname, 'rb') as f:
				Contact.update(my_enc_pr_key=f.read()).where(Contact.id==self.curId).execute()
			QMessageBox.information(self, 'Info', 'Imported.')
		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))

	def import_sgn_pub_key(self):
		fname, _ = QFileDialog.getOpenFileName(self, 'Choose public key', os.getcwd())
		if not fname:
			return
		try:
			with open(fname, 'rb') as f:
				Contact.update(my_sgn_pub_key=f.read()).where(Contact.id==self.curId).execute()
			QMessageBox.information(self, 'Info', 'Imported.')
		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))

	def import_sgn_pr_key(self):
		fname, _ = QFileDialog.getOpenFileName(self, 'Choose private key', os.getcwd())
		if not fname:
			return
		try:
			with open(fname, 'rb') as f:
				Contact.update(my_sgn_pr_key=f.read()).where(Contact.id==self.curId).execute()
			QMessageBox.information(self, 'Info', 'Imported.')
		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))

	def export_enc_pub_key(self):
		fname, _ = QFileDialog.getSaveFileName(self, 'Save public key', os.getcwd(),"Keys (*.puk)")
		if not fname:
			return
		else:
			try:
				c = [x for x in Contact.select(Contact.my_enc_pub_key).where(Contact.id==self.curId).limit(1).iterator()]
				if c:
					c = c[0]
					if c.my_enc_pub_key:
						with open(fname, 'wb') as f:
							f.write(c.my_enc_pub_key)
						QMessageBox.information(self, 'Info', 'Exported.')
					else:
						QMessageBox.information(self, 'Info', 'There is no key.')
			except Exception as e:
				QMessageBox.critical(self, 'Error', str(e))	

	def export_enc_pr_key(self):
		fname, _ = QFileDialog.getSaveFileName(self, 'Save private key', os.getcwd(),"Keys (*.prk)")
		if not fname:
			return
		else:
			try:
				c = [x for x in Contact.select(Contact.my_enc_pr_key).where(Contact.id==self.curId).limit(1).iterator()]
				if c:
					c = c[0]
					if c.my_enc_pr_key:
						with open(fname, 'wb') as f:
							f.write(c.my_enc_pr_key)
						QMessageBox.information(self, 'Info', 'Exported.')
					else:
						QMessageBox.information(self, 'Info', 'There is no key.')
			except Exception as e:
				QMessageBox.critical(self, 'Error', str(e))	

	def export_sgn_pub_key(self):
		fname, _ = QFileDialog.getSaveFileName(self, 'Save public key', os.getcwd(),"Keys (*.puk)")
		if not fname:
			return
		else:
			try:
				c = [x for x in Contact.select(Contact.my_sgn_pub_key).where(Contact.id==self.curId).limit(1).iterator()]
				if c:
					c = c[0]
					if c.my_sgn_pub_key:
						with open(fname, 'wb') as f:
							f.write(c.my_sgn_pub_key)
						QMessageBox.information(self, 'Info', 'Exported.')
					else:
						QMessageBox.information(self, 'Info', 'There is no key.')
			except Exception as e:
				QMessageBox.critical(self, 'Error', str(e))	

	def export_sgn_pr_key(self):
		fname, _ = QFileDialog.getSaveFileName(self, 'Save private key', os.getcwd(),"Keys (*.prk)")
		if not fname:
			return
		else:
			try:
				c = [x for x in Contact.select(Contact.my_sgn_pr_key).where(Contact.id==self.curId).limit(1).iterator()]
				if c:
					c = c[0]
					if c.my_sgn_pr_key:
						with open(fname, 'wb') as f:
							f.write(c.my_sgn_pr_key)
						QMessageBox.information(self, 'Info', 'Exported.')
					else:
						QMessageBox.information(self, 'Info', 'There is no key.')
			except Exception as e:
				QMessageBox.critical(self, 'Error', str(e))	


class ReadUi_Widget(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		uic.loadUi('read.ui', self)


class ReadWidget(QMainWindow):
	def __init__(self, parent, msg, status, pth, fmsg, encrypted, signed, uid, uidv, boxid, usid, bname):
		super().__init__(parent)
		self.path = pth
		self.encrypted = encrypted
		self.signed = signed
		self.fmsg = fmsg
		self.msg = msg
		self.uid = uid
		self.uidv = uidv
		self.boxid = boxid
		self.bname = bname
		self.usId = usid
		s = msg['subject']
		if not s:
			s = 'Message'
		self.setWindowTitle(s)
		w = ReadUi_Widget()
		self.setCentralWidget(w)
		if self.usId is None:
			w.saveB.hide()
		w.body.setHtml(msg['body'])
		for a in msg.get('attachments',[]):
			w.attchs.addItem(a)
		w.header.append(f"Date: {msg['date']}")
		w.header.append(f"From: {', '.join([f'<{s[1]}> {s[0]}' for s in msg['from']])}")
		w.header.append(f"To: {', '.join([f'<{s[1]}> {s[0]}' for s in msg['to']])}")
		w.header.append(f"Subject: {msg['subject']}")
		w.status.setText(status)
		w.header.setReadOnly(True)
		w.body.setReadOnly(True)
		w.attchs.itemClicked.connect(self.showFile)
		w.saveB.clicked.connect(self.save)
		self.setMinimumSize(750,500)
		self.show()

	def showFile(self, item):
		try:
			if sys.platform == "win32":
				os.startfile(self.path)
			else:
				opener = "open" if sys.platform == "darwin" else "xdg-open"
				subprocess.call([opener, self.path])
		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))

	def closeEvent(self, event):
		shutil.rmtree(self.path, ignore_errors=True)
		event.accept()

	@default_error_handler
	def save(self):
		b = None
		with db.atomic():
			b = MailFolder.get_or_none(account=self.usId, name=self.boxid)
			if not b:
				b = MailFolder.create(account=self.usId, uidvalidity=self.uidv, name=self.boxid, vname=self.bname)
		m = Mail.get_or_none(uid=self.uid, uidvalidity=self.uidv, box=b.id)
		if m:
			QMessageBox.warning(self, 'Info', 'Message has been already saved.')
		else:
			Mail.insert(from_=','.join([s[1] for s in self.msg['from']]),
			  to_=','.join([s[1] for s in self.msg['to']]),
			  subject=self.msg['subject'],
			  box=b.id,
			  uid=self.uid,
			  uidvalidity=self.uidv,
			  message=self.fmsg.as_bytes(),
			  date_time=self.msg.get('date'),
			  encrypted=self.encrypted,
			  signed=self.signed).execute()
			QMessageBox.information(self, 'Info', 'Saved.')


class ComposeWindow(QDialog):
	def __init__(self, parent):
		super().__init__(parent)
		uic.loadUi('compose2.ui', self)
		self.parent = parent
		self.paths = []
		self.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.resetData)
		self.addBtn.clicked.connect(self.addAttachment)
		self.rmBtn.clicked.connect(self.removeAttachment)
		self.ed = myEditor()
		ed = self.ed
		ed.setWindowFlags(
			ed.windowFlags() & ~QtCore.Qt.Window)
		lt = QVBoxLayout()
		lt.addWidget(ed)
		drB=self.buttonBox.button(QDialogButtonBox.Apply)
		drB.setText('Save as draft')
		drB.clicked.connect(self.saveAsDraft)
		self.buttonBox.button(QDialogButtonBox.Ok).setText('Send')
		self.widget.setLayout(lt)

	def resetData(self):
		self.recepients.clear()
		self.subject.clear()
		self.ed.editor.clear()
		self.attchs.clear()
		self.paths=[]
		self.encrypted.setChecked(True)

	def addAttachment(self):
		fname = QFileDialog.getOpenFileName(self, 'Open file', os.getcwd())[0]
		if fname and (fname not in self.paths):
			self.paths.append(fname)
			self.attchs.addItem(fname)

	def removeAttachment(self):
		for it in self.attchs.selectedItems():
			r = self.attchs.row(it)
			i = self.attchs.takeItem(r)
			del i
			del self.paths[r]

	@default_error_handler
	def saveAsDraft(self):
		if not self.recepients.text().strip():
			QMessageBox.warning(self,'Error', 'Input the contact.')
			return
		#if self.encrypted.isChecked() or self.signd.isChecked():
		#	QMessageBox.warning(self, '', 'Unable to save encrypted or signed message as draft.')
		if self.encrypted.isChecked():
			QMessageBox.warning(self, 'Info', 'Unable to save encrypted message as draft.')
		elif self.signd.isChecked():
			p = self.parent
			u = p.curU
			c = Contact.get_or_none(email=self.recepients.text().strip(), account=u)
			if not c:
				QMessageBox.warning(self, 'Info', 'Add recepient to contacts.')
				return
			msg = MIMEMultipart()
			msg['From']=p.curAc
			msg["To"] = self.recepients.text()
			msg["Subject"] = self.subject.text()
			msg.attach(MIMEText(self.ed.editor.toHtml(), "html"))
			for a in self.paths:
				with open(a, 'rb') as at:
					part = MIMEBase("application", "octet-stream")
					part.set_payload(at.read())
				encoders.encode_base64(part)
				part.add_header(
					"Content-Disposition",
					"attachment", filename=os.path.basename(a)
				)
				msg.attach(part)
			saveAsDraft(u.imaphost, u.imapport, u.email, u.passw, sign_mail(msg, c.my_sgn_pr_key))
			QMessageBox.information(self, 'Info', 'Saved.')
		else:
			p = self.parent
			u = p.curU
			msg = MIMEMultipart()
			msg['From']=p.curAc
			msg["To"] = self.recepients.text()
			msg["Subject"] = self.subject.text()
			msg.attach(MIMEText(self.ed.editor.toHtml(), "html"))
			for a in self.paths:
				with open(a, 'rb') as at:
					part = MIMEBase("application", "octet-stream")
					part.set_payload(at.read())
				encoders.encode_base64(part)
				part.add_header(
					"Content-Disposition",
					"attachment", filename=os.path.basename(a)
				)
				msg.attach(part)
			saveAsDraft(u.imaphost, u.imapport, u.email, u.passw, msg)
			QMessageBox.information(self, 'Info', 'Saved.')


	@default_error_handler
	def sendMail(self):
		if self.encrypted.isChecked():
			p = self.parent
			r = self.recepients.text().strip()
			u = p.curU
			c = Contact.get_or_none(email=r, account=u)
			if not c:
				QMessageBox.warning(self, 'Info', 'Add recepient to contacts and request his public key for encrypted communication.')
				return
			if not c.pub_enc_key:
				QMessageBox.warning(self, 'Info', "You don't have recepient's public key.")
				return
			msg = MIMEMultipart()
			msg['From']=p.curAc
			msg["To"] = r
			msg["Subject"] = self.subject.text()
			msg.attach(MIMEText(self.ed.editor.toHtml(), "html"))
			for a in self.paths:
				with open(a, 'rb') as at:
					part = MIMEBase("application", "octet-stream")
					part.set_payload(at.read())
				encoders.encode_base64(part)
				part.add_header(
					"Content-Disposition",
					"attachment", filename=os.path.basename(a)
				)
				msg.attach(part)
			send_mail(u.smtphost, u.smtpport, u.email, u.passw, 
				sign_and_enc(msg, c.my_sgn_pr_key, c.pub_enc_key))
		elif self.signd.isChecked():
			p = self.parent
			u = p.curU
			r = self.recepients.text().strip()
			c = Contact.get_or_none(email=r, account=u)
			if not c:
				QMessageBox.warning(self, 'Info', 'Add recepient to contacts.')
				return
			msg = MIMEMultipart()
			msg['From']=p.curAc
			msg["To"] = self.recepients.text()
			msg["Subject"] = self.subject.text()
			msg.attach(MIMEText(self.ed.editor.toHtml(), "html"))
			for a in self.paths:
				with open(a, 'rb') as at:
					part = MIMEBase("application", "octet-stream")
					part.set_payload(at.read())
				encoders.encode_base64(part)
				part.add_header(
					"Content-Disposition",
					"attachment", filename=os.path.basename(a)
				)
				msg.attach(part)
			send_mail(u.smtphost, u.smtpport, u.email, u.passw, sign_mail(msg, c.my_sgn_pr_key))
		else:
			p = self.parent
			u = p.curU
			msg = MIMEMultipart()
			msg['From']=p.curAc
			msg["To"] = self.recepients.text()
			msg["Subject"] = self.subject.text()
			msg.attach(MIMEText(self.ed.editor.toHtml(), "html"))
			for a in self.paths:
				with open(a, 'rb') as at:
					part = MIMEBase("application", "octet-stream")
					part.set_payload(at.read())
				encoders.encode_base64(part)
				part.add_header(
					"Content-Disposition",
					"attachment", filename=os.path.basename(a)
				)
				msg.attach(part)
			send_mail(u.smtphost, u.smtpport, u.email, u.passw, msg)

	def accept(self):
		try:
			if self.recepients.text().strip():
				self.sendMail()
				super().accept()
			else:
				QMessageBox.warning(self,'Error', 'Input the contact.')
		except Exception as e:
			QMessageBox.critical(self, 'Error', str(e))


class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		uic.loadUi('main2.ui', self)
		self.compB.clicked.connect(self.compose)
		self.compw = None
		self.boxes.itemClicked.connect(self.setBox)
		self.getB.clicked.connect(self.loadMail)
		self.syncB.clicked.connect(self.sync)
		self.modes.addItem("Online")
		self.modes.addItem("Offline")
		self.modes.currentIndexChanged.connect(self.setMode)
		self.cbox = None
		self.menubar = QMenuBar()
		self.menubar.addAction("Accounts", self.openAccounts)
		self.menubar.addAction("Contacts", self.openContacts)
		self.setMenuBar(self.menubar)
		self.prevpB.clicked.connect(self.prevPage)
		self.nextpB.clicked.connect(self.nextPage)
		self.page.valueChanged.connect(self.pageChange)
		self.mails.setColumnCount(5)
		self.mails.setSelectionMode(QTableView.MultiSelection)
		self.mails.setSelectionBehavior(QTableView.SelectRows)
		self.mails.setEditTriggers(QTableView.NoEditTriggers)
		self.mails.doubleClicked.connect(self.readMail)
		self.curAc = None
		self.curU = None
		self.flag1 = False
		self.bids = []
		self.loadAccounts()
		self.psize = 20
		self.delB.clicked.connect(self.delSelected)
		self.delAB.clicked.connect(self.delAll)
		self.accounts.currentIndexChanged.connect(self.setAccount)
		self.show()
		self.getBoxes()

	def prevPage(self):
		self.page.setValue(self.page.value()-1)
		self.loadMail()
	
	def nextPage(self):
		self.page.setValue(self.page.value()+1)
		self.loadMail()

	def getBoxes(self):
		self.boxes.clear()
		self.bids = []
		self.mids = []
		self.mails.clear()
		self.mails.setRowCount(0)
		try:
			u = self.curU
			if u:
				if self.modes.currentIndex() == 0:
					imap = None
					try:
						imap = IMAP4_SSL(u.imaphost, u.imapport)
					except Exception as e:
						traceback.print_exc()
						QMessageBox.critical(self, 'Error', "Can't connect")
						return
					imap.login(u.email, u.passw)
					for b in imap.list()[1]:
						l = b.decode().split(' "/" ')
						fls = [x for x in l[0][1:].rstrip(')').split()]
						if "\\Noselect" not in fls:
							fls = [x for x in fls if x != '\\HasChildren' and x != '\\HasNoChildren']
							if fls:
								self.boxes.addItem(" ".join(fls))
							else:
								self.boxes.addItem(l[1])
							self.bids.append(l[1])
					imap.logout()
				else:
					for b in MailFolder.select().where(MailFolder.account==u.id).iterator():
						self.boxes.addItem(b.vname)
						self.bids.append(b.id)
				if self.bids:
					self.boxes.setCurrentRow(0)
					self.cbox = self.bids[0]
				else:
					self.cbox = None
		except Exception as e:
			traceback.print_exc()
			QMessageBox.critical(self, 'Error', str(e))

	def loadAccounts(self):
		self.flag1 = True
		self.accounts.clear()
		for u in User.select(User.email).order_by('email').iterator():
			self.accounts.addItem(u.email)
		self.flag1 = False
		i = self.accounts.findText(self.curAc, QtCore.Qt.MatchFixedString)
		if i >= 0:
			self.accounts.setCurrentIndex(i)
		else:
			if self.accounts.count():
				self.curAc = self.accounts.itemText(0)
				self.curU = User.get_or_none(email=self.curAc)
				self.accounts.setCurrentIndex(0)
				#self.getBoxes()
			else:
				self.curAc = None
				self.curU = None

	def openAccounts(self):
		d=AccountsWindow(self)
		d.exec_()
		self.loadAccounts()

	def openContacts(self):
		if self.curAc:
			d=ContactsWindow(self, self.curAc)
			d.exec_()

	def getImapMails(self):
		u = self.curU
		imap = None
		try:
			imap = IMAP4_SSL(u.imaphost, u.imapport)
		except Exception as e:
			QMessageBox.critical(self, 'Error', "Can't access box")
			return
		try:
			imap.login(u.email, u.passw)
			imap.select(self.cbox)
			rv, data = imap.search(None, "ALL")
			self.mids = []
			self.mails.clear()
			self.mails.setRowCount(0)
			if self.page.value() > 1:
				data = data[0].split()[-self.page.value()*self.psize:-self.page.value()*self.psize+self.psize]
			else:
				data = data[0].split()[-self.page.value()*self.psize:]
			for num in reversed(data):
				rv, data = imap.fetch(num, '(RFC822)')
				m = mailparser.parse_from_bytes(data[0][1])
				rowPosition = self.mails.rowCount()
				self.mails.insertRow(rowPosition)
				if m.headers.get('X-PYQT-CLIENT-ENCRYPTED'):
					self.mails.setItem(rowPosition, 0, 
						QTableWidgetItem('*'))
				elif m.headers.get('X-PYQT-CLIENT-SIGNED'):
					self.mails.setItem(rowPosition, 0, 
					QTableWidgetItem('s'))
				else:
					self.mails.setItem(rowPosition, 0, 
						QTableWidgetItem('-'))
				if m.message.get('date'):
					self.mails.setItem(rowPosition, 1, QTableWidgetItem(
						str(datetime.fromtimestamp(eutils.mktime_tz(eutils.parsedate_tz(m.message.get('date')))))
					))
				self.mails.setItem(rowPosition, 2, QTableWidgetItem(",".join([str(x[1]) for x in m.from_])))
				self.mails.setItem(rowPosition, 4, QTableWidgetItem(",".join([str(x[1]) for x in m.to_])))
				self.mails.setItem(rowPosition, 3, QTableWidgetItem(str(m.subject)[:30]))
				self.mids.append(num)
			self.mails.setHorizontalHeaderLabels(["E","Date", "From", "Subject", "To"])
			imap.close()
			imap.logout()
			self.mails.resizeColumnsToContents()
		except Exception as e:
			traceback.print_exc()
			QMessageBox.critical(self, 'Error', str(e))

	@default_error_handler
	def getLocalMails(self):
		self.mids = []
		self.mails.clear()
		self.mails.setRowCount(0)
		for m in Mail.select(
			Mail.encrypted, Mail.to_, Mail.subject, Mail.from_, Mail.id, Mail.date_time
			).where(Mail.box==self.cbox).offset((self.page.value()-1)*self.psize).limit(self.psize).order_by(Mail.date_time.desc()).iterator():
			rowPosition = self.mails.rowCount()
			self.mails.insertRow(rowPosition)
			if m.encrypted:
				self.mails.setItem(rowPosition, 0, 
					QTableWidgetItem('*'))
			elif m.signed:
				self.mails.setItem(rowPosition, 0, 
					QTableWidgetItem('s'))
			else:
				self.mails.setItem(rowPosition, 0, 
					QTableWidgetItem('-'))
			self.mails.setItem(rowPosition, 1, QTableWidgetItem(
					str(m.date_time)
				))
			self.mails.setItem(rowPosition, 2, QTableWidgetItem(m.from_))
			self.mails.setItem(rowPosition, 4, QTableWidgetItem(m.to_))
			self.mails.setItem(rowPosition, 3, QTableWidgetItem(str(m.subject)[:30]))
			self.mids.append(m.id)
		self.mails.setHorizontalHeaderLabels(["E","Date", "From", "Subject", "To"])
		self.mails.resizeColumnsToContents()

	def loadMail(self):
		if self.curAc:
			if self.modes.currentIndex() == 0:
				#t = GenericThread(self.getImapMails)
				#d = LoadingWindow(self, t)
				#d.exec_()
				self.getImapMails()
			else:
				self.getLocalMails()

	def pageChange(self, value):
		#self.loadMail()
		pass

	def setBox(self, item):
		self.cbox = self.bids[self.boxes.row(item)]
		self.page.setValue(1)
		self.loadMail()

	def setAccount(self, v):
		value = self.accounts.itemText(v)
		if self.curAc != value and not self.flag1:
			self.curAc = value
			self.curU=User.get_or_none(email=self.curAc)
			self.getBoxes()
			self.mids = []
			self.mails.clear()
			self.mails.setRowCount(0)

	def setMode(self, value):
		self.page.setValue(1)
		self.getBoxes()

	@default_error_handler
	def sync(self):
		if self.curAc:
			if not self.cbox:
				QMessageBox.warning(self, 'Error', 'Mailfolder is not chosen.')
				return
			u = self.curU
			b = None
			if self.modes.currentIndex() == 0:
				b = self.cbox
			else:
				b = MailFolder.get(id=self.cbox).name
			imap = None
			try:
				imap = IMAP4_SSL(u.imaphost, u.imapport)
			except Exception as e:
				QMessageBox.critical(self, 'Error', "Can't access box")
				return
			imap.login(u.email, u.passw)
			stat, mcount = imap.select(b)
			mcount = mcount[0].decode()

			ret = QMessageBox.question(self, "Question", f"Are you sure to download {mcount} messages?\n(You CAN'T cancel this operation.)")
			if ret == QMessageBox.Yes:
				uidv = imap.response('UIDVALIDITY')[1][0].decode()
				fold=None
				with db.atomic():
					fold = MailFolder.get_or_none(account=u.id, name=b)
					if fold and fold.uidvalidity != uidv:
						fold.uidvalidity = uidv
						fold.save()
				if not fold:
					fold=MailFolder.create(account=u.id, name=b, uidvalidity=uidv, vname=self.boxes.currentItem().text())
				Mail.delete().where(Mail.box==fold.id, Mail.uidvalidity!=uidv).execute()
				rv, data = imap.search(None, "ALL")
				data = data[0].split()
				Mail.delete().where(Mail.box==fold.id, Mail.uid.not_in([x.decode() for x in data])).execute()
				for num in reversed(data):
					mid = num.decode()
					if Mail.select(Mail.id).where(Mail.box==fold.id,Mail.uid==mid,Mail.uidvalidity==uidv).exists():
						continue
					rv, data = imap.fetch(num, '(RFC822)')
					data = mailparser.parse_from_bytes(data[0][1])
					is_enc = bool(data.headers.get('X-PYQT-CLIENT-ENCRYPTED'))
					is_sgnd = bool(data.headers.get('X-PYQT-CLIENT-SIGNED'))
					date_time=datetime.fromtimestamp(eutils.mktime_tz(eutils.parsedate_tz(data.message.get('date')))) if data.message.get('date') else None
					from_=data.from_
					subject=data.subject
					to_=data.to
					Mail.insert(box=fold.id, uid=mid, uidvalidity=uidv,
						subject=subject, 
						to_=','.join([s[1] for s in to_]), 
						from_=','.join([s[1] for s in from_]),
						date_time=date_time,
						encrypted=is_enc,
						signed=is_sgnd,
						message = data.message.as_bytes()).execute()
				imap.close()
				imap.logout()
				QMessageBox.information(self, 'Info', 'Synced.')
			else:
				imap.close()
				imap.logout()
		else:
			QMessageBox.warning(self, 'Error', 'Account is not chosen.')

	def compose(self):
		if self.compw == None:
			self.compw = ComposeWindow(self)
		self.compw.exec_()

	def readMail(self, item):
		row = item.row()
		i = self.mids[row]
		if self.modes.currentIndex() == 0:
			try:
				u = self.curU
				imap = None
				try:
					imap = IMAP4_SSL(u.imaphost, u.imapport)
				except Exception as e:
					QMessageBox.critical(self, 'Error', "Can't access box")
					return
				imap.login(u.email, u.passw)
				imap.select(self.cbox)
				uidv = imap.response('UIDVALIDITY')[1][0].decode()
				with db.atomic():
					b = MailFolder.get_or_none(account=u.id, name=self.cbox)
					if b and b.uidvalidity != uidv:
						b.uidvalidity = uidv
						b.save()
				#typ, data = imap.search(None, '(HEADER Message-ID "%s")' % i)
				rw, data = imap.fetch(i, '(RFC822)')
				imap.close()
				imap.logout()

				data = mailparser.parse_from_bytes(data[0][1])

				if data.headers.get('X-PYQT-CLIENT-ENCRYPTED'):
					from_ = data.from_
					to = data.to
					fr = from_[0][1]
					t = to[0][1]
					if fr == self.curAc and t != self.curAc:
						QMessageBox.warning(self, 'Info', 'Cannot decrypt sent message.')
						return
					else: 
						c = Contact.get_or_none(email=fr, account=u)
						if c:
							subject = data.subject
							msg = None
							status = None
							try:
								msg, status = dec_and_ver(data.message, c.my_enc_pr_key, c.pub_sgn_key)
							except:
								QMessageBox.critical(self, 'Error', "Can't decrypt.")
								return
							msg = mailparser.parse_from_bytes(msg)
							m = {}
							m['date']=datetime.fromtimestamp(eutils.mktime_tz(eutils.parsedate_tz(data.message.get('date')))) if data.message.get('date') else None
							m['from']=from_
							m['subject']=subject
							m['body']=msg.body
							m['to']=to
							pth = None
							if msg.attachments:
								pth = os.path.join(os.getcwd(), f"tmp/{self.curAc}/{randint(1,9999999999)}")
								try:
									msg.write_attachments(pth)
									m['attachments']=[a['filename'] for a in msg.attachments]
								except:
									pass
							w = ReadWidget(self, m, status, pth, data.message, True, True, i.decode(), uidv, self.cbox, u.id, self.boxes.currentItem().text())
						else:
							QMessageBox.warning(self, 'Info', "Sender isn't in contact list.")
							return
				elif data.headers.get('X-PYQT-CLIENT-SIGNED'):
					m = {}
					m['date']=datetime.fromtimestamp(eutils.mktime_tz(eutils.parsedate_tz(data.message.get('date')))) if data.message.get('date') else None
					m['from']=data.from_
					c = Contact.get_or_none(email=data.from_[0][1], account=u)
					if c:
						c = c.pub_sgn_key
					m['subject']=data.subject
					m['body']=data.body
					m['to']=data.to
					pth = None
					if data.attachments:
						pth = os.path.join(os.getcwd(), f"tmp/{self.curAc}/{randint(1,9999999999)}")
						try:
							data.write_attachments(pth)
							m['attachments']=[a['filename'] for a in data.attachments][:-1]
						except:
							pass
					w = ReadWidget(self, m, verify_mail(data.message, c), pth, data.message, False, True, i.decode(), uidv, self.cbox, u.id, self.boxes.currentItem().text())
				else:
					m = {}
					m['date']=datetime.fromtimestamp(eutils.mktime_tz(eutils.parsedate_tz(data.message.get('date')))) if data.message.get('date') else None
					m['from']=data.from_
					m['subject']=data.subject
					m['body']=data.body
					m['to']=data.to
					pth = None
					if data.attachments:
						pth = os.path.join(os.getcwd(), f"tmp/{self.curAc}/{randint(1,9999999999)}")
						try:
							data.write_attachments(pth)
							m['attachments']=[a['filename'] for a in data.attachments]
						except:
							pass
					w = ReadWidget(self, m, 'Not signed.', pth, data.message, False, False, i.decode(), uidv, self.cbox, u.id, self.boxes.currentItem().text())

			except Exception as e:
				#traceback.print_exc()
				QMessageBox.critical(self, 'Error', str(e))
		else:
			try:
				u = self.curU
				m = Mail.get(id=i)
				data = mailparser.parse_from_bytes(m.message)
				is_enc = m.encrypted
				is_sgnd = m.signed
				del m
				if is_enc:
					from_ = data.from_
					to = data.to
					fr = from_[0][1]
					t = to[0][1]
					if fr == self.curAc and t != self.curAc:
						QMessageBox.warning(self, 'Info', 'Cannot decrypt sent message.')
						return
					else: 
						c = Contact.get_or_none(email=fr, account=u)
						if c:
							subject = data.subject
							msg = None
							status = None
							try:
								msg, status = dec_and_ver(data.message, c.my_enc_pr_key, c.pub_sgn_key)
							except:
								QMessageBox.critical(self, 'Error', "Can't decrypt.")
								return
							msg = mailparser.parse_from_bytes(msg)
							m = {}
							m['date']=datetime.fromtimestamp(eutils.mktime_tz(eutils.parsedate_tz(data.message.get('date'))))
							m['from']=from_
							m['subject']=subject
							m['body']=msg.body
							m['to']=to
							pth = None
							if msg.attachments:
								pth = os.path.join(os.getcwd(), f"tmp/{self.curAc}/{randint(1,9999999999)}")
								try:
									msg.write_attachments(pth)
									m['attachments']=[a['filename'] for a in msg.attachments]
								except:
									pass
							w = ReadWidget(self, m, status, pth, None, True, True, None, None, None, None, None)
						else:
							QMessageBox.warning(self, 'Info', "Sender isn't in contact list.")
							return
				elif is_sgnd:
					m = {}
					m['date']=datetime.fromtimestamp(eutils.mktime_tz(eutils.parsedate_tz(data.message.get('date'))))
					m['from']=data.from_
					c = Contact.get_or_none(email=data.from_[0][1], account=u)
					if c:
						c = c.pub_sgn_key
					m['subject']=data.subject
					m['body']=data.body
					m['to']=data.to
					pth = None
					if data.attachments:
						pth = os.path.join(os.getcwd(), f"tmp/{self.curAc}/{randint(1,9999999999)}")
						try:
							data.write_attachments(pth)
							m['attachments']=[a['filename'] for a in data.attachments][:-1]
						except:
							pass
					w = ReadWidget(self, m, verify_mail(data.message, c), pth, None, False, True, None, None, None, None, None)
				else:
					m = {}
					m['date']=datetime.fromtimestamp(eutils.mktime_tz(eutils.parsedate_tz(data.message.get('date'))))
					m['from']=data.from_
					m['subject']=data.subject
					m['body']=data.body
					m['to']=data.to
					pth = None
					if data.attachments:
						pth = os.path.join(os.getcwd(), f"tmp/{self.curAc}/{randint(1,9999999999)}")
						try:
							data.write_attachments(pth)
							m['attachments']=[a['filename'] for a in data.attachments]
						except:
							pass
					w = ReadWidget(self, m, 'Not signed.', pth, None, False, False, None, None, None, None, None)
			except Exception as e:
				#traceback.print_exc()
				QMessageBox.critical(self, 'Error', str(e))

	@default_error_handler
	def delSelected(self):
		if self.mails.rowCount() > 0:
			selected = self.mails.selectionModel().selectedRows()
			if selected:
				selected = [self.mids[x.row()] for x in selected]
				if self.modes.currentIndex() == 0:
					u = self.curU
					imap = None
					try:
						imap = IMAP4_SSL(u.imaphost, u.imapport)
					except Exception as e:
						QMessageBox.critical(self, 'Error', "Can't access box")
						return
					imap.login(u.email, u.passw)
					imap.select(self.cbox)
					for s in selected:
						imap.store(s, '+FLAGS', '\\Deleted')
					imap.close()
					imap.logout()
					self.getImapMails()
				else:
					Mail.delete().where(Mail.id<<selected).execute()
					self.getLocalMails()


	@default_error_handler
	def delAll(self):
		if self.curAc and self.cbox is not None:
			ret = QMessageBox.question(self, '', 'Are you sure to delete all messages in this folder?')
			if ret == QMessageBox.Yes:
				if self.modes.currentIndex() == 0:
					u = self.curU
					imap = None
					try:
						imap = IMAP4_SSL(u.imaphost, u.imapport)
					except Exception as e:
						QMessageBox.critical(self, 'Error', "Can't access box")
						return
					imap.login(u.email, u.passw)
					imap.select(self.cbox)
					_, data = imap.search(None, 'ALL')
					for num in data[0].split():
						imap.store(num, '+FLAGS', '\\Deleted')
					imap.close()
					imap.logout()
					self.getImapMails()
				else:
					MailFolder.delete().where(MailFolder.id==self.cbox).execute()
					self.getBoxes()
				QMessageBox.information(self, 'Info', 'Deleted.')




if __name__ == '__main__':
	app = QApplication(sys.argv)
	if not os.path.isfile("./db"):
		create_tables()
	client = MainWindow()
	sys.exit(app.exec_())
