import {
    appendSpinner,
    hideSpinner,
    showSpinner,
    translate,
    setAllUsers,
    createClickableUser
} from './utils.js';
import { removeFriend } from './api/user-management.js';
import user from './User.js';

export async function deleteFriend(username) {
    try {
        await removeFriend(username);

        const friends = user.friends;
        const updatedFriends = friends.filter(
            friend => friend.username !== username
        );
        user.friends = updatedFriends;
        return true;

    } catch (error) {
        console.error('Error deleting friend:', error);
        return false;
    }
}

export async function loadFriendsList() {
    try {
        const friendsList = document.getElementById('friends-list');
        const spinner = appendSpinner(friendsList);
        showSpinner(spinner);

        
        await setAllUsers();
        const friendRequests = JSON.parse(
            localStorage.getItem('friend_requests')) || [];
        const friends = JSON.parse(
            localStorage.getItem('friends')) || [];


        friendsList.innerHTML = '';

        if (friends.length === 0 && friendRequests.length === 0) {
            friendsList.innerHTML = `
            <p>
            ${translate("No friends available")}
            </p>`;
        }
        else {
            friends.forEach(usr => {

                const message = usr.displayname;
                createClickableUser(usr, message, friendsList);
            });

            friendRequests.forEach(usr => {

                const message = `${usr.displayname}` +
                `${translate(" (Wants to be friends with you)")}`;
                createClickableUser(usr, message, friendsList);
            });
        }
        hideSpinner(spinner);
    } catch (error) {
        console.error('Error fetching friends:', error);
    }
}
