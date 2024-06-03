var excludeIndex = 0;
var lastInteractEvent = 0
var currentExcludeZones = []

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
 * Canvas is a bit larger and higher (102%) than the picture
 * @param excludeTable      Table to which we write the new exclusion zones 
 * @param testStepId        
 * @returns
 */
function initDraw(excludeTable, testStepId, stepSnapshotId, refSnapshotId) {
    
    var canvas = document.getElementById('canvas_' + testStepId + '_' + stepSnapshotId);
    var staticCanvas = document.getElementById('canvasStatic_' + testStepId + '_' + stepSnapshotId);
    var picture = document.getElementById("stepSnapshot_" + testStepId + '_' + stepSnapshotId)
    
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
    
    /**
    Get ratio between drawing zone (the canvas) and the picture at full size
    */
    function getCanvasRatio() {
        let canvasWidth = picture.clientWidth;
        return getIntValue(canvas.getAttribute("width")) / getIntValue(canvasWidth);
    }

    function updateSizeAndCoords() {
        canvasCoords = canvas.getBoundingClientRect();
        canvasRatio = getCanvasRatio();
        pictureRectangle = picture.getBoundingClientRect();
    }
    
    /**
    Return the X value of the mouse, in the limit of the picture
    */
    function computeMouseXPosition() {
        if (mouse.x < pictureRectangle.x) {
            return pictureRectangle.x
        } else if (mouse.x > pictureRectangle.x + pictureRectangle.width) {
            return pictureRectangle.x + pictureRectangle.width
        } else {
            return mouse.x;
        }
    }
    
    /**
    Return the Y value of the mouse, in the limit of the picture
    */
    function computeMouseYPosition() {
        if (mouse.y < pictureRectangle.y) {
            return pictureRectangle.y
        } else if (mouse.y > pictureRectangle.y + pictureRectangle.height) {
            return pictureRectangle.y + pictureRectangle.height
        } else {
            return mouse.y;
        }
    }

    var mouse = {
        x: 0,
        y: 0,
        startX: 0,
        startY: 0
    };
    
    var canvasCoords = null;
    var newExcludeZone = null;
    var canvasRatio = null;
    var pictureRectangle = null;

    updateSizeAndCoords();
    
    $( window ).resize(function() {
        updateSizeAndCoords();
    });
    
    canvas.onmousemove = function (e) {

        setMousePosition(e);
        if (newExcludeZone !== null) {
            
            // compute the offset of the picture inside the canvas element so that rectangles are correctly placed in canvas object
            let canvasOffsetX = pictureRectangle.left - canvasCoords.left
            let canvasOffsetY = pictureRectangle.top - canvasCoords.top
            
            let mouseX = computeMouseXPosition();
            let mouseY = computeMouseYPosition();

            newExcludeZone.style.width = Math.abs(mouseX - mouse.startX) + 'px';
            newExcludeZone.style.height = Math.abs(mouseY - mouse.startY) + 'px';
            newExcludeZone.style.left = (mouseX - mouse.startX < 0) ? mouseX - pictureRectangle.left + canvasOffsetX  + 'px' : Math.min(pictureRectangle.width, mouse.startX - pictureRectangle.left) + canvasOffsetX + 'px';
            newExcludeZone.style.top = (mouseY - mouse.startY < 0) ? mouseY - pictureRectangle.top + canvasOffsetY + 'px' : Math.min(pictureRectangle.height, mouse.startY - pictureRectangle.top) + canvasOffsetY + 'px';

        }
    }
    

    canvas.onclick = function (e) {
        
        // don't do anything if last interaction has just ended to avoid creating a new exclude zone while dragging or resizing
        if ((Date.now() - lastInteractEvent) < 1000) {
            return;
        }
        
        // update coordinates / sizes before doing any actions as adding a rectangle may display browser scrollbar which changes positions
        updateSizeAndCoords();
        
        if (newExcludeZone !== null) {
            
            canvas.style.cursor = "default";
            console.log("finsihed.");
            
            // newExcludeZone is positionned relative to canvas, but we need coordinates relative to picture
            let canvasOffsetX = pictureRectangle.left - canvasCoords.left
            let canvasOffsetY = pictureRectangle.top - canvasCoords.top
            
            // change coordinates according to ratio between real image size and its size on screen
            let realLeft = Math.max(0, parseFloat(newExcludeZone.style.left) - canvasOffsetX) * canvasRatio;
            let realTop = Math.max(0, parseFloat(newExcludeZone.style.top) - canvasOffsetY) * canvasRatio;
            let realWidth = parseFloat(newExcludeZone.style.width) * canvasRatio;
            let realHeight = parseFloat(newExcludeZone.style.height) * canvasRatio;
            
            // change coordinates in pixels to coordinates in percentages, so that rectangles are resized when browser window is also resized
            newExcludeZone.style.width = parseFloat(newExcludeZone.style.width) * 100 / canvas.clientWidth + '%';
            newExcludeZone.style.height = parseFloat(newExcludeZone.style.height) * 100 / canvas.clientHeight + '%';
            newExcludeZone.style.left = parseFloat(newExcludeZone.style.left) * 100 / canvas.clientWidth + '%';
            newExcludeZone.style.top = parseFloat(newExcludeZone.style.top) * 100 / canvas.clientHeight + '%';

            // add line to exclude excludeTable
            let row = document.createElement('tr')
            let colActive = document.createElement('td')
            let activeBox = document.createElement('input')
            let inputId = 'new_exclude_input_' + excludeIndex
            activeBox.type = 'checkbox';
            activeBox.checked = 'checked';
            activeBox.setAttribute('name', 'new_exclude_' + testStepId + '_' + stepSnapshotId);
            activeBox.setAttribute('id', inputId);
            activeBox.setAttribute('related_to', newExcludeZone.id); // link this checkbox to the exclude zone rectangle
            activeBox.setAttribute('r_x', realLeft);
            activeBox.setAttribute('r_y', realTop);
            activeBox.setAttribute('r_w', realWidth);
            activeBox.setAttribute('r_h', realHeight);
            activeBox.setAttribute('canvas_ratio', canvasRatio);
            activeBox.setAttribute('target_snapshot', refSnapshotId);
            
            // click will enable/disable the static element (on summary) and its equivalent on edition modal
            // activeBox.setAttribute('onclick', "toggleElement('new_exclude_" + excludeIndex + "');toggleElement('new_exclude_" + excludeIndex + "Static');");
            activeBox.setAttribute('onclick', "toggleElement('new_exclude_" + excludeIndex + "');");
            colActive.appendChild(activeBox);
            
            // column for color
            let colColor = document.createElement('td');
            colColor.setAttribute('style', "background-color: darkred");
            
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
            row.appendChild(colApplyTo);
            excludeTable.appendChild(row);
            
            newExcludeZone = null;
            
        } else {
                        
            
            excludeIndex++;
            console.log("begun." + mouse.x);
            
            // canvas is a bit larger and higher than picture to be able to start a rectangle on borders
            // adjust coordinates
            mouse.startX = computeMouseXPosition();
            mouse.startY = computeMouseYPosition();
            
  
            newExcludeZone = document.createElement('div');
            newExcludeZone.className = 'rectangle resize-drag deletable'
            newExcludeZone.id = 'new_exclude_' + excludeIndex;
            newExcludeZone.style.left = mouse.startX + 'px';
            newExcludeZone.style.top = mouse.startY + 'px';
            canvas.appendChild(newExcludeZone);
            canvas.style.cursor = "crosshair";
            
        }
    }
}

var dragStartPosition = null

interact('.resize-drag')
  .resizable({
    // resize from all edges and corners
    edges: { left: true, right: true, bottom: true, top: true },

    listeners: {
        move: resizeMoveListener,
        start (event) {
            dragStartPosition = event.target.getBoundingClientRect();
        },
        end: updateRealCoordinates,
    },
    modifiers: [
      // keep the edges inside the parent
      interact.modifiers.restrictEdges({
        outer: 'parent'
      }),

      // minimum size
      interact.modifiers.restrictSize({
        min: { width: 10, height: 10 }
      })
    ],

    inertia: true
  })
  .draggable({
    listeners: { 
        move: dragMoveListener ,
        start (event) {
            dragStartPosition = event.target.getBoundingClientRect();
        },
        end: updateRealCoordinates,
    },
    inertia: true,
    modifiers: [
      interact.modifiers.restrictRect({
        restriction: '.snapshot',
        endOnly: true
      })
    ]
  })
  
interact('.deletable')
  .on('tap', function(event) {
    lastInteractEvent = Date.now();
  })
  .on('doubletap', function(event) {
    deleteExcludeZone(event);
  })
  
function resizeMoveListener (event) {
    var target = event.target
    var x = (parseFloat(target.getAttribute('data-x')) || 0)
    var y = (parseFloat(target.getAttribute('data-y')) || 0)

    // update the element's style
    target.style.width = event.rect.width + 'px'
    target.style.height = event.rect.height + 'px'

    // translate when resizing from top or left edges
    x += event.deltaRect.left
    y += event.deltaRect.top

    target.style.transform = 'translate(' + x + 'px,' + y + 'px)'

    target.setAttribute('data-x', x)
    target.setAttribute('data-y', y)
    lastInteractEvent = Date.now();
}
  
function dragMoveListener (event) {
    var target = event.target
    // keep the dragged position in the data-x/data-y attributes
    var x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx
    var y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy

    // translate the element
    target.style.transform = 'translate(' + x + 'px, ' + y + 'px)'

    // update the posiion attributes
    target.setAttribute('data-x', x)
    target.setAttribute('data-y', y)
    
    lastInteractEvent = Date.now();
}

function updateRealCoordinates (event) {
    let dragEndPosition = event.target.getBoundingClientRect();
    let excludeZoneCheckbox = document.querySelectorAll('input[related_to=' + event.target.id + ']')[0];
    let canvasRatio = parseFloat(excludeZoneCheckbox.getAttribute('canvas_ratio'));
    excludeZoneCheckbox.setAttribute('r_x', Math.max(0, parseFloat(excludeZoneCheckbox.getAttribute('r_x')) + (dragEndPosition.x - dragStartPosition.x) * canvasRatio));
    excludeZoneCheckbox.setAttribute('r_y', Math.max(0, parseFloat(excludeZoneCheckbox.getAttribute('r_y')) + (dragEndPosition.y - dragStartPosition.y) * canvasRatio));
    excludeZoneCheckbox.setAttribute('r_w', parseFloat(excludeZoneCheckbox.getAttribute('r_w')) + (dragEndPosition.width - dragStartPosition.width) * canvasRatio);
    excludeZoneCheckbox.setAttribute('r_h', parseFloat(excludeZoneCheckbox.getAttribute('r_h')) + (dragEndPosition.height - dragStartPosition.height) * canvasRatio);
    dragStartPosition = null;
}

/**
Deletes the current exclude zone from canvas
Also hide it's related line in excludeZoneTable
Uncheck the input so that it's ignored in updates to server
*/
function deleteExcludeZone(event) {
    event.target.remove()
    lastInteractEvent = Date.now();
    
    // get the input checkbox element related to this exclude zone
    let nodeToHide = document.querySelector('[related_to=' + event.target.id + ']');
    nodeToHide.style = "display: none;";
    nodeToHide.checked = false;
    
    // also hide the whole line
    nodeToHide.parentNode.parentNode.style = "display: none;";
}

/**
 * Change the "snapshot" attribute of the input element representing the exclude zone
 * @param inputElementId    the <input> element
 * @param value         id of the target snapshot (reference or step snapshot)
 * @returns
 */
function changeExcludeZoneTarget(inputElementId, value) {
    document.getElementById(inputElementId).setAttribute("target_snapshot", value)
}

/**
 * draw rectangles on canvas, based on the content of the table containing "exclude" elements
 * @param canvas            the canvas element where to draw rectangles
 * @param snapshotHeight    height of the snapshot on which rectangles will be drawn. It helps calculating canvas ratio
 * @param idSuffix          a suffix to add to 'id' of each rectangle to differentiate rectangles from editable zone and rectangles from summary
 * @param testStepId        
 * @returns
 */
function drawExistingExcludeZones(canvas, snapshotHeight, idSuffix, testStepId, snapshotId) {
    
    // do not draw if canvas / snapshot is not visible
    if (snapshotHeight == 0) {
        return
    }
    
    // remove old rectangles to redraw from excludeZoneTable
    document.querySelectorAll('#canvas' + idSuffix + '_' + testStepId + '_' + snapshotId + ' > .rectangle').forEach(node => node.remove());
    
    let snapshot = document.getElementById('stepSnapshot' + idSuffix + '_' + testStepId + '_' + snapshotId);
    let canvasRatio = getIntValue(snapshot.clientWidth) / getIntValue(canvas.getAttribute("width"));
    let currentExcludes = document.querySelectorAll('#excludeZoneTable_' + testStepId + '_' + snapshotId + ' input');
    
    // exclude zone rectangle is positionned relative to canvas, but we have coordinates relative to picture
    let canvasCoords = canvas.getBoundingClientRect();
    let snapshotRectangle = snapshot.getBoundingClientRect();
    let canvasOffsetX = snapshotRectangle.left - canvasCoords.left;
    let canvasOffsetY = snapshotRectangle.top - canvasCoords.top;

    for(var i= 0; i < currentExcludes.length; i++) {
        if (currentExcludes[i].checked) {

            var idx = getIntValue(currentExcludes[i].id) 
            
            element = document.createElement('div');
            if (idSuffix === '') { // for the editable rectangles
                element.className = 'rectangle deletable';
                currentExcludes[i].setAttribute('related_to', 'zone_' + currentExcludes[i].id);
                element.id = 'zone_' + currentExcludes[i].id;
            } else {
                element.className = 'rectangle';
            }
            
            element.style.left = (parseFloat(currentExcludes[i].getAttribute('r_x')) * canvasRatio + canvasOffsetX) * 100 / canvas.clientWidth + '%';
            element.style.top = (parseFloat(currentExcludes[i].getAttribute('r_y')) * canvasRatio + canvasOffsetY) * 100 / canvas.clientHeight + '%';
            element.style.width = parseFloat(currentExcludes[i].getAttribute('r_w')) * canvasRatio * 100 / canvas.clientWidth + '%';
            element.style.height = parseFloat(currentExcludes[i].getAttribute('r_h')) * canvasRatio * 100 / canvas.clientHeight + '%';
            element.style.borderColor = currentExcludes[i].getAttribute('color')
             
            canvas.appendChild(element);
        }
    }
}

/**
 * Get cookie value
 * @param name      cookie name
 * @returns
 */
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
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
    var csrftoken = getCookie('csrftoken');
    
    // add new exclude zones
    // these ajax calls are not asynchronous as they MUST finish before we call computing 
    for(let i= 0; i < newExcludes.length; i++) {
        if (newExcludes[i].checked) {
            $.ajax({
                type: 'POST',
                async: false,
                headers: {"X-CSRFToken": csrftoken},
                url: '/snapshot/api/exclude/',
                data: "x=" + Math.round(newExcludes[i].getAttribute('r_x'))
                    + "&y=" + Math.round(newExcludes[i].getAttribute('r_y'))
                    + "&width=" + Math.round(newExcludes[i].getAttribute('r_w'))
                    + "&height=" + Math.round(newExcludes[i].getAttribute('r_h'))
                    + "&snapshot=" + newExcludes[i].getAttribute('target_snapshot')
                    
            });
        }
    }
    
    var currentExcludes = document.querySelectorAll('#excludeZoneTable_' + testStepId + '_' + snapshotId + ' input');

    for(let i= 0; i < currentExcludes.length; i++) {
        
        // do not update new exclude zones
        if (currentExcludes[i].id.startsWith('new_exclude')) {
            continue
        }
        
        // remove exclude zones that should not be kept
        if (!currentExcludes[i].checked) {

            // these ajax calls are not asynchronous as they MUST finish before we call computing 
            $.ajax({
                type: 'DELETE',
                headers: {"X-CSRFToken": csrftoken},
                url: '/snapshot/api/exclude/' + getIntValue(currentExcludes[i].id) + '/',
                async: false    
            });
        } else {
        
            // change target snapshot
            $.ajax({
                type: 'PATCH',
                async: false,
                headers: {"X-CSRFToken": csrftoken},
                url: '/snapshot/api/exclude/' + getIntValue(currentExcludes[i].id) + '/',
                data: "snapshot=" + currentExcludes[i].getAttribute('target_snapshot')  
            });
        }
    }
    
    // recompute difference
    $.ajax({
        type: 'POST',
        headers: {"X-CSRFToken": csrftoken},
        url: '/snapshot/compare/compute/' + snapshotId + '/',
        async: false    
    });

    // reload step
    updatePanel('/snapshot/compare/picture/' + testCaseId + '/' + testStepId, 'step_' + testStepId);


}

