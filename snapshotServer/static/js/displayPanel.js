function displayDifference(pointList) {
	var canvas = document.getElementById("diff");
	var ctx = canvas.getContext("2d");
	ctx.fillStyle = "#FF0000";
	ctx.save();
	for(var i= 0; i < pointList.length; i++)
	{
		ctx.fillRect(pointList[i][0],pointList[i][1],1,1);
	}	
}

function getIntValue(strValue) {
	if (typeof strValue === 'number') {
		return strValue;
	}
	
	var number = strValue.match(/\d+/);
	return parseInt(number, 10);
}



function initDraw(canvas, excludeTable, excludeIndex) {
	
    function setMousePosition(e) {
        var ev = e || window.event; //Moz || IE
        if (ev.pageX) { //Moz
            mouse.x = ev.pageX;
            mouse.y = ev.pageY;
        } else if (ev.clientX) { //IE
            mouse.x = ev.clientX + document.body.scrollLeft;
            mouse.y = ev.clientY + document.body.scrollTop;
        }
    };
    
    function getCanvasRatio() {
        canvasWidth = document.getElementById("stepSnapshot").clientWidth;
        return getIntValue(canvas.getAttribute("width")) / getIntValue(canvasWidth);
    };

    function getCanvasCoords() {
    	return $('#canvas').offset();
    };
    
    function updateSizeAndCoords() {
    	canvasCoords = getCanvasCoords();
    	canvas.style.height = document.getElementById("stepSnapshot").clientHeight;
    	canvasRatio = getCanvasRatio();
    }

    var mouse = {
        x: 0,
        y: 0,
        startX: 0,
        startY: 0
    };
    
    var canvasCoords = null;
    var element = null;
    var canvasRatio = null;
    
    updateSizeAndCoords();
    
    $( window ).resize(function() {
    	updateSizeAndCoords();
    });
    
    canvas.onmousemove = function (e) {
    	
        setMousePosition(e);
        if (element !== null) {
            element.style.width = Math.abs(mouse.x - mouse.startX) + 'px';
            element.style.height = Math.abs(mouse.y - mouse.startY) + 'px';
            element.style.left = (mouse.x - mouse.startX < 0) ? mouse.x - canvasCoords.left  + 'px' : mouse.startX - canvasCoords.left + 'px';
            element.style.top = (mouse.y - mouse.startY < 0) ? mouse.y - canvasCoords.top + 'px' : mouse.startY - canvasCoords.top + 'px';

        }
    }

    canvas.onclick = function (e) {
    	
        if (element !== null) {
            
            canvas.style.cursor = "default";
            console.log("finsihed.");
            
            // change coordinates according to ratio between real image size and its size on screen
            var realLeft = Math.round(getIntValue(element.style.left) * canvasRatio);
            var realTop = Math.round(getIntValue(element.style.top) * canvasRatio);
            var realWidth = Math.round(getIntValue(element.style.width) * canvasRatio);
            var realHeight = Math.round(getIntValue(element.style.height) * canvasRatio);
            
            // change coordinates in pixels to coordinates in percentages, so that rectangles are resized when browser window is also resized
            element.style.width = getIntValue(element.style.width) * 100 / canvas.clientWidth + '%';
            element.style.height = getIntValue(element.style.height) * 100 / canvas.clientHeight + '%';
            element.style.left = getIntValue(element.style.left) * 100 / canvas.clientWidth + '%';
            element.style.top = getIntValue(element.style.top) * 100 / canvas.clientHeight + '%';

            // add line to exclude excludeTable
            row = document.createElement('tr');
            colActive = document.createElement('td');
            activeBox = document.createElement('input')
            activeBox.type = 'checkbox';
            activeBox.checked = 'checked';
            activeBox.setAttribute('name', 'new_exclude');
            activeBox.setAttribute('r_x', realLeft);
            activeBox.setAttribute('r_y', realTop);
            activeBox.setAttribute('r_w', realWidth);
            activeBox.setAttribute('r_h', realHeight);
            activeBox.setAttribute('onclick', "toggleElement('new_exclude_" + excludeIndex + "');");
            colActive.appendChild(activeBox);
            colPosition = document.createElement('td');
            colPosition.innerHTML = '(x, y, width, height)=(' + realLeft + ', ' + realTop + ', ' + realWidth + ', ' + realHeight + ')';
            row.appendChild(colActive);
            row.appendChild(colPosition);
            excludeTable.appendChild(row);
            
            element = null;
            
        } else {
        	        	
        	
            excludeIndex++;
            console.log("begun.");
            mouse.startX = mouse.x;
            mouse.startY = mouse.y;
            element = document.createElement('div');
            element.className = 'rectangle'
            element.id = 'new_exclude_' + excludeIndex;
            element.style.left = mouse.x + 'px';
            element.style.top = mouse.y + 'px';
            canvas.appendChild(element);
            canvas.style.cursor = "crosshair";
            
            
        }
    }
}

function drawExistingExcludeZones() {

	var canvas = document.getElementById('canvas');
	canvas.style.height = document.getElementById("stepSnapshot").clientHeight;
	var canvasRatio = getIntValue(canvas.clientWidth) / getIntValue(canvas.getAttribute("width"));
	var currentExcludes = document.getElementsByName('exclude');

	for(var i= 0; i < currentExcludes.length; i++) {
		if (currentExcludes[i].checked) {
			var idx = getIntValue(currentExcludes[i].id) 
			element = document.createElement('div');
		    element.className = 'rectangle'
		    element.id = 'exclude_' + idx;
		    
		    
		     element.style.left = Math.round(getIntValue(currentExcludes[i].getAttribute('r_x')) * canvasRatio) * 100 / canvas.clientWidth + '%';
		    element.style.top = Math.round(getIntValue(currentExcludes[i].getAttribute('r_y')) * canvasRatio) * 100 / canvas.clientHeight + '%';
		    element.style.width = Math.round(getIntValue(currentExcludes[i].getAttribute('r_w')) * canvasRatio) * 100 / canvas.clientWidth + '%';
		    element.style.height = Math.round(getIntValue(currentExcludes[i].getAttribute('r_h')) * canvasRatio) * 100 / canvas.clientHeight + '%';
		     
		    canvas.appendChild(element);
		}
	}
}

function updateExcludeZones(snapshotId, refSnapshotId, testCaseId, testStepId) {
	var diff = document.getElementById('diff');

	var newExcludes = document.getElementsByName('new_exclude');
	
	// add new exclude zones
	for(var i= 0; i < newExcludes.length; i++) {
		if (newExcludes[i].checked) {
			$.post({
				url: '/snapshot/api/exclude/',
				data: "x=" + newExcludes[i].getAttribute('r_x')
					+ "&y=" + newExcludes[i].getAttribute('r_y')
					+ "&width=" + newExcludes[i].getAttribute('r_w')
					+ "&height=" + newExcludes[i].getAttribute('r_h')
					+ "&snapshot=" + refSnapshotId
					
			});
		}
	}
	
	// remove exclude zones that should not be kept
	var currentExcludes = document.getElementsByName('exclude');
	console.log(currentExcludes);
	for(var i= 0; i < currentExcludes.length; i++) {
		if (!currentExcludes[i].checked) {
			$.ajax({
				type: 'DELETE',
				url: '/snapshot/api/exclude/' + getIntValue(currentExcludes[i].id) + '/',
				async: false	
			});
		}
	}
	
	// recompute difference
	$.ajax({
		type: 'POST',
		url: '/snapshot/compare/compute/' + snapshotId + '/',
		async: false	
	});
	
	// reload page
	updatePanel('/snapshot/compare/picture/' + testCaseId + '/' + testStepId, 'display');
	

}