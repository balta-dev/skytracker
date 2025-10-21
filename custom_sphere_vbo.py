import numpy as np
import pyglet
from pyglet.gl import *

def create_sphere_vertex_list(radius=1.0, slices=32, stacks=32):
    vertices = []
    normals = []
    texcoords = []
    indices = []

    for i in range(stacks + 1):
        phi = i * np.pi / stacks
        for j in range(slices + 1):
            theta = j * 2 * np.pi / slices
            x = np.sin(phi) * np.cos(theta)
            y = np.cos(phi)
            z = np.sin(phi) * np.sin(theta)
            vertices.extend([x * radius, y * radius, z * radius])
            normals.extend([x, y, z])
            texcoords.extend([j / slices, i / stacks])

    for i in range(stacks):
        for j in range(slices):
            first = i * (slices + 1) + j
            second = first + slices + 1
            indices.extend([first, second, first + 1])
            indices.extend([second, second + 1, first + 1])

    vertex_list = pyglet.graphics.vertex_list_indexed(
        len(vertices)//3,
        indices,
        ('v3f/static', vertices),
        ('n3f/static', normals),
        ('t2f/static', texcoords)
    )
    return vertex_list

def draw_sphere(vertex_list, size=1.0):
    glPushMatrix()
    glScalef(size, size, size)
    vertex_list.draw(GL_TRIANGLES)
    glPopMatrix()