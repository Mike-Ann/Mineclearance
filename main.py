import os
import sys
import time
import random
import pygame


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

'''游戏相关参数'''
FPS = 60
GRIDSIZE = 30
NUM_MINES = 50
GAME_MATRIX_SIZE = (30, 16)
BORDERSIZE = 5
SCREENSIZE = (GAME_MATRIX_SIZE[0] * GRIDSIZE + BORDERSIZE * 2, (GAME_MATRIX_SIZE[1] + 2) * GRIDSIZE + BORDERSIZE)

'''颜色'''
BACKGROUND_COLOR = (225, 225, 225)
RED = (200, 0, 0)

'''雷类'''
class Mine(pygame.sprite.Sprite):
    def __init__(self, images, position, status_code=0, **kwargs):
        pygame.sprite.Sprite.__init__(self)
        # 导入图片
        self.images = images
        self.image = self.images['blank']
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position
        # 雷当前的状态
        self.status_code = status_code
        # 真雷还是假雷(默认是假雷)
        self.is_mine_flag = False
        # 周围雷的数目
        self.num_mines_around = -1

    '''设置当前的状态码'''
    def setstatus(self, status_code):
        self.status_code = status_code

    '''埋雷'''
    def burymine(self):
        self.is_mine_flag = True

    '''设置周围雷的数目'''
    def setnumminesaround(self, num_mines_around):
        self.num_mines_around = num_mines_around

    '''画到屏幕上'''
    def draw(self, screen):
        # 状态码为0, 代表该雷未被点击
        if self.status_code == 0:
            self.image = self.images['blank']
        # 状态码为1, 代表该雷已被点开
        elif self.status_code == 1:
            self.image = self.images['mine'] if self.is_mine_flag else self.images[str(self.num_mines_around)]
        # 状态码为2, 代表该雷被玩家标记为雷
        elif self.status_code == 2:
            self.image = self.images['flag']
        # 状态码为3, 代表该雷被玩家标记为问号
        elif self.status_code == 3:
            self.image = self.images['ask']
        # 状态码为4, 代表该雷正在被鼠标左右键双击
        elif self.status_code == 4:
            assert not self.is_mine_flag
            self.image = self.images[str(self.num_mines_around)]
        # 状态码为5, 代表该雷在被鼠标左右键双击的雷的周围
        elif self.status_code == 5:
            self.image = self.images['0']
        # 状态码为6, 代表该雷被踩中
        elif self.status_code == 6:
            assert self.is_mine_flag
            self.image = self.images['blood']
        # 状态码为7, 代表该雷被误标
        elif self.status_code == 7:
            assert not self.is_mine_flag
            self.image = self.images['error']
        # 绑定图片到屏幕
        screen.blit(self.image, self.rect)
    @property
    def opened(self):
        return self.status_code == 1

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
        # 雷型矩阵
        self.mines_matrix = []
        for j in range(GAME_MATRIX_SIZE[1]):
            mines_line = []
            for i in range(GAME_MATRIX_SIZE[0]):
                position = i * GRIDSIZE + BORDERSIZE, (j + 2) * GRIDSIZE
                mines_line.append(Mine(images=images, position=position))
            self.mines_matrix.append(mines_line)
        # 随机埋雷
        for i in random.sample(range(GAME_MATRIX_SIZE[0]*GAME_MATRIX_SIZE[1]), NUM_MINES):
            self.mines_matrix[i//GAME_MATRIX_SIZE[0]][i%GAME_MATRIX_SIZE[0]].burymine()
        # 游戏当前的状态
        self.status_code = -1
        # 记录鼠标按下时的位置和按的键
        self.mouse_pos = None
        self.mouse_pressed = None

    '''画出当前的游戏状态图'''
    def draw(self, screen):
        for row in self.mines_matrix:
            for item in row: item.draw(screen)

    '''设置当前的游戏状态'''
    def setstatus(self, status_code):
        # 0: 正在进行游戏, 1: 游戏结束, -1: 游戏还没开始
        self.status_code = status_code

    '''根据玩家的鼠标操作情况更新当前的游戏状态地图'''
    def update(self, mouse_pressed=None, mouse_pos=None, type_='down'):
        assert type_ in ['down', 'up']
        # 记录鼠标按下时的位置和按的键
        if type_ == 'down' and mouse_pos is not None and mouse_pressed is not None:
            self.mouse_pos = mouse_pos
            self.mouse_pressed = mouse_pressed
        # 鼠标点击的范围不在游戏地图内, 无响应
        if self.mouse_pos[0] < BORDERSIZE or self.mouse_pos[0] > SCREENSIZE[0] - BORDERSIZE or \
           self.mouse_pos[1] < GRIDSIZE * 2 or self.mouse_pos[1] > SCREENSIZE[1] - BORDERSIZE:
            return
        # 鼠标点击在游戏地图内, 代表开始游戏(即可以开始计时了)
        if self.status_code == -1:
            self.status_code = 0
        # 如果不是正在游戏中, 按鼠标是没有用的
        if self.status_code != 0:
            return
        # 鼠标位置转矩阵索引
        coord_x = (self.mouse_pos[0] - BORDERSIZE) // GRIDSIZE
        coord_y = self.mouse_pos[1] // GRIDSIZE - 2
        mine_clicked = self.mines_matrix[coord_y][coord_x]
        # 鼠标按下
        if type_ == 'down':
            # --鼠标左右键同时按下
            if self.mouse_pressed[0] and self.mouse_pressed[2]:
                if mine_clicked.opened and mine_clicked.num_mines_around > 0:
                    mine_clicked.setstatus(status_code=4)
                    num_flags = 0
                    coords_around = self.getaround(coord_y, coord_x)
                    for (j, i) in coords_around:
                        if self.mines_matrix[j][i].status_code == 2:
                            num_flags += 1
                    if num_flags == mine_clicked.num_mines_around:
                        for (j, i) in coords_around:
                            if self.mines_matrix[j][i].status_code == 0:
                                self.openmine(i, j)
                    else:
                        for (j, i) in coords_around:
                            if self.mines_matrix[j][i].status_code == 0:
                                self.mines_matrix[j][i].setstatus(status_code=5)
        # 鼠标释放
        else:
            # --鼠标左键
            if self.mouse_pressed[0] and not self.mouse_pressed[2]:
                if not (mine_clicked.status_code == 2 or mine_clicked.status_code == 3):
                    if self.openmine(coord_x, coord_y):
                        self.setstatus(status_code=1)
            # --鼠标右键
            elif self.mouse_pressed[2] and not self.mouse_pressed[0]:
                if mine_clicked.status_code == 0:
                    mine_clicked.setstatus(status_code=2)
                elif mine_clicked.status_code == 2:
                    mine_clicked.setstatus(status_code=3)
                elif mine_clicked.status_code == 3:
                    mine_clicked.setstatus(status_code=0)
            # --鼠标左右键同时按下
            elif self.mouse_pressed[0] and self.mouse_pressed[2]:
                mine_clicked.setstatus(status_code=1)
                coords_around = self.getaround(coord_y, coord_x)
                for (j, i) in coords_around:
                    if self.mines_matrix[j][i].status_code == 5:
                        self.mines_matrix[j][i].setstatus(status_code=0)

    '''打开雷'''
    def openmine(self, x, y):
        mine_clicked = self.mines_matrix[y][x]
        if mine_clicked.is_mine_flag:
            for row in self.mines_matrix:
                for item in row:
                    if not item.is_mine_flag and item.status_code == 2:
                        item.setstatus(status_code=7)
                    elif item.is_mine_flag and item.status_code == 0:
                        item.setstatus(status_code=1)
            mine_clicked.setstatus(status_code=6)
            return True
        mine_clicked.setstatus(status_code=1)
        coords_around = self.getaround(y, x)
        num_mines = 0
        for (j, i) in coords_around:
            num_mines += int(self.mines_matrix[j][i].is_mine_flag)
        mine_clicked.setnumminesaround(num_mines)
        if num_mines == 0:
            for (j, i) in coords_around:
                if self.mines_matrix[j][i].num_mines_around == -1:
                    self.openmine(i, j)
        return False

    '''获得坐标点的周围坐标点'''
    def getaround(self, row, col):
        coords = []
        for j in range(max(0, row-1), min(row+1, GAME_MATRIX_SIZE[1]-1)+1):
            for i in range(max(0, col-1), min(col+1, GAME_MATRIX_SIZE[0]-1)+1):
                if j == row and i == col:
                    continue
                coords.append((j, i))
        return coords

    '''是否正在游戏中'''
    @property
    def gaming(self):
        return self.status_code == 0

    '''被标记为雷的雷数目'''
    @property
    def flags(self):
        num_flags = 0
        for row in self.mines_matrix:
            for item in row: num_flags += int(item.status_code == 2)
        return num_flags

    '''已经打开的雷的数目'''
    @property
    def openeds(self):
        num_openeds = 0
        for row in self.mines_matrix:
            for item in row: num_openeds += int(item.opened)
        return num_openeds

'''主函数'''
def main():
    # 游戏初始化
    pygame.init()
    screen = pygame.display.set_mode(SCREENSIZE)
    pygame.display.set_caption('扫雷')

    # 导入所有图片
    images = {}
    for key, value in IMAGE_PATHS.items():
        try:
            if key in ['face_fail', 'face_normal', 'face_success']:
                image = pygame.image.load(value)
                images[key] = pygame.transform.smoothscale(image, (int(GRIDSIZE*1.25), int(GRIDSIZE*1.25)))
            else:
                image = pygame.image.load(value).convert()
                images[key] = pygame.transform.smoothscale(image, (GRIDSIZE, GRIDSIZE))
        except pygame.error as e:
            print(f"无法加载图片 {key}: {value}")
            print(f"错误信息: {e}")
            sys.exit(1)

    # 载入字体
    font = pygame.font.Font(FONT_PATH, FONT_SIZE)

    # 实例化游戏地图
    minesweeper_map = MinesweeperMap(images)
    position = (SCREENSIZE[0] - int(GRIDSIZE * 1.25)) // 2, (GRIDSIZE * 2 - int(GRIDSIZE * 1.25)) // 2
    emoji_button = EmojiButton(images, position=position)
    fontsize = font.size(str(NUM_MINES))
    remaining_mine_board = TextBoard(str(NUM_MINES), font, (30, (GRIDSIZE*2-fontsize[1])//2-2), RED)
    fontsize = font.size('000')
    time_board = TextBoard('000', font, (SCREENSIZE[0]-30-fontsize[0], (GRIDSIZE*2-fontsize[1])//2-2), RED)
    time_board.is_start = False

    # 游戏主循环
    clock = pygame.time.Clock()
    while True:
        screen.fill(BACKGROUND_COLOR)
        # 按键检测
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                mouse_pressed = pygame.mouse.get_pressed()
                minesweeper_map.update(mouse_pressed=mouse_pressed, mouse_pos=mouse_pos, type_='down')
            elif event.type == pygame.MOUSEBUTTONUP:
                minesweeper_map.update(type_='up')
                if emoji_button.rect.collidepoint(pygame.mouse.get_pos()):
                    minesweeper_map = MinesweeperMap(images)
                    time_board.update('000')
                    time_board.is_start = False
                    remaining_mine_board.update(str(NUM_MINES))
                    emoji_button.setstatus(status_code=0)

        # --更新时间显示
        if minesweeper_map.gaming:
            if not time_board.is_start:
                start_time = time.time()
                time_board.is_start = True
            time_board.update(str(int(time.time() - start_time)).zfill(3))

        # --更新剩余雷的数目显示
        remianing_mines = max(NUM_MINES - minesweeper_map.flags, 0)
        remaining_mine_board.update(str(remianing_mines).zfill(2))

        # --更新表情
        if minesweeper_map.status_code == 1:
            emoji_button.setstatus(status_code=1)
        if minesweeper_map.openeds + minesweeper_map.flags == GAME_MATRIX_SIZE[0] * GAME_MATRIX_SIZE[1]:
            minesweeper_map.status_code = 1
            emoji_button.setstatus(status_code=2)

        # --显示当前的游戏状态地图
        minesweeper_map.draw(screen)
        emoji_button.draw(screen)
        remaining_mine_board.draw(screen)
        time_board.draw(screen)

        # --更新屏幕
        pygame.display.update()
        clock.tick(FPS)


'''run'''
if __name__ == '__main__':
    main()
