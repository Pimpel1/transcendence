import user from '../User.js';
import { setupGameScreenContinueListener } from '../utils.js';

export function onlineGameScreen(player2Name) {
    const player = user.player;
    player.resetControls('ArrowUp', 'ArrowDown');

    player.registerGame(player2Name);
    player.setEndgameCallback(setupGameScreenContinueListener);
}
