// auth.js - Authentication utilities

// Check if user is authenticated
function ensureAuthenticated() {
    if (!localStorage.getItem("jwt")) {
        window.location.href = "/login.html";
    }
}

// Add JWT token to all Webix AJAX requests
webix.attachEvent("onBeforeAjax", function(mode, url, data, request, headers){
    const token = localStorage.getItem("jwt");
    if (token) {
        headers["Authorization"] = "Bearer " + token;
    }
});

// Login function
function login(username, password) {
    return fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
}

// Register function
function register(nama, username, email, password, role) {
    return fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nama, username, email, password, role })
    });
}

// Logout function
function logout() {
    localStorage.removeItem("jwt");
    window.location.href = "/login.html";
}

// Get current user info from token
function getCurrentUser() {
    const token = localStorage.getItem("jwt");
    if (!token) return null;
    
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload;
    } catch (e) {
        return null;
    }
}