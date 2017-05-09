function updatePanel(url, idToUpdate) {
	$.ajax({
	  url: url,
	  success: function(data) {
	  $('#' + idToUpdate).html(data);
	  }
	});
}

function displayDifference(pointList) {
	var canvas = document.getElementById("diff");
	canvas.style.height = document.getElementById("stepSnapshot").clientHeight;
	canvas.style.width = document.getElementById("stepSnapshot").clientWidth;
	var ctx = canvas.getContext("2d");
	ctx.fillStyle = "#FF0000";
	for(var i= 0; i < pointList.length; i++)
	{
		ctx.fillRect(pointList[i][0],pointList[i][1],1,1);
	}	
}
