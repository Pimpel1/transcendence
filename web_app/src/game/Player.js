import { GameSocket } from "./GameSocket.js";
import { MatchmakerSocket } from "./MatchmakerSocket.js";
import { PongGame } from './PongGame.js';
import { TournamentSession } from './TournamentSession.js';
import {
    generateFillingButton,
    generateRankingsString,
    isGameScreenActive,
    setPongFrame,
    setupGameScreenContinueListener,
    showMessage,
    showNotification,
    toggleVisibility,
    translate,
    updateHistory,
    userIsBusy
} from '../utils.js';
import {
    getMyGames as getMatchmakerMyGames,
    createGame as createMatchmakerGame,
    createTournament as createMatchmakerTournament,
    joinTournament as joinMatchmakerTournament,
    deleteGame as deleteMatchmakerGame,
    getGameDetails as getMatchmakerGameDetails,
} from '../api/matchmaker-service.js';
import {
    getDisplaynames as getUsermanagementDisplaynames,
} from '../api/user-management.js';
import { logout } from '../login.js';
import { arena } from "../arena.js";

const DEFAULT_LOCAL_RIGHT_UP_KEY = 'ArrowUp';
const DEFAULT_LOCAL_RIGHT_DOWN_KEY = 'ArrowDown';
const DEFAULT_LOCAL_LEFT_UP_KEY = 'w';
const DEFAULT_LOCAL_LEFT_DOWN_KEY = 's';

export class Player {
    constructor(name, up=null, down=null, isUser=false) {
        this.name = name;
        this.up = up;
        this.down = down;
        this.data = null;
        this.pongGame = null;
        this.gameSocket = null;
        this.matchmakerSocket = null;
        this.gameId = null;
        this.position = null;
        this.endgameCallback = null;
        this.isUser = isUser;
        this.liveButton = null;
        this.player1Name = '';
        this.player2Name = '';
        this.tournamentInfos = '';
        this.statusInfos = '';
        this.tournamentSession = null;
        this.waitingToContinue = false;
    }

    setControls(up, down) {
        this.up = up;
        this.down = down;
    }

    setLocalDefaultControls(position) {
        const [up, down] = position === 'left' ?
            [DEFAULT_LOCAL_LEFT_UP_KEY, DEFAULT_LOCAL_LEFT_DOWN_KEY] :
            [DEFAULT_LOCAL_RIGHT_UP_KEY, DEFAULT_LOCAL_RIGHT_DOWN_KEY];

        this.setControls(up, down);
    }

    resetControls(up=null, down=null) {
        this.up = up;
        this.down = down;
    }

    joinGame(pongGame) {
        this.pongGame = pongGame;
    }

    leaveGame() {
        this.pongGame = null;
    }

    connectToGame(gameId, position) {
        console.log(`${this.name} connecting to game #${gameId}`);
        this.gameId = gameId;
        this.position = position;
        this.gameSocket = new GameSocket(
            this.gameId, this.position, this.up, this.down
        );
        this.setupGameSocketEventListeners();
        if (this.isUser) {
            this.setLiveButton();
        }
    }

    disconnectFromGame() {
        if (this.gameSocket) {
            console.log(
                `${this.name} disconnecting from game #${this.gameId}`
            );
            this.gameSocket.close();
            this.gameSocket = null;
            if (this.isUser && !this.tournamentSession) {
                this.unsetLiveButton();
            }
        }
    }

    setEndgameCallback(callback) {
        this.endgameCallback = callback;
    }

    connectToMatchmaker() {
        console.log(`${this.name} connecting to matchmaker-service`);
        this.matchmakerSocket = new MatchmakerSocket(this.name);
        this.setupMatchmakerSocketEventListeners();
    }

    disconnectFromMatchmaker() {
        if (this.matchmakerSocket){
            console.log(`${this.name} disconnecting from matchmaker-service`);
            this.matchmakerSocket.close();
            this.matchmakerSocket = null;
        }
    }

    setupGameSocketEventListeners() {
        this.gameSocket.onOpen(() => {
            console.log(`${this.name} connected to game-service`);
        });

        this.gameSocket.onMessage((e) => {
            this.handleGameMessage(e);
        });

        this.gameSocket.onClose(() => {
            this.cleanup();
            console.log(`${this.name} disconnected from game-service`);
        });

        this.gameSocket.onError((error) => {
            console.error(`${this.name} \
                experienced game-service error: ${error.message}`);
        });
    }

    setupMatchmakerSocketEventListeners() {
        this.matchmakerSocket.onOpen(() => {
            console.log(`${this.name} connected to matchmaker-service`);
        });

        this.matchmakerSocket.onMessage((e) => {
            this.handleMatchmakerMessage(e);
        });

        this.matchmakerSocket.onClose(() => {
            console.log(`${this.name} disconnected from matchmaker-service`);
            logout();
        });

        this.matchmakerSocket.onError((error) => {
            console.error(`${this.name} \
                experienced matchmaker-service error: ${error.message}`);
        });
    }

    displayStatus(msg) {
        this.statusInfos = msg;
        if (isGameScreenActive()) {
            const status = document.getElementById('status');
            if (status) {
                status.innerText = `
                    ${translate(msg)}
                `;
            }
        }
    }

    displayGame() {
        if (isGameScreenActive()) {
            const status = document.getElementById('status');
            if (status) {
                status.innerText = '';
            }
            const { width, height, paddleSize, ballSize } = this.data;
            let pongGame = new PongGame('pongCanvas');
            this.joinGame(pongGame);
            this.pongGame.initialise(width, height, paddleSize, ballSize);
        }
    }

    displayNames() {
        if (isGameScreenActive()) {
            document.getElementById(
                'leftPlayer'
            ).innerText = this.player1Name;
            document.getElementById(
                'rightPlayer'
            ).innerText = this.player2Name;
            document.getElementById(
                'tournamentInfo'
            ).innerText = this.tournamentInfos;
        }
    }

    clearNames() {
        if (isGameScreenActive()) {
            document.getElementById('leftPlayer').innerText = '';
            document.getElementById('rightPlayer').innerText = '';
            document.getElementById('tournamentInfo').innerText = '';
        }
    }

    registerGameInfos(player1Name, player2Name, tournamentInfos=null) {
        this.player1Name = player1Name;
        this.player2Name = player2Name;
        if (tournamentInfos) {
            this.tournamentInfos = tournamentInfos;
        }
    }

    handleGameMessage(e) {
        const data = JSON.parse(e.data);
        const { type } = data;

        try {
            if (type === 'initial_message') {
                 this.handleGameInitialMessage(data);
            } else if (type === 'update_message') {
                this.handleGameUpdateMessage(data);
            } else if (type === 'endgame_message') {
                this.handleGameEndgameMessage(data);
            }
        } catch (error) {
            console.error(`${this.name} \
                experienced game-service error: ${error}`);
        }
    }

    handleGameInitialMessage(data) {
        console.log(`${this.name} received initial message`);
        this.data = data;
        this.statusInfos = '';
        if (this.isUser && document.getElementById('pongCanvas')) {
            this.displayGame();
            this.displayNames();
        }
    }

    handleGameUpdateMessage(data) {
        const {
            ballX,
            ballY,
            paddleLeft,
            paddleRight,
            scoreLeft,
            scoreRight } = data;
        if (this.isUser && this.pongGame) {
            this.pongGame.render(
                paddleLeft, paddleRight, ballX, ballY, scoreLeft, scoreRight
            );
        }
    }

    async handleGameEndgameMessage(data) {
        if (this.isUser) {
            if (this.pongGame) {
                const endGameMessage = await this.getEndGameMessage();
                this.pongGame.endGameOverlay(endGameMessage);
            }
            else {
                showMessage(
                    `${translate('Your opponent forfeited the game.')}`,
                    'info'
                );
            }
        }

        this.cleanup();

        if (this.endgameCallback) {
            this.endgameCallback();
        }
    }

    async getEndGameMessage() {
        if (this.isUser && this.pongGame) {
            try {
                const game_details = await getMatchmakerGameDetails(
                    this.gameId
                );
                const { winner } = game_details;
                if (winner === null)
                    return "Game Over";
                else {
                    const displaynames = await getUsermanagementDisplaynames(
                        [winner]
                    );
                    return `${displaynames.displaynames[0]} wins!`;
                }
            }
            catch (error) {
                console.error(
                    `${this.name} failed to get game details;`, error
                );
                return '';
            }
        }
        return '';
    }

    handleMatchmakerMessage(e) {
        const data = JSON.parse(e.data);
        const { type } = data;

        try {
            if (type === 'game_start') {
                this.handleMatchmakerGameStartMessage(data);
            }
            else if (type === 'challenge') {
                this.handleMatchMakerChallengeMessage(data);
            }
            else if (type === 'tournament_start') {
                this.handleMatchmakerTournamentStartMessage(data);
            }
            else if (type === 'tournament_end') {
                this.handleMatchmakerTournamentEndMessage(data);
            }
            else if (type === 'tournament_update') {
                this.handleMatchmakerTournamentUpdateMessage(data);
            }

        } catch (error) {
            console.error(`${this.name} \
                experienced matchmaker-service error: ${error}`);
        }
    }

    async acceptChallenge(fillingButton, opponent_name, opponent_displayname) {
        if (this.isUser && await userIsBusy()) {
            showMessage(
                `${translate("You can't accept a challenge ")}` +
                ` ${translate("because you're already involved elsewhere")}.`,
                `danger`
            );
        }
        else {
            fillingButton.remove();

            const game = await getMatchmakerMyGames(
                'status=waiting_for_players'
            );
            if (!game.length) {
                showMessage(
                    `${translate("Something went wrong")}`,
                    `danger`
                );
                return ;
            }
            else {
                console.log(`Invitation of ${opponent_displayname} accepted`);
                this.setEndgameCallback(setupGameScreenContinueListener);
    
                this.resetControls('ArrowUp', 'ArrowDown');
                this.registerGame(opponent_name);
            }
        }
    }

    rejectChallenge(game_id, fillingButton, opponent_displayname) {
        if (document.body.contains(fillingButton)) {
            fillingButton.remove();
            deleteMatchmakerGame(game_id);

            showMessage(
                `${translate("You rejected the invitation of")}` +
                ` ${opponent_displayname}.`,
                'danger'
            );
        }
    }

    async handleMatchMakerChallengeMessage(data) {
        console.log(`${this.name} received Matchmaker 'challenge' message`);
        const { opponent_name, game_id } = data;
        const displaynames = await getUsermanagementDisplaynames(
            [opponent_name]);
        const opponent_displayname = displaynames.displaynames[0];

        const timeout = parseInt(window.config.gameConnectionTimeout);

        const fillingButton = generateFillingButton(
            timeout,
            `${translate("Accept challenge against")}` +
            ` ${opponent_displayname}.`
        );

        fillingButton.addEventListener('click', () => {
            this.acceptChallenge(
                fillingButton,
                opponent_name,
                opponent_displayname
            );
        });

        const rejectChallengeMethod = () => {
            this.rejectChallenge(
                game_id,
                fillingButton,
                opponent_displayname
            );
        };

        window.addEventListener('beforeunload', rejectChallengeMethod);
        window.addEventListener('pagehide', rejectChallengeMethod);
        setTimeout(rejectChallengeMethod, timeout * 1000);
    }

    async handleMatchmakerGameStartMessage(data) {
        console.log(`${this.name} received Matchmaker 'game_start' message`);
        const { game_id, player_position, opponent_name, game_details} = data;
        const timeout = parseInt(window.config.gameConnectionTimeout);
 
        const displaynames = await getUsermanagementDisplaynames(
            [game_details.player1, game_details.player2, opponent_name]);
        this.player1Name = displaynames.displaynames[0];
        this.player2Name = displaynames.displaynames[1];
        const opponent_displayname = displaynames.displaynames[2];

        const fillingButton = generateFillingButton(
            timeout,
            `${translate("Join game against")}` +
            ` ${opponent_displayname}.`
        );

        fillingButton.addEventListener('click', () => {
            fillingButton.remove();
            setPongFrame();
            this.displayStatus("Waiting for your opponent...");
            this.disconnectFromGame();
            this.connectToGame(game_id, player_position);
        });

        setTimeout(() => {
            if (document.body.contains(fillingButton)) {
                fillingButton.remove();
                showMessage(
                    `${translate("You forfeited the game against")}` +
                    ` ${opponent_name}.`,
                    'danger'
                );
            }
        }, timeout * 1000);
    }

    handleMatchmakerTournamentStartMessage(data) {
        const { tournament_id, tournament_details } = data;

        this.tournamentSession = new TournamentSession(tournament_details);

        console.log(
            `${this.name} received Matchmaker 'tournament_start' message` +
            ` (ID: ${tournament_id})`
        );
    }

    async handleMatchmakerTournamentEndMessage(data) {
        const { tournament_id, tournament_details } = data;

        this.tournamentSession.update(tournament_details);

        const displaynames = await getUsermanagementDisplaynames(
            this.tournamentSession.ranking
        );
        const rankingString = generateRankingsString(
            this.tournamentSession.leaderboard,
            displaynames
        );
        showNotification(
            displaynames.displaynames[0] + ' ' +
            translate('won the tournament!') +
            rankingString +
            '<br><br>' + translate('Press any key to continue')
        );

        this.unsetLiveButton();
        this.tournamentSession = null;

        const handleKeyDown = () => {
            if (isGameScreenActive()) {
                window.removeEventListener('keydown', handleKeyDown);
                arena();
            }
        };

        window.addEventListener('keydown', handleKeyDown);

        console.log(
            `${this.name} received Matchmaker 'tournament_end' message` +
            ` (ID: ${tournament_id})`
        );
    }

    handleMatchmakerTournamentUpdateMessage(data) {
        const { tournament_id, tournament_details} = data;

        if (this.tournamentSession)
            this.tournamentSession.update(tournament_details);

        console.log(
            `${this.name} received Matchmaker 'tournament_update' message` +
            ` (ID: ${tournament_id})`
        );
    }

    registerGame(opponent = null) {
        let opponentName;

        if (typeof opponent === 'string' && opponent.length > 0) {
            opponentName = opponent;
        } else if (typeof opponent === 'object' && opponent.name) {
            opponentName = opponent.name;
        } else {
            opponentName = '*anyone*';
        }

        console.log(`
            ${this.name} in the waiting room for game vs ${opponentName}
        `);

        const payload = {
            player1: this.name,
            ...(opponentName !== '*anyone*' ? { player2: opponentName } : {})
        };

        createMatchmakerGame(payload)
            .then(data => {
                const { game_details } = data;
                console.log(
                    `${this.name} successfully registered game ` +
                    `(ID: ${game_details.id})`
                );
            })
            .catch(error => {
                console.error(`${this.name} failed to register game;`, error);
            });
    }

    registerTournament(tournament_name, pool_size) {
        console.log(
            `${this.name} starting tournament for ${pool_size} players`
        );

        const payload = {
            player: this.name,
            pool_size: pool_size,
            tournament_name: tournament_name
        };

        createMatchmakerTournament(payload)
            .then(data => {
                const { message, tournament_url, tournament_details } = data;
                const tournament_id = tournament_details.id;
                console.log(
                    `${this.name} successfully registered tournament ` +
                    `(ID: ${tournament_id}, URL: ${tournament_url}, ` +
                    `Message: ${message})`
                );
                return tournament_id;
            })
            .catch(error => {
                console.error(
                    `${this.name} failed to register tournament;`, error
                );
            });
    }

    joinTournament(tournament_id) {
        joinMatchmakerTournament(tournament_id, this.name)
            .then(() => {
                console.log(
                    `${this.name} joined tournament (ID: ${tournament_id})`
                );
            })
            .catch(error => {
                console.error(
                    `${this.name} failed to join tournament;`, error
                );
            });
    }

    liveButtonClick() {
        updateHistory(
            '/local-game',
            '/local-game',
            { screen: '/local-game' }
        );
        if (this.statusInfos !== '') {
            setPongFrame();
            showNotification(this.statusInfos);
        }
        else {
            setPongFrame();
            this.displayGame();
            this.displayNames();
        }
    }

    setLiveButton() {
        if (this.isUser) {
            this.unsetLiveButton();
            if (this.liveButton === null) {
                this.liveButton = document.createElement('button');
                this.liveButton.id = 'live';
                this.liveButton.innerText = 'live';
                this.liveButton.classList.add(
                    'btn',
                    'btn-secondary',
                    'btn-sm',
                    'ms-2',
                    'me-2'
                );
                const dropdownIcon = document.querySelector(
                    '#navbarDropdown'
                ).parentElement;
                dropdownIcon.parentNode.insertBefore(
                    this.liveButton,
                    dropdownIcon
                );
            }
            toggleVisibility(['live'], []);
            this.liveButton.addEventListener(
                'click',
                this.liveButtonClick.bind(this)
            );
        }
    }

    unsetLiveButton() {
        if (this.isUser && this.liveButton !== null) {
            toggleVisibility([], ['live']);
            this.liveButton.removeEventListener(
                'click',
                this.liveButtonClick.bind(this)
            );
            this.liveButton.remove();
            this.liveButton = null;
        }
    }

    cleanup() {
        //this.registerGameInfos('', '', '');
        this.disconnectFromGame();
    }
}
