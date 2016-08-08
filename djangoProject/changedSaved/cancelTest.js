function cancelTest(id){
	var userToken = prompt('Enter Token:');
	//check if user entered a token
	if (userToken.length != 0 && userToken.length <=8){
		//get requets to database, checks if it exists and if so changes the database
		var url = 'http://smtdb-test.cal.ci.spirentcom.com/tracker/getTest&var='+userToken+"&id="+id;
		console.log("getting: "+url);
		$.get(url, function(data){
		//parse the results
		var myresults = $(data).filter('td').toArray();
		if (myresults.length > 1){
		alert('Error: Database has more than 1 entry with the token');
		}
		else if (myresults.length == 0){
		alert('Error: Invalid Token');
		}
		else{
		//succesfully updated the database, refresh the page
		window.location.href = 'http://smtdb-test.cal.ci.spirentcom.com/tracker/piv_queue_hw'
		}
	}).fail(function(){
	alert("Error: Get Request to Database Failed");});
	}
	else{
		alert("Error: Invalid Token");
	}
}
