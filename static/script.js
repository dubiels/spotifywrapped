document.addEventListener('DOMContentLoaded', function() {
    const darkModeEnabled = document.body.classList.contains('dark-mode');
    if (darkModeEnabled) {
        document.body.classList.add('dark-mode');
    }
    document.getElementById('toggle-dark-mode').addEventListener('click', function() {
        console.log("Dark mode button clicked!");
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        fetch('/toggle-dark-mode/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.dark_mode) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
        })
        .catch(error => {
            console.error("Error in fetch request:", error);
        });
    });
});

document.querySelectorAll('.star').forEach(star => {
    star.addEventListener('click', function() {
        let value = this.getAttribute('data-value');
        document.querySelectorAll('.star').forEach(s => {
            s.classList.remove('selected');
            if (s.getAttribute('data-value') <= value) {
                s.classList.add('selected');
            }
        });
    });
});