import { translate } from '../utils.js';
import { getPlayerDetails } from '../api/matchmaker-service.js';

export async function loadPlayerDetailsScreen() {
    const params = new URLSearchParams(window.location.search);
    const playerName = params.get('playerName');

    if (!playerName) {
        console.error('No player name provided');
        return;
    }

    const player = await getPlayerDetails(playerName);
    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = `
        <div class="container mt-5">
            <div class="card-container">
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Player Details')}</h4>
                    </div>
                    <div class="listing-card-body">
                        <p>
                            <strong>${translate('Name')}:</strong>
                            ${player.name}
                        </p>
                        <p>
                            <strong>${translate('Total games')}:</strong>
                            ${player.total_games}
                        </p>
                        <p>
                            <strong>${translate('Total wins')}:</strong>
                            ${player.total_wins}
                        </p>
                        <p>
                            <strong>${translate('Total losses')}:</strong>
                            ${player.total_losses}
                        </p>
                        <p>
                            <strong>${translate('Win rate')}:</strong>
                            ${player.win_rate}
                        </p>
                        <p>
                            <strong>${translate('Connected')}:</strong>
                            ${player.connected}
                        </p>
                    </div>
                    <div class="listing-card-footer">
                        <a href="/listings" class="btn btn-primary">
                            ${translate('Back to Listings')}
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
}
