// Canvas represents the frontend's playing field

export class Canvas {
    constructor(canvasID, aspectRatio = 16 / 9) {
        this.init(canvasID, aspectRatio);
    }

    init(canvasID, aspectRatio = 16 / 9) {
        this.id = document.getElementById(canvasID);
        this.ctx = this.id.getContext('2d');
        this.aspectRatio = aspectRatio;
    }

    resizeCanvas() {
        const navbar = document.querySelector('.navbar');
        const navbarHeight = navbar ? navbar.offsetHeight : 0;
        const mainContent = document.getElementById('main-content');
        const desiredHeight = window.innerWidth / this.aspectRatio;
        const maxHeight = window.innerHeight - navbarHeight;

        if (desiredHeight <= maxHeight) {
            this.id.width = mainContent.clientWidth;
            this.id.height = desiredHeight;
        } else {
            this.id.height = maxHeight;
            this.id.width = this.id.height * this.aspectRatio;
        }
    }

    resizeFlexWrapper() {
        const navbar = document.querySelector('.navbar');
        const navbarHeight = navbar ? navbar.offsetHeight : 0;
        const flexWrapper = document.querySelector('.flex-wrapper');

        if (flexWrapper) {
            flexWrapper.style.height =
                `${window.innerHeight - navbarHeight}px`;
        }
    }

    resize() {
        this.resizeFlexWrapper();
        this.resizeCanvas();
    }

    clear() {
        this.ctx.clearRect(0, 0, this.id.width, this.id.height);
    }

    fill(color) {
        this.ctx.fillStyle = color;
        this.ctx.fillRect(0, 0, this.id.width, this.id.height);
    }

    cleanup() {
        if (this.id) {
            this.id.width = 0;
            this.id.height = 0;
        }
        this.ctx = null;
        this.id = null;
    }
}
