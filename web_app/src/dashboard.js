import { editProfileScreen } from './profile.js';
import { loadMatchHistoryList } from './matchhistory.js';
import {
    translate,
    updateHistory,
    isAuthenticated,
    resizeWindow,
} from './utils.js';
import { login } from './login.js';
import { arena } from './arena.js';
import { getPlayerDetails, getPlayerStats } from './api/matchmaker-service.js';
import { loadFriendsList } from './friends.js';
import user from './User.js';

export async function loadDashboard() {
    updateHistory(
        '/dashboard',
        '/dashboard',
        { screen: '/dashboard' }
        );

    const authenticated = await isAuthenticated();

    if (!authenticated) {
        console.log('User not authenticated. Redirecting to Login.');
        login();
        return;
    }

    const displayname = user.displayname;
    const avatar = `data:image/jpeg;base64,${user.avatar}`;
    
    await fetchAndStorePlayerStats(user.name);
    const wins = user.wins;
    const losses = user.losses;

    const mainContent = document.getElementById('main-content');

    mainContent.innerHTML = `
    <div id="mainContentWrapper">
        <div 
            class="wrapper w-100" 
            style="
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                align-items:
                center;
            "
        >
            <!-- User profile -->
            <div id="profileCard" class="card mb-4 w-100">
                <div class="card-header" style="background-color: #6c757d;">
                    <h5 class="mb-0 text-white">${translate("My profile")}</h5>
                </div>
                <div class="card-body text-center">
                    <img
                        src="${avatar}"
                        alt="avatar"
                        class="rounded-circle img-fluid"
                        style="width: 150px;"
                    >
                    <h5 class="my-3">${displayname}</h5>
                    <p class="text-muted mb-1">
                        ${translate("Wins and losses")}
                    </p>
                    <div class="d-flex justify-content-center mb-4">
                        <div class="me-3">
                            <div class="box green-box d-flex align-items-center
                                    justify-content-center">
                                <span class="text-white fs-4">${wins}</span>
                            </div>
                        </div>
                        <div>
                            <div class="box red-box d-flex align-items-center
                                    justify-content-center">
                                <span class="text-white fs-4">${losses}</span>
                            </div>
                        </div>
                    </div>
                    <div class="d-flex justify-content-center mb-2">
                        <button
                            id="edit-profile"
                            class="btn btn-secondary btn-lg me-2"
                        >
                            ${translate("Edit profile")}
                        </button>
                        <button
                            id="enter-arena"
                            class="btn btn-secondary btn-lg"
                        >
                            ${translate("Enter arena")}
                        </button>
                    </div>
                </div>
            </div>

            <!-- Friends List -->
            <div class="card mb-4 w-100 customList">
                <div class="card-header" style="background-color: #6c757d;">
                    <h5 class="mb-0 text-white">
                        ${translate("Friends List")}
                    </h5>
                </div>
                <div
                    class=
                        "card-body d-flex flex-column justify-content-center"
                    id="friends-list"
                    style="max-height: 3000px; overflow-y: auto;"
                >
                </div>
            </div>

            <!-- Match Result with Score -->
            <div class="card mb-4 w-100 customList">
                <div class="card-header" style="background-color: #6c757d;">
                    <h5 class="mb-0 text-white">
                        ${translate("Match Result")}
                    </h5>
                </div>
                <div 
                    class="
                        card-body 
                        d-flex 
                        flex-column 
                        justify-content-center"
                    id="match-history"
                >
                </div>
            </div>
        </div>
    </div>
    `;

    resizeWindow();

    document.getElementById('edit-profile').addEventListener('click', () => {
        editProfileScreen();
    });

    document.getElementById('enter-arena').addEventListener('click', () => {
        arena();
    });

    loadFriendsList();
    loadMatchHistoryList(user.name);
}

async function fetchAndStorePlayerStats(username) {
    try {

        const stats = await getPlayerStats(username);

        const totalWins = stats.total_wins;
        const totalLosses = stats.total_losses;

        user.wins = totalWins;
        user.losses = totalLosses;

        console.log('Player stats stored in User object: ' +
            { totalWins, totalLosses });
    } catch (error) {
        console.error('Failed to fetch and store player stats:', error);
    }
}
