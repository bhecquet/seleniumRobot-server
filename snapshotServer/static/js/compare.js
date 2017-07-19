
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

function toggleElement(elementId) {
    $("#" + elementId).toggle();
}

function displaySelected(url) {
	data = 'browsers='
	var selectedOptions = $('#browsers').find('.checked').find('input');
	for (var i=0, len=selectedOptions.length; i<len; i++) {
        data += selectedOptions[0].value + ",";
    }
	
	$.ajax({
		url: url,
		data: data,
		async: false,
		success: function(data) {
			$('#' + idToUpdate).html(data);
		}
	});
}

$(document).ready(function () {
    $("#browsers").ultraselect({autoListSelected: true, maxWidth: "90px"});
    $("#environments").ultraselect({autoListSelected: true, maxWidth: "90px"});
    $("#testCases").ultraselect({autoListSelected: true, maxWidth: "90px"});
    
    $('#sessionFrom').datepicker({
    	format: 'dd-mm-yyyy',
        todayBtn: 'linked',
        endDate: 'today',
        autoclose: true
        
    })
    $('#sessionTo').datepicker({
    	format: 'dd-mm-yyyy',
    	todayBtn: 'linked',
    	endDate: 'today',
    	autoclose: true
    	
    })
    
});
