import { localGameScreen } from './game/local_game.js';
import { localTournamentScreen } from './game/local_tournament.js';
import {
    createButton,
    createForm,
    createFormInput,
    resizeWindow,
    sanitizeInput,
    showMessage,
    toggleVisibility,
    translate,
    updateHistory,
    userIsBusy,
} from './utils.js';
import user from './User.js';

export function localArena() {
    updateHistory(
        '/local-arena',
        '/local-arena',
        { screen: '/local-arena' }
    );

    const mainContent = document.getElementById('main-content');

    const homeHtml = `
        <div id="mainContentWrapper">
            <div class="description">
                <h1>Pong</h1>
                ${createButton('localGameButton', 'Local Game')}
                ${createButton('localTournamentButton', 'Local Tournament')}
                ${createForm('localGameForm', [
                    ['player1Name', 'Player 1 Name', 'Player 1'],
                    ['player2Name', 'Player 2 Name', 'Player 2'],
                ], 'Start Game')}
                ${createForm('localTournamentForm', [
                    ['tournamentName', 'Tournament Name',
                        'Pong World Cup 2024'],
                    [
                        'poolSize',
                        'Pool Size',
                        '4', 'number',
                        { min: 2, max: 8 }
                    ],
                ], 'Start Tournament', ['playersContainer'])}
            </div>
        </div>
    `;

    mainContent.innerHTML = homeHtml;

    resizeWindow();

    const htmlElements = [
        'localGameButton',
        'localTournamentButton',
        'localGameForm',
        'localTournamentForm',
    ];

    // Button click handlers *************************************************
    function handleLocalGameButtonClick() {
        toggleVisibility(['localGameForm'], htmlElements);
    }

    function handleLocalTournamentButtonClick() {
        toggleVisibility(['localTournamentForm'], htmlElements);
        updatePlayerFields();
    }

    // Form submit handlers **************************************************
    async function handleLocalGameFormSubmit(event) {
        event.preventDefault();
        if (await userIsBusy()) {
            showMessage(
                `${translate("You can't create a local game")} ` +
                ` ${translate("because you're already involved elsewhere")}.`,
                `danger`
            );
            return;
        }
        const player1Name = sanitizeInput(
            document.getElementById('player1Name').value
        );
        const player2Name = sanitizeInput(
            document.getElementById('player2Name').value
        );

        if (player1Name && player2Name) {
            if (player1Name !== player2Name) {
                updateHistory(
                    '/local-game',
                    '/local-game',
                    { screen: '/local-game' }
                );
                localGameScreen(player1Name, player2Name, true);
            } else {
                showMessage(
                    `${translate('Please enter unique player names.')}`,
                    'danger'
                );
            }
        } else {
            showMessage(
                `${translate('Please enter both player names.')}`,
                'danger'
            );
        }
    }

    async function handleLocalTournamentFormSubmit(event) {
        event.preventDefault();
        if (await userIsBusy()) {
            showMessage(
                `${translate("You can't create a local tournament")} ` +
                ` ${translate("because you're already involved elsewhere")}.`,
                `danger`
            );
            return;
        }

        const poolSize = parseInt(
            document.getElementById('poolSize').value,
            10
        );
        const tournamentName = sanitizeInput(
            document.getElementById('tournamentName').value,
            30
        );

        const players = [];
        for (let i = 1; i <= poolSize; i++) {
            const playerName = sanitizeInput(
                document.getElementById(`tournamentPlayer${i}Name`).value
            );
            if (playerName) {
                players.push(playerName);
            }
        }

        if (players.length === poolSize) {
            if (new Set(players).size !== players.length) {
                showMessage(
                    `${translate('Please enter unique player names.')}`,
                    'danger'
                );
            } else {
                const button = event.target.querySelector('button');
                button.disabled = true;
                button.innerText = `${translate("Creating")}...`;

                updateHistory(
                    '/local-tournament',
                    '/local-tournament',
                    { screen: '/local-tournament' }
                );
                localTournamentScreen(players, tournamentName);
            }
        } else {
            showMessage(
                `${translate('Please enter all player names.')}`,
                'danger'
            );
        }
    }

    function handlePoolSizeInput() {
        updatePlayerFields();
    }

    function updatePlayerFields() {
        const poolSize = parseInt(
            document.getElementById('poolSize').value,
            10
        );

        if (poolSize < 2 || poolSize > 8) {
            showMessage(
                `${translate('Pool size must be between 2 and 8.')}`,
                'danger'
            );
            return;
        }

        const container = document.getElementById(
            'playersContainer'
        );
        container.innerHTML = '';
        for (let i = 1; i <= poolSize; i++) {
            const playerField = document.createElement('div');
            playerField.className = 'form-group';
            playerField.innerHTML = createFormInput(
                `tournamentPlayer${i}Name`,
                `Player ${i} Name`,
                `Player ${i}`
            );
            container.appendChild(playerField);
        }
    }

    // Button Event listeners ************************************************
    document.getElementById('localGameButton')
        .addEventListener('click', handleLocalGameButtonClick);
    document.getElementById('localTournamentButton')
        .addEventListener('click', handleLocalTournamentButtonClick);

    // Form Event listeners **************************************************
    document.getElementById('localGameForm')
        .addEventListener('submit', handleLocalGameFormSubmit);
    document.getElementById('localTournamentForm')
        .addEventListener('submit', handleLocalTournamentFormSubmit);

    // Other listeners *******************************************************
    document.getElementById('poolSize')
        .addEventListener('input', handlePoolSizeInput);

    updatePlayerFields();
}
