import math
import random
import time
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

WIN_W, WIN_H = 1000, 700
ARENA_SIZE = 20.0
NUM_MICE = 8
NUM_OBSTACLES = 6
CAT_SPEED = 3.6
CAT_ROT_SPEED = 140.0
MOUSE_SPEED = 1.4
CATCH_DISTANCE = 1.0
GAME_TIME = 90.0
INITIAL_LIVES = 3

state = {
    'score': 0,
    'lives': INITIAL_LIVES,
    'time_left': GAME_TIME,
    'game_over': False,
    'last_time': time.time(),
    'cat_pos': [0.0, 0.0, 0.0],
    'cat_angle': 0.0,
    'cat_height': 0.5,
    'cam_angle': -30.0,
    'cam_height': 7.0,
    'cam_radius': 14.0,
    'mice': [],
    'obstacles': []
}

keys_down = set()

def rand_in_arena(margin=1.5):
    r = ARENA_SIZE - margin
    return (random.uniform(-r, r), 0.0, random.uniform(-r, r))

def clamp(v, a, b):
    return max(a, min(b, v))

def spawn_mouse():
    x, _, z = rand_in_arena(margin=3.0)
    return {'pos': [x, 0.0, z], 'angle': random.uniform(0, 360), 'speed': MOUSE_SPEED, 'cool': random.uniform(0.4, 1.8)}

def spawn_obstacle():
    x, _, z = rand_in_arena(margin=4.0)
    sx = random.uniform(1.0, 3.0)
    sz = random.uniform(1.0, 3.0)
    return {'pos': [x, 0.0, z], 'sx': sx, 'sz': sz}

def draw_floor():
    half = ARENA_SIZE
    glDisable(GL_LIGHTING)
    glColor3f(0.82, 0.71, 0.55)
    glBegin(GL_QUADS)
    glVertex3f(-half, 0.0, -half)
    glVertex3f(half, 0.0, -half)
    glVertex3f(half, 0.0, half)
    glVertex3f(-half, 0.0, half)
    glEnd()
    glEnable(GL_LIGHTING)

def draw_walls():
    half = ARENA_SIZE
    wall_h = 2.2
    thickness = 0.2
    glPushMatrix()
    glDisable(GL_LIGHTING)
    glColor3f(0.0, 1.0, 0.0)
    glPushMatrix(); glTranslatef(0, wall_h/2.0, -half - thickness/2.0); glScalef(2*half + 0.2, wall_h, thickness); glutSolidCube(1.0); glPopMatrix()
    glPushMatrix(); glTranslatef(0, wall_h/2.0, half + thickness/2.0); glScalef(2*half + 0.2, wall_h, thickness); glutSolidCube(1.0); glPopMatrix()
    glPushMatrix(); glTranslatef(-half - thickness/2.0, wall_h/2.0, 0); glScalef(thickness, wall_h, 2*half + 0.2); glutSolidCube(1.0); glPopMatrix()
    glPushMatrix(); glTranslatef(half + thickness/2.0, wall_h/2.0, 0); glScalef(thickness, wall_h, 2*half + 0.2); glutSolidCube(1.0); glPopMatrix()
    glEnable(GL_LIGHTING)
    glPopMatrix()

def draw_cat():
    x, _, z = state['cat_pos']
    angle = state['cat_angle']
    glPushMatrix()
    glTranslatef(x, state['cat_height'], z)
    glRotatef(-angle, 0, 1, 0)
    glEnable(GL_COLOR_MATERIAL)
    glColor3f(1.0, 1.0, 1.0)
    glPushMatrix(); glScalef(0.9, 0.5, 1.2); glutSolidSphere(0.5, 24, 18); glPopMatrix()
    glPushMatrix(); glTranslatef(0.0, 0.45, 0.6); glutSolidSphere(0.28, 20, 16)
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix(); glTranslatef(0.14, 0.28, 0.0); glRotatef(-30,0,0,1); glBegin(GL_TRIANGLES); glVertex3f(0,0,0); glVertex3f(-0.08,0.15,0); glVertex3f(0.08,0.15,0); glEnd(); glPopMatrix()
    glPushMatrix(); glTranslatef(-0.14, 0.28, 0.0); glRotatef(30,0,0,1); glBegin(GL_TRIANGLES); glVertex3f(0,0,0); glVertex3f(-0.08,0.15,0); glVertex3f(0.08,0.15,0); glEnd(); glPopMatrix()
    glPopMatrix()
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix(); glTranslatef(0.0, 0.3, -0.6); glRotatef(-145,1,0,0); quad=gluNewQuadric(); gluCylinder(quad,0.08,0.06,0.9,10,1); gluDeleteQuadric(quad); glPopMatrix()
    glDisable(GL_COLOR_MATERIAL)
    glPopMatrix()

def draw_mouse(m):
    x, _, z = m['pos']
    glPushMatrix()
    glTranslatef(x, 0.12, z)
    glColor3f(0.7, 0.7, 0.7)
    glutSolidSphere(0.18, 12, 10)
    glPopMatrix()

def draw_obstacle(ob):
    x, _, z = ob['pos']
    sx, sz = ob['sx'], ob['sz']
    glPushMatrix()
    glTranslatef(x, 0.5, z)
    glColor3f(1.0, 0.0, 0.0)
    glScalef(sx, 1.0, sz)
    glutSolidCube(1.0)
    glPopMatrix()

def reset_game():
    state['score']=0
    state['lives']=INITIAL_LIVES
    state['time_left']=GAME_TIME
    state['game_over']=False
    state['cat_pos']=[0.0,0.0,0.0]
    state['cat_angle']=0.0
    state['mice']=[spawn_mouse() for _ in range(NUM_MICE)]
    state['obstacles']=[spawn_obstacle() for _ in range(NUM_OBSTACLES)]
    state['last_time']=time.time()

def process_input(dt):
    if 'a' in keys_down: state['cat_angle']+=CAT_ROT_SPEED*dt
    if 'd' in keys_down: state['cat_angle']-=CAT_ROT_SPEED*dt
    move=0.0
    if 'w' in keys_down: move+=CAT_SPEED*dt
    if 's' in keys_down: move-=CAT_SPEED*dt
    if move!=0.0:
        rad=math.radians(state['cat_angle'])
        dx=math.sin(rad)*move
        dz=math.cos(rad)*move
        nx=state['cat_pos'][0]+dx
        nz=state['cat_pos'][2]+dz
        blocked=False
        for ob in state['obstacles']:
            ox, _, oz = ob['pos']
            halfx=ob['sx']/2.0+0.4
            halfz=ob['sz']/2.0+0.4
            if (ox-halfx<=nx<=ox+halfx) and (oz-halfz<=nz<=oz+halfz): blocked=True; break
        bound=ARENA_SIZE-0.8
        if not blocked: state['cat_pos'][0]=clamp(nx,-bound,bound); state['cat_pos'][2]=clamp(nz,-bound,bound)

def update_mice(dt):
    for m in state['mice']:
        m['cool']-=dt
        if m['cool']<=0.0: m['angle']+=random.uniform(-80,80); m['cool']=random.uniform(0.6,2.0)
        rad=math.radians(m['angle'])
        dx=math.sin(rad)*m['speed']*dt
        dz=math.cos(rad)*m['speed']*dt
        nx=m['pos'][0]+dx
        nz=m['pos'][2]+dz
        bound=ARENA_SIZE-1.0
        if nx<-bound or nx>bound: m['angle']=180-m['angle']; nx=clamp(nx,-bound,bound)
        if nz<-bound or nz>bound: m['angle']=-m['angle']; nz=clamp(nz,-bound,bound)
        for ob in state['obstacles']:
            ox,_,oz=ob['pos']
            if abs(nx-ox)<(ob['sx']/1.8) and abs(nz-oz)<(ob['sz']/1.8): m['angle']+=random.choice([100,-100]); nx=m['pos'][0]; nz=m['pos'][2]; break
        m['pos'][0]=nx; m['pos'][2]=nz
        if random.random()<0.01: m['angle']+=random.uniform(-20,20)

def check_catches():
    cx, _, cz = state['cat_pos']
    for m in list(state['mice']):
        mx, _, mz = m['pos']
        d2=(mx-cx)*(mx-cx)+(mz-cz)*(mz-cz)
        if d2<=(CATCH_DISTANCE*CATCH_DISTANCE):
            state['mice'].remove(m)
            state['score']+=1
            state['mice'].append(spawn_mouse())

def idle():
    now=time.time()
    dt=now-state['last_time']
    if dt<=0: dt=1e-4
    if dt>0.12: dt=0.12
    state['last_time']=now
    if not state['game_over']:
        state['time_left']-=dt
        if state['time_left']<=0.0: state['game_over']=True
        process_input(dt)
        update_mice(dt)
        check_catches()
    glutPostRedisplay()

def draw_text(x,y,text,font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(float(x),float(y))
    for ch in str(text): glutBitmapCharacter(font, ord(ch))

def draw_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_LIGHTING)
    glColor3f(1.0,1.0,1.0)
    draw_text(12, WIN_H-28,f"Score: {state['score']}")
    draw_text(12, WIN_H-52,f"Lives: {state['lives']}")
    draw_text(12, WIN_H-76,f"Time: {int(state['time_left'])}s")
    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display():
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, WIN_W/float(WIN_H), 0.1, 200.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    cam_ang_rad=math.radians(state['cam_angle'])
    cam_x=math.cos(cam_ang_rad)*state['cam_radius']
    cam_z=math.sin(cam_ang_rad)*state['cam_radius']
    catx,_,catz=state['cat_pos']
    eye=(catx+cam_x,state['cam_height'],catz+cam_z)
    center=(catx,0.8,catz)
    gluLookAt(eye[0],eye[1],eye[2],center[0],center[1],center[2],0,1,0)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_NORMALIZE)
    light_pos=[8.0,18.0,8.0,1.0]
    glLightfv(GL_LIGHT0,GL_POSITION,light_pos)
    glLightfv(GL_LIGHT0,GL_DIFFUSE,[0.95,0.95,0.95,1.0])
    glLightfv(GL_LIGHT0,GL_SPECULAR,[0.8,0.8,0.8,1.0])
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT,[0.05,0.05,0.05,1.0])
    draw_floor()
    draw_walls()
    for ob in state['obstacles']: draw_obstacle(ob)
    for m in state['mice']: draw_mouse(m)
    draw_cat()
    draw_hud()
    glutSwapBuffers()

def keyboard(key,x,y):
    k=key.decode('utf-8').lower() if isinstance(key, bytes) else key.lower()
    if k=='f' or ord(k[0])==27: glutLeaveMainLoop()
    elif k=='r': reset_game()
    elif k in ('w','a','s','d'): keys_down.add(k)

def keyboard_up(key,x,y):
    k=key.decode('utf-8').lower() if isinstance(key, bytes) else key.lower()
    if k in keys_down: keys_down.remove(k)

def special_keys(key,x,y):
    if key==GLUT_KEY_LEFT: state['cam_angle']-=6.0
    elif key==GLUT_KEY_RIGHT: state['cam_angle']+=6.0

def init_gl():
    glClearColor(0.5,0.8,1.0,1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_COLOR_MATERIAL)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGB|GLUT_DEPTH)
    glutInitWindowSize(WIN_W,WIN_H)
    glutInitWindowPosition(50,50)
    glutCreateWindow(b"Cat Chase 3D")
    init_gl()
    reset_game()
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special_keys)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__=='__main__': main()
