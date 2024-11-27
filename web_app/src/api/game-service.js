const BaseUrl = `${window.config.apiBaseUrl}/game-service`;

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
                console.error('game-service unhealthy');
            }
            return result;
        })
        .catch((error) => {
            console.error(`game-service unhealthy [${error.message}]`);
            return false;
        });
}
