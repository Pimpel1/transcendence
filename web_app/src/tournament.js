import { 
    resizeWindow,
    sanitizeInput,
    showMessage,
    translate,
    updateHistory, 
    userIsBusy
} from './utils.js';
import { onlineArena } from './online_arena.js';
import {
    createTournament, 
    getTournamentDetails, 
    joinTournament, 
    leaveTournament 
} from './api/matchmaker-service.js';
import { getDisplaynames } from './api/user-management.js';
import user from './User.js';

export function loadCreateTournamentScreen() {
    const mainContent = document.getElementById('main-content');
    updateHistory(
        '/create-tournament',
        '/create-tournament',
        { screen: '/create-tournament' }
    );

    mainContent.innerHTML = `
    <div id="mainContentWrapper">
        <div class="wrapper w-100">
            <div class="card mb-4 w-100">
                <div class="card-header" style="background-color: #6c757d;">
                    <h5 class="mb-0 text-white">
                    ${translate("Create a new tournament")}
                    </h5>
                </div>
                <div class="card-body text-center">
                    <form id="create-tournament-form">
                        <div class="form-group
                            <label for="tournament-name">
                            ${translate("Tournament Name")}
                            </label>
                            <input
                                type="text"
                                class="form-control"
                                id="tournament-name"
                                name="tournament-name"
                                required
                            />
                        </div>
                        <div class="form-group
                            <label for="number-of-players">
                            ${translate("Number of players")}
                            </label>
                            <input
                                type="number"
                                class="form-control"
                                id="number-of-players"
                                name="number-of-players"
                                required
                                min="2"
                                max="32"
                            />
                        </div>
                        <button id="submit"
                                type="submit"
                                class="btn btn-secondary
                                btn-lg me-2 mt-2">
                            ${translate("Create Tournament")}
                        </button>
                        <button id="cancel"
                                type="cancel"
                                class="btn btn-secondary
                                btn-lg mt-2">
                            ${translate("Cancel")}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    `;

    resizeWindow();

    document.getElementById('create-tournament-form')
        .addEventListener('submit', async (event) => {
        event.preventDefault();
        if (await userIsBusy()) {
            showMessage(
                `${translate("You can't create a tournament")}` +
                ` ${translate("because you're already involved elsewhere")}.`,
                `danger`
            );
            return;
        }
        const cancel = document.getElementById('cancel');
        cancel.disabled = true;
        const submit = document.getElementById('submit');
        submit.disabled = true;
        submit.innerText = `${translate("Creating")}...`;
        const tournamentName = sanitizeInput(
            document.getElementById('tournament-name').value,
            30
        );
        const numberOfPlayers = parseInt(
            document.getElementById('number-of-players').value);
        try {
            const data = await createTournament({
                tournament_name: tournamentName,
                pool_size: numberOfPlayers
            });
            loadTournamentDataScreen(data.tournament_id);
        }
        catch (error) {
            showMessage(
                `${translate("You can't create a tournament")} ` +
                ` ${translate("of less than 2 players")}.`,
                `danger`
            );
            cancel.disabled = false;
            submit.disabled = false;
            submit.innerText = `${translate("Create Tournament")}`;
        }
    });

    document.querySelector('button[type="cancel"]')
        .addEventListener('click', () => {
            onlineArena();
        }
    );
}

export async function loadTournamentDataScreen(tournamentId) {
    try {
        const tournament = await getTournamentDetails(tournamentId);
        updateHistory(
            `/tournament/${tournamentId}`,
            `/tournament/${tournamentId}`,
            { screen: `/tournament/${tournamentId}` }
        );
        
        const mainContent = document.getElementById('main-content');

        const tournamentName = tournament.name;
        const players = tournament.players;
        const leaderboard = tournament.leaderboard;
        const status = tournament.status;
        const poolSize = tournament.pool_size;

        mainContent.innerHTML = `
        <div id="mainContentWrapper">
            <div class="wrapper w-100">
                <div class="card mb-4 w-100">
                    <div class="card-header" 
                        style="background-color: #6c757d;">
                        <h5 class="mb-0 text-white">${tournamentName}</h5>
                    </div>
                    <div class="card-body text-center">
                        <div id="tournament-leaderboard"></div>
                        <div class="d-flex justify-content-center mb-2"></div>
                            <button
                                id="leave-tournament"
                                class="btn btn-secondary
                                btn-lg me-2 mt-2 d-none"
                            >
                                ${translate("Leave tournament")}
                            </button>
                            <button
                                id="join-tournament"
                                class="btn btn-secondary
                                btn-lg me-2 mt-2 d-none"
                            >
                                ${translate("Join tournament")}
                            </button>
                            <button
                                id="back-to-tournaments"
                                class="btn btn-secondary btn-lg me-2 mt-2"
                            >
                                ${translate("Back to tournaments")}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;

        resizeWindow();

        const player = user.name;
        if (players.includes(player)) {
            document.getElementById(
                'leave-tournament').classList.remove('d-none');
        } else {
            document.getElementById(
                'join-tournament').classList.remove('d-none');
        }

        if (status === 'in_progress' || status === 'finished') {
            document.getElementById(
                'join-tournament').classList.add('d-none');
            document.getElementById(
                'leave-tournament').classList.add('d-none');
        }

        const leaderboardTable = document.getElementById(
            'tournament-leaderboard');
        leaderboardTable.innerHTML = `
                <h5 class="card-title text-center" id="leaderboard-title">
                ${translate("Leaderboard")}
                </h5>
                <table class="table table-striped table-bordered table-hover">
                    <thead>
                        <tr>
                            <th scope="col">${translate("Rank")}</th>
                            <th scope="col">${translate("Player")}</th>
                            <th scope="col">${translate("Score")}</th>
                        </tr>
                    </thead>
                    <tbody id="leaderboard-rows"></tbody>
                </table>`;

        const leaderboardRows = document.getElementById('leaderboard-rows');

        const displayNames = await getDisplaynames(players);
        const displayNamesMap = {};
        displayNames.displaynames.forEach((displayName, index) => {
            displayNamesMap[players[index]] = displayName;
        });

        if (leaderboard.length === 0) {
            for (let i = 0; i < poolSize; i++) {
                const row = document.createElement('tr');
                if (players.length <= i) {
                    row.innerHTML = `
                        <td>${i + 1}</td>
                        <td>${translate("Waiting for player")}</td>
                        <td>0</td>`;
                } else {
                    row.innerHTML = `
                        <td>${i + 1}</td>
                        <td>${displayNamesMap[players[i]]}</td>
                        <td>0</td>`;
                }
                leaderboardRows.appendChild(row);   
            }
        } else {
            leaderboard.forEach((player, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${displayNamesMap[player.player_name]}</td>
                    <td>${player.points}</td>`;
                leaderboardRows.appendChild(row);
            }
            );
            document.getElementById(
                'leaderboard-title'
            ).innerText = `${translate("Leaderboard")} - ${translate(status)}`;
        }

        document.getElementById(
            'join-tournament').addEventListener('click', async () => {
            await joinTournament(tournamentId);
            document.getElementById('join-tournament').classList.add('d-none');
            document.getElementById(
                    'leave-tournament').classList.remove('d-none');
            loadTournamentDataScreen(tournamentId);
        });

        document.getElementById('leave-tournament').addEventListener(
            'click', async () => {
            await leaveTournament(tournamentId);
            document.getElementById(
                'leave-tournament').classList.add('d-none');
            document.getElementById(
                'join-tournament').classList.remove('d-none');
            loadTournamentDataScreen(tournamentId);
        });

        document.getElementById('back-to-tournaments').addEventListener(
            'click', () => {
            onlineArena();
        });

    } catch (error) {
        console.error(error);
    }
}
