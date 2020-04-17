var excludeIndex = 0;

function displayDifference(pointList, canvasSelector) {
	for (let canvas of document.querySelectorAll(canvasSelector)) {
		var ctx = canvas.getContext("2d");
		ctx.fillStyle = "#FF0000";
		ctx.save();
		for(var i= 0; i < pointList.length; i++)
		{
			ctx.fillRect(pointList[i][0],pointList[i][1],1,1);
		}	
	}
}

/**
 * Extract any int from the provided string
 * e.g: 'foo_4' => 4
 * @param strValue
 * @returns
 */
function getIntValue(strValue) {
	if (typeof strValue === 'number') {
		return strValue;
	}
	
	var number = strValue.match(/\d+/);
	return parseInt(number, 10);
}


/**
 * initialize drawing on canvas
 * @param excludeTable		Table to which we write the new exclusion zones	
 * @param testStepId		
 * @returns
 */
function initDraw(excludeTable, testStepId, stepSnapshotId, refSnapshotId) {
	
	var canvas = document.getElementById('canvas_' + testStepId + '_' + stepSnapshotId);
	var staticCanvas = document.getElementById('canvasStatic_' + testStepId + '_' + stepSnapshotId);
	
    function setMousePosition(e) {
		let scrollPosition = $('#editionModal_' + testStepId + '_' + stepSnapshotId).scrollTop();
        let ev = e || window.event; //Moz || IE
        /*if (ev.pageX) { //Moz
            mouse.x = ev.pageX;
            mouse.y = ev.pageY;
        } else if (ev.clientX) { //IE*/
            mouse.x = ev.clientX + document.body.scrollLeft;
            mouse.y = ev.clientY + scrollPosition;
        //}
    }
    
    function getCanvasRatio() {
        let canvasWidth = document.getElementById("stepSnapshot_" + testStepId + '_' + stepSnapshotId).clientWidth;
        return getIntValue(canvas.getAttribute("width")) / getIntValue(canvasWidth);
    }

    function getCanvasCoords() {
    	return $('#canvas_' + testStepId + '_' + stepSnapshotId).offset();
    }
    
    function updateSizeAndCoords() {
    	canvasCoords = getCanvasCoords();
    	canvas.style.height = document.getElementById("stepSnapshot_" + testStepId + '_' + stepSnapshotId).clientHeight;
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
//    	console.log("scroll: " + $(document).scrollTop())
        setMousePosition(e);
        if (element !== null) {
            element.style.width = Math.abs(mouse.x - mouse.startX) + 'px';
            element.style.height = Math.abs(mouse.y - mouse.startY) + 'px';
            element.style.left = (mouse.x - mouse.startX < 0) ? mouse.x - canvasCoords.left  + 'px' : mouse.startX - canvasCoords.left + 'px';
            element.style.top = (mouse.y - mouse.startY < 0) ? mouse.y - canvasCoords.top + $(document).scrollTop() + 'px' : mouse.startY - canvasCoords.top + $(document).scrollTop() + 'px';

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
            let row = document.createElement('tr')
            let colActive = document.createElement('td')
            let activeBox = document.createElement('input')
            let inputId = 'new_exclude_input_' + excludeIndex
            activeBox.type = 'checkbox';
            activeBox.checked = 'checked';
            activeBox.setAttribute('name', 'new_exclude_' + testStepId + '_' + stepSnapshotId);
            activeBox.setAttribute('id', inputId);
            activeBox.setAttribute('r_x', realLeft);
            activeBox.setAttribute('r_y', realTop);
            activeBox.setAttribute('r_w', realWidth);
            activeBox.setAttribute('r_h', realHeight);
            activeBox.setAttribute('target_snapshot', refSnapshotId);
			
			// clic will enable/disable the static element (on summary) and its equivalent on edition modal
            activeBox.setAttribute('onclick', "toggleElement('new_exclude_" + excludeIndex + "');toggleElement('new_exclude_" + excludeIndex + "Static');");
            colActive.appendChild(activeBox);
            
            // column for color
            let colColor = document.createElement('td');
            colColor.setAttribute('style', "background-color: darkred");
            
            // colum for position / dimension of the zone
            let colPosition = document.createElement('td');
            colPosition.innerHTML = '(x, y, width, height)=(' + realLeft + ', ' + realTop + ', ' + realWidth + ', ' + realHeight + ')';
            
            // column for snapshot to which this exclude zone will apply
            let colApplyTo = document.createElement('td');
            let selectBox = document.createElement('select');
            selectBox.setAttribute("onchange", "changeExcludeZoneTarget('" + inputId + "', this.value);")
            let applyToReference = document.createElement('option');
            applyToReference.setAttribute('value', refSnapshotId);
            applyToReference.setAttribute('selected', 'true');
            applyToReference.innerHTML = 'reference';
            
            let applyToStep = document.createElement('option');
            applyToStep.setAttribute('value', stepSnapshotId);
            applyToStep.innerHTML = 'this snapshot only';
            
            selectBox.appendChild(applyToReference)
            selectBox.appendChild(applyToStep)
            colApplyTo.appendChild(selectBox)
            
            row.appendChild(colActive);
            row.appendChild(colColor);
            row.appendChild(colPosition);
            row.appendChild(colApplyTo);
            excludeTable.appendChild(row);
            
			// copy the created rectangle so that it is displayed in summary
			var elementCopy = element.cloneNode(true);
			elementCopy.id = element.id + "Static";
			
			staticCanvas.appendChild(elementCopy);
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

/**
 * Change the "snapshot" attribute of the input element representing the exclude zone
 * @param inputElementId	the <input> element
 * @param value			id of the target snapshot (reference or step snapshot)
 * @returns
 */
function changeExcludeZoneTarget(inputElementId, value) {
	console.log(value)
	document.getElementById(inputElementId).setAttribute("target_snapshot", value)
}

/**
 * draw rectangles on canvas, based on the content of the table containing "exclude" elements
 * @param canvas			the canvas element where to draw rectangles
 * @param snapshotHeight	height of the snapshot on which rectangles will be drawn. It helps calculating canvas ratio
 * @param idSuffix			a suffix to add to 'id' of each rectangle to differentiate rectangles from editable zone and rectangles from summary
 * @param testStepId		
 * @returns
 */
function drawExistingExcludeZones(canvas, snapshotHeight, idSuffix, testStepId, snapshotId) {
	
	// do not draw if canvas / snapshot is not visible
	if (snapshotHeight == 0) {
		return
	}
	
	canvas.style.height = snapshotHeight;
	var canvasRatio = getIntValue(canvas.clientWidth) / getIntValue(canvas.getAttribute("width"));
	var currentExcludes = document.querySelectorAll('#excludeZoneTable_' + testStepId + '_' + snapshotId + ' input');
	//console.log("canvas: " + canvas.clientWidth + '-' + canvas.clientHeight + '-' + snapshotHeight);
	
	
	for(var i= 0; i < currentExcludes.length; i++) {
		if (currentExcludes[i].checked) {

			var idx = getIntValue(currentExcludes[i].id) 
			
			element = document.createElement('div');
		    element.className = 'rectangle'
		    element.id = 'exclude_' + idx + idSuffix;
		    
		    
		    element.style.left = Math.round(getIntValue(currentExcludes[i].getAttribute('r_x')) * canvasRatio) * 100 / canvas.clientWidth + '%';
		    element.style.top = Math.round(getIntValue(currentExcludes[i].getAttribute('r_y')) * canvasRatio) * 100 / snapshotHeight + '%';
		    element.style.width = Math.round(getIntValue(currentExcludes[i].getAttribute('r_w')) * canvasRatio) * 100 / canvas.clientWidth + '%';
		    element.style.height = Math.round(getIntValue(currentExcludes[i].getAttribute('r_h')) * canvasRatio) * 100 / snapshotHeight + '%';
		    element.style.borderColor = currentExcludes[i].getAttribute('color')
		     
		    canvas.appendChild(element);
		}
	}
}

/**
 * Store in database the list of exclusion zones. Look for newly created zones (name=new_exclude_<stepId>) and for current
 * @param snapshotId
 * @param refSnapshotId
 * @param testCaseId
 * @param testStepId
 * @returns
 */
function updateExcludeZones(snapshotId, refSnapshotId, testCaseId, testStepId) {
	var newExcludes = document.getElementsByName('new_exclude_' + testStepId + '_' + snapshotId);
	
	// add new exclude zones
	// these ajax calls are not asynchronous as they MUST finish before we call computing 
	for(let i= 0; i < newExcludes.length; i++) {
		if (newExcludes[i].checked) {
			$.ajax({
				type: 'POST',
				async: false,
				url: '/snapshot/api/exclude/',
				data: "x=" + newExcludes[i].getAttribute('r_x')
					+ "&y=" + newExcludes[i].getAttribute('r_y')
					+ "&width=" + newExcludes[i].getAttribute('r_w')
					+ "&height=" + newExcludes[i].getAttribute('r_h')
					+ "&snapshot=" + newExcludes[i].getAttribute('target_snapshot')
					
			});
		}
	}
	
	var currentExcludes = document.querySelectorAll('#excludeZoneTable_' + testStepId + '_' + snapshotId + ' input');

	for(let i= 0; i < currentExcludes.length; i++) {
		
		// remove exclude zones that should not be kept
		if (!currentExcludes[i].checked) {

			// these ajax calls are not asynchronous as they MUST finish before we call computing 
			$.ajax({
				type: 'DELETE',
				url: '/snapshot/api/exclude/' + getIntValue(currentExcludes[i].id) + '/',
				async: false	
			});
		}
		
		// change target snapshot
		$.ajax({
			type: 'PATCH',
			async: false,
			url: '/snapshot/api/exclude/' + getIntValue(currentExcludes[i].id) + '/',
			data: "snapshot=" + currentExcludes[i].getAttribute('target_snapshot')
				
		});
	}
	
	// recompute difference
	$.ajax({
		type: 'POST',
		url: '/snapshot/compare/compute/' + snapshotId + '/',
		async: false	
	});

	// reload step
	updatePanel('/snapshot/compare/picture/' + testCaseId + '/' + testStepId, 'step_' + testStepId);


}