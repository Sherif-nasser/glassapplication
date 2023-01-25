import json

import frappe
from frappe import _, msgprint
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.item.item import get_item_defaults
from frappe.utils import cint, cstr, flt
from frappe.utils import cint, cstr, flt, get_link_to_form, getdate, new_line_sep, nowdate



@frappe.whitelist()
def make_subcontracting_order(source_name, target_doc=None):

	return get_mapped_subcontracting_order(source_name, target_doc)


def get_mapped_subcontracting_order(source_name, target_doc=None):
	
	if target_doc and isinstance(target_doc, str):
		target_doc = json.loads(target_doc)
		for key in ["service_items", "items", "supplied_items"]:
			if key in target_doc:
				del target_doc[key]
		target_doc = json.dumps(target_doc)

	target_doc = get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			"Purchase Order": {
				"doctype": "Subcontracting Order",
				"field_map": {},
				"field_no_map": ["total_qty", "total", "net_total"],
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Purchase Order Item": {
				"doctype": "Subcontracting Order Service Item",
				"field_map": {},
				"field_no_map": [],
			},
		},
		target_doc,
	)

	target_doc.populate_items_table()

	if target_doc.set_warehouse:
		for item in target_doc.items:
			item.warehouse = target_doc.set_warehouse
	else:
		source_doc = frappe.get_doc("Purchase Order", source_name)
		if source_doc.set_warehouse:
			for item in target_doc.items:
				item.warehouse = source_doc.set_warehouse
		else:
			for idx, item in enumerate(target_doc.items):
				item.warehouse = source_doc.items[idx].warehouse
	
	
	target_doc.price_list_currency = source_doc.price_list_currency
	target_doc.price_list_exchange_rate = source_doc.plc_conversion_rate
	source_doc = frappe.get_doc("Purchase Order", source_name)
	for item in target_doc.items:
		for itemname in source_doc.items:
			item.company_currency = itemname.rate
			item.rate = itemname.base_rate


	return target_doc


def set_missing_values(source, target_doc):
	if target_doc.doctype == "Purchase Order" and getdate(target_doc.schedule_date) < getdate(
		nowdate()
	):
		target_doc.schedule_date = None
	target_doc.run_method("set_missing_values")
	target_doc.run_method("calculate_taxes_and_totals")


def update_item(obj, target, source_parent):
	target.conversion_factor = obj.conversion_factor
	target.qty = flt(flt(obj.stock_qty) - flt(obj.ordered_qty)) / target.conversion_factor
	target.stock_qty = target.qty * target.conversion_factor
	if getdate(target.schedule_date) < getdate(nowdate()):
		target.schedule_date = None

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None, args=None):
	print("SHERIIIIIIIIIF")
	if args is None:
		args = {}
	if isinstance(args, str):
		args = json.loads(args)

	def postprocess(source, target_doc):
		if frappe.flags.args and frappe.flags.args.default_supplier:
			# items only for given default supplier
			supplier_items = []
			for d in target_doc.items:
				default_supplier = get_item_defaults(d.item_code, target_doc.company).get("default_supplier")
				if frappe.flags.args.default_supplier == default_supplier:
					supplier_items.append(d)
			target_doc.items = supplier_items

		set_missing_values(source, target_doc)

	def select_item(d):
		filtered_items = args.get("filtered_children", [])
		child_filter = d.name in filtered_items if filtered_items else True

		return d.ordered_qty < d.stock_qty and child_filter

	doclist = get_mapped_doc(
		"Material Request",
		source_name,
		{
			"Material Request": {
				"doctype": "Purchase Order",
				"validation": {"docstatus": ["=", 1], "material_request_type": ["=", "Purchase"]},
			},
			"Material Request Item": {
				"doctype": "Purchase Order Item",
				"field_map": [
					["name", "material_request_item"],
					["parent", "material_request"],
					["uom", "stock_uom"],
					["uom", "uom"],
					["sales_order", "sales_order"],
					["sales_order_item", "sales_order_item"],
				],
				"postprocess": update_item,
				"condition": select_item,
			},
		},
		target_doc,
		postprocess,
	)

	# print(f"ZOOOOOOOOOOOOOOOOOOOOOOOOOOO")
	# print(f"doclist  {doclist}")
	source_doc = frappe.get_doc("Material Request", source_name)
	# print(f"doclist  {source_doc.items}")
	for item in doclist.items:
		for itemname in source_doc.items:
			item.fg_item = itemname.finished_good_item  
			# item.rate = itemname.base_rate

	return doclist