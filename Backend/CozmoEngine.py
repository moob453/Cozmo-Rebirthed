from time import sleep


class Engine:
    def __init__(self, energy, boardem, sleeping):
        self.energy = energy
        self.boardem = boardem
        self.sleeping = sleeping

    def tick(self):
        if self.boardem > 100:
            self.sleeping = True
        if self.sleeping:
            print("cozmo is sleeping")
            self.boardem = 0
            sleep(0.1)
        self.boardem += 1
        sleep(0.1)


Cozmo = Engine(100, 0, False)
while True:
    
    Cozmo.tick()
    print(Cozmo.boardem)
    if Cozmo.boardem > 50:
        print("cozmo is getting bored")