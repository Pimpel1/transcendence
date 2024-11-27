// Pitch represents game-service's playing field

export class Pitch {
    constructor(width, height, paddleSize, ballSize) {
        this.width = width;
        this.height = height;
        this.paddleSize = paddleSize;
        this.ballSize = ballSize;
        this.aspectRatio = width / height;
        this.heightToWidthRatio = height / width;
        this.paddleToHeightRatio = paddleSize / height;
        this.ballToHeightRatio = ballSize / height;
    }

    cleanup() {
        this.width = 0;
        this.height = 0;
        this.paddleSize = 0;
        this.ballSize = 0;
        this.aspectRatio = 0;
        this.heightToWidthRatio = 0;
        this.paddleToHeightRatio = 0;
        this.ballToHeightRatio = 0;
    }
}
