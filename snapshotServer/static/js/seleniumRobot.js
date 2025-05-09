$(function () {

			var data = [
	   		{
			    value: $('.testSuccess').length,
			    color: "#2BC400",
			    label: "Success"
			}, {
			    value: $('.testFailed').length,
			    color: "#FF6666",
			    label: "Failed"
			}, {
			    value: $('.testSkipped').length,
			    color: "#00CCFF",
			    label: "Skipped"
			}];

			var options = {
	    		segmentShowStroke: true,
			    animateRotate: true,
			    animateScale: false,
			    percentageInnerCutout: 0,
			    segmentStrokeColor: "#fff",
			    segmentStrokeWidth: 2,
			    animationSteps: 100,
			    animationEasing: "easeOutBounce",
			    tooltipTemplate: "<%if (label){%><%=label %>: <%}%><%= value %>",
			    onAnimationComplete: function()
        			{this.showTooltip(this.segments, true);},
        		tooltipEvents: [],
			    showTooltips: true,
			}

			var ctx = document.getElementById("pieChart").getContext("2d");
			var myChart = new Chart(ctx).Doughnut(data, options);
			//document.getElementById('pieChartLegend').innerHTML = myChart.generateLegend();

		});
		
console.log("activate popover")		

$(function () {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl)
    })

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl)
    })

})

		
