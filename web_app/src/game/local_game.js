import { PongGame } from './PongGame.js';
import { Player } from './Player.js';
import { createGame } from '../api/matchmaker-service.js';
import {
    translate,
    setPongFrame,
    showMessage,
    setupGameScreenContinueListener
} from '../utils.js';
import user from '../User.js';
import { localArena } from '../local_arena.js';


export function localGameScreen(
    player1Name = 'player1', player2Name = 'player2', fromForm = false
) {
    console.log(`Loading local game screen: ${player1Name} vs ${player2Name}`);

    setPongFrame();

    if (user.player.gameSocket !== null){
        resumeGame();
    }
    else if (fromForm){
        startLocalGame(player1Name, player2Name);
    }
    else {
        localArena();
        showMessage(
            `${translate('The game you are trying to access had ended')}`,
            'error'
        );
    }
}

function resumeGame(){
    user.player.pongGame.reinit('pongCanvas');
}

async function startLocalGame(player1Name, player2Name) {
    let pongGame = new PongGame('pongCanvas');
    const player1 = new Player(player1Name);
    const player2 = user.player;
    player2.name = player2Name;

    player2.registerGameInfos(
        player1Name,
        player2Name
    );
    player2.displayNames();

    player1.joinGame(pongGame);
    player2.joinGame(pongGame);

    player2.setEndgameCallback(setupGameScreenContinueListener);

    try {
        const { game_details: { id, player1_position, player2_position } } =
            await createGame({
                player1: player1.name,
                player2: player2.name,
                type: 'local',
            });

        player1.connectToGame(id, player1_position);
        player2.connectToGame(id, player2_position);

    } catch (error) {
        console.error('Error:', error);
    }
}
