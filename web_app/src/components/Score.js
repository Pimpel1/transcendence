export class Score {
    constructor(position) {
        this.position = position;
        this.x = 0;
        this.y = 0;
        this.size = 0;
        this.value = 0;
    }

    setCanvasSize(canvasWidth, canvasHeight) {
        this.canvasWidth = canvasWidth;
        this.canvasHeight = canvasHeight;
    }

    setScoreSize() {
        this.size = this.canvasHeight * 0.05;
    }

    update(score) {
        this.value = score;
    }

    rePosition(newCanvasWidth, newCanvasHeight) {
        this.y = newCanvasHeight * 0.15;
        if (this.position === 'left') {
            this.x = 0.3 * newCanvasWidth;
        }
        else {
            this.x = 0.7 * newCanvasWidth;
        }
    }

    resize(newCanvasWidth, newCanvasHeight) {
        this.rePosition(newCanvasWidth, newCanvasHeight);
        this.setCanvasSize(newCanvasWidth, newCanvasHeight);
        this.setScoreSize();
    }

    draw(ctx) {
        ctx.font = `${this.size}px 'Press Start 2P', cursive`;
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.value, this.x, this.y);
    }

    render(ctx, score) {
        this.update(score);
        this.draw(ctx);
    }

    cleanup() {
        this.x = 0;
        this.y = 0;
        this.size = 0;
        this.value = 0;
        this.canvasWidth = 0;
        this.canvasHeight = 0;
    }
}
