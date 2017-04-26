import arrow
import csv

__verbose__ = False

def dbg(*args):
	if __verbose__:
		for arg in args:
			print arg

def amex_date(d_str):
	return d_str[:10]

def parse_date(d_str,d_format):
	date = None
	try:
		date = arrow.get(d_str,d_format)
	except:
		dbg("could not parse date, maybe this is amex?")
		try:
			date = arrow.get(d_str[:10],d_format)
			dbg("amex parse successful")
			dbg(date)
		except:
			dbg("amex date didn't work, fuck this")
			date = None
	return date

class Transaction(object):
	def __init__(self, amount, date, date_format, name):
			dbg(amount)
			try:
				self.amount = float(amount)
			except Exception as e:
				dbg("could not parse transaction amount")
				# print amount, date, name
				self.amount = None
				# raise e
			self.date = parse_date(date, date_format)
			self.name = name
			self.tags = []
	
	def __repr__(self):
		return "%s, %s, %s:%s" % (self.date, self.amount, self.name, self.tags)

	def add_tags(self, *args):
		for arg in args:
			self.tags.append(arg)

class TransactionList(object):
	"""
	contains a list of transactions and special helper functions like counting, summing and sorting
	"""
	def __init__(self,*args):
		self.transactions = []
		if args is not None and len(args) > 0:
			if type(args[0]) == "<type 'list'>":
				for t in args[0]:
					self.transactions.append(t)
			else:
				for t in args:
					self.transactions.append(t)

	def __repr__(self):
		return sorted(self.transactions, key=lambda x: x.date).__repr__()

	def append(self, t):
		self.transactions.append(t)

	def sum(self):
		return sum([t.amount for t in self.transactions])

	@property
	def count(self):
		return len(self.transactions)

	@staticmethod
	def join(*args):
		"""
		joins together several transaction lists and returns a new list
		"""
		joined_transactions = TransactionList()
		print args
		for tlist in args:
			for t in tlist.transactions:
				joined_transactions.append(t)
		return joined_transactions

	def deltas(self):
		ins = []
		total_ins = 0
		outs = []
		total_outs = 0
		for t in self.transactions:
			if t.amount > 0:
				ins.append(t)
				total_ins += t.amount
			else:
				outs.append(t)
				total_outs += t.amount
		return "%s ins, %s outs, %s total in and %s total out, %s balance" % (len(ins), len(outs), total_ins, total_outs, total_ins + total_outs)		

	def transactions_by_date(self,begin_str,end_str):
		begin = arrow.get(begin_str,"MM/DD/YYYY")
		end = arrow.get(end_str,"MM/DD/YYYY")
		transactions = TransactionList()
		for t in self.transactions:
			if t.date >= begin and t.date <= end:
				transactions.append(t)
		return transactions

	def transactions_by_month(self,year,month):
		transactions = TransactionList()
		for t in self.transactions:
			if t.date.month == month and t.date.year == year:
				transactions.append(t)
		return transactions

class Source(object):
	"""
	a collection of Transactions from a single source (e.g., bank, credit card)
	"""
	def __init__(self, name, fund_type):
		self.name = name
		self.fund_type = fund_type
		self.transactions = TransactionList()
		self.balance = None

	def __repr__(self):
		return "Source named %s with %s transactions" % (self.name, self.transactions.count)
	
	def parse_file(self, filename, date_format, date_index, amount_index, name_index):
		self.date_format = date_format
		self.missing_transactions = False
		with open(filename, "rb") as f:
			filereader = csv.reader(f, delimiter=',', quotechar='"')
			for row in filereader:
				t = Transaction(row[amount_index], row[date_index], self.date_format, row[name_index])
				if t.date is None or t.amount is None:
					self.missing_transactions = True
				t.add_tags(self.name) # add the source name as a tag
				t.add_tags(self.fund_type)
				self.transactions.append(t)
		if self.missing_transactions:
			dbg("could not parse some transactions")

	def deltas(self):
		self.transactions.deltas()

	def transactions_by_date(self,begin,end):
		return self.transactions.transactions_by_date(begin,end)

	def transactions_by_month(self,year,month):
		return self.transactions.transactions_by_month(year,month)

class Finances(object):
	"""
	A collection of Sources that affect the overall financial picture
	"""
	def __init__(self,*sources):
		# print sources
		self.sources = []
		self.debits = []
		self.credits = []
		# self.last_updated = last_updated
		for source in sources:
			print source
			self.add_source(source)

	def add_source(self,source):
		self.sources.append(source)
		if source.fund_type == "debit":
			self.debits.append(source)
		if source.fund_type == "credit":
			self.credits.append(source)

	def show_me_the_monthy(self, year, month):
		"""
		illustrates the financial deltas over a given month
		cash are positive debit transactions and negative credit transactions
		debts are negative debit transactions and positive credit transactions
		"""
		cash = TransactionList()
		debts = TransactionList()
		for debit_source in self.debits:
			for t in debit_source.transactions_by_month(year,month).transactions:
				if t.amount > 0:
					cash.append(t)
				else:
					debts.append(t)
		for credit_source in self.credits:
			for t in credit_source.transactions_by_month(year,month).transactions:
				if t.amount > 0:
					debts.append(t)
				else:
					cash.append(t)
		total_cash = cash.sum()
		total_debts = debts.sum()
		print "In %s/%s, spent %s, made %s for a total change of %s" % (month, year, total_debts, total_cash, total_cash+total_debts)

	def summary_by_date(self,begin,end):
		cash = TransactionList()
		debts = TransactionList()
		for debit_source in self.debits:
			for t in debit_source.transactions_by_date(begin,end).transactions:
				if t.amount > 0:
					cash.append(t)
				else:
					debts.append(t)
		for credit_source in self.credits:
			for t in credit_source.transactions_by_date(begin,end).transactions:
				if t.amount > 0:
					debts.append(t)
				else:
					cash.append(t)
		total_cash = cash.sum()
		total_debts = debts.sum()
		print "Between %s and %s, spent %s, made %s for a total change of %s" % (begin, end, total_debts, total_cash, total_cash+total_debts)



# a = Transaction(56, "5/6/1992", "hello world")
# a.add_tags("venmo")
# a.add_tags("dining")
# print a

bofa = Source("bofa","debit")
bofa.parse_file("bofa_since_11.16.csv", date_format="MM/DD/YYYY", date_index=0, amount_index=2, name_index=1)
chase = Source("chase","credit")
chase.parse_file("chase_since_11.16.CSV", date_format="MM/DD/YYYY", date_index=1,amount_index=4,name_index=3)
amex = Source("amex","credit")
amex.parse_file("amex_data_since_11.16.csv",date_format="MM/DD/YYYY",date_index=0,amount_index=7,name_index=2)
f = Finances(bofa,amex,chase)
f.show_me_the_monthy(2017,1)
f.show_me_the_monthy(2017,2)
f.show_me_the_monthy(2017,3)
f.summary_by_date("01/15/2017","02/15/2017")
f.summary_by_date("02/15/2017","03/15/2017")
f.summary_by_date("03/15/2017","04/15/2017")




