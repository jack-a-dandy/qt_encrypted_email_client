from peewee import (
	SqliteDatabase, Model, CharField, IntegerField, ForeignKeyField,
	BooleanField, BlobField, DateTimeField
)

db = SqliteDatabase('./db')

class BaseModel(Model):
	class Meta:
		database = db


class User(BaseModel):
	email = CharField(unique=True)
	passw = CharField()
	smtphost = CharField()
	smtpport = IntegerField()
	imaphost = CharField()
	imapport = IntegerField()

	class Meta:
		table_name = "users"


class Contact(BaseModel):
	email = CharField()
	pub_enc_key = BlobField(null=True)
	pub_sgn_key = BlobField(null=True)
	my_enc_pub_key = BlobField(null=True)
	my_enc_pr_key = BlobField(null=True)
	my_sgn_pub_key = BlobField(null=True)
	my_sgn_pr_key = BlobField(null=True)
	account = ForeignKeyField(User, on_delete='CASCADE', on_update='CASCADE')

	class Meta:
		table_name = "contacts"
		indexes = (
				(("email", "account_id"), True),
			)


class MailFolder(BaseModel):
	name = CharField()
	vname = CharField()
	account = ForeignKeyField(User, on_delete='CASCADE', on_update='CASCADE')
	uidvalidity = IntegerField(null=False)

	class Meta:
		table_name = 'folders'
		indexes = (
				(("name", "account_id"), True),
			)


class Mail(BaseModel):
	uid = IntegerField(null=False)
	uidvalidity = IntegerField(null=False)
	box = ForeignKeyField(MailFolder, on_delete='CASCADE', on_update='CASCADE')
	encrypted = BooleanField()
	signed = BooleanField(null=True)
	from_ = CharField()
	to_ = CharField()
	subject = CharField(null=True)
	message = BlobField(null=True)
	date_time = DateTimeField(null=True)

	class Meta:
		table_name = "mails"


MODELS = (User, Contact, MailFolder, Mail)

def create_tables():
	db.create_tables(MODELS)