"""
扫雷游戏配置文件
包含游戏参数、难度设置和颜色定义
"""

from enum import Enum

class Difficulty(Enum):
    """游戏难度枚举"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class GameState(Enum):
    """游戏状态枚举"""
    NOT_STARTED = -1
    PLAYING = 0
    GAME_OVER = 1
    GAME_WON = 2

class MineStatus(Enum):
    """地雷状态枚举"""
    HIDDEN = 0
    OPENED = 1
    FLAGGED = 2
    QUESTIONED = 3
    DOUBLE_CLICKED = 4
    DOUBLE_CLICKED_AROUND = 5
    MINE_EXPLODED = 6
    WRONG_FLAG = 7

# 游戏参数
FPS = 60
GRIDSIZE = 30
BORDERSIZE = 5

# 难度设置
DIFFICULTY_SETTINGS = {
    Difficulty.EASY: {
        'grid_size': (9, 9),
        'num_mines': 10,
        'name': '简单'
    },
    Difficulty.MEDIUM: {
        'grid_size': (16, 16),
        'num_mines': 40,
        'name': '中等'
    },
    Difficulty.HARD: {
        'grid_size': (30, 16),
        'num_mines': 99,
        'name': '困难'
    }
}

# 默认难度
DEFAULT_DIFFICULTY = Difficulty.MEDIUM
GAME_MATRIX_SIZE = DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY]['grid_size']
NUM_MINES = DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY]['num_mines']

# 屏幕尺寸计算
SCREENSIZE = (
    GAME_MATRIX_SIZE[0] * GRIDSIZE + BORDERSIZE * 2,
    (GAME_MATRIX_SIZE[1] + 2) * GRIDSIZE + BORDERSIZE
)

# 颜色定义
COLORS = {
    'background': (225, 225, 225),
    'red': (200, 0, 0),
    'green': (0, 200, 0),
    'blue': (0, 0, 200),
    'dark_gray': (128, 128, 128),
    'light_gray': (192, 192, 192),
    'white': (255, 255, 255),
    'black': (0, 0, 0)
}

# 字体设置
FONT_SIZE = 40