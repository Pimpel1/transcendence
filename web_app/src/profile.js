import { loadDashboard } from './dashboard.js';
import { 
    toggleVisibility,
    resizeWindow,
    sanitizeInput,
    showMessage,
    translate,
    updateHistory, 
    showSpinner,
    hideSpinner,
    userIsBusy,
    fillingButtonIsActive
} from './utils.js';
import { deleteFriend } from './friends.js';
import { friendRequest, updateUser } from './api/user-management.js';
import user from './User.js';
import { getPlayerDetails } from './api/matchmaker-service.js';
import { onlineGameScreen } from './game/online_game.js';

export async function userProfileScreen(otherUser) {
    
    await user.initialize();

    const mainContent = document.getElementById('main-content');
    updateHistory(
        '/user-profile/' + otherUser.username,
        '/user-profile/' + otherUser.username,
        { screen: '/user-profile/' + otherUser.username }
    );
    const username = otherUser.username;
    
    const allUsers = JSON.parse(
        localStorage.getItem('allusers')) || [];
    const friendRequests = JSON.parse(
        localStorage.getItem('friend_requests')) || [];
    const friends = JSON.parse(
        localStorage.getItem('friends')) || [];
        
    let friend = false;
    otherUser = allUsers.find(
        otherUser => otherUser.username === username
    );
        
    if (!otherUser) {
        otherUser = friendRequests.find(
            otherUser => otherUser.username === username);
    }

    if (!otherUser) {
        otherUser = friends.find(otherUser => otherUser.username === username);
        friend = true;
    }

    const playerDetails = await getPlayerDetails(otherUser.username);
    const avatar = `data:image/jpeg;base64,${otherUser.avatar}`;
    const displayname = otherUser.displayname;
    const wins = playerDetails.total_wins;
    const losses = playerDetails.total_losses;

    mainContent.innerHTML = `
    <div id="mainContentWrapper">
        <div class="card mb-4 w-50 align-">
            <div class="card-header" style="background-color: #6c757d;">
                <h5 class="mb-0 text-white">
                ${displayname} ${" " + translate("Profilescreen")}
                </h5>
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
                ${translate("Status")}: 
                <i class="fas fa-circle" id="status-icon"></i> 
                <span id="status-text"></span>
                </p>

                <p class="text-muted mb-1">${translate("Wins and losses")}</p>
                <div class="d-flex justify-content-center mb-4">
                    <div class="me-3">
                        <div class="box green-box d-flex \
                        align-items-center justify-content-center">
                            <span class="text-white fs-4">${wins}</span>
                        </div>
                    </div>
                    <div>
                        <div class="box red-box d-flex \
                        align-items-center justify-content-center">
                            <span class="text-white fs-4">${losses}</span>
                        </div>
                    </div>
                </div>
                <div class="d-flex justify-content-center mb-2">
                    <button id="add-friend"
                            class="btn btn-secondary
                            btn-lg me-2 d-none">
                        ${translate("Add Friend")}
                    </button>
                    <button id="delete-friend"
                            class="btn btn-secondary
                            btn-lg me-2 d-none">
                        ${translate("Delete Friend")}
                    </button>
                    <button id="pending-request"
                            class="btn btn-secondary
                            btn-lg me-2 d-none">
                        ${translate("Sent friend request")}
                    </button>
                </div>
                <button id="challenge"
                        class="btn btn-secondary
                        btn-lg">
                    ${translate("Challenge to a match")}
                </button>
            </div>
        </div>
    </div>
    `;

    resizeWindow();
    
    if (friend) {
        const deleteFriendButton = document.getElementById('delete-friend');
        deleteFriendButton.classList.remove('d-none');
        deleteFriendButton.addEventListener('click', async () => {
            showSpinner();
            toggleVisibility([], ["delete-friend"]);
            const isDeleted = await deleteFriend(username);
            await userProfileScreen(otherUser);
            hideSpinner();
            if (isDeleted) {
                showMessage(
                    `${username}` +
                    ` ${translate("has been deleted from your friends list")}`,
                    'success'
                );
            }
            else {
                showMessage(`
                    ${translate("An unexpected error occurred " +
                        "while deleting the friend.")}`,
                    'danger');
            }
        });
    } else if (user.sent_request_to.includes(username)) {
        const pendingRequest = document.getElementById('pending-request');
        pendingRequest.classList.remove('d-none');
    } else {
        const addFriendButton = document.getElementById('add-friend');
        addFriendButton.classList.remove('d-none');
        addFriendButton.addEventListener('click', async () => {
            showSpinner();
            toggleVisibility([], ["add-friend"]);
            const isRequested = await sendFriendRequest(username);
            await userProfileScreen(otherUser);
            hideSpinner();
            if (isRequested) {
                showMessage(
                    `${translate("Friend request sent successfully!")}`,
                    'success'
                );
            }
            else {
                showMessage(`
                    ${translate(
                        "An error occurred while sending the friend request."
                    )}
                `,
                'danger');
            }
        });
    }

    let status = (playerDetails.connected === true);
    
    const statusIcon = document.getElementById('status-icon');
    const statusText = document.getElementById('status-text');
    const challengeButton = document.getElementById('challenge');

    if (status) {
        statusIcon.classList.add('text-success');
        statusText.textContent = translate("Online");
    } else {
        statusIcon.classList.add('text-danger');
        statusText.textContent = translate("Offline");
        challengeButton.disabled = true;
    }

    challengeButton.addEventListener('click', async () => {
        const player = await getPlayerDetails(username);

        if (!player.connected || fillingButtonIsActive()) {
            showMessage(
                `${translate("Something went wrong")} `,
                `danger`
            );
        }
        else if (await userIsBusy()) {
            showMessage(
                `${translate("You can't send a challenge")} ` +
                ` ${translate("because you're already involved elsewhere")}.`,
                `danger`
            );
        }
        else {
            showMessage(
                `${translate("Sending a challenge to")} ` +
                ` ${displayname}...`,
                `info`
            );
            onlineGameScreen(username);
        }
    });
}

async function sendFriendRequest(username) {
    try {
        await friendRequest(username);
        return true;
    } catch (error) {
        console.error('Error sending friend request:', error);
        return false;
    }
}

export function editProfileScreen() {
    updateHistory(
        '/edit-profile',
        '/edit-profile',
        { screen: '/edit-profile' }
    );
    const mainContent = document.getElementById('main-content');

    mainContent.innerHTML = `
    <div id="mainContentWrapper">
        <div class="card mb-4 w-50 align-">
            <div class="card-header" style="background-color: #6c757d;">
                <h5 class="mb-0">${translate("Update profile")}</h5>
            </div>
            <div class="card-body">
                <form>
                    <!-- Display Name Input -->
                    <div class="mb-3">
                        <label for="displayname" class="form-label">
                            ${translate("Display Name")}
                        </label>
                        <input
                            type="text"
                            class="form-control"
                            id="displayname"
                            placeholder=${translate("Enter your display name")}
                        >
                    </div>

                    <!-- Preferred Language Selection -->
                    <div class="mb-3">
                        <label for="preferredLanguage" class="form-label">
                            ${translate("Preferred Language")}
                        </label>
                        <select class="form-select" id="preferredLanguage">
                            <option value="english">
                            ${translate("English")}
                            </option>
                            <option value="french">
                            ${translate("French")}
                            </option>
                            <option value="dutch">
                            ${translate("Dutch")}
                            </option>
                        </select>
                    </div>

                    <!-- Avatar Upload -->
                    <div class="mb-3">
                        <label for="avatarUpload" class="form-label">
                            ${translate("Upload Avatar")}
                        </label>
                        <input class="form-control" type="file"
                            id="avatarUpload" accept="image/*">
                    </div>

                    <!-- Submit Button -->
                    <div class="d-flex justify-content-center mb-2">
                        <button id="submit" type="submit"
                            class="btn btn-secondary btn-lg me-2">
                            ${translate("Save")}
                        </button>
                        <button id="cancel" type="button"
                            class="btn btn-secondary btn-lg">
                            ${translate("Cancel")}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
`;

    resizeWindow();

    document.getElementById('cancel').addEventListener('click', () => {
        updateHistory('/dashboard', '/dashboard', { screen: '/dashboard' });
        loadDashboard();
    });

    document.getElementById('submit').addEventListener('click', () => {
        event.preventDefault();
        updateHistory('/dashboard', '/dashboard', { screen: '/dashboard' });
        validateUpdateProfileForm();
    });

}

async function validateUpdateProfileForm() {
    const displayname = sanitizeInput(
        document.getElementById('displayname').value, 30
    );
    const language = document.getElementById('preferredLanguage').value;
    const avatarFile = document.getElementById('avatarUpload').files[0];

    let avatarBase64 = null;
    let avatarMimeType = null;

    if (avatarFile) {
        const reader = new FileReader();
        reader.onload = () => {
            const base64Data = reader.result.split(',')[1];
            avatarMimeType = reader.result.split(';')[0].split(':')[1];
            avatarBase64 = `data:image/jpeg;base64,${base64Data}`;

            sendUpdateRequest();
        };
        reader.onerror = (error) => {
            console.error('Error reading file:', error);
        };

        reader.readAsDataURL(avatarFile);
    } else {
        sendUpdateRequest();
    }
    
    async function sendUpdateRequest() {
        try {
            await updateUser({
                displayname: displayname,
                language: language,
                avatar: avatarBase64
            });

            console.log('Info saved successfully.');
            await user.initialize();

            loadDashboard();
        } catch (error) {
            console.error('Error in sendUpdateRequest:', error);
            showMessage(`${translate('Something went wrong...')}`, 'danger');
        }
    }
}
