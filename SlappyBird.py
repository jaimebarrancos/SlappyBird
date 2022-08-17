import os
import pygame
from pygame.locals import *
from pygame import mixer
import math
import sqlite3
import random

#button pressing bools
pressed_1 = False

#VARIABLES
SCREEN_WIDHT = 1980
SCREEN_HEIGHT = 1080
GAME_SPEED = 1
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
audio_songs_path = 'assets/audio/songs/'
audio_jump_path = 'assets/audio/jump/'

#Bird
standardBirdSize = (220, 220) # image x, y
gravityMagnitude = 0.3;
pygame.mixer.init()

class Bird(pygame.sprite.Sprite):
    speed = 0 #initial speed value

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        
        self.isSlapping = False
        self.isJumping = False

        self.image = pygame.image.load('assets/sprites/bird/fly/passaro_direita.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.rect[0] = 860
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
        self.jumpImage = pygame.image.load('assets/sprites/bird/fly/passaro_direita_2.png').convert_alpha()
        self.jump_audio_list = getAudioList(audio_jump_path)


    def update(self):
        
        if self.isJumping:
            #self.runAnimation(self.animation_frames, self.AllAnimImages) # fly
            self.runJumpAnimation()
        elif self.isSlapping:
            self.runAnimation(self.animation_frames, self.AllSlapAnimImages)
        else:
            self.runAnimation(self.animation_frames, self.AllAnimImages) # fly

        #update mask
        self.image = self.AnimImage
        self.mask = pygame.mask.from_surface(self.image) # image without background to handle collision

        self.unDive()
        self.buttonPress(700) #whatefuck

        #apply movement changes
        self.rect[1] = self.rect[1] + self.speed

    def slap(self):
        self.current_frame = 10
        self.index = 0 # restart index for slappin animation start in beggining
        self.isSlapping = True

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

    def checkCollision(collideWith):
        if pygame.sprite.collide_mask(bird, collideWith) == None:
            return False
        else: return True

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
        self.rect[0] = xpos

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
        self.rect[0] = xpos

    def update(self):
        #update mask
        self.rect[0] -= GAME_SPEED   
        self.mask = pygame.mask.from_surface(self.image)


    '''
# personNumber identifies the person to have food ex personNumber = 7, a 7a pessoa tem food
class Food(pygame.sprite.Sprite):
    def __init__(self, personNumber, ypos, xpos):
        pygame.sprite.Sprite.__init__(self)
    '''

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

# Background
BACKGROUND = pygame.image.load('assets/sprites/background_day.png')
screen = pygame.display.set_mode((SCREEN_WIDHT, SCREEN_HEIGHT))

pygame.init()
pygame.display.set_caption('Slappy Bird')

obstacle_dict = {} # dictionary with name of image as key (ex: "flower") and image as value
getImageDict(obstacle_path, obstacle_dict)

person_dict = {} # dictionary with name of image as key (ex: "chad") and image as value
getImageDict(people_path, person_dict)

#SQL to load all obstacles into the list
def execRowQuery(sqlite_select_Query, the_list):
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
            
            newObstacle = Obstacle(obstacle_dict[imgType], height, spawnLocation);
            obstacle_list.append(newObstacle)

            obstacle_group.add(newObstacle)
            obstacle_group.draw(screen)

        cursor.close()

    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("The SQLite connection is closed")

#SQL to load all people into the list
def execRowQueryPeople(sqlite_select_Query, the_list):
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
            
            newPerson = Person(person_dict[imgType], height, spawnLocation);
            people_list.append(newPerson)

            people_group.add(newPerson)
            people_group.draw(screen)

        cursor.close()

    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("The SQLite connection is closed")



#to exit main menu put false
startlevel = True
while startlevel:
    mapX = 0 # goes backward: -1, -2 ...

    obstacle_group = pygame.sprite.Group()
    people_group = pygame.sprite.Group()
    bird_group = pygame.sprite.Group()

    obstacle_Query = 'SELECT * FROM Obstacles'
    obstacle_list = [] # list with all obstacles
    
    people_Query = 'SELECT * FROM People'
    people_list = [] # list with all people

    execRowQuery(obstacle_Query, obstacle_list)
    execRowQueryPeople(people_Query, people_list)

    bird = Bird()
    bird_group.add(bird)

    startlevel = False


while True:

    clock.tick(60) #gets called every frame (60 fps)

    for event in pygame.event.get():
        if event.type == KEYDOWN:
            if event.key == pygame.K_DOWN:
                pressed_1 = True
            if event.key == pygame.K_SPACE:
                Bird.slap(bird)
            if event.key == pygame.K_c:
                Bird.jump(bird)
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                pressed_1 = False
        if event.type == QUIT:
            pygame.quit()

    if bird.isSlapping:
        for person in people_list:
            if Bird.checkCollision(person):
                mixer.music.load(audio_slap_path)
                mixer.music.play()
    else:  
        for obs in obstacle_list:
            if Bird.checkCollision(obs):
                print("Collision")
    
    screen.blit(BACKGROUND, (mapX, 0))
    mapX -=1

    bird_group.update()

    bird_group.draw(screen)

    obstacle_group.update()
    obstacle_group.draw(screen)

    people_group.update()
    people_group.draw(screen)

    pygame.display.update()




#TODO bird jump towords screen (increase size of bird while going up then decrease) 