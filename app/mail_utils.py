from smtplib import SMTP_SSL, SMTP
from imaplib import IMAP4_SSL, Time2Internaldate
import time
import ssl
from cipher_utils import *
from copy import deepcopy
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import message_from_bytes
from email.header import Header
from email import encoders

def send_mail(smtp_host, smtp_port, login, passw, message):
	smtp=None
	try:
		context = ssl.SSLContext(ssl.PROTOCOL_TLS)
		smtp = SMTP(smtp_host, smtp_port)
		smtp.starttls(context=context)
		smtp.ehlo()
	except:
		smtp = SMTP_SSL(smtp_host, smtp_port)
		smtp.ehlo()
	smtp.login(login, passw) 
	smtp.sendmail(message['From'], message["To"], message.as_string())
	smtp.quit()

def saveAsDraft(imaphost, imapport, login, passw, message):
	imap = IMAP4_SSL(imaphost, imapport)
	imap.login(login, passw)
	dr = None
	for b in imap.list()[1]:
		l = b.decode().split(' "/" ')
		if 'Drafts' in l[0]:
			dr = l[1]
			break
	stat, _ = imap.select(dr)
	if stat != 'OK':
		imap.logout()
		raise Exception("Can't connect to Drafts folder")
	imap.append(dr, '\\Draft', Time2Internaldate(time.time()), message.as_bytes())
	imap.close()
	imap.logout()


def _pop_headers(msg, blacklist=None):
	"""Removes headers from message and removes list of removed headers.

	Args:
		msg (:obj:`email.message.Message`): The message object to sign and encrypt.
		blacklist (:obj:`list` of `str`):

	Returns:
		list: removed headers

	Attention:
		side effect:  will remove headers from passed in `msg`

	Attention:
		duplicate headers are not supported at this point

	"""

	blacklisted_headers = set()
	blacklisted_headers.add('content-type')
	blacklisted_headers.add('mime-version')

	if blacklist:
		for item in blacklist:
			blacklisted_headers.add(item.lower())

	headers = []
	for header in msg.items():
		# print("processing: {} - {}".format(header[0], header[1]))
		if header[0].lower() in blacklisted_headers:
			continue

		if isinstance(header[0], Header):
			print("\n\n---\nFound a header!\n---\n\n")
		headers.append(header)
		msg.__delitem__(header[0])

	return headers


def sign_and_enc(msg, sgnk, enck):
	msg = deepcopy(msg)
	pheaders = _pop_headers(msg)
	msg3 = MIMEMultipart()
	msg3.attach(msg)
	part = MIMEBase("application", "octet-stream")
	part.set_payload(DSACipher().sign(sgnk, msg.as_bytes()))
	encoders.encode_base64(part)
	part.add_header(
					"Content-Disposition",
					"attachment", filename="digest"
				)
	msg3.attach(part)
	aeskey = AESCipher().generate()
	part = MIMEBase("application", "octet-stream")
	part.set_payload(AESCipher().encrypt(aeskey, msg3.as_bytes()))
	encoders.encode_base64(part)
	part.add_header(
					"Content-Disposition",
					"attachment", filename="enc_message"
				)
	msg3 = MIMEMultipart()
	msg3.attach(part)
	part = MIMEBase("application", "octet-stream")
	part.set_payload(RSACipher().encrypt(enck, aeskey))
	encoders.encode_base64(part)
	part.add_header(
					"Content-Disposition",
					"attachment", filename="key"
				)
	msg3.attach(part)
	for header in pheaders:
		try:
			msg3.replace_header(header[0], str(header[1]))
		except KeyError:
			msg3.add_header(header[0], str(header[1]))
	msg3.add_header('X-PYQT-CLIENT-ENCRYPTED', 'True')
	return msg3

def dec_and_ver(msg, ek, sk):
	#pheaders = _pop_headers(msg2)
	parts = list(msg.walk())
	if len(parts) != 3:
		raise Exception('Incorrect message structure.')
	key = RSACipher().decrypt(ek,parts[2].get_payload(decode=True))
	msg = message_from_bytes(AESCipher().decrypt(key, parts[1].get_payload(decode=True)))
	digest = None
	for part in msg.walk(): 
		if part.get_content_maintype() == 'multipart':
			continue
		if part.get('Content-Disposition') is None:
			continue
		if part.get_filename() == "digest":
			digest = part
	if not digest:
		raise Exception('Incorrect message structure.')
	p = None
	for part in msg.walk(): 
		if part.get_content_maintype() == 'multipart':
			p = part
	if not p:
		raise Exception('Incorrect message structure.')
	msg = p.as_bytes()
	digest = digest.get_payload(decode=True)
	status = "Not verified!"
	if sk is None:
		status = "No public key available!"
	else:
		try:
			status = "Verified." if DSACipher().verify(sk, msg, digest) else "Not verified!"
		except Exception as e:
			status = "Error during decrypting."
	return msg, status

def sign_mail(msg, sgnk):
	msg = deepcopy(msg)
	pheaders = _pop_headers(msg)
	part = MIMEBase("application", "octet-stream")
	part.set_payload(DSACipher().sign(sgnk, msg.as_bytes()))
	encoders.encode_base64(part)
	part.add_header(
					"Content-Disposition",
					"attachment", filename="digest"
				)
	msg.attach(part)
	for header in pheaders:
		try:
			msg.replace_header(header[0], str(header[1]))
		except KeyError:
			msg.add_header(header[0], str(header[1]))
	msg.add_header('X-PYQT-CLIENT-SIGNED', 'True')
	return msg

def verify_mail(msg, sk):
	if sk is None:
		return "No public key available!"
	msg = deepcopy(msg)
	digest = None
	i = 0
	di = 0
	for part in msg.walk(): 
		if part.get_content_maintype() == 'multipart':
			i+=1
			continue
		if part.get('Content-Disposition') is None:
			i+=1
			continue
		if part.get_filename() == "digest":
			i+1
			digest = part
			di = i
	if not digest:
		raise Exception('Incorrect message structure.')
	digest = digest.get_payload(decode=True)
	del msg.get_payload()[di]
	_pop_headers(msg)
	status = "Not verified!"
	try:
		status = "Verified." if DSACipher().verify(sk, msg.as_bytes(), digest) else "Not verified!"
	except Exception as e:
		status = "Error during decrypting."
	return status


