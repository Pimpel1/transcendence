import { getUserDetails } from './api/user-management.js';
import { Player } from './game/Player.js';
import { 
    setLanguage,
    isAuthenticated,
    setAllUsers
} from './utils.js';

const DEFAULT_NAME = 'DefaultName';
const DEFAULT_LANGUAGE = navigator.language.split('-')[0];
const DEFAULT_UP_KEY = 'ArrowUp';
const DEFAULT_DOWN_KEY = 'ArrowDown';

class User {
    constructor(
        name = DEFAULT_NAME, 
        upKey = DEFAULT_UP_KEY, 
        downKey = DEFAULT_DOWN_KEY
    ) {
        if (User.instance) {
            return User.instance;
        }

        this.player = new Player(name, upKey, downKey, true);
        this.email = '';
        this.name = name;
        this.displayname = name;
        this.avatar = null;
        this.language = DEFAULT_LANGUAGE;
        this.wins = 0;
        this.losses = 0;
        this.online = false;
        this.friends = [];
        this.sent_request_to = [];

        User.instance = this;
    }

    connect() {
        this.player.connectToMatchmaker();
    }

    async initialize() {
        if (await isAuthenticated()) {
            await this._initializeAuthenticatedUser();
        } else {
            await this._initializeAnonymousUser();
        }
    }

    async _initializeAuthenticatedUser() {
        try {
            const {
                email,
                username,
                displayname,
                avatar,
                language,
                wins,
                losses,
                status,
                friends,
                sent_request_to
            } = await getUserDetails();

            this.email = email;
            this.name = username;
            this.displayname = displayname;
            this.avatar = avatar;
            this.language = language;
            this.wins = wins;
            this.losses = losses;
            this.online = status;
            this.friends = friends;
            this.sent_request_to = sent_request_to;

            this.player.name = this.name;
            this.connect();

            await setLanguage(this.language);
            await setAllUsers();
        } catch (error) {
            console.log(`Error initializing user [${error}]`);
            await this.reset();
        }
    }

    async _initializeAnonymousUser() {
        try {
            await setLanguage(DEFAULT_LANGUAGE);
        } catch (error) {
            console.log(`Error initializing anonymous user [${error}]`);
        }
    }

    async reset() {
        try {
            this.player.disconnectFromMatchmaker();
            this.player.name = 'DefaultName';
            
            this.email = null;
            this.name = DEFAULT_NAME;
            this.displayname = DEFAULT_NAME;
            this.avatar = null;
            this.language = DEFAULT_LANGUAGE;
            this.wins = 0;
            this.losses = 0;
            this.online = false;
            this.friends = [];
            this.sent_request_to = [];

            await setLanguage(DEFAULT_LANGUAGE);
        } catch (error) {
            console.log(`Error resetting user [${error}]`);
        }
    }
}

const user = new User();

export default user;
