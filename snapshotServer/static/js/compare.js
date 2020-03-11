
$(document).ready(function () {
	
	var exclusionDrawnOnModal = false;
    
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
