import { csrfTokens } from "../csrf.js";

const BaseUrl = `${window.config.apiBaseUrl}/auth-service`;

export function validateJwt() {
    return fetch(`${BaseUrl}/api/validate-jwt`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfTokens["auth-service"],
        },
    })
    .then((response) => {
        if (response.status === 401) {
            return { authenticated: false };
        }
        if (!response.ok) {
            throw new Error("Failed to validate JWT");
        }
        return response.json().then((data) => {
            return { authenticated: true, ...data };
        });
    });
}

export function verifyOtp(code) {
    return fetch(`${BaseUrl}/api/verify-otp`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfTokens["auth-service"],
        },
        body: JSON.stringify({ otp: code }),
    })
    .then((response) => {
        if (!response.ok) {
            const status = response.status;
            return response.json().then(data => {
                throw new Error(
                    `${status}: ${
                        data.error || "Failed to verify OTP"
                    }`
                );
            });
        }
        return response.json();
    });
}

export function authLogout() {
    return fetch(`${BaseUrl}/api/logout`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfTokens["auth-service"],
        },
    })
    .then((response) => {
        if (!response.ok) {
            throw new Error("Failed to logout");
        }
        return response.json();
    });
}

export function isHealthy() {
    const timeout = new Promise((_, reject) => {
        setTimeout(() => {reject(new Error('Timeout'));}, 3000);
    });

    const fetchPromise = fetch(
        `${BaseUrl}/health`
    ).then(response => response.ok);

    return Promise.race([fetchPromise, timeout])
        .then(result => {
            if (!result) {
                console.error('auth-service unhealthy');
            }
            return result;
        })
        .catch((error) => {
            console.error(`auth-service unhealthy [${error.message}]`);
            return false;
        });
}

