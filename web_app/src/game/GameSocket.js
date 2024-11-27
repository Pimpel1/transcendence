export class GameSocket {
    constructor(gameId, playerPosition, up=null, down=null) {
        const baseUrl = `${window.config.wsBaseUrl}/game-service/ws/game/`;

        if (up == null) {
            if (playerPosition === 'left') {
                this.up = 'w';
                this.down = 's';
            } else if (playerPosition === 'right') {
                this.up = 'ArrowUp';
                this.down = 'ArrowDown';
            }
        } else {
            this.up = up;
            this.down = down;
        }

        const queryParams =
            `?position=${playerPosition}` +
            `&up=${this.up}` +
            `&down=${this.down}`;
        const url = `${baseUrl}${gameId}${queryParams}`;

        this.socket = new WebSocket(url);
        this.boundSendGameKeyEvent = this.sendGameKeyEvent.bind(this);
        window.addEventListener('keydown', this.boundSendGameKeyEvent);
        window.addEventListener('keyup', this.boundSendGameKeyEvent);
    }


    onOpen(callback) {
        this.socket.onopen = callback;
    }

    onMessage(callback) {
        this.socket.onmessage = callback;
    }

    onClose(callback) {
        this.socket.onclose = callback;
    }

    onError(callback) {
        this.socket.onerror = callback;
    }

    sendMessage(message) {
        if (this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(message);
        } else {
            console.warn(
                'GameSocket is not open. Unable to send message:',
                message
            );
        }
    }

    sendGameKeyEvent(e) {
        if (e.key !== this.up && e.key !== this.down) { 
            return;
        }
        this.sendMessage(JSON.stringify({
            messageType: 'key_event_message',
            key: e.key,
            event: e.type
        }));
    }

    close() {
        window.removeEventListener('keydown', this.boundSendGameKeyEvent);
        window.removeEventListener('keyup', this.boundSendGameKeyEvent);
        if (
            this.socket.readyState === WebSocket.OPEN ||
            this.socket.readyState === WebSocket.CLOSING
        ) {
            this.socket.close();
        }
    }
}
