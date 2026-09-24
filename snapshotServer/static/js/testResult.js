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
document.addEventListener("DOMContentLoaded", function () {
    const modalElement = document.getElementById(
        "errorCauseModal"
    );

    /*
     * Prepare the modal when an Add/Edit cause button is clicked.
     */
    if (modalElement) {
        modalElement.addEventListener(
            "show.bs.modal",
            function (event) {
                const triggerButton = event.relatedTarget;

                if (!triggerButton) {
                    return;
                }

                const causeId =
                    triggerButton.dataset.causeId || "";

                const causeType =
                    triggerButton.dataset.causeType ||
                    "Application";

                const comment =
                    triggerButton.dataset.comment || "";

                const exception =
                    triggerButton.dataset.exception || "";

                const errorMessage =
                    triggerButton.dataset.errorMessage || "";

                const stepName =
                    triggerButton.dataset.stepName || "";

                const testCaseId =
                    triggerButton.dataset.testCaseId || "";

                const testStepId =
                    triggerButton.dataset.testStepId || "";

                const modalTitle = document.getElementById(
                    "errorCauseModalLabel"
                );

                const submitButton = document.getElementById(
                    "errorCauseModalSubmit"
                );

                document.getElementById(
                    "modalExistingCauseId"
                ).value = causeId;

                document.getElementById(
                    "modalCauseType"
                ).value = causeType;

                document.getElementById(
                    "modalCauseComment"
                ).value = comment;

                document.getElementById(
                    "modalException"
                ).value = exception;

                document.getElementById(
                    "modalErrorMessage"
                ).value = errorMessage;

                document.getElementById(
                    "modalStepName"
                ).value = stepName;

                document.getElementById(
                    "modalTestCaseId"
                ).value = testCaseId;

                document.getElementById(
                    "modalTestStepId"
                ).value = testStepId;

                const statusElement =
                    modalElement.querySelector(
                        ".save-cause-status"
                    );

                if (statusElement) {
                    statusElement.textContent = "";
                    statusElement.className =
                        "save-cause-status";
                    statusElement.style.display = "none";
                }

                if (causeId) {
                    modalTitle.textContent = "Update cause";
                    submitButton.textContent = "Update cause";
                } else {
                    modalTitle.textContent = "Add a cause";
                    submitButton.textContent = "Save cause";
                }

                submitButton.disabled = false;
            }
        );
    }

    /*
     * Create shortcuts below the test result header.
     */
    const headerShortcut = document.getElementById(
        "errorCauseHeaderShortcut"
    );

    const causeButtons = document.querySelectorAll(
        ".declare-cause-button"
    );

    if (
        !headerShortcut ||
        causeButtons.length === 0
    ) {
        return;
    }

    const shortcutCard = document.createElement("div");

    shortcutCard.className = "error-cause-shortcut-card";

    const shortcutContent = document.createElement("div");

    shortcutContent.className = "error-cause-shortcut-content";

    const shortcutIcon = document.createElement("span");

    shortcutIcon.className = "error-cause-shortcut-icon";
    shortcutIcon.textContent = "!";

    const shortcutText = document.createElement("div");

    shortcutText.className = "error-cause-shortcut-text";

    const shortcutTitle = document.createElement("strong");

    shortcutTitle.textContent = "Cause review";

    const shortcutDescription = document.createElement("span");

    if (causeButtons.length === 1) {
        shortcutDescription.textContent = "1 failed step";
    } else {
        shortcutDescription.textContent =
            causeButtons.length + " failed steps";
    }

    shortcutText.appendChild(shortcutTitle);
    shortcutText.appendChild(shortcutDescription);

    shortcutContent.appendChild(shortcutIcon);
    shortcutContent.appendChild(shortcutText);

    const actionsElement = document.createElement("div");

    actionsElement.className = "error-cause-shortcut-actions";

    causeButtons.forEach(function (causeButton, index) {
        const shortcutButton = document.createElement("button");

        shortcutButton.type = "button";
        shortcutButton.className =
            "btn btn-sm btn-outline-primary";

        const hasExistingCause =
            Boolean(causeButton.dataset.causeId);

        if (causeButtons.length === 1) {
            shortcutButton.textContent =
                hasExistingCause
                    ? "Edit cause"
                    : "Add cause";
        } else {
            const stepName =
                causeButton.dataset.stepName ||
                "Step " + (index + 1);

            shortcutButton.textContent =
                hasExistingCause
                    ? "Edit " + stepName
                    : "Add cause for " + stepName;
        }

        shortcutButton.addEventListener(
            "click",
            function () {
                causeButton.click();
            }
        );

        actionsElement.appendChild(shortcutButton);
    });

    shortcutCard.appendChild(shortcutContent);
    shortcutCard.appendChild(actionsElement);

    headerShortcut.appendChild(shortcutCard);

});
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