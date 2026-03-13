function runErrorAnalysis(currentTestId) {

    document.querySelectorAll('.error-cause').forEach(function(element) {
        element.innerText = 'Analysis requested, reload page to see update'
    });

    var csrftoken = getCookie('csrftoken');
    $.ajax({
        type: 'POST',
        async: false,
        headers: {"X-CSRFToken": csrftoken},
        url: '/snapshot/errorAnalysis/' + currentTestId + '/'

    });
}

