
function updatePanel(url, idToUpdate, data="") {
	$.ajax({
		url: url,
		data: data,
		success: function(data) {
			$('#' + idToUpdate).html(data);
		}
	});
}