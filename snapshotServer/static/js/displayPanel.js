function displayDifference(pointList) {
	console.log("toti");
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

function toggleElement(elementId) {
    $("#" + elementId).toggle();
}

function initDraw(canvas, excludeTable, excludeIndex) {
	console.log("toti2");
    function setMousePosition(e) {
        var ev = e || window.event; //Moz || IE
        if (ev.pageX) { //Moz
            mouse.x = ev.pageX + window.pageXOffset;
            mouse.y = ev.pageY + window.pageYOffset;
        } else if (ev.clientX) { //IE
            mouse.x = ev.clientX + document.body.scrollLeft;
            mouse.y = ev.clientY + document.body.scrollTop;
        }
    };

    var mouse = {
        x: 0,
        y: 0,
        startX: 0,
        startY: 0
    };
    
    var canvasCoords = canvas.getBoundingClientRect();
    var element = null;
    
    canvas.style.height = document.getElementById("stepSnapshot").clientHeight;
    canvas.style.width = document.getElementById("stepSnapshot").clientWidth;

    canvas.onmousemove = function (e) {
        setMousePosition(e);
        if (element !== null) {
            element.style.width = Math.abs(mouse.x - mouse.startX) + 'px';
            element.style.height = Math.abs(mouse.y - mouse.startY) + 'px';
            element.style.left = (mouse.x - mouse.startX < 0) ? mouse.x - canvasCoords.x  + 'px' : mouse.startX - canvasCoords.x + 'px';
            element.style.top = (mouse.y - mouse.startY < 0) ? mouse.y - canvasCoords.y + 'px' : mouse.startY - canvasCoords.y + 'px';

        }
    }

    canvas.onclick = function (e) {
        if (element !== null) {
            
            canvas.style.cursor = "default";
            console.log("finsihed.");
            
            // add line to exclude excludeTable
            row = document.createElement('tr');
            colActive = document.createElement('td');
            activeBox = document.createElement('input')
            activeBox.type = 'checkbox';
            activeBox.checked = 'checked';
            activeBox.setAttribute('name', 'new_exclude');
            activeBox.setAttribute('r_x', element.style.left.substring(0, element.style.left.length - 2));
            activeBox.setAttribute('r_y', element.style.top.substring(0, element.style.top.length - 2));
            activeBox.setAttribute('r_w', element.style.width.substring(0, element.style.width.length - 2));
            activeBox.setAttribute('r_h', element.style.height.substring(0, element.style.height.length - 2));
            activeBox.setAttribute('onclick', "toggleElement('exclude_" + excludeIndex + "');");
            colActive.appendChild(activeBox);
            colPosition = document.createElement('td');
            colPosition.innerHTML = '(x,y)=(' + element.style.left + ',' + element.style.top + '), (width,height)=(' + element.style.width + ',' + element.style.height + ')';
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
            element.id = 'exclude_' + excludeIndex;
            element.style.left = mouse.x + 'px';
            element.style.top = mouse.y + 'px';
            canvas.appendChild(element)
            canvas.style.cursor = "crosshair";
            
            
        }
    }
}

function updateExcludeZones(refSnapshotId) {
	var canvas = document.getElementById('canvas');
	
	// TODO: parcourir les enfants et supprimer tous les éléments
	// parcourir ensuite les lignes du tableau d'exclusion et redessiner les zones
	// pour cela, le tableau devra contenir des balises avec attributs spécifiques, à moins que cela ne soit
	// appelé par le template qui passera en paramètre la liste des zones
	
	var newExcludes = document.getElementsByName('new_exclude');
	
	// add new exclude zones
	for(var i= 0; i < newExcludes.length; i++) {
		if (newExcludes[i].checked) {
			$.post({
				url: '/api/exclude/',
				data: "x=" + newExcludes[i].getAttribute('r_x')
					+ "&y=" + newExcludes[i].getAttribute('r_y')
					+ "&width=" + newExcludes[i].getAttribute('r_w')
					+ "&height=" + newExcludes[i].getAttribute('r_y')
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
				url: '/api/exclude/' + currentExcludes[i].id.substring(16, currentExcludes[i].id.lenght) + '/',
					
			});
		}
	}
}