import unittest


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.max_hp = 100
        self.hp = 100

    def take_damage(self, damage):
        self.hp -= damage


class TestEnemy(unittest.TestCase):

    def test_enemy_takes_damage(self):
        enemy = Enemy(0, 300)

        enemy.take_damage(10)

        self.assertEqual(enemy.hp, 90)


if __name__ == "__main__":
    unittest.main()