from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtGui import QMatrix4x4, QVector3D
from PyQt5.QtCore import Qt
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

class MaterialPreviewWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(MaterialPreviewWidget, self).__init__(parent)
        self.shape = "Sphere"
        self.textures = {}
        self.rotation = QMatrix4x4()
        self.lastPos = None

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width / height, 0.1, 100.0)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -5)
        glMultMatrixf(self.rotation.data())

        if self.shape == "Sphere":
            self.draw_sphere()
        elif self.shape == "Cube":
            self.draw_cube()
        elif self.shape == "Plane":
            self.draw_plane()

    def draw_sphere(self):
        quad = gluNewQuadric()
        gluQuadricTexture(quad, GL_TRUE)
        glBindTexture(GL_TEXTURE_2D, self.textures.get("Albedo", 0))
        gluSphere(quad, 1.0, 32, 32)
        gluDeleteQuadric(quad)

    def draw_cube(self):
        glBindTexture(GL_TEXTURE_2D, self.textures.get("Albedo", 0))
        glBegin(GL_QUADS)
        for i in range(6):
            glNormal3fv(self.normals[i])
            for j in range(4):
                glTexCoord2fv(self.texCoords[j])
                glVertex3fv(self.vertices[self.faces[i][j]])
        glEnd()

    def draw_plane(self):
        glBindTexture(GL_TEXTURE_2D, self.textures.get("Albedo", 0))
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glTexCoord2f(0, 0); glVertex3f(-1, 0, -1)
        glTexCoord2f(1, 0); glVertex3f(1, 0, -1)
        glTexCoord2f(1, 1); glVertex3f(1, 0, 1)
        glTexCoord2f(0, 1); glVertex3f(-1, 0, 1)
        glEnd()

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & Qt.LeftButton:
            rotation = QMatrix4x4()
            rotation.rotate(dx / 5, 0, 1, 0)
            rotation.rotate(dy / 5, 1, 0, 0)
            self.rotation = rotation * self.rotation

        self.lastPos = event.pos()
        self.update()

    def set_shape(self, shape):
        self.shape = shape
        self.update()

    def update_material(self, textures):
        self.textures.clear()
        for name, img_data in textures.items():
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img_data.shape[1], img_data.shape[0], 0,
                         GL_RGB, GL_UNSIGNED_BYTE, img_data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            self.textures[name] = texture_id
        self.update()

    vertices = [
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
    ]

    faces = [
        [0, 1, 2, 3], [1, 5, 6, 2], [5, 4, 7, 6],
        [4, 0, 3, 7], [3, 2, 6, 7], [4, 5, 1, 0]
    ]

    normals = [
        [0, 0, -1], [1, 0, 0], [0, 0, 1],
        [-1, 0, 0], [0, 1, 0], [0, -1, 0]
    ]

    texCoords = [[0, 0], [1, 0], [1, 1], [0, 1]]
