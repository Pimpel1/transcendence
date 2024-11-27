import { arena } from './arena.js';
import { loadDashboard } from './dashboard.js';
import { localArena } from './local_arena.js';
import { loadGameDetailsScreen } from './listings/game_details.js';
import { loadListingsScreen } from './listings/listings.js';
import { loadTournamentDetailsScreen } from './listings/tournament_details.js';
import { loadPlayerDetailsScreen } from './listings/player_details.js';
import { login, logout, twoFactorAuthScreen } from './login.js';
import { editProfileScreen } from './profile.js';
import { updateHistory } from './utils.js';
import { localGameScreen } from './game/local_game.js';
import { localTournamentScreen } from './game/local_tournament.js';
import { onlineGameScreen } from './game/online_game.js';
import { onlineTournamentScreen } from './game/online_tournament.js';
import { userProfileScreen } from './profile.js';
import { onlineArena } from './online_arena.js';
import { 
    loadCreateTournamentScreen,
    loadTournamentDataScreen
 } from './tournament.js';

const routes = () => ({
    '/login': login,
    '/logout': logout,
    '/auth-failure': localArena,
    '/arena': arena,
    '/auth-success': loadDashboard,
    '/two-factor-auth': twoFactorAuthScreen,
    '/local-game': localGameScreen,
    '/online-game': onlineGameScreen,
    '/local-tournament': localTournamentScreen,
    '/online-tournament': onlineTournamentScreen,
    '/home': arena,
    '/listings': loadListingsScreen,
    '/game-details': loadGameDetailsScreen,
    '/tournament-details': loadTournamentDetailsScreen,
    '/player-details': loadPlayerDetailsScreen,
    '/edit-profile': editProfileScreen,
    '/dashboard': loadDashboard,
    '/local-arena': localArena,
    '/online-arena': onlineArena,
    '/create-tournament': loadCreateTournamentScreen,
});

function userProfileRouteHandler(username) {
    const allUsers = JSON.parse(localStorage.getItem('allusers')) || [];
    const otherUser = allUsers.find(user => user.username === username);

    if (otherUser) {
        userProfileScreen(otherUser);
    } else {
        console.error('User not found');
        arena();
    }
}

function getRouteHandler(path) {
    const routeHandlers = routes();

    // Direct route matches
    if (routeHandlers[path]) {
        return routeHandlers[path];
    }

    // Handle dynamic routes
    const userProfileMatch = path.match(/^\/user-profile\/(.+)/);
    const tournamentDetailMatch = path.match(/^\/tournament\/(.+)/);
    if (userProfileMatch) {
        const username = userProfileMatch[1];
        return () => userProfileRouteHandler(username);
    } else if (tournamentDetailMatch) {
        const id = tournamentDetailMatch[1];
        return () => loadTournamentDataScreen(id);
    }

    return arena;
}

export function handleRouting() {
    const path = window.location.pathname;
    updateHistory(path, path, { screen: path });
    const routeHandler = getRouteHandler(path);
    routeHandler();
}

export function handleClick(event) {
    const link = event.target.closest('a');
    if (
        link &&
        (link.classList.contains('nav-link') ||
            link.classList.contains('navbar-brand'))
    ) {
        const path = link.getAttribute('href');

        if (path && path !== '#') {
            event.preventDefault();
            updateHistory(path, path, { screen: path });
            handleRouting();
        }
    }
}
