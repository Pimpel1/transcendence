import {
    appendSpinner,
    hideSpinner,
    showSpinner,
    translate
} from './utils.js';
import { getPlayerStats } from './api/matchmaker-service.js';
import { getDisplaynames } from './api/user-management.js';


export async function loadMatchHistoryList(username) {
    try {
        const matchList = document.getElementById('match-history');
        const spinner = appendSpinner(matchList);
        showSpinner(spinner);

        const stats = await getPlayerStats(
            username, 'limit=5&status=finished'
        );

        matchList.innerHTML = '';

        if (stats.games.length === 0) {
            matchList.innerHTML = `
                <p>${translate("No match history available")}</p>`;
        } else {
            console.log("Match history data:", stats);
            matchList.innerHTML = `
                <h5 class="card-title text-center">
                ${translate("Match History")}
                </h5>
                <table class="table table-striped table-bordered table-hover">
                    <thead>
                        <tr>
                            <th scope="col">${translate("Date")}</th>    
                            <th scope="col">${translate("Player 1")}</th>
                            <th scope="col">${translate("Player 2")}</th>
                            <th scope="col">${translate("Score")}</th>
                            <th scope="col">${translate("Winner")}</th>
                        </tr>
                    </thead>
                    <tbody id="matchhistory-rows"></tbody>
                </table>
            `;
            const matchHistoryRows = document.getElementById(
                                            'matchhistory-rows');

            for (const game of stats.games) {
                const date = game.date.split('T')[0];
                const player1 = game.player1_name;
                const player2 = game.player2_name;
                const winner = game.winner_name;
                const displaynames = await getDisplaynames(
                                        [player1, player2, winner]);
                const player1Score = game.player1_score;
                const player2Score = game.player2_score;
				if (winner === null) displaynames.displaynames[2] = "-";

                matchHistoryRows.innerHTML += `
                    <tr>
                        <td>${date}</td>    
                        <td>${displaynames.displaynames[0]}</td>
                        <td>${displaynames.displaynames[1]}</td>
                        <td>${player1Score}-${player2Score}</td>
                        <td>${displaynames.displaynames[2]}</td>
                    </tr>
                `;
            }
        }
        hideSpinner(spinner);
    } catch (error) {
        console.error('Error fetching match history:', error);
    }
}
