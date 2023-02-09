from curses import wrapper
import erpnext
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.meta import get_field_precision
from frappe.utils import flt
from erpnext.setup.utils import get_exchange_rate


@frappe.whitelist()
def test():
	frappe.msgprint("test")

@frappe.whitelist()
def get_accounts_data(parentAccount,posting_date,company,account=None):
	    
	
	# validate_mandatory(company,posting_date)
	company_currency = erpnext.get_company_currency(company)
	precision = get_field_precision(
		frappe.get_meta("Exchange Rate Revaluation Account").get_field("new_balance_in_base_currency"),
		company_currency,
	)
	

	if parentAccount:
		account_details = get_accounts_from_gle(parentAccount,company,posting_date)
	
	

	# for d in account_details:
	#     current_exchange_rate = (
	#         d.balance / d.balance_in_account_currency if d.balance_in_account_currency else 0
	#     )
	#     new_exchange_rate = get_exchange_rate(d.account_currency, company_currency, posting_date)
	#     new_balance_in_base_currency = flt(d.balance_in_account_currency * new_exchange_rate)
	#     gain_loss = flt(new_balance_in_base_currency, precision) - flt(d.balance, precision)
	#     if gain_loss:
	#         accounts.append(
	#             {
	#                 "account": d.account,
	#                 "party_type": d.party_type,
	#                 "party": d.party,
	#                 "account_currency": d.account_currency,
	#                 "balance_in_base_currency": d.balance,
	#                 "balance_in_account_currency": d.balance_in_account_currency,
	#                 "current_exchange_rate": current_exchange_rate,
	#                 "new_exchange_rate": new_exchange_rate,
	#                 "new_balance_in_base_currency": new_balance_in_base_currency,
	#             }
	#         )

	# if not accounts:
	#     throw_invalid_response_message(account_details)

	return account_details


def validate_mandatory(company,posting_date):
		if not (company and posting_date):
			frappe.throw(_("Please select Company and Posting Date to getting entries"))
                        


def get_accounts_from_gle(parentAccount,company,posting_date):
		company_currency = erpnext.get_company_currency(company)
		# print(company_currency)
		
		# print(company)
		# account = frappe.db.sql_list(
		# 	"""
		# 	select name
		# 	from tabAccount
		# 	where is_group = 0
		# 		and report_type = 'Balance Sheet'
		# 		and parent_account =%s
		# 		and root_type in ('Asset', 'Liability', 'Equity')
		# 		and account_type != 'Stock'
		# 		and company=%s
		# 		and account_currency != %s
		# 	order by name""",
		# 	(parentAccount,company, company_currency),
		# )
		# print(account)
		##['dd - DS', 'العملاء االاجانب - DS', 'خزنة يورو - DS', 'صندوق دولار - DS', 'عملاء اجانب - DS']
		# print("after account")
		account_details = []
		if parentAccount:
			print("within account")
			account_details = frappe.db.sql(
				"""
				select
					account, party_type, party, account_currency,
					sum(debit_in_account_currency) - sum(credit_in_account_currency) as balance_in_account_currency,
					sum(debit) - sum(credit) as balance
				from `tabGL Entry`
				where account = %s
				and posting_date <= %s
				and is_cancelled = 0

			""",
				 (parentAccount, posting_date),
				
			)
		print("Before Account Details")
		

		return account_details



def throw_invalid_response_message(account_details):
		if account_details:
			message = _("No outstanding invoices require exchange rate revaluation")
		else:
			message = _("No outstanding invoices found")
		frappe.msgprint(message)