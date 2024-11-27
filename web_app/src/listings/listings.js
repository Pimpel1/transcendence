import { translate } from '../utils.js';
import {
    getGameList,
    getTournamentList,
    getPlayerList
} from '../api/matchmaker-service.js';

export function loadListingsScreen() {
    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = `
        <div class="container mt-5">
            <div class="card-container">
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Games looking for players')}</h4>
                    </div>
                    <ul id="games-looking-for-player"
                        class="list-group list-group-flush">
                    </ul>
                </div>
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Games scheduled')}</h4>
                    </div>
                    <ul id="games-scheduled"
                        class="list-group list-group-flush">
                    </ul>
                </div>
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Games in progress')}</h4>
                    </div>
                    <ul id="games-in-progress"
                        class="list-group list-group-flush">
                    </ul>
                </div>
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Games completed')}</h4>
                    </div>
                    <ul id="games-completed"
                        class="list-group list-group-flush">
                    </ul>
                </div>
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>
                            ${translate('Tournaments looking for players')}
                        </h4>
                    </div>
                    <ul id="tournaments-looking-for-players"
                        class="list-group list-group-flush">
                    </ul>
                </div>
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Tournaments in progress')}</h4>
                    </div>
                    <ul id="tournaments-in-progress"
                        class="list-group list-group-flush">
                    </ul>
                </div>
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Tournaments completed')}</h4>
                    </div>
                    <ul id="tournaments-completed"
                        class="list-group list-group-flush">
                    </ul>
                </div>
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Connected players')}</h4>
                    </div>
                    <ul id="connected-players"
                        class="list-group list-group-flush">
                    </ul>
                </div>
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Disconnected players')}</h4>
                    </div>
                    <ul id="disconnected-players"
                        class="list-group list-group-flush">
                    </ul>
                </div>
            </div>
        </div>
    `;

    loadData();
}

async function loadData() {
    const tournaments = await getTournamentList();
    const games = await getGameList();
    const players = await getPlayerList();

    populateList(
        'games-looking-for-player',
        games.filter(g => g.status === 'waiting_for_players'),
        'game'
    );
    populateList(
        'games-scheduled',
        games.filter(g => g.status === 'scheduled'),
        'game'
    );
    populateList(
        'games-in-progress',
        games.filter(g => g.status === 'in_progress'),
        'game'
    );
    populateList(
        'games-completed',
        games.filter(g => g.status === 'finished'),
        'game'
    );
    populateList(
        'tournaments-looking-for-players',
        tournaments.filter(t => t.status === 'waiting_for_players'),
        'tournament'
    );
    populateList(
        'tournaments-in-progress',
        tournaments.filter(t => t.status === 'in_progress'),
        'tournament'
    );
    populateList(
        'tournaments-completed',
        tournaments.filter(t => t.status === 'finished'),
        'tournament'
    );
    populateList(
        'connected-players',
        players.filter(p => p.connected),
        'player'
    );
    populateList(
        'disconnected-players',
        players.filter(p => !p.connected),
        'player'
    );
}

function populateList(elementId, items, type) {
    const listElement = document.getElementById(elementId);
    listElement.innerHTML = items.map(item => {
        const idOrName = type === 'player' ? item.name : item.id;
        let detailsPath;

        switch (type) {
            case 'game':
                detailsPath = `/game-details?gameId=${idOrName}`;
                break;
            case 'tournament':
                detailsPath = `/tournament-details?tournamentId=${idOrName}`;
                break;
            case 'player':
                detailsPath = `/player-details?playerName=${idOrName}`;
                break;
            default:
                detailsPath = '/';
        }

        return `<li class="list-group-item">
            <a href="${detailsPath}" class="details-link">${item.name}</a>
        </li>`;
    }).join('');
}
