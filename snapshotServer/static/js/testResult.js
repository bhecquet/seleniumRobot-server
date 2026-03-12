function runErrorAnalysis(currentTestId) {

    document.querySelectorAll('.errorCause').forEach(function(element) {
        element.innerText = 'Analysis requested'
    });

    var csrftoken = getCookie('csrftoken');
    $.ajax({
        type: 'POST',
        async: false,
        headers: {"X-CSRFToken": csrftoken},
        url: '/snapshot/errorAnalysis/' + currentTestId + '/'

    });
}

