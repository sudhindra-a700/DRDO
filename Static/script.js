document.addEventListener('DOMContentLoaded', () => {
    const expertPanel = document.getElementById('expertPanel');
    const intervieweePanel = document.getElementById('intervieweePanel');
    const contentDiv = document.getElementById('content');

    expertPanel.addEventListener('click', () => {
        loadContent('login.html', 'expert');
    });

    intervieweePanel.addEventListener('click', () => {
        loadContent('login.html', 'interviewee');
    });

    function loadContent(page, userType) {
        fetch(page)
            .then(response => response.text())
            .then(html => {
                contentDiv.innerHTML = html;
                attachFormListener(userType); 
            });
    }

    function attachFormListener(userType) {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) { 
            const additionalField = document.getElementById('additionalField');
            if (userType === 'expert') {
                additionalField.innerHTML = '<input type="text" id="id" placeholder="ID" required>';
            } else {
                additionalField.innerHTML = '<input type="text" id="regNo" placeholder="Registration No." required>';
            }

            loginForm.addEventListener('submit', (event) => {
                event.preventDefault();
               
            });
        }

       
    }
});