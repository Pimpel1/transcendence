export class MatchmakerSocket {
    constructor(playerName) {
          const baseUrl =
            `${window.config.wsBaseUrl}/matchmaker-service/ws/connect`;
        const queryParams = `?player_name=${playerName}`;
        const url = `${baseUrl}${queryParams}`;
        this.socket = new WebSocket(url);
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
        if (this.socket.readyState === WebSocket.CONNECTING) {
            // try again in 100ms
            setTimeout(() => {
                this.sendMessage(message);
            }, 100);
        }
        else if (this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(message);
        } else {
            console.warn(
                'MatchmakerSocket is not open. Unable to send message:',
                message
            );
        }
    }

    close() {
        if (
            this.socket.readyState === WebSocket.OPEN ||
            this.socket.readyState === WebSocket.CLOSING
        ) {
            this.socket.close();
        }
    }

}
