import { translate } from '../utils.js';
import { getTournamentDetails } from '../api/matchmaker-service.js';

export async function loadTournamentDetailsScreen() {
    const params = new URLSearchParams(window.location.search);
    const tournamentId = params.get('tournamentId');

    if (!tournamentId) {
        console.error('No tournament ID provided');
        return;
    }

    const tournament = await getTournamentDetails(tournamentId);
    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = `
        <div class="container mt-5">
            <div class="card-container">
                <div class="listing-card">
                    <div class="listing-card-header">
                        <h4>${translate('Tournament Details')}</h4>
                    </div>
                    <div class="listing-card-body">
                        <p>
                            <strong>${translate('Name')}:</strong>
                            ${tournament.name}
                        </p>
                        <p>
                            <strong>${translate('Pool size')}:</strong>
                            ${tournament.pool_size}
                        </p>
                        <p>
                            <strong>${translate('Players')}:</strong>
                            ${tournament.players}
                        </p>
                        <p>
                            <strong>${translate('Status')}:</strong>
                            ${tournament.status}
                        </p>
                        <p>
                            <strong>${translate('Current round')}:</strong>
                            ${tournament.current_round}
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
