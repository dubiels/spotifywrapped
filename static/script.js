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

const toggle = document.getElementById('theme-toggle');
const body = document.body;

// Check local storage for theme preference
if (localStorage.getItem('theme') === 'light') {
    body.classList.remove('dark-theme');
    toggle.checked = true; // Set toggle to light mode if stored
} else {
    // Default to dark theme
    body.classList.add('dark-theme');
    toggle.checked = false; // Default is unchecked (dark theme)
}

// Event listener for theme toggle
toggle.addEventListener('change', () => {
    if (toggle.checked) {
        body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
    }
});  