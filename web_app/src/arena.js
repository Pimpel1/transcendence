import {
    createButton,
    isAuthenticated,
    resizeWindow,
    updateHistory,
} from './utils.js';
import { localArena } from './local_arena.js';
import { onlineArena } from './online_arena.js';


export async function arena() {
    updateHistory(
        '/arena',
        '/arena',
        { screen: '/arena' }
        );

    const authenticated = await isAuthenticated();
    if (!authenticated) {
        console.log('User not authenticated. Redirecting to Local Arena.');
        localArena();
        return;
    }

    const mainContent = document.getElementById('main-content');

    const homeHtml = `
        <div id="mainContentWrapper">
            <div class="description">
                <h1>Pong</h1>
                ${createButton('localGameButton', 'Local')}
                ${createButton('onlineGameButton', 'Online')}
            </div>
        </div>
    `;

    mainContent.innerHTML = homeHtml;
    resizeWindow();

    // Button Event listeners ************************************************
    document.getElementById('localGameButton')
        .addEventListener('click', localArena);
    document.getElementById('onlineGameButton')
        .addEventListener('click', onlineArena);
}
