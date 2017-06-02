
function updatePanel(url, idToUpdate, data="") {
	$.ajax({
		url: url,
		data: data,
		async: false,
		success: function(data) {
			$('#' + idToUpdate).html(data);
		}
	});
}

function clearTestList() {
	document.getElementById('testList').innerHTML = '';
	document.getElementById('stepList').innerHTML = '';
	document.getElementById('display').innerHTML = '';
}