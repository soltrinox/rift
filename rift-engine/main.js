// main.js

// Import necessary modules and files
import { Game } from './gameLogic.js';
import { Paddle } from './paddle.js';
import { Ball } from './ball.js';

// Create game instance
const gameCanvas = document.getElementById('gameCanvas');
const game = new Game(gameCanvas);

// Initialize game
game.start();

// Event listener for paddle movement
document.addEventListener('keydown', (event) => {
  game.movePaddle(event.key);
});

// Game loop
function gameLoop() {
  game.update();
  game.draw();

  if (!game.gameOver) {
    requestAnimationFrame(gameLoop);
  }
}

// Start game loop
gameLoop();

// Function to start the game
export function startGame() {
  game.start();
}

// Function to reset the game
export function resetGame() {
  game.reset();
}

// Function to move the paddle
export function movePaddle(key) {
  game.movePaddle(key);
}

// Function to draw the game elements
export function draw() {
  game.draw();
}
