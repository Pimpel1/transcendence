import { csrfTokens } from "../csrf.js";
import { showMessage } from "../utils.js";

const BaseUrl = `${window.config.apiBaseUrl}/user-management`;

export function removeFriend(username) {
    return fetch(`${BaseUrl}/delete-friend`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfTokens['user-management'],
        },
        body: JSON.stringify({ username }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to delete friend');
            });
        }
        return response.json();
    });
}

export function getFriendsList() {
    return fetch(`${BaseUrl}/my-friends`, {
        referrer:"https://localhost:8443"
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to get friends list');
        }
        return response.json();
    })
    .then(data => data.friends);
}

export function getUserDetails() {
    return fetch(`${BaseUrl}/user-details`, {
        referrer: `${window.config.apiBaseUrl}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(
                `Failed to get user details [Status: ${response.status}]`
            );
        }
        return response.json();
    })
    .then(data => {
        return data;
    })
    .catch(error => {
        console.error("Error fetching user details:", error);
        throw error;
    });
}


export function getUserList() {
    return fetch(`${BaseUrl}/all-users`, {
        referrer: "https://localhost:8443"
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to get users list');
        }
        return response.json();
    });
}

export function friendRequest(username) {
    return fetch(`${BaseUrl}/send-friend-request`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfTokens['user-management'],
        },
        body: JSON.stringify({ username }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to send friend request');
            });
        }
        return response.json();
    });
}

export function updateUser(userDetails) {
    return fetch(`${BaseUrl}/update`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfTokens['user-management'],
        },
        body: JSON.stringify(userDetails),
    })
    .then(response => {
        if (!response.ok) {
            const status = response.status;
            return response.json().then(data => {
                if (status === 401){
                    showMessage(
                        'Displayname is already taken ! Choose another one!',
                        'danger'
                        );
                }
                throw new Error(
                    `${status}: ${
                        data.error || 'Failed to update user details'
                    }`
                );
            });
        }
        return response.json();
    })
    .catch(error => {
        throw new Error('Failed to update user details');
    });
}

export async function getDisplaynames(usernames) {
    return fetch(`${BaseUrl}/get-displaynames`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfTokens['user-management'],
        },
        body: JSON.stringify(usernames),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(
                `Error fetching displaynames: ${response.statusText}`
            );
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
                console.error('user-management unhealthy');
            }
            return result;
        })
        .catch((error) => {
            console.error(`user-management unhealthy [${error.message}]`);
            return false;
        });
}
