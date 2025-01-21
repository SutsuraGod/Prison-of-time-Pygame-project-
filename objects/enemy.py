import assets
import pygame
import configs
import random
import groups

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.start_health = 4
        self.start_speed = 180 // configs.FPS

        self.health = 4
        self.last_enemy_attack_time = 0
        self.cooldown_attack = 1000
        self.right_images = [assets.load_sprite('run1.png'),
                             assets.load_sprite('run2.png'),
                             assets.load_sprite('run3.png'),
                             assets.load_sprite('run7.png'),
                             assets.load_sprite('run8.png'),
                             ]
        self.left_images = [pygame.transform.flip(image, True, False) for image in self.right_images]

        self.image = self.right_images[0]
        self.image = pygame.transform.scale(self.image, (100, 100))
        self.counter_images = 0

        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = 180 // configs.FPS

        # переменные для реализаци движения врага по произвольной траектории,
        # которая меняется через некоторые промежутки времени
        self.direction1 = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.change_time = pygame.time.get_ticks() + random.randint(100000, 300000)

        self.dot = ''
        self.dot_timer = 0

    def move(self, player, player_rect, obstacles, player_pos):  # метод для реализации движения врага
        if self.health <= 0:
            groups.current_level.enemies.remove(self)
            self.kill()
        
        if self.dot_timer % 60 == 0:
            if self.dot == 'fire':
                self.health -= 1
            if self.dot == 'freeze':
                self.speed = 60 // configs.FPS

        if self.dot_timer != 0:
            self.dot_timer -= 1
        
        if self.dot_timer == 0:
            self.speed = self.start_speed

        # рассчитываем расстояние до игрока простым способом
        distance_to_player = ((player_pos[0] - self.rect.x) ** 2 + (player_pos[1] - self.rect.y) ** 2) ** 0.5
        # если расстояние менее 400, то враг переходит в состояние преследования
        if distance_to_player < 400:
            self.state = "chase"
        else:
            self.state = "patrol"

        if self.state == "chase":  # Режим преследования
            # Рассчитываем направление врага к игроку с помощью вектора
            direction = pygame.math.Vector2(player_rect.centerx - self.rect.centerx,
                                            player_rect.centery - self.rect.centery)

            # Анимация движения
            if direction[0] < 0:
                if self.counter_images % 6 == 0:
                    self.left_images.append(self.left_images.pop(0))
                    self.image = self.left_images[0]
                    self.image = pygame.transform.scale(self.image, (100, 100))
                    self.mask = pygame.mask.from_surface(self.image)
                self.counter_images += 1
            else:
                if self.counter_images % 6 == 0:
                    self.right_images.append(self.right_images.pop(0))
                    self.image = self.right_images[0]
                    self.image = pygame.transform.scale(self.image, (100, 100))
                    self.mask = pygame.mask.from_surface(self.image)
                self.counter_images += 1

            # Если враг достиг игрока, останавливаем движение
            if direction.length() <= 10:
                current_enemy_attack_time = pygame.time.get_ticks()
                if current_enemy_attack_time - self.last_enemy_attack_time >= self.cooldown_attack:
                    player.health -= 1
                    self.last_enemy_attack_time = current_enemy_attack_time
                return

            direction = direction.normalize()  # Нормализуем, чтобы скорость была постоянной
            new_position = self.rect.center + direction * self.speed  # Двигаем врага

            # Проверка столкновений с препятствиями
            if self.rect.left <= 50 or self.rect.right >= configs.SCREEN_WIDTH - 50:
                self.direction1.x *= -1

            if self.rect.top <= 50 or self.rect.bottom >= configs.SCREEN_HEIGHT - 50:
                self.direction1.y *= -1

            for obstacle in obstacles:
                if pygame.sprite.collide_mask(self, obstacle):
                    # Препятствие найдено, пытаемся обойти его
                    self.avoid_obstacle(obstacle, direction)
                    return

            # Если нет столкновения, обновляем позицию врага
            self.rect.center = new_position

        else:  # Режим патрулирования
            # Проверка столкновений с препятствиями
            for obstacle in obstacles:
                if pygame.sprite.collide_mask(self, obstacle):
                    # Препятствие найдено, пытаемся обойти его
                    self.avoid_obstacle(obstacle, self.direction1)
                    return

            # Анимация движения
            if self.direction1[0] < 0:
                if self.counter_images % 6 == 0:
                    self.left_images.append(self.left_images.pop(0))
                    self.image = self.left_images[0]
                    self.image = pygame.transform.scale(self.image, (100, 100))
                    self.mask = pygame.mask.from_surface(self.image)
                self.counter_images += 1
            else:
                if self.counter_images % 6 == 0:
                    self.right_images.append(self.right_images.pop(0))
                    self.image = self.right_images[0]
                    self.image = pygame.transform.scale(self.image, (100, 100))
                    self.mask = pygame.mask.from_surface(self.image)
                self.counter_images += 1
            #

            # Двигаем врага
            self.rect.x += self.direction1.x * self.speed
            self.rect.y += self.direction1.y * self.speed

            # Проверка столкновения со стенами
            if self.rect.left <= 50 or self.rect.right >= configs.SCREEN_WIDTH - 50:
                self.direction1.x *= -1

            if self.rect.top <= 50 or self.rect.bottom >= configs.SCREEN_HEIGHT - 50:
                self.direction1.y *= -1

            # Смена направления
            if pygame.time.get_ticks() > self.change_time:
                self.direction1 = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
                self.change_time = pygame.time.get_ticks() + random.randint(10000, 30000)

    def avoid_obstacle(self, obstacle, direction):  # Метод для реализации обхода препятствий, отклоняя направление

        offset = 7  # Сколько будет отклоняться враг от исходного направления

        # Пробуем сместить врага вправо или влево
        new_direction = direction.rotate(135)  # Поворот на 135 градусов
        new_position = self.rect.center + new_direction * offset
        self.rect.center = new_position

        self.rect.center += direction * 1  # Медленно двигаться по текущему направлению
