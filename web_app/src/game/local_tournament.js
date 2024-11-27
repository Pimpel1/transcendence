import { Player } from './Player.js';
import { 
    generateRankingsString,
    isGameScreenActive,
    setPongFrame,
    setupGameScreenContinueListener,
    showNotification,
    translate
} from '../utils.js';
import {
    createTournament,
    getTournamentDetails,
    startGame
} from '../api/matchmaker-service.js';
import { arena } from '../arena.js';
import user from '../User.js';
import { TournamentSession } from './TournamentSession.js';


export async function localTournamentScreen(playerNames, tournamentName) {
    console.log(
        `Loading local tournament screen with players: ` +
        `${playerNames.join(', ')}`
    );

    const players = playerNames.map(name => new Player(name));

    try{
        const tournament = await createTournament({
            pool_size: players.length,
            tournament_name: tournamentName,
            players: playerNames,
            type: 'local',
        });
        playLocalTournament(tournament.tournament_details, players);
    } catch (error) {
        console.error('Error:', error);
    }
}

function playLocalTournament(tournamentDetails, players) {
    const { games } = tournamentDetails;
    const allGames = games.flatMap(round => round.games);

    setPongFrame();

    function getReadyNextGame(index) {
        if (index >= allGames.length) {
            handleEndTournament(tournamentDetails.id);
            return;
        }

        const game = allGames[index];
        const { name } = game;

        showNotification(
            name + `<br><br>${translate('Press any key to continue')}`
        );

        const player1 = players.find(player => player.name === game.player1);
        const player2 = user.player;
        player2.tournamentSession = new TournamentSession(tournamentDetails);
        player2.name = game.player2;
        player2.setLiveButton();

        function onKeyDown(
            game, name, player1, player2, tournamentDetails, index
        ) {
            if (isGameScreenActive()) {
                user.player.statusInfos = '';
                playNextGame(
                    game, name, player1, player2, tournamentDetails, index
                );
                window.removeEventListener('keydown', handleKeyDown);
            }
        }
        function handleKeyDown(event) {
            onKeyDown(game, name, player1, player2, tournamentDetails, index);
        }
        window.addEventListener('keydown', handleKeyDown);
    }

    function playNextGame(
        game, gameName, player1, player2, tournamentDetails, index
    ) {
        console.log(
            `Starting game "${player1.name} vs ${player2.name}" ` +
            `(ID: ${game.id})`
          );

        player2.registerGameInfos(
            player1.name,
            player2.name,
            `${tournamentDetails.name}  |  ` +
            `${translate('Round')} ${game.round}`
        );
        player2.displayNames();

        startGame(game.id);

        [player1, player2].forEach((player, index) => {
            player.position = game[`player${index + 1}` + '_position'];
            player.setLocalDefaultControls(player.position);
            player.connectToGame(game.id, player.position);
        });

        let endGameHandled = false;

        const handleEndgame = () => {
            if (endGameHandled) return;
            endGameHandled = true;
            player2.clearNames();
            setupGameScreenContinueListener(() => {
                getReadyNextGame(index + 1);
            });
        };

        player1.setEndgameCallback(handleEndgame);
        player2.setEndgameCallback(handleEndgame);
    }

    async function handleEndTournament(id) {
        tournamentDetails = getTournamentDetails(id);

        const { winner, leaderboard } = await tournamentDetails;
        console.log(
            `id: ${id}` +
            `winner: ${winner}` +
            `tournamentdetails: ${tournamentDetails}`
        );
        const rankingString = generateRankingsString(leaderboard);
        showNotification(
            translate('Congratulations') + ' ' +
            winner + ', ' +
            translate('You won the tournament!') +
            rankingString +
            '<br><br>' + translate('Press any key to continue')
        );

        const handleKeyDown = () => {
            if (isGameScreenActive()) {
                window.removeEventListener('keydown', handleKeyDown);
                arena();
            }
        };
        window.addEventListener('keydown', handleKeyDown);

        user.player.unsetLiveButton();
        user.player.tournamentSession = null;
        user.player.statusInfos = '';
    }

    getReadyNextGame(0);
}
