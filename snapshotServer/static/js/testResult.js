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
document.addEventListener("submit", async function (event) {
    const form = event.target.closest("form.error-cause-form");

    if (!form) {
        return;
    }

    event.preventDefault();

    const statusElement = form.querySelector(
        ".save-cause-status"
    );

    const submitButton = form.querySelector(
        ".save-cause-button"
    );

    statusElement.style.display = "none";
    submitButton.disabled = true;

    try {
        const response = await fetch(form.action, {
            method: "POST",
            body: new FormData(form),
            credentials: "same-origin",
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        });

        const data = await response.json();

        statusElement.textContent = data.message;
        statusElement.style.display = "block";

        if (response.ok) {
            statusElement.className =
                "save-cause-status alert alert-success";

            const existingCauseIdInput = form.querySelector(
                'input[name="existingCauseId"]'
            );

            if (existingCauseIdInput && data.causeId) {
                existingCauseIdInput.value = data.causeId;
            }

            submitButton.textContent = "Update cause";
        } else {
            statusElement.className =
                "save-cause-status alert alert-danger";
        }
    } catch (error) {
        console.error("Error while saving the cause:", error);

        statusElement.textContent =
            "An error occurred while saving the cause.";

        statusElement.className =
            "save-cause-status alert alert-danger";

        statusElement.style.display = "block";
    } finally {
        submitButton.disabled = false;
    }
});