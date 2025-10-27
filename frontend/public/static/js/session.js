let inactivityTimer;
let activityCheckInterval;

function startInactivityTimer() {
    console.log('Starting inactivity timer for auto-logout...');
    const resetTimer = () => {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(() => {
            forceLogoutDueToInactivity();
        }, 600000);
    };
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click', 'keydown'];
    events.forEach(event => {
        document.addEventListener(event, resetTimer, true);
    });
    events.forEach(event => {
        document.addEventListener(event, updateServerActivity, true);
    });
    resetTimer();
    startServerSessionCheck();
}

function updateServerActivity() {
    if (Math.random() < 0.1) {
        fetch('/api/update-activity', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': ApiClient.getCSRFToken()
            },
            credentials: 'same-origin'
        }).catch(error => console.log('Activity update failed:', error));
    }
}

function startServerSessionCheck() {
    activityCheckInterval = setInterval(() => {
        checkServerSession();
    }, 120000);
}

function checkServerSession() {
    fetch('/api/check-session', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                forceLogoutDueToInactivity();
            }
        }
        return response.json();
    })
    .then(data => {
        if (data && data.session_valid === false) {
            forceLogoutDueToInactivity();
        }
    })
    .catch(error => {
        console.log('Session check failed:', error);
    });
}

function forceLogoutDueToInactivity() {
    console.log('Auto-logout due to inactivity');
    clearTimeout(inactivityTimer);
    clearInterval(activityCheckInterval);
    NotificationManager.show('Your session has expired due to inactivity. Redirecting to login...', 'warning');
    fetch('/auth/logout', {
        method: 'POST',
        headers: {
            'X-CSRFToken': ApiClient.getCSRFToken()
        },
        credentials: 'same-origin'
    })
    .finally(() => {
        setTimeout(() => {
            window.location.href = "/login?expired=true";
        }, 2000);
    });
}

function showSessionExpiredMessage() {
    console.log('Session expired, showing message...');
    NotificationManager.show('Your session has expired. Please login again.', 'info');
    setTimeout(() => {
        window.location.href = "/login?expired=true";
    }, 3000);
}

function initializeSessionTimeout() {
    const isAuthenticated = document.body.classList.contains('user-authenticated') ||
                           document.querySelector('[data-user-authenticated="true"]') ||
                           document.querySelector('.user-account-menu');
    if (isAuthenticated) {
        console.log('User is authenticated, starting inactivity timer...');
        startInactivityTimer();
    } else {
        console.log('User not authenticated, skipping inactivity timer');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initializeSessionTimeout();
});

window.addEventListener('beforeunload', function() {
    clearTimeout(inactivityTimer);
    clearInterval(activityCheckInterval);
});