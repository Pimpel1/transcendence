const csrfTokens = {};

async function fetchCsrfToken(serviceUrl) {
    const response = await fetch(
        `${serviceUrl}/get-csrf-token`, { credentials: 'include' }
    );
    if (!response.ok) throw new Error('service offline');
    const data = await response.json();
    return data.csrfToken;
}


async function fetchWithRetry(serviceUrl, service, delay = 4000) {
    try {
        return await fetchCsrfToken(serviceUrl);
    } catch (error) {
        console.log(
            `Waiting for ${service} to set CSRF token. [${error}]`
        );
        await new Promise(resolve => setTimeout(resolve, delay));
        return fetchWithRetry(serviceUrl, service, delay);
    }
}


export function loadCsrfTokens() {
    const services = [
        'user-management',
        'auth-service',
        'matchmaker-service',
        'game-service'
    ].filter(service => !csrfTokens[service]);

    const fetchPromises = services.map(service => 
        fetchWithRetry(`${window.config.apiBaseUrl}/${service}`, service)
            .then(token => {
                console.log(`Set CSRF token for ${service}`);
                csrfTokens[service] = token;
            })
            .catch(error => {
                console.error(
                    `Failed to set CSRF token for ${service} [${error}]`
                );
            })
    );

    return Promise.all(fetchPromises)
        .catch(error => {
            console.error('Error while setting CSRF tokens', error);
        });
}


export { csrfTokens };
