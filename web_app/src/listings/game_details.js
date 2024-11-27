import { translate } from '../utils.js';
import { getGameDetails } from '../api/matchmaker-service.js';

export async function loadGameDetailsScreen() {
    const params = new URLSearchParams(window.location.search);
    const gameId = params.get('gameId');

    if (!gameId) {
        console.error('No game ID provided');
        return;
    }

    const game = await getGameDetails(gameId);
    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = `
        <div class="container mt-5">
            <div class="card-container">
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Game Details')}</h4>
                    </div>
                    <div class="listing-card-body">
                        <p>
                            <strong>${translate('Name')}:</strong>
                            ${game.name}
                        </p>
                        <p>
                            <strong>${translate('Player 1')}:</strong>
                            ${game.player1}
                        </p>
                        <p>
                            <strong>${translate('Player 2')}:</strong>
                            ${game.player2}
                        </p>
                        <p>
                            <strong>${translate('Status')}:</strong>
                            ${game.status}
                        </p>
                        <p>
                            <strong>${translate('Score player 1')}:</strong>
                            ${game.player1_score}
                        </p>
                        <p>
                            <strong>${translate('Score player 2')}:</strong>
                            ${game.player2_score}
                        </p>
                        <p>
                            <strong>${translate('Winner')}:</strong>
                            ${game.winner}
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
