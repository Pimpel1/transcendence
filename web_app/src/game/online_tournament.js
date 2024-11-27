import { showMessage } from '../utils.js';
import { createTournament } from '../api/matchmaker-service.js';
import user from '../User.js';

export async function onlineTournamentScreen(
    playerName, tournamentName, poolSize
) {
    if (!playerName || playerName.length === 0) {
        playerName = null;
    }
    if (!tournamentName || tournamentName.length === 0) {
        tournamentName = null;
    }

    console.log(
        `Loading online tournament screen for tournament: ${
            tournamentName ? tournamentName : 'Undefined Tournament'
        } for ${poolSize} players${
            playerName ? `. Joining: ${playerName}` : '.'
        }`
    );
    try {
        tournament = await createTournament({
            tournament_name: tournamentName,
            pool_size: poolSize,
            players: playerName ? [playerName] : [],
            type: 'online',
        });
        showMessage(
            `Tournament created successfully (ID: ${tournament.id})`,
            'success'
        );
    } catch (error) {
        console.error('Error:', error);
    }

    if (playerName) {
        const player = user.getPlayer();
        player.name = playerName;
    }
}
