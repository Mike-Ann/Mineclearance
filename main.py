import os
import sys
import time
import random
import pygame
from enum import Enum
from typing import List, Tuple


# 获取资源路径
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

'''图片素材路径'''
IMAGE_PATHS = {
    '0': resource_path('resources/images/0.bmp'),
    '1': resource_path('resources/images/1.bmp'),
    '2': resource_path('resources/images/2.bmp'),
    '3': resource_path('resources/images/3.bmp'),
    '4': resource_path('resources/images/4.bmp'),
    '5': resource_path('resources/images/5.bmp'),
    '6': resource_path('resources/images/6.bmp'),
    '7': resource_path('resources/images/7.bmp'),
    '8': resource_path('resources/images/8.bmp'),
    'ask': resource_path('resources/images/ask.bmp'),
    'blank': resource_path('resources/images/blank.bmp'),
    'blood': resource_path('resources/images/blood.bmp'),
    'error': resource_path('resources/images/error.bmp'),
    'face_fail': resource_path('resources/images/face_fail.png'),
    'face_normal': resource_path('resources/images/face_normal.png'),
    'face_success': resource_path('resources/images/face_success.png'),
    'flag': resource_path('resources/images/flag.bmp'),
    'mine': resource_path('resources/images/mine.bmp')
}

'''字体路径'''
FONT_PATH = resource_path('resources/font/font.TTF')
FONT_SIZE = 40

class GameState(Enum):
    NOT_STARTED = -1
    PLAYING = 0
    GAME_OVER = 1
    GAME_WON = 2

class MineStatus(Enum):
    HIDDEN = 0
    OPENED = 1
    FLAGGED = 2
    QUESTIONED = 3
    DOUBLE_CLICKED = 4
    DOUBLE_CLICKED_AROUND = 5
    MINE_EXPLODED = 6
    WRONG_FLAG = 7

'''游戏相关参数'''
FPS = 60
GRIDSIZE = 40
NUM_MINES = 50
GAME_MATRIX_SIZE = (30, 16)
BORDERSIZE = 5
SCREENSIZE = (GAME_MATRIX_SIZE[0] * GRIDSIZE + BORDERSIZE * 2, (GAME_MATRIX_SIZE[1] + 2) * GRIDSIZE + BORDERSIZE)

'''颜色'''
BACKGROUND_COLOR = (225, 225, 225)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 200)

'''雷类'''
class Mine(pygame.sprite.Sprite):
    def __init__(self, images, position, status_code=MineStatus.HIDDEN, **kwargs):
        super().__init__()
        self.images = images
        self.image = self.images['blank']
        self.rect = self.image.get_rect(topleft=position)
        self.status_code = status_code
        self.is_mine = False
        self.num_mines_around = -1

    def set_status(self, status: MineStatus):
        """设置当前状态"""
        self.status_code = status

    def bury_mine(self):
        """设置此格子为地雷"""
        self.is_mine = True

    def set_mines_around(self, count: int):
        """设置周围地雷数量"""
        self.num_mines_around = count

    def draw(self, screen):
        """绘制地雷格子"""
        image_map = {
            MineStatus.HIDDEN: 'blank',
            MineStatus.OPENED: 'mine' if self.is_mine else str(self.num_mines_around),
            MineStatus.FLAGGED: 'flag',
            MineStatus.QUESTIONED: 'ask',
            MineStatus.DOUBLE_CLICKED: str(self.num_mines_around),
            MineStatus.DOUBLE_CLICKED_AROUND: '0',
            MineStatus.MINE_EXPLODED: 'blood',
            MineStatus.WRONG_FLAG: 'error'
        }
        
        image_key = image_map.get(self.status_code, 'blank')
        self.image = self.images[image_key]
        screen.blit(self.image, self.rect)

    @property
    def opened(self) -> bool:
        """是否已打开"""
        return self.status_code == MineStatus.OPENED

    @property
    def flagged(self) -> bool:
        """是否被标记为旗子"""
        return self.status_code == MineStatus.FLAGGED

'''文字板类'''
class TextBoard(pygame.sprite.Sprite):
    def __init__(self, text, font, position, color, **kwargs):
        pygame.sprite.Sprite.__init__(self)
        self.text = text
        self.font = font
        self.position = position
        self.color = color
    def draw(self, screen):
        text_render = self.font.render(self.text, True, self.color)
        screen.blit(text_render, self.position)
    def update(self, text):
        self.text = text

'''表情按钮类'''
class EmojiButton(pygame.sprite.Sprite):
    def __init__(self, images, position, status_code=0, **kwargs):
        pygame.sprite.Sprite.__init__(self)
        # 导入图片
        self.images = images
        self.image = self.images['face_normal']
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position
        # 表情按钮的当前状态
        self.status_code = status_code

    '''画到屏幕上'''
    def draw(self, screen):
        # 状态码为0, 代表正常的表情
        if self.status_code == 0:
            self.image = self.images['face_normal']
        # 状态码为1, 代表失败的表情
        elif self.status_code == 1:
            self.image = self.images['face_fail']
        # 状态码为2, 代表成功的表情
        elif self.status_code == 2:
            self.image = self.images['face_success']
        # 绑定图片到屏幕
        screen.blit(self.image, self.rect)

    '''设置当前的按钮的状态'''
    def setstatus(self, status_code):
        self.status_code = status_code

'''扫雷地图类'''
class MinesweeperMap():
    def __init__(self, images, **kwargs):
        self.images = images
        self.mines_matrix = []
        self.game_state = GameState.NOT_STARTED
        self.mouse_pos = None
        self.mouse_pressed = None
        
        self._init_matrix()
        self._place_mines()
        self._calculate_mines_around()
    
    def _init_matrix(self):
        """初始化游戏矩阵"""
        for j in range(GAME_MATRIX_SIZE[1]):
            mines_line = []
            for i in range(GAME_MATRIX_SIZE[0]):
                position = i * GRIDSIZE + BORDERSIZE, (j + 2) * GRIDSIZE
                mines_line.append(Mine(images=self.images, position=position))
            self.mines_matrix.append(mines_line)
    
    def _place_mines(self):
        """随机放置地雷"""
        total_cells = GAME_MATRIX_SIZE[0] * GAME_MATRIX_SIZE[1]
        mine_positions = random.sample(range(total_cells), NUM_MINES)
        for pos in mine_positions:
            y, x = divmod(pos, GAME_MATRIX_SIZE[0])
            self.mines_matrix[y][x].bury_mine()
    
    def _calculate_mines_around(self):
        """计算每个格子周围的地雷数量"""
        for y in range(GAME_MATRIX_SIZE[1]):
            for x in range(GAME_MATRIX_SIZE[0]):
                mine = self.mines_matrix[y][x]
                if not mine.is_mine:
                    count = sum(1 for j, i in self._get_around_coords(y, x) 
                               if self.mines_matrix[j][i].is_mine)
                    mine.set_mines_around(count)

    def draw(self, screen):
        """绘制游戏地图"""
        for row in self.mines_matrix:
            for mine in row:
                mine.draw(screen)

    def set_game_state(self, state: GameState):
        """设置游戏状态"""
        self.game_state = state

    def update(self, mouse_pressed=None, mouse_pos=None, type_='down'):
        """根据鼠标操作更新游戏状态"""
        assert type_ in ['down', 'up']
        
        if type_ == 'down' and mouse_pos is not None and mouse_pressed is not None:
            self.mouse_pos = mouse_pos
            self.mouse_pressed = mouse_pressed
            
        if not self._is_click_in_bounds():
            return
            
        if self.game_state == GameState.NOT_STARTED:
            self.game_state = GameState.PLAYING
            
        if self.game_state != GameState.PLAYING:
            return
            
        x, y = self._get_grid_coords()
        mine = self.mines_matrix[y][x]
        
        if type_ == 'down':
            self._handle_mouse_down(x, y, mine)
        else:
            self._handle_mouse_up(x, y, mine)
    
    def _is_click_in_bounds(self) -> bool:
        """检查点击是否在有效范围内"""
        return (BORDERSIZE <= self.mouse_pos[0] <= SCREENSIZE[0] - BORDERSIZE and
                GRIDSIZE * 2 <= self.mouse_pos[1] <= SCREENSIZE[1] - BORDERSIZE)
    
    def _get_grid_coords(self) -> Tuple[int, int]:
        """获取网格坐标"""
        x = (self.mouse_pos[0] - BORDERSIZE) // GRIDSIZE
        y = self.mouse_pos[1] // GRIDSIZE - 2
        return x, y
    
    def _handle_mouse_down(self, x: int, y: int, mine: Mine):
        """处理鼠标按下事件"""
        left, _, right = self.mouse_pressed
        
        if left and right and mine.opened and mine.num_mines_around > 0:
            mine.set_status(MineStatus.DOUBLE_CLICKED)
            self._handle_double_click_around(x, y)
    
    def _handle_mouse_up(self, x: int, y: int, mine: Mine):
        """处理鼠标释放事件"""
        left, _, right = self.mouse_pressed
        
        if left and not right:
            self._handle_left_click(x, y, mine)
        elif right and not left:
            self._handle_right_click(mine)
        elif left and right:
            self._handle_double_click_release(x, y)
    
    def _handle_left_click(self, x: int, y: int, mine: Mine):
        """处理左键点击"""
        if mine.status_code not in [MineStatus.FLAGGED, MineStatus.QUESTIONED]:
            if self._open_mine(x, y):
                self.set_game_state(GameState.GAME_OVER)
    
    def _handle_right_click(self, mine: Mine):
        """处理右键点击"""
        status_transitions = {
            MineStatus.HIDDEN: MineStatus.FLAGGED,
            MineStatus.FLAGGED: MineStatus.QUESTIONED,
            MineStatus.QUESTIONED: MineStatus.HIDDEN
        }
        mine.set_status(status_transitions.get(mine.status_code, MineStatus.HIDDEN))
    
    def _handle_double_click_around(self, x: int, y: int):
        """处理双击周围格子"""
        mine = self.mines_matrix[y][x]
        around_coords = self._get_around_coords(y, x)
        
        flags_count = sum(1 for j, i in around_coords 
                       if self.mines_matrix[j][i].status_code == MineStatus.FLAGGED)
        
        if flags_count == mine.num_mines_around:
            for j, i in around_coords:
                if self.mines_matrix[j][i].status_code == MineStatus.HIDDEN:
                    self._open_mine(i, j)
        else:
            for j, i in around_coords:
                if self.mines_matrix[j][i].status_code == MineStatus.HIDDEN:
                    self.mines_matrix[j][i].set_status(MineStatus.DOUBLE_CLICKED_AROUND)
    
    def _handle_double_click_release(self, x: int, y: int):
        """处理双击释放"""
        self.mines_matrix[y][x].set_status(MineStatus.OPENED)
        around_coords = self._get_around_coords(y, x)
        
        for j, i in around_coords:
            if self.mines_matrix[j][i].status_code == MineStatus.DOUBLE_CLICKED_AROUND:
                self.mines_matrix[j][i].set_status(MineStatus.HIDDEN)

    def _open_mine(self, x: int, y: int) -> bool:
        """打开指定位置的格子，返回是否触雷"""
        mine = self.mines_matrix[y][x]
        
        if mine.is_mine:
            self._reveal_all_mines()
            mine.set_status(MineStatus.MINE_EXPLODED)
            return True
            
        if mine.status_code != MineStatus.HIDDEN:
            return False
            
        self._flood_fill(x, y)
        return False
    
    def _flood_fill(self, x: int, y: int):
        """使用洪水填充算法打开空白区域"""
        if x < 0 or x >= GAME_MATRIX_SIZE[0] or y < 0 or y >= GAME_MATRIX_SIZE[1]:
            return
            
        mine = self.mines_matrix[y][x]
        if mine.status_code != MineStatus.HIDDEN or mine.is_mine:
            return
            
        mine.set_status(MineStatus.OPENED)
        
        if mine.num_mines_around == 0:
            for j, i in self._get_around_coords(y, x):
                self._flood_fill(i, j)
    
    def _reveal_all_mines(self):
        """显示所有地雷和错误标记"""
        for row in self.mines_matrix:
            for mine in row:
                if mine.is_mine and mine.status_code == MineStatus.HIDDEN:
                    mine.set_status(MineStatus.OPENED)
                elif not mine.is_mine and mine.status_code == MineStatus.FLAGGED:
                    mine.set_status(MineStatus.WRONG_FLAG)
    
    def _get_around_coords(self, row: int, col: int) -> List[Tuple[int, int]]:
        """获取周围8个格子的坐标"""
        coords = []
        for j in range(max(0, row-1), min(row+1, GAME_MATRIX_SIZE[1]-1)+1):
            for i in range(max(0, col-1), min(col+1, GAME_MATRIX_SIZE[0]-1)+1):
                if j == row and i == col:
                    continue
                coords.append((j, i))
        return coords
    
    @property
    def is_playing(self) -> bool:
        """是否正在游戏中"""
        return self.game_state == GameState.PLAYING
    
    @property
    def flags_count(self) -> int:
        """被标记为旗子的数量"""
        return sum(1 for row in self.mines_matrix 
                  for mine in row if mine.flagged)
    
    @property
    def opened_count(self) -> int:
        """已打开的格子数量"""
        return sum(1 for row in self.mines_matrix 
                  for mine in row if mine.opened)
    
    @property
    def is_won(self) -> bool:
        """是否获胜"""
        total_cells = GAME_MATRIX_SIZE[0] * GAME_MATRIX_SIZE[1]
        return self.opened_count + self.flags_count == total_cells and self.flags_count == NUM_MINES

class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREENSIZE)
        pygame.display.set_caption('扫雷')
        self.clock = pygame.time.Clock()
        self.images = self._load_images()
        self.font = pygame.font.Font(FONT_PATH, FONT_SIZE)
        self.reset_game()
    
    def _load_images(self) -> dict:
        """加载所有图片资源"""
        images = {}
        for key, value in IMAGE_PATHS.items():
            try:
                if key in ['face_fail', 'face_normal', 'face_success']:
                    image = pygame.image.load(value)
                    images[key] = pygame.transform.smoothscale(
                        image, (int(GRIDSIZE*1.25), int(GRIDSIZE*1.25)))
                else:
                    image = pygame.image.load(value).convert()
                    images[key] = pygame.transform.smoothscale(image, (GRIDSIZE, GRIDSIZE))
            except pygame.error as e:
                print(f"无法加载图片 {key}: {value}")
                print(f"错误信息: {e}")
                sys.exit(1)
        return images
    
    def reset_game(self):
        """重置游戏"""
        self.minesweeper_map = MinesweeperMap(self.images)
        self.start_time = None
        self._create_ui_elements()
    
    def _create_ui_elements(self):
        """创建UI元素"""
        # 表情按钮
        emoji_pos = ((SCREENSIZE[0] - int(GRIDSIZE * 1.25)) // 2, 
                    (GRIDSIZE * 2 - int(GRIDSIZE * 1.25)) // 2)
        self.emoji_button = EmojiButton(self.images, position=emoji_pos)
        
        # 剩余地雷计数器
        text_size = self.font.size(str(NUM_MINES))
        self.remaining_mines_text = TextBoard(
            str(NUM_MINES).zfill(3), self.font, 
            (30, (GRIDSIZE*2-text_size[1])//2-2), RED)
        
        # 计时器
        time_size = self.font.size('000')
        self.time_text = TextBoard(
            '000', self.font, 
            (SCREENSIZE[0]-30-time_size[0], (GRIDSIZE*2-time_size[1])//2-2), RED)
    
    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                mouse_pressed = pygame.mouse.get_pressed()
                self.minesweeper_map.update(
                    mouse_pressed=mouse_pressed, mouse_pos=mouse_pos, type_='down')
            elif event.type == pygame.MOUSEBUTTONUP:
                self.minesweeper_map.update(type_='up')
                if self.emoji_button.rect.collidepoint(pygame.mouse.get_pos()):
                    self.reset_game()
        return True
    
    def update(self):
        """更新游戏状态"""
        # 更新计时器
        if self.minesweeper_map.is_playing:
            if self.start_time is None:
                self.start_time = time.time()
            elapsed = int(time.time() - self.start_time)
            self.time_text.update(str(min(elapsed, 999)).zfill(3))
        
        # 更新剩余地雷数
        remaining = max(NUM_MINES - self.minesweeper_map.flags_count, 0)
        self.remaining_mines_text.update(str(remaining).zfill(3))
        
        # 检查游戏状态
        if self.minesweeper_map.game_state == GameState.GAME_OVER:
            self.emoji_button.setstatus(status_code=1)
        elif self.minesweeper_map.is_won:
            self.minesweeper_map.game_state = GameState.GAME_WON
            self.emoji_button.setstatus(status_code=2)
    
    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(BACKGROUND_COLOR)
        self.minesweeper_map.draw(self.screen)
        self.emoji_button.draw(self.screen)
        self.remaining_mines_text.draw(self.screen)
        self.time_text.draw(self.screen)
        pygame.display.update()
    
    def run(self):
        """运行游戏主循环"""
        while True:
            if not self.handle_events():
                break
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

'''主函数'''
def main():
    game = GameManager()
    game.run()


'''run'''
if __name__ == '__main__':
    main()


