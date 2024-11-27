import { csrfTokens } from '../csrf.js';

const BaseUrl = `${window.config.apiBaseUrl}/matchmaker-service`;

export function getGameList() {
    return fetch(`${BaseUrl}/api/games`)
        .then((response) => {
            if (!response.ok) {
                throw new Error('Failed to fetch games');
            }
            response.json();
        })
        .then((data) => data.games);
}

export function getGameDetails(gameId) {
    return fetch(`${BaseUrl}/api/games/${gameId}`)
        .then((response) => {
            if (!response.ok) {
                throw new Error('Failed to fetch game details');
            }
            return response.json();
        });
}

export function getTournamentList() {
    return fetch(`${BaseUrl}/api/tournaments`)
        .then((response) => {
            if (!response.ok) {
                throw new Error('Failed to fetch tournaments');
            }
            return response.json();
        })
        .then((data) => data.tournaments);
}

export function getPlayerList() {
    return fetch(`${BaseUrl}/api/players`)
        .then((response) => {
            if (!response.ok) {
                throw new Error('Failed to fetch players');
            }
            return response.json();
        })
        .then((data) => data.players);
}

export function getPlayerDetails(playerName) {
    return fetch(`${BaseUrl}/api/players/${playerName}`)
        .then((response) => {
            if (!response.ok) {
                throw new Error('Failed to fetch player details');
            }
            return response.json();
        });
}

export function createGame(gameData) {
    return fetch(`${BaseUrl}/api/games`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfTokens['matchmaker-service'],
        },
        body: JSON.stringify(gameData),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to create game');
        }
        return response.json();
    });
}

export function deleteGame(gameId) {
    return fetch(`${BaseUrl}/api/games/${gameId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrfTokens['matchmaker-service'],
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to delete game');
        }
        return response.json();
    });
}

export function createTournament(tournamentData) {
    return fetch(`${BaseUrl}/api/tournaments`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfTokens['matchmaker-service'],
        },
        body: JSON.stringify(tournamentData),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to create tournament');
        }
        return response.json();
    });
}

export function joinTournament(tournamentId, playerName='') {
    return fetch(`${BaseUrl}/api/tournaments/${tournamentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfTokens['matchmaker-service'],
        },
        body: JSON.stringify({
            player: playerName,
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to join tournament');
        }
    });
}

export function leaveTournament(tournamentId, playerName='') {
    return fetch(`${BaseUrl}/api/tournaments/${tournamentId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfTokens['matchmaker-service'],
        },
        body: JSON.stringify({
            player: playerName,
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to leave tournament');
        }
    });
}

export function getPlayerStats(username, query_string='') {
    if (query_string){
        query_string = `?${query_string}`;
    }

    return fetch(`${BaseUrl}/api/players/${username}/stats${query_string}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch player stats');
            }
            return response.json();
        })
        .then(data => data.stats);
}

export function getTournaments(query_string='') {
    if (query_string){
        query_string = `?${query_string}`;
    }

    return fetch(`${BaseUrl}/api/tournaments${query_string}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch tournaments');
            }
            return response.json();
        })
        .then(data => data.tournaments);
}

export function getTournamentDetails(tournamentId) {
    return fetch(`${BaseUrl}/api/tournaments/${tournamentId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch tournament details');
            }
            return response.json();
        });
}

export function startGame(gameId) {
    return fetch(`${BaseUrl}/api/games/start/${gameId}`, {
        method: 'PUT',
        headers: {
            'X-CSRFToken': csrfTokens['matchmaker-service'],
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to start game');
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
                console.error('matchmaker-service unhealthy');
            }
            return result;
        })
        .catch((error) => {
            console.error(`matchmaker-service unhealthy [${error.message}]`);
            return false;
        });
}

export function getMyGames(query_string='') {
    if (query_string){
        query_string = `?${query_string}`;
    }
    return fetch(`${BaseUrl}/api/games/me${query_string}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch my games');
            }
            return response.json();
        })
        .then(data => data.games);
}
