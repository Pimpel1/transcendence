import user from "./User.js";
import { userProfileScreen } from './profile.js';
import { arena } from "./arena.js";
import { getTranslation } from "./api/translation-service.js";
import { isHealthy as gameServiceIsHealthy } from "./api/game-service.js";
import { 
    validateJwt,
    isHealthy as authServiceIsHealthy 
} from "./api/auth-service.js";
import { 
    getUserList,
    isHealthy as userManagementIsHealthy 
} from "./api/user-management.js";
import { 
    deleteGame  as matchmakerDeleteGame,
    getMyGames as matchmakerGetMyGames,
    isHealthy as matchmakerServiceIsHealthy 
} from "./api/matchmaker-service.js";
import { 
    isHealthy as translationServiceIsHealthy 
} from "./api/translation-service.js";
import { logout } from "./login.js";

export function isAuthenticated() {
    return validateJwt()
        .then((result) => result.authenticated)
        .catch(() => false);
}

export function updateHistory(url, title, state) {
  if (window.location.pathname !== url) {
        history.pushState(state, title, url);
    }
}

export function translate(key) {
    const translations = JSON.parse(localStorage.getItem('translations'));
    if (!translations) {
        console.error('Translations not found in local storage');
        return key;
    }
    return translations[key] ? translations[key] : key;
}

export async function setLanguage(language) {
    console.log('Setting User language:', language);
    try {
        const translation = await getTranslation(language);
        localStorage.setItem('translations', JSON.stringify(translation));

        document.getElementById(
            'loginButton').textContent = translate("Sign In");
        document.getElementById(
            'arenaButton').textContent = translate("Play");
        document.getElementById(
            'dashboardButton').textContent = translate("Profile");
        document.getElementById(
            'logoutButton').textContent = translate("Sign Out");
    } catch (error) {
        throw new Error(`Error getting translations: ${error}`);
    }
}

export async function setAllUsers() {
    const data = await getUserList();

    const friendRequests = JSON.stringify(data.friend_requests);

    localStorage.setItem('allusers', JSON.stringify(data.users));
    localStorage.setItem('friend_requests', friendRequests);
    localStorage.setItem('friends', JSON.stringify(data.friends));
}

export function showMessage(message, type) {
    const mainContentWrapper = document.getElementById('mainContentWrapper');
    let messageDiv = document.getElementById('message');

    if (!messageDiv) {
        messageDiv = document.createElement('div');
        messageDiv.id = 'message';
        messageDiv.classList.add('mt-3', 'text-center');
        mainContentWrapper.insertBefore(
            messageDiv, mainContentWrapper.firstChild
        );
    }

    messageDiv.innerHTML = `
        <div class="alert alert-${type}" role="alert">
            ${message}
        </div>
    `;
    setTimeout(hideMessage, 5000);
}

function hideMessage() {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.innerHTML = '';
    }
}

export function generateRankingsString(leaderboard, displaynames=null) {
    let str = '';
    for (let rank = 0; rank < leaderboard.length; rank++) {
        const player = leaderboard[rank];
        const name = displaynames ?
            displaynames.displaynames[rank] : player.player_name;
        str += `<br><br>${rank + 1}. ${name}:` +
            ` ${player.points} pts`;
    }
    return str;
}

export function createButton(id, text) {
    return `
        <button id="${id}" class="btn btn-secondary btn-lg mt-3"
                style="min-width: 374px;">
            ${translate(text)}
        </button>
    `;
}

export function createFormInput(
    id, label, value = '', type = 'text', attributes = {}
) {
    const attributeString = Object.entries(attributes)
        .map(([key, value]) => `${key}="${value}"`)
        .join(' ');

    return `
        <div class="form-group">
            <label for="${id}" style="color: #b2b4b1;">
                ${translate(label)}:
            </label>
            <input type="${type}" id="${id}" class="form-control"
                   value="${translate(value)}" required ${attributeString}>
        </div>
    `;
}

export function createForm(id, inputs, buttonText, extraDivs = []) {
    return `
        <form id="${id}" class="mt-3 d-none">
            ${inputs.map(input => createFormInput(...input)).join('')}
            ${extraDivs.map(divName => `<div id="${divName}"></div>`).join('')}
            <button type="submit" class="btn btn-primary"
                    style="margin-top: 8px;">
                ${translate(buttonText)}
            </button>
        </form>
    `;
}

export function toggleVisibility(elementIdsToShow, elementIdsToHide) {
    elementIdsToHide.forEach(id => {
        document.getElementById(id).classList.add('d-none');
    });
    elementIdsToShow.forEach(id => {
        document.getElementById(id).classList.remove('d-none');
    });
}

export function checkCookiesAndLocalStorage() {
    const message = document.getElementById('main-content');
    try {
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        const isCookieEnabled = navigator.cookieEnabled;
        if (!isCookieEnabled) {
            message.innerHTML = `
            <div class="alert alert-danger">
                Cookies are not enabled. Please enable them to use this
                application.
            </div>
        `;
        }
    } catch (e) {
        message.innerHTML = `
        <div class="alert alert-danger">
            Local storage is not available. Please enable it to use this
            application.
        </div>
    `;
    }
}

export function setPongFrame() {
    if (isGameScreenActive()) {
        return ;
    }
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
        mainContent.innerHTML = `
            <div id=mainContentWrapper>
                <div id="pongFrame" class="pong-frame">
                    <div class="player-info">
                        <span id="leftPlayer"></span>
                        <span id="tournamentInfo"></span>
                        <span id="rightPlayer"></span>
                    </div>
                    <div class="status">
                        <span id="status"></span>
                    </div>
                    <div id="canvas" class="canvas-container">
                        <canvas id="pongCanvas"></canvas>
                    </div>
                </div>
            </div>
        `;
        resizeWindow();
    }
}

export function generateFillingButton(timeout, text) {
    const overlayButton = document.createElement('button');
    overlayButton.id = 'filling-button';
    overlayButton.className = 'overlay-button';
    overlayButton.textContent = text;
    document.body.appendChild(overlayButton);

    const fillDiv = document.createElement('div');
    fillDiv.id = 'filling-div';
    fillDiv.className = 'fill-div';
    fillDiv.style.animationDuration = `${timeout}s`;
    overlayButton.appendChild(fillDiv);
    return overlayButton;
}


export function showNotification(message, type='dark') {
    user.player.statusInfos = message;

    if (!document.getElementById('status')) { return; }
    if (!document.getElementById('pongFrame')) { 
        setPongFrame();
    }
    document.getElementById('status').innerHTML = message;
}

export function sanitizeInput(input, maxLength = 20) {
    const div = document.createElement('div');
    div.innerText = input.trim();
    const sanitized = div.innerHTML;
    return sanitized.substring(0, maxLength);
}

export async function backendIsHealthy() {
    const serviceChecks = [
        authServiceIsHealthy(),
        userManagementIsHealthy(),
        matchmakerServiceIsHealthy(),
        gameServiceIsHealthy(),
        translationServiceIsHealthy(),
    ];
    
    const health = await Promise.all(serviceChecks);
    return health.every(isHealthy => isHealthy);
}

export function periodicBackendHealthCheck() {
    console.log('Starting periodic backend health check');
    const interval = 5000;
    const intervalId = setInterval(async () => {
        const isHealthy = await backendIsHealthy();
        if (!isHealthy) {
            showSpinner();
            clearInterval(intervalId);
            waitForBackendHealth();
        }
    }, interval);
}

export async function waitForBackendHealth() {
    console.info('Backend is experiencing issues. Waiting for recovery...');
    const interval = 1000;
    const intervalId = setInterval(async () => {
        const isHealthy = await backendIsHealthy();
        if (isHealthy) {
            await logout();
            await arena();
            hideSpinner();
            showMessage(
                `${translate(
                    'Service has been restored. ' +
                    'We apologize for the earlier disruption.'
                )}`,
                'warning'
            );
            clearInterval(intervalId);
            periodicBackendHealthCheck();
        }
    }, interval);
}

export function showSpinner(
    element = document.getElementById('spinner-container')
) {
    element.style.display = 'flex';
}

export function hideSpinner(
    element = document.getElementById('spinner-container')
) {
    element.style.display = 'none';
}

export function appendSpinner(htmlElement) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border text-secondary';
    spinner.setAttribute('role', 'status');
    htmlElement.appendChild(spinner);
    return spinner;
}

export function resizeWindow() {
    const navbar = document.querySelector('.navbar');
    const navbarHeight = navbar ? navbar.offsetHeight : 0;
    const wrapper = document.getElementById('mainContentWrapper');
    const pongframe = document.getElementById('pongFrame');
    if (wrapper) {
        wrapper.style.minHeight = `${
            window.innerHeight - navbarHeight
        }px`;
    }
    if (pongframe) {
        const maxHeight = window.innerHeight - navbarHeight - 100;
        const maxWidth = window.innerWidth - 100;
        if ((maxHeight - 20) / maxWidth < 0.75) {
            pongframe.style.height = maxHeight + 'px';
            pongframe.style.width = (
                pongframe.clientHeight - 20
            ) / 0.75 + 'px';
        }
        else {
            pongframe.style.width = maxWidth + 'px';
            pongframe.style.height = (
                ((pongframe.clientWidth) * 0.75) + 20
            ) + 'px';
        }
        pongframe.width = window.innerWidth-120;
        pongframe.height = window.innerHeight - navbarHeight-120;
    }
}

export function isGameScreenActive() {
    return document.getElementById('pongFrame') !== null;
}

export function setupGameScreenContinueListener(callback=arena){
    showNotification(
        `${translate('Press any key to continue')}`
    );
    const handleKeyDown = () => {
        if (isGameScreenActive()) {
            if (user.player.pongGame) {
                user.player.pongGame.clear();
            }
            user.player.waitingToContinue = false;
            user.player.unsetLiveButton();
            window.removeEventListener('keydown', handleKeyDown);
            callback();
        }
    };
    user.player.waitingToContinue = true;
    if (!user.player.liveButton) {
        user.player.setLiveButton();
    }
    window.addEventListener('keydown', handleKeyDown);
}

export function createClickableUser(usr, message, userList) {
    const userDiv = document.createElement('div');
    userDiv.className = 'd-flex align-items-center mb-3';

    const img = document.createElement('img');
    img.src = `data:image/jpeg;base64,${usr.avatar}`;
    img.alt = usr.displayname;
    img.className = 'rounded-circle img-fluid me-3';
    img.style.width = '50px';

    const button = document.createElement('button');
    button.className = 'btn btn-link p-0';
    button.textContent = message;

    button.addEventListener('click', () => {
        userProfileScreen(usr);
    });

    userDiv.appendChild(img);
    userDiv.appendChild(button);

    userList.appendChild(userDiv);
}

export async function userIsBusy() {
    let game;
    try {
        game = await matchmakerGetMyGames(
            'status=waiting_for_players&joined=true'
        );
    }
    catch {
        game = [];
    }
    return !!(
        user.player.gameSocket ||
        user.player.tournamentSession ||
        user.player.waitingToContinue ||
        game.length
    );
}

export function fillingButtonIsActive() {
    const fillingButton = document.getElementById('filling-button');
    return !!(fillingButton);
}

export async function deleteOngoingGame() {
    let game;
    try {
        game = await matchmakerGetMyGames(
            'status=waiting_for_players&joined=true'
        );
        if (!game.length)
            return ;
    }
    catch {
        game = [];
    }
    if (game[0]) {
        await matchmakerDeleteGame(game[0].id);
    }
}
