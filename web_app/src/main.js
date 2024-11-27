import { handleRouting, handleClick } from './routing.js';
import { 
    checkCookiesAndLocalStorage,
    deleteOngoingGame,
    hideSpinner,
    periodicBackendHealthCheck,
    resizeWindow
} from './utils.js';
import { loadCsrfTokens } from './csrf.js';
import { twoFactorAuthScreen } from './login.js';
import { login } from './login.js';
import { arena } from './arena.js';
import { loadDashboard } from './dashboard.js';
import { logout } from './login.js';
import user from './User.js';

document.addEventListener("DOMContentLoaded", () => {
    const spinnerContainer = document.getElementById('spinner-container');
    const mainContent = document.getElementById('main-content');
    const loginButton = document.getElementById('loginButton');
    const arenaButton = document.getElementById('arenaButton');
    const dashboardButton = document.getElementById('dashboardButton');
    const logoutButton = document.getElementById('logoutButton');

    checkCookiesAndLocalStorage();
    user.initialize();

    loginButton.addEventListener('click', login);
    arenaButton.addEventListener('click', arena);
    dashboardButton.addEventListener('click', loadDashboard);
    logoutButton.addEventListener('click', logout);
    window.addEventListener('popstate', handleRouting);
    window.addEventListener('click', handleClick);
    window.addEventListener('resize', resizeWindow);
    window.addEventListener('beforeunload', async () => {
        await deleteOngoingGame();
    });

    loadCsrfTokens().finally(() => {
        user.initialize().finally(() => {
            hideSpinner(spinnerContainer);
            mainContent.style.display = 'block';
            if (window.location.pathname === '/two-factor-auth') {
                twoFactorAuthScreen();
            }
            else {
                arena();
            }
            periodicBackendHealthCheck();
        });
    });
});
