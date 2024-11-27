import {
    appendSpinner,
    hideSpinner,
    resizeWindow,
    showSpinner,
    translate,
    updateHistory,
    setAllUsers,
    createClickableUser
} from './utils.js';
import { 
    loadTournamentDataScreen,
    loadCreateTournamentScreen
} from './tournament.js';
import { getTournaments } from './api/matchmaker-service.js';


export function onlineArena() {
    updateHistory(
        '/online-arena',
        '/online-arena',
        { screen: '/online-arena' }
    );

    const mainContent = document.getElementById('main-content');

    mainContent.innerHTML = `
        <div id="mainContentWrapper">
            <div class="row">
                <div class="col-md-6 col-12">
                    <div class="card mb-4 w-100 customList">
                        <div class="card-header"
                        style="background-color: #6c757d;">
                            <h5 class="mb-0 text-white">
                            ${translate("All Users List")}
                            </h5>
                        </div>
                        <div class="card-body d-flex flex-column
                        justify-content-center"
                        id="users-list" style="max-height: 3000px;
                        overflow-y: auto;">
                        </div>
                    </div>
                </div>

                <!-- Tournaments List (50%) -->
                <div class="col-md-6 col-12">
                    <div class="card mb-4 w-100 customList">
                        <div class="card-header"
                            style="background-color: #6c757d;">
                            <h5 class="mb-0 text-white">
                            ${translate("Available Tournaments")}
                            </h5>
                        </div>
                        <div class="card-body d-flex flex-column
                                    justify-content-center"
                                    id="tournaments-list"
                                    style="max-height: 3000px;
                                    overflow-y: auto;">
                        </div>
                        <div class="d-flex justify-content-center mb-2">
                            <button id="create-tournament"
                                    class="btn btn-secondary
                                            btn-lg me-2">
                                ${translate("Create Tournament")}
                            </button>                    
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    resizeWindow();

    loadUsersList();
    loadAllTournaments();

    document.getElementById(
        'create-tournament').addEventListener('click', () => {
        loadCreateTournamentScreen();
    });
}

async function loadUsersList() {
    try {
        const usersList = document.getElementById('users-list');
        const spinner  = appendSpinner(usersList);
        showSpinner(spinner);

        await setAllUsers();
        const allUsers = JSON.parse(
            localStorage.getItem('allusers')) || [];
        const friendRequests = JSON.parse(
            localStorage.getItem('friend_requests')) || [];
        const friends = JSON.parse(
            localStorage.getItem('friends')) || [];

        usersList.innerHTML = '';

        friendRequests.forEach(usr => {
            
            const message = `${usr.displayname}` +
                `${translate(" (Wants to be friends with you)")}`;
            createClickableUser(usr, message, usersList);
        });

        friends.forEach(usr => {
        
            const message = `${usr.displayname}` +
                `${translate(" (Friend)")}`;
            createClickableUser(usr, message, usersList);
        });

        allUsers.forEach(usr => {
            
            const message = usr.displayname;
            createClickableUser(usr, message, usersList);
        });

        hideSpinner(spinner);
    } catch (error) {
        console.error('Error fetching users:', error);
    }
}

async function loadAllTournaments() {
    try {
        const tournamentsList = document.getElementById('tournaments-list');
        const spinner = appendSpinner(tournamentsList);
        showSpinner(spinner);

        const tournaments = await getTournaments('type=online');
        
        tournamentsList.innerHTML = '';
        if (tournaments.length === 0) {
            tournamentsList.innerHTML = `
            <p>
            ${translate("No tournaments available")}
            </p>`;
        } else {
            tournaments.forEach(tournament => {
                
                const tournamentDiv = document.createElement('div');
                tournamentDiv.className = 'd-flex align-items-center' +
                ' justify-content-between mb-3';

                const nameSpan = document.createElement('span');
                nameSpan.textContent = tournament.name +
                 ' (' + translate(tournament.status) + ')';

                const button = document.createElement('button');
                button.className = 'btn btn-secondary btn-lg mt-3';
                button.textContent = translate('Details');
                button.addEventListener('click', () => {
                    onTournamentClick(tournament.id);
                });

                tournamentDiv.appendChild(nameSpan);
                tournamentDiv.appendChild(button);
                tournamentsList.appendChild(tournamentDiv);
            }); 
        }
        hideSpinner(spinner);
    } catch (error) {
        console.error('Error fetching tournaments:', error);
    }
}

function onTournamentClick(tournamentID) {
    loadTournamentDataScreen(tournamentID);
}