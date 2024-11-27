export class Overlay {
    constructor() {
        this.x = 0;
        this.y = 0;
        this.size = 0;
        this.value = '';
    }

    setCanvasSize(canvasWidth, canvasHeight) {
        this.canvasWidth = canvasWidth;
        this.canvasHeight = canvasHeight;
    }

    setOverlaySize() {
        this.size = this.canvasHeight * 0.07;
    }

    update(message) {
        this.value = message;
    }

    rePosition(newCanvasWidth, newCanvasHeight) {
        this.y = newCanvasHeight / 2;
        this.x = newCanvasWidth / 2;
    }

    resize(newCanvasWidth, newCanvasHeight) {
        this.rePosition(newCanvasWidth, newCanvasHeight);
        this.setCanvasSize(newCanvasWidth, newCanvasHeight);
        this.setOverlaySize();
    }

    draw(ctx) {
        ctx.font = `${this.size}px 'Press Start 2P', cursive`;
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.value, this.x, this.y);
    }

    render(ctx, message) {
        this.update(message);
        this.draw(ctx);
    }
    
    cleanup() {
        this.x = 0;
        this.y = 0;
        this.size = 0;
        this.value = '';
        this.canvasWidth = 0;
        this.canvasHeight = 0;
    }
}