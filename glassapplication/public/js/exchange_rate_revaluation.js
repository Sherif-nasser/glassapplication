frappe.ui.form.on('Exchange Rate Revaluation', {
    
})


frappe.ui.form.on('Exchange Rate Revaluation Account', {
    account:function(frm,cdt,cdn){
        var d = locals[cdt][cdn];
     
        frappe.call({
			method: "glassapplication.exchangeRate.get_accounts_data",
			
            args:{
                posting_date :frm.doc.posting_date,
                company: frm.doc.company,
                parentAccount: d.account
            } ,
			callback: function(r){
                console.log(r.message);
                if(r.message){
                    var accountDetails = r.message;
                    // console.log(accountDetails[0][4])
                    // console.log(accountDetails[0][5])
                    d.balance_in_account_currency = accountDetails[0][4];
                    d.balance_in_base_currency = accountDetails[0][5];
                    refresh_field("accounts");
                }
				
			}
		});
    }
});