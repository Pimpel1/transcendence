const BaseUrl = `${window.config.apiBaseUrl}/translation-service`;

export function getTranslation(language) {
    return fetch(`${BaseUrl}/api/translations/${language}`)
        .then((response) => {
            if (!response.ok) {
                throw new Error('Failed to get translations');
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
                console.error('translation-service unhealthy');
            }
            return result;
        })
        .catch((error) => {
            console.error(`translation-service unhealthy [${error.message}]`);
            return false;
        });
}
