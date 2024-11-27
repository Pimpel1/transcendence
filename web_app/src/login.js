import { arena } from './arena.js';
import { 
    verifyOtp,
    authLogout,
    isHealthy as authServiceIsHealthy
} from './api/auth-service.js';
import {
    deleteOngoingGame,
    isAuthenticated,
    resizeWindow,
    sanitizeInput,
    showMessage,
    translate
} from './utils.js';
import user from './User.js';

export async function login() {
    const authenticated = await isAuthenticated();

    if (authenticated) {
        console.log('User is already logged in.');
        showMessage(
            `${translate('You are already logged in.')}`,
            'info'
        );
        return;
    }

    window.location.href =
        `${window.config.apiBaseUrl}/auth-service/api/oauth-login`;
}

export function twoFactorAuthScreen() {
    const urlParams = new URLSearchParams(window.location.search);
    const email = urlParams.get('email');
    const username = urlParams.get('username');
    const displayname = urlParams.get('displayname');

    user.email = email;
    user.name = username;
    user.displayname = displayname;

    const mainContent = document.getElementById('main-content');
    mainContent.innerHTML = `
        <div id=mainContentWrapper class="two-factor-auth">
            <div
                class="container
                    d-flex
                    justify-content-center
                    align-items-center"
            >
                <div class="card p-4 shadow-sm custom-card">
                    <h3 class="card-title mb-4 text-center">
                        Two-Factor Authentication
                    </h3>
                    <form id="twoFactorAuthForm">
                        <div class="form-group mb-3">
                            <label for="code">Enter Code</label>
                            <input
                                type="text"
                                class="form-control"
                                id="code"
                                required
                            >
                        </div>
                        <button
                            type="submit"
                            class="btn btn-secondary w-100"
                        >
                            Verify Code
                        </button>
                    </form>
                </div>
            </div>
        </div>
    `;

    resizeWindow();

    const form = document.getElementById('twoFactorAuthForm');
    form.addEventListener(
        'submit',
        (event) => handleTwoFactorAuthSubmit(event)
    );

    function resizeTwoFactorAuthScreen() {
        const navbar = document.querySelector('.navbar');
        const navbarHeight = navbar ? navbar.offsetHeight : 0;
        const twoFactorAuthElement =
            document.querySelector('.two-factor-auth');
        const containerElement = document.querySelector('.container');
        if (twoFactorAuthElement) {
            twoFactorAuthElement.style.height =
                `${window.innerHeight - navbarHeight}px`;
            containerElement.style.height =
                `${window.innerHeight - navbarHeight}px`;
        }
    }

    window.addEventListener('resize', resizeTwoFactorAuthScreen);

    resizeTwoFactorAuthScreen();
}

function handleTwoFactorAuthSubmit(event) {
    event.preventDefault();

    const code = sanitizeInput(document.getElementById('code').value);
    if (code) {
        verifyTwoFactorAuth(code);
    } else {
        showMessage(
            `${translate(
                'Code is required. Please enter the code sent to your email.'
            )}`,
            'danger'
        );
    }
}

async function verifyTwoFactorAuth(code) {
    try {
        await verifyOtp(code);
        console.log('2FA successful.');
        user.initialize();
        arena();
    } catch (error) {
        console.error('Error during verification:', error);
        if (error.message.startsWith('403')) {
            showMessage(
                `${translate('Invalid code. Please try again.')}`,
                'danger'
            );
        }
        else {
            showMessage(
                `${translate(
                    'Error verifying code. Please try again later.'
                )}`,
                'danger'
            );
        }
    }
}

export async function logout() {
    try {
        eraseButtons();
        await deleteOngoingGame();
        if (!await authServiceIsHealthy())
            throw new Error('auth-service offline');

        localStorage.clear();
        await user.reset();

        const authenticated = await isAuthenticated();
        if (!authenticated) {
            console.log('User is already logged out.');
            return;
        }
        else {
            await authLogout();
            console.log('User logged out successfully.');
        }
        arena();
    } catch (error) {
        console.error('Error logging out:', error);
        showMessage(
            `${translate('Error logging out. Please try again.')}`,
            'danger'
        );
    }
}

function eraseButtons() {
    const fillingButton = document.getElementById('filling-button');
    const fillingDiv = document.getElementById('filling-div');
    if (fillingButton) {
        fillingButton.remove();
    }
    if (fillingDiv) {
        fillingDiv.remove();
    }
    user.player.disconnectFromGame();
}
