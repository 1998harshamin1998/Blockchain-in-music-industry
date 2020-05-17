list=[{u'name': u'tushar', u'bday': u'18031998', u'gender': u'Male', u'age': 22, u'phone': u'8888888888', u'company_name': u'ss', u'api_key': u'tushar88888ss88888tushar@gmailcom', u'email': u'tushar@gmail.com'}]

for i in list:
	if '8888888888' in i.values():
		print('true') 
	else:
		print('false')

<script>
    var container1 = document.getElementById("pending_contracts");
    var contract_names= {{ contract_names | tojson }};
    var alb_names= {{ album_names | tojson }};
    var revenue= {{ rev_per_view | tojson }};
    var timestamp= {{ timestamps | tojson }};
    for(i=0; i<contract_names.length; i++){
      container1.insertAdjacentHTML('beforeend', '<tr><td>'+contract_names[i]+'</td><td>'+alb_names[i]+'</td><td>'+revenue[i]+'</td><td>'+timestamps[i]+'</td></tr>');
    }

  </script>


