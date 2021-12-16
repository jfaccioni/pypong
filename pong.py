import curses
import random

GAME_LEVEL = {
    '3': 5,  # hard
    '2': 10,  # normal
    '1': 15,  # easy
}
GAME_LEVEL_MESSAGE = 'Select game level:\n(1): Easy\n(2): Normal\n(3): Hard\nYour choice: '

COMPUTER_LEVEL = {
    '3': 0.05,  # hard
    '2': 0.2,  # normal
    '1': 0.5,  # easy
}
COMPUTER_LEVEL_MESSAGE = 'Select computer AI level:\n(1): Easy\n(2): Normal\n(3): Hard\nYour choice: '


GAME_SPEED = {
    '3': 50,  # fast
    '2': 100,  # normal
    '1': 200,  # slow
}
GAME_SPEED_MESSAGE = 'Select game speed:\n(1): Slow\n(2): Normal\n(3): Fast\nYour choice: '


class Velocity:
    def __init__(self, x=1, y=1):
        self.x = x
        self.y = y


class Entity:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class Paddle(Entity):
    def move_up(self):
        if not self.is_touching_top_wall():
            self.y -= 1
    
    def is_touching_top_wall(self):
        return self.y <= 1
        
    def move_down(self, window_height):
        if not self.is_touching_bottom_wall(window_height=window_height):
            self.y += 1
    
    def is_touching_bottom_wall(self, window_height):
        return self.y + self.height >= window_height - 1


class PlayerPaddle(Paddle):
    def move(self, key, window_height):
        if key == curses.KEY_UP:
            self.move_up()
        if key == curses.KEY_DOWN:
            self.move_down(window_height=window_height)


class ComputerPaddle(Paddle):
    def __init__(self, x, y, width, height, level):
        super().__init__(x=x, y=y, width=width, height=height)
        self.level = level
    
    def move(self, ball_y_position, window_height):
        if random.random() < self.level:
            return  # Computer skips this turn
        if ball_y_position > self.y + self.width:  # ball is below computer paddle
            self.move_down(window_height=window_height)
        elif ball_y_position < self.y:  # ball is above computer
            self.move_up()


class Ball(Entity):
    velocity = Velocity()
    
    def has_collided_with_left_paddle(self, paddle):
        if self.x == paddle.x + paddle.width:
            if paddle.y <= self.y + self.height and self.y <= paddle.y + paddle.height:
                return True
        return False

    def has_collided_with_right_paddle(self, paddle):
        if self.x == paddle.x - self.width:
            if paddle.y <= self.y + self.height and self.y <= paddle.y + paddle.height:
                return True
        return False
    
    def has_collided_with_vertical_wall(self, window_width):
        if self.x == 1 or self.x == (window_width - (self.width + 1)):
            return True
        return False
    
    def has_collided_with_horizontal_wall(self, window_height):
        if self.y == 1 or self.y == (window_height - (self.height + 1)):
            return True
        return False
            
    def move(self):
        self.x += self.velocity.x
        self.y += self.velocity.y


def main():
    """Main function of this script."""
    game_level = select_game_option(GAME_LEVEL, GAME_LEVEL_MESSAGE)
    computer_level = select_game_option(COMPUTER_LEVEL, COMPUTER_LEVEL_MESSAGE)
    game_speed = select_game_option(GAME_SPEED, GAME_SPEED_MESSAGE)
    score = curses.wrapper(game_loop, game_level, computer_level, game_speed)
    show_game_over(score)


def select_game_option(data_dict, message):
    """Selects an option of the game, based on the input dictionary."""
    while True:
        answer = input(message)
        if answer in data_dict.keys():
            return data_dict[answer]
        print('Invalid option, please type 1, 2 or 3.\n')


def game_loop(window, game_level, computer_level, game_speed):
    """Main game loop. Returns the score obtained by the player."""
    curses.curs_set(0)
    window_height, window_width = window.getmaxyx()
    
    # Initializes scores and objects
    player_score = 0
    computer_score = 0
    player_paddle = PlayerPaddle(x=10, y=10, width=2, height=game_level)
    computer_paddle = ComputerPaddle(x=window_width - 10, y=window_height - (game_level + 10), width=2, height=game_level, level=computer_level)
    ball = Ball(x=int(window_width/2) - 1, y=int(window_height/2) - 1, width=2, height=2)
    
    # Game main loop
    while True:
        # Sets the game border and speed
        window.border(0)
        window.timeout(game_speed)
        
        # Draws everything to the screen
        draw_score(window, window_width, player_score, computer_score)
        for entity in [player_paddle, computer_paddle, ball]:
            draw_entity(window, entity)
        
        # Moves player paddle, computer paddle and ball
        next_key = window.getch()
        player_paddle.move(key=next_key, window_height=window_height)
        computer_paddle.move(ball_y_position=ball.y, window_height=window_height)
        ball.move()
        
        # Checks for collision with paddles
        if (
            ball.has_collided_with_left_paddle(paddle=player_paddle) or
            ball.has_collided_with_right_paddle(paddle=computer_paddle)
            ):
            ball.velocity.x = -ball.velocity.x
        
        # Checks for collision with walls
        if ball.has_collided_with_horizontal_wall(window_height=window_height):
            ball.velocity.y = -ball.velocity.y
        if ball.has_collided_with_vertical_wall(window_width=window_width):
            if ball.x == 1:  # Collided with left wall
                computer_score += 1
            if ball.x == window_width - (ball.width + 1):
                player_score += 1  # Collided with r wall
            ball = Ball(x=int(window_width/2) - 1, y=int(window_height/2) - 1, width=2, height=2)
            ball.velocity.x = -ball.velocity.x
        
        # Clears the screen for redrawing on next loop
        window.clear()
    
        # Checks for victory conditions
        if computer_score == 10 or player_score == 10:
            return computer_score, player_score


def draw_score(window, window_width, player_score, computer_score):
    """Draws the score on the screen."""
    window.addch(2, 2, str(player_score))
    window.addch(2, window_width-3, str(computer_score))


def draw_entity(window, entity):
    """Draws the Entity on the screen."""
    for i in range(entity.width):
        xpos = entity.x + i
        for j in range(entity.height):
            ypos = entity.y + j
            window.addch(ypos, xpos, '█')


def show_game_over(score):
    """Shows the score once the game has ended."""
    winner = 'Computer' if score[1] > score[0] else 'Player'
    print(
        f'Player score: {score[0]}\n'
        f'Computer score: {score[1]}\n'
        f'Winner: {winner}!'
    )


if __name__ == '__main__':
    main()
