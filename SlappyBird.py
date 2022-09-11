import os
import pygame
from pygame.locals import *
from pygame import mixer
import math
import sqlite3
import random
import pygame_menu
import time

#bools
pressed_1 = False
isSlappingPerson = False
hasFinishedTutorial = False

#VARIABLES
mapX = -3650 # goes backward: -1, -2 ...
initialMapX = mapX
SCREEN_WIDTH = 1980
SCREEN_HEIGHT = 1080
GAME_SPEED = 3
obstacle_path = "assets/sprites/obstacles"
people_path = "assets/sprites/people"
bird_fly_path = "assets/sprites/bird/fly"
bird_slap_path = 'assets/sprites/bird/slap'
clock = pygame.time.Clock()

#LIMITS
skyLimit = 80
groundLimit = 1000

#Sound
mixer.init()
mixer.music.set_volume(0.7)
audio_slap_path = 'assets/audio/slap/slap1.mp3'
audio_slap_miss_path = 'assets/audio/slap/whoosh.mp3'
audio_songs_path = 'assets/audio/songs/'
audio_jump_path = 'assets/audio/jump/'
audio_dive_path = 'assets/audio/dive/whoosh.mp3'

#Bird
standardBirdSize = (220, 220) # image x, y
gravityMagnitude = 0.3;
pygame.mixer.init()


class Bird(pygame.sprite.Sprite):
    speed = 0 #initial speed value

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        
       
        self.lives = 3
        self.totalInvulnerabilityTime = 60 * 3 # 3 seconds
        self.currentInvulnerabilityTime = self.totalInvulnerabilityTime
        self.isInvulnerable = False

        self.waitTimerBattery = 0
        self.waitTimeBattery = 75 # 1.25 seconds

        self.isSlapping = False
        self.isJumping = False

        self.image = pygame.image.load('assets/sprites/bird/fly/passaro_direita.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.rect[0] = 400 # Bird spot
        self.rect[1] = 80

        self.current_image = 0
        self.animation_frames = 9 # how many frames to wait before changing animation
        self.current_frame = 0
        self.index = 0

        self.AllAnimImages = getImageList(bird_fly_path)
        self.AnimImage = self.AllAnimImages[self.index] # 'AnimImage' is the current image of the animation.
                
        self.AllSlapAnimImages = getImageList(bird_slap_path)
        self.slapAnimNum = len(self.AllSlapAnimImages)

        #Jump animation
        self.goBackDown = False
        self.jump_limit = 280
        self.jump_acceleration = 0.4
        self.jump_speed = 3
        self.birdSizeX = standardBirdSize[0]
        self.birdSizeY = standardBirdSize[1]
        self.jumpImage = pygame.image.load('assets/sprites/bird/passaro_direita_jump.png').convert_alpha()
        self.jump_audio_list = getAudioList(audio_jump_path)

    def update(self):
        global isSlappingPerson
        if self.isJumping:
            #self.runAnimation(self.animation_frames, self.AllAnimImages) # fly
            self.runJumpAnimation()
        elif self.isSlapping:
            self.runAnimation(self.animation_frames, self.AllSlapAnimImages)
            isSlappingPerson = True
        else:
            self.runAnimation(self.animation_frames, self.AllAnimImages) # fly
            
        if self.isInvulnerable:
            self.currentInvulnerabilityTime -=1
            #TODO change image
            if self.currentInvulnerabilityTime == 0:
                self.currentInvulnerabilityTime = self.totalInvulnerabilityTime
                self.isInvulnerable = False

        #update mask
        self.image = self.AnimImage
        self.mask = pygame.mask.from_surface(self.image) # image without background to handle collision

        self.unDive()
        self.buttonPress(700) #whatefuck

        #apply movement changes
        self.rect[1] = self.rect[1] + self.speed


    def checkObsCollision(self, collideWith):
        if not pygame.sprite.collide_mask(self, collideWith) == None: # if it collides
            if not self.isInvulnerable:
                self.isInvulnerable = True
                self.lives -= 1
                
                pygame.mixer.Channel(1).play(pygame.mixer.Sound('assets/audio/hit/hit.mp3'))
                pygame.mixer.Channel(1).set_volume(0.4)

    def checkPersonCollision(self, collideWith):
        global batteryCharge
        
        if not pygame.sprite.collide_mask(self, collideWith) == None:
            pygame.mixer.Channel(6).play(pygame.mixer.Sound(audio_slap_path))
            if self.waitTimerBattery == 0:
                self.waitTimerBattery += 1
                batteryCharge += 1
                if batteryCharge == 4:
                    batteryCharge = 3

            return True



    def slap(self):
        global isSlappingPerson
        self.current_frame = 10
        self.index = 0 # restart index for slappin animation start in beggining
        self.isSlapping = True
        isSlappingPerson = True

    def jump(self):
        audio = random.choice(self.jump_audio_list)
        audio.play()

        #self.index = 0 # restart index for slappin animation start in beggining
        self.isJumping = True
        
    def runJumpAnimation(self): #animation is different then rest bird animations
        self.AnimImage = self.jumpImage
        if self.birdSizeX < standardBirdSize[0]:
            self.jump_speed = 0
            self.birdSizeX = standardBirdSize[0]
            self.birdSizeY = standardBirdSize[1]
            self.isJumping = False
            self.goBackDown = False

        else:
            self.birdSizeX = self.birdSizeX + self.jump_speed
            self.birdSizeY = self.birdSizeY + self.jump_speed
            self.AnimImage = pygame.transform.scale(self.AnimImage, (self.birdSizeX, self.birdSizeY)) # image is from Sprite class outside my code
            if self.birdSizeX < self.jump_limit and self.goBackDown == False:
                self.jump_speed += self.jump_acceleration
            else:
                self.goBackDown = True
                self.jump_speed -= self.jump_acceleration

    def runAnimation(self, numOfWaitFrames, listOfAllImages): #listOfAllImages in this animation
        if self.index < len(listOfAllImages):
            if self.current_frame >= numOfWaitFrames: # has to wait for frames to change animation
                self.current_frame = 0
                self.AnimImage = listOfAllImages[self.index]
                self.index +=1
        else:
            self.isSlapping = False # add other animation variables here all to false
            self.index = 0
             
        self.AnimImage = pygame.transform.scale(self.AnimImage, standardBirdSize) #bigger
        self.current_frame += 1

    def buttonPress(self, diveHeight):
        if pressed_1:
            self.diveHold(diveHeight)
            #print("\n" + str(self.rect[1]) + " button pressed \n")

    def diveHold(self, diveHeight): 
        if self.shouldItDive(diveHeight): 
            self.speed = self.applySacredFormula(diveHeight)

            #because they are float values somewhat in this range (change if increase or decrease base acceleration alot)
            if self.rect[1] < diveHeight + 10 and self.rect[1] > diveHeight -10:
                self.speed = 0

    def unDive(self): # height = rect[1] = y  is counted top to bottom so 0 height is the sky
        if self.rect[1] > skyLimit or self.rect[1] < groundLimit: 
            #self.speed = self.applySacredFormulaUnDive(70)
            self.speed -= 1
            #print(self.speed)
            if self.rect[1] < skyLimit:
                self.rect[1] = skyLimit # safety mesure
            #because they are float values somewhat in this range (change if increase or decrease base acceleration alot)
            if self.rect[1] < skyLimit + 20 and self.rect[1] > skyLimit -10:
                self.speed = 0

    #if its below the place the button takes him this returns false
    def shouldItDive(self, diveHeight):
        if self.rect[1] > diveHeight:
            return False
        elif self.rect[1] < skyLimit - 10 or self.rect[1] > groundLimit:
            return False
        else:
           return True
       
    def applySacredFormula(self, diveHeight):
        x = diveHeight - self.rect[1] #height
        #print("vel: " + str(math.sqrt(x * gravityMagnitude * 2)))
        return math.sqrt(x * gravityMagnitude * 2) #initial velocity (current velocity of dive)

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, image, ypos, xpos):
        pygame.sprite.Sprite.__init__(self)

        self.image = image
        self.rect = image.get_rect()
        self.rect[1] = ypos
        self.spawnLoc = xpos + mapX
        self.rect[0] = 1920

    def update(self):
        #update mask
        self.rect[0] -= GAME_SPEED   
        self.mask = pygame.mask.from_surface(self.image)


class Person(pygame.sprite.Sprite):
    def __init__(self, image, ypos, xpos):
        pygame.sprite.Sprite.__init__(self)

        self.image = image
        self.rect = image.get_rect()
        self.rect[1] = ypos
        self.rect[0] = xpos + mapX

    def update(self):
        #update mask
        self.rect[0] -= GAME_SPEED   
        self.mask = pygame.mask.from_surface(self.image)


def getImageDict(the_path, the_dict):
    filenames = [f for f in os.listdir(the_path) if f.endswith('.png') or f.endswith('.tif')]
    
    for name in filenames:
        imagename = os.path.splitext(name)[0] 
        the_dict[imagename] = pygame.image.load(os.path.join(the_path, name)).convert_alpha()

def getImageList(the_path):
    myImageList = []
    for file_name in os.listdir(the_path):
        theimage = pygame.image.load(the_path + os.sep + file_name).convert_alpha()
        x = the_path + os.sep + file_name
        myImageList.append(theimage)
    return myImageList

def getAudioList(the_path):
    myAudioList = []
    for file_name in os.listdir(the_path):
        x = the_path + os.sep + file_name
        y = file_name
        theaudio = pygame.mixer.Sound(the_path + file_name)
        myAudioList.append(theaudio)
    return myAudioList

pygame.init()
# Background
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
BACKGROUND = pygame.image.load('assets/sprites/background_day.png').convert()


pygame.display.set_caption('Slappy Bird')
FPS = 60

# Text Renderer
def text_format(message, textFont, textSize, textColor):
    newFont = pygame.font.Font(textFont, textSize)
    newText = newFont.render(message, 0, textColor)
 
    return newText

# Colors
white=(255, 255, 255)
black=(0, 0, 0)
gray=(50, 50, 50)
red=(255, 0, 0)
green=(0, 255, 0)
blue=(0, 0, 255)
yellow=(255, 255, 0)
 
# Game Fonts
font = "assets/fonts/pixelFont.ttf"

obstacle_dict = {} # dictionary with name of image as key (ex: "flower") and image as value
getImageDict(obstacle_path, obstacle_dict)

person_dict = {} # dictionary with name of image as key (ex: "chad") and image as value
getImageDict(people_path, person_dict)

#SQL to load all obstacles into the list
def execRowQuery(sqlite_select_Query):
    try:
        sqliteConnection = sqlite3.connect('assets/database/SlappyBirdDB.db')
        cursor = sqliteConnection.cursor()

        print(sqlite_select_Query)
        cursor.execute(sqlite_select_Query)
        record = cursor.fetchall()
        
        for row in record:
            print("\n new row: " + str(row))
            imgType = row[1]
            spawnLocation = row[2]
            height = row[3]
            
            newObstacle = Obstacle(obstacle_dict[imgType], height, spawnLocation)
            obstacle_list.append(newObstacle)
            
        cursor.close()

    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("The SQLite connection is closed")

#SQL to load all people into the list
def execRowQueryPeople(sqlite_select_Query):
    try:
        sqliteConnection = sqlite3.connect('assets/database/SlappyBirdDB.db')
        cursor = sqliteConnection.cursor()

        print(sqlite_select_Query)
        cursor.execute(sqlite_select_Query)
        record = cursor.fetchall()
        
        for row in record:
            print("\n new row: " + str(row))
            imgType = row[1]
            spawnLocation = row[2]
            height = row[3]
            
            newPerson = Person(person_dict[imgType], height, spawnLocation)
            people_list.append(newPerson)
            people_group.add(newPerson)
        cursor.close()

    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("The SQLite connection is closed")


obstacle_group = pygame.sprite.Group()
people_group = pygame.sprite.Group()
bird_group = pygame.sprite.Group()

obstacle_Query = 'SELECT * FROM Obstacles'
people_Query = 'SELECT * FROM People'

bird = Bird()
bird_group.add(bird)
obstacle_list = [] # list with all obstacle instances
people_list = [] # list with all people instances

def spawn():
    global initialMapX
    i = 0
    while i<len(obstacle_list): #check all spawn locations; i starts at 1!
        if mapX == -obstacle_list[i].spawnLoc + initialMapX:  #if map in one of those spawn locations, spawn the obstacle
            obstacle_group.add(obstacle_list[i])
        i += 1

def deSpawn():
    i = 0
    while i<len(obstacle_list):
        if -1000 < obstacle_list[i].rect[0] and -900 > obstacle_list[i].rect[0]: #which one of spawned obstacles should despawn
            obstacle_group.remove(obstacle_list[i])
            obstacle_list.pop(i)
        i+=1

'''
def deSpawn():
    i = 0
    while i<len(obstacle_list):
        if 300 < obstacle_list[i].rect[0] and 400 > obstacle_list[i].rect[0]: #which one of spawned obstacles should despawn
            obstacle_group.remove(obstacle_list[i])
            obstacle_list.pop(i)
        i+=1
'''
#-mapObstacles.get(i) = -spawn_location so -mapObstacles.get(i) - 2100 = - despawn_location


def initializer():
    global mapX
    global obstacle_list
    global people_list
    global obstacle_group
    global people_group
    obstacle_group = pygame.sprite.Group()
    people_group = pygame.sprite.Group()
    obstacle_list = [] # list with all obstacles
    people_list = [] # list with all people
    execRowQuery(obstacle_Query)
    execRowQueryPeople(people_Query)
    bird.lives = 3
    #mapX = 0


# Main Menu
def main_menu():
 
    menu=True
    selected="start"
 
    while menu:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
                quit()
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_UP:
                    selected="start"
                elif event.key==pygame.K_DOWN:
                    selected="quit"
                if event.key==pygame.K_RETURN:
                    if selected=="start":
                        initializer()
                        runGame()
                    if selected=="quit":
                        pygame.quit()
                        quit()
 
        # Main Menu UI
        screen.fill(blue)
        title=text_format("Slappy Bird", font, 90, yellow)
        if selected=="start":
            text_start=text_format("START", font, 75, white)
        else:
            text_start = text_format("START", font, 75, black)
        if selected=="quit":
            text_quit=text_format("QUIT", font, 75, white)
        else:
            text_quit = text_format("QUIT", font, 75, black)
 
        title_rect=title.get_rect()
        start_rect=text_start.get_rect()
        quit_rect=text_quit.get_rect()
        
        #sansyboi = pygame.image.load('assets/sprites/menu/sans.png')
        #smalSans = pygame.transform.scale(sansyboi, (450, 600))
        #screen.blit(smalSans, (1300, 600))
        #image_widget.translate(100, 100)

        # Main Menu Text
        screen.blit(title, (SCREEN_WIDTH/2 - (title_rect[2]/2), 80))
        screen.blit(text_start, (SCREEN_WIDTH/2 - (start_rect[2]/2), 300))
        screen.blit(text_quit, (SCREEN_WIDTH/2 - (quit_rect[2]/2), 360))
        screen.blit(text_quit, (SCREEN_WIDTH/2 - (quit_rect[2]/2), 360))


        #screen.blit(pygame.image.load('assets/sprites/menu/wally.png'), (1300, 90))
        screen.blit(pygame.transform.scale(pygame.image.load('assets/sprites/menu/passaro_dano.png'), (450, 600)), (1300, 00))
        screen.blit(pygame.transform.scale(pygame.image.load('assets/sprites/menu/majestic_bird.png'), (1000, 850)), (480, 200))
        screen.blit(pygame.transform.scale(pygame.image.load('assets/sprites/menu/passaro_baixo.png'), (450, 450)), (100, 00))
        pygame.display.update()
        clock.tick(FPS)

def showLifeCounter():
    life_text = text_format('vida ', font, 75, white)
    life_num = text_format(str(bird.lives), font, 75, red)
    screen.blit(life_text, (70, 45))
    screen.blit(life_num, (300, 45))


def wait(time): # time in seconds
    cutSceneTimer = 0
    while True:
        if cutSceneTimer < time * 60:
            clock.tick(FPS)
            cutSceneTimer +=1
        else: 
            cutSceneTimer = 0
            break
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit()
                quit()

empty_battery = pygame.image.load('assets/sprites/battery/empty_bat.png')
empty_battery = pygame.transform.scale(empty_battery, (400, 250))
charge1_bat = pygame.image.load('assets/sprites/battery/charge1_bat.png')
charge1_bat = pygame.transform.scale(charge1_bat, (400, 250))
charge2_bat = pygame.image.load('assets/sprites/battery/charge2_bat.png')
charge2_bat = pygame.transform.scale(charge2_bat, (400, 250))
charge3_bat = pygame.image.load('assets/sprites/battery/charge3_bat.png')
charge3_bat = pygame.transform.scale(charge3_bat, (400, 250))


batteryCharge = 0
def showBattery(): # if charged can jump
    if batteryCharge == 0:
        screen.blit(empty_battery, (1550, 0))
    elif batteryCharge == 1:
        screen.blit(charge1_bat, (1550, 0))
    elif batteryCharge == 2:
        screen.blit(charge2_bat, (1550, 0))
    elif batteryCharge == 3:
        screen.blit(charge3_bat, (1550, 0))
        tip_text = text_format('Clicka "c" para saltares de perigo!', font, 35, green)
        screen.blit(tip_text, (1200, 200))

def showStartCutscene():
    scene_image = pygame.image.load('assets/cutscene/intro/intro_manga_1.png')
    scene_image_2 = pygame.image.load('assets/cutscene/intro/intro_manga_2.png')
    scene_image_3 = pygame.image.load('assets/cutscene/intro/intro_manga_3.png')
    scene_image_4 = pygame.image.load('assets/cutscene/intro/intro_manga_4.png')

    screen.blit(scene_image, (0, 0))
    pygame.display.update()
    wait(3)

    screen.blit(scene_image_2, (0, 0))
    pygame.display.update()
    wait(3)

    screen.blit(scene_image_3, (0, 0))
    pygame.display.update()
    wait(3)

    screen.blit(scene_image_4, (0, 0))
    pygame.display.update()
    wait(3)

def runGame():

    #Load audio
    bushwick = pygame.mixer.Sound('assets/audio/songs/bushwick.mp3')
    tutorial = pygame.mixer.Sound('assets/audio/extra/tutorial.mp3')
    yoshi = pygame.mixer.Sound('assets/audio/songs/yoshi.mp3')
    tiagoChad = pygame.mixer.Sound('assets/audio/extra/tiagoChad.mp3')

    playSlapAudio = True
    slapped_chad = False
    global mapX
    global pressed_1
    global batteryCharge
    global isSlappingPerson
    global hasFinishedTutorial

    if hasFinishedTutorial:
        mapX = -12000 #skip tutorial

    while True:
        

        clock.tick(FPS)
        print (mapX)
        print("\n")


        # insert extras here
        if mapX == 199:
            hasFinishedTutorial = True
        
        if mapX == - 30:
            pygame.mixer.Channel(2).play(tutorial, 0, 0, 0)

        if mapX == - 380:
            pygame.mixer.Channel(3).play(bushwick, 0, 0, 2000)
        
        if mapX == - 4000:
            pygame.mixer.Channel(3).pause()
            pygame.mixer.Channel(4).play(yoshi, 0, 0, 2000)

        '''
        if mapX == - 7550 and slapped_chad:
            pygame.mixer.Channel(4).pause()
            pygame.mixer.Channel(3).unpause()
            pygame.mixer.Channel(5).play(tiagoChad, 0, 0, 1000)

            wait(40)        

        if mapX == 8000:
            pygame.mixer.Channel(3).pause()
            pygame.mixer.Channel(4).unpause()
        '''
        # SUS BIT

        if bird.lives == 0:
            main_menu()

        if mapX == 0:
            showStartCutscene()

        if bird.waitTimerBattery <= bird.waitTimeBattery and not bird.waitTimerBattery == 0:
            bird.waitTimerBattery += 1
        else:
            bird.waitTimerBattery = 0

        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == pygame.K_DOWN:
                    pressed_1 = True
                    if playSlapAudio:
                        mixer.music.load(audio_dive_path)
                        mixer.music.play()
                        playSlapAudio = False
                if event.key == pygame.K_SPACE:
                    if bird.waitTimerBattery ==	0:
                        Bird.slap(bird)                
                if event.key == pygame.K_c:
                    if batteryCharge == 3:
                        Bird.jump(bird)
                        batteryCharge = 0
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    pressed_1 = False
                    playSlapAudio = True

            if event.type == QUIT:
                pygame.quit()

        if bird.isSlapping:
            if isSlappingPerson == True:
                for person in people_list:
                    if bird.checkPersonCollision(person):
                        isSlappingPerson = True                            
                        if mapX < -7200 and mapX > -8000:
                            slapped_chad = True
                        break
                    elif not bird.checkPersonCollision(person):
                        isSlappingPerson = False
                        mixer.music.load(audio_slap_miss_path)
                        mixer.music.set_volume(0.2)
                        mixer.music.play()
            else:
                bird.waitTimerBattery = 0
        start = time.time()
           
        for obs in obstacle_list:
            if obstacle_group.has(obs):
                bird.checkObsCollision(obs)
        end = time.time() 

                    
        screen.blit(BACKGROUND, (mapX, 0))

        mapX -=1
        

        showLifeCounter()
        showBattery()

        spawn()
        deSpawn()


        bird_group.update()
        if mapX < - 350 and mapX > - 3600: # entre valores
            bird.image = pygame.image.load('assets/sprites/bird/passaro_phone.png').convert_alpha()
            bird.image = pygame.transform.scale(bird.image, (300, 600))
        bird_group.draw(screen)

        obstacle_group.update()
        obstacle_group.draw(screen)

        people_group.update()
        people_group.draw(screen)

        pygame.display.update()
        print("----------:   " + str(end - start))
main_menu()


#TODO  obstacle filled with obstacles only have 1 tiny path