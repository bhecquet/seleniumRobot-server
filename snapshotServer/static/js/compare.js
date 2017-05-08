function updatePanel(url, idToUpdate) {
	$.ajax({
	  url: url,
	  success: function(data) {
	  $('#' + idToUpdate).html(data);
	  }
	});
}
