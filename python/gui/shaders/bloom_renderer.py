"""
Sistema de renderizado con efecto Bloom/Glow usando shaders
Integrado para SkyTracker
"""
from pyglet.gl import *
from config import *
import ctypes


# ============================================================================
# SHADERS
# ============================================================================

VERTEX_SHADER = """
#version 120
void main() {
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_TexCoord[0] = gl_MultiTexCoord0;
    gl_FrontColor = gl_Color;
}
"""

# Extrae solo las partes brillantes de la imagen
BRIGHTNESS_SHADER = """
#version 120
uniform sampler2D texture;
uniform float threshold;

void main() {
    vec4 color = texture2D(texture, gl_TexCoord[0].xy);
    float brightness = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
    
    if (brightness > threshold) {
        gl_FragColor = color;
    } else {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
"""

# Blur gaussiano horizontal
BLUR_H_SHADER = """
#version 120
uniform sampler2D texture;
uniform float blur_size;

void main() {
    vec4 sum = vec4(0.0);
    vec2 tc = gl_TexCoord[0].xy;
    
    // Pesos gaussianos
    float weights[5];
    weights[0] = 0.227027;
    weights[1] = 0.1945946;
    weights[2] = 0.1216216;
    weights[3] = 0.054054;
    weights[4] = 0.016216;
    
    sum += texture2D(texture, tc) * weights[0];
    
    for(int i = 1; i < 5; i++) {
        float offset = blur_size * float(i);
        sum += texture2D(texture, tc + vec2(offset, 0.0)) * weights[i];
        sum += texture2D(texture, tc - vec2(offset, 0.0)) * weights[i];
    }
    
    gl_FragColor = sum;
}
"""

# Blur gaussiano vertical
BLUR_V_SHADER = """
#version 120
uniform sampler2D texture;
uniform float blur_size;

void main() {
    vec4 sum = vec4(0.0);
    vec2 tc = gl_TexCoord[0].xy;
    
    // Pesos gaussianos
    float weights[5];
    weights[0] = 0.227027;
    weights[1] = 0.1945946;
    weights[2] = 0.1216216;
    weights[3] = 0.054054;
    weights[4] = 0.016216;
    
    sum += texture2D(texture, tc) * weights[0];
    
    for(int i = 1; i < 5; i++) {
        float offset = blur_size * float(i);
        sum += texture2D(texture, tc + vec2(0.0, offset)) * weights[i];
        sum += texture2D(texture, tc - vec2(0.0, offset)) * weights[i];
    }
    
    gl_FragColor = sum;
}
"""

# Combina la escena original con el bloom
COMBINE_SHADER = """
#version 120
uniform sampler2D scene;
uniform sampler2D bloom;
uniform float bloom_strength;

void main() {
    vec4 scene_color = texture2D(scene, gl_TexCoord[0].xy);
    vec4 bloom_color = texture2D(bloom, gl_TexCoord[0].xy);
    
    gl_FragColor = scene_color + bloom_color * bloom_strength;
}
"""


# ============================================================================
# CLASES AUXILIARES
# ============================================================================

class ShaderProgram:
    """Compila y gestiona un programa de shaders"""
    
    def __init__(self, vertex_src, fragment_src):
        self.program = glCreateProgram()
        self.compiled = False
        
        try:
            # Compilar vertex shader
            vertex = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex, 1, ctypes.cast(
                ctypes.pointer(ctypes.c_char_p(vertex_src.encode())),
                ctypes.POINTER(ctypes.POINTER(ctypes.c_char))
            ), None)
            glCompileShader(vertex)
            
            # Check vertex compilation
            result = ctypes.c_int()
            glGetShaderiv(vertex, GL_COMPILE_STATUS, ctypes.byref(result))
            if not result.value:
                print(f"ERROR: Vertex shader compilation failed")
                glDeleteShader(vertex)
                return
            
            # Compilar fragment shader
            fragment = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment, 1, ctypes.cast(
                ctypes.pointer(ctypes.c_char_p(fragment_src.encode())),
                ctypes.POINTER(ctypes.POINTER(ctypes.c_char))
            ), None)
            glCompileShader(fragment)
            
            # Check fragment compilation
            result = ctypes.c_int()
            glGetShaderiv(fragment, GL_COMPILE_STATUS, ctypes.byref(result))
            if not result.value:
                print(f"ERROR: Fragment shader compilation failed")
                glDeleteShader(vertex)
                glDeleteShader(fragment)
                return
            
            # Linkear programa
            glAttachShader(self.program, vertex)
            glAttachShader(self.program, fragment)
            glLinkProgram(self.program)
            
            # Check linking
            result = ctypes.c_int()
            glGetProgramiv(self.program, GL_LINK_STATUS, ctypes.byref(result))
            if not result.value:
                print(f"ERROR: Program linking failed")
                glDeleteShader(vertex)
                glDeleteShader(fragment)
                return
            
            glDeleteShader(vertex)
            glDeleteShader(fragment)
            
            self.compiled = True
            
        except Exception as e:
            print(f"ERROR: Shader compilation failed: {e}")
            self.compiled = False
    
    def use(self):
        if self.compiled:
            glUseProgram(self.program)
    
    def set_uniform_1f(self, name, value):
        if self.compiled:
            location = glGetUniformLocation(self.program, name.encode())
            if location != -1:
                glUniform1f(location, value)
    
    def set_uniform_1i(self, name, value):
        if self.compiled:
            location = glGetUniformLocation(self.program, name.encode())
            if location != -1:
                glUniform1i(location, value)


class FrameBuffer:
    """Framebuffer Object para renderizar a textura"""
    
    def __init__(self, width, height, with_depth=False):
        self.width = width
        self.height = height
        self.created = False
        self.with_depth = with_depth
        self.depth_buffer = None
        
        try:
            # Crear textura
            self.texture = GLuint()
            glGenTextures(1, ctypes.byref(self.texture))
            glBindTexture(GL_TEXTURE_2D, self.texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, 
                         GL_RGBA, GL_UNSIGNED_BYTE, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            
            # Crear FBO
            self.fbo = GLuint()
            glGenFramebuffers(1, ctypes.byref(self.fbo))
            glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, 
                                   GL_TEXTURE_2D, self.texture, 0)
            
            # CAMBIO: Crear depth buffer si es necesario
            if with_depth:
                self.depth_buffer = GLuint()
                glGenRenderbuffers(1, ctypes.byref(self.depth_buffer))
                glBindRenderbuffer(GL_RENDERBUFFER, self.depth_buffer)
                glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, width, height)
                glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                                         GL_RENDERBUFFER, self.depth_buffer)
                print(f"  ✓ Depth buffer creado para FBO {width}x{height}")
            
            # Verificar
            status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            if status != GL_FRAMEBUFFER_COMPLETE:
                raise Exception(f"Framebuffer incomplete: {hex(status)}")
            
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            glBindRenderbuffer(GL_RENDERBUFFER, 0)
            self.created = True
            
        except Exception as e:
            print(f"ERROR creating framebuffer: {e}")
            import traceback
            traceback.print_exc()
            self.created = False
    
    def bind(self):
        if self.created:
            glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
            glViewport(0, 0, self.width, self.height)
    
    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
    
    def bind_texture(self, unit=0):
        if self.created:
            glActiveTexture(GL_TEXTURE0 + unit)
            glBindTexture(GL_TEXTURE_2D, self.texture)


# ============================================================================
# BLOOM RENDERER
# ============================================================================

class BloomRenderer:
    """Renderizador con efecto Bloom/Glow"""
    
    def __init__(self, width, height):
        from config import BLOOM_ENABLED, BLOOM_THRESHOLD, BLOOM_STRENGTH, BLOOM_BLUR_PASSES

        self.width = width
        self.height = height
        self.enabled = False
        self.user_enabled = BLOOM_ENABLED
        
        print("Inicializando Bloom Renderer...")
        
        try:
            # CAMBIO: Solo scene_fbo necesita depth buffer
            self.scene_fbo = FrameBuffer(width, height, with_depth=True)
            self.bright_fbo = FrameBuffer(width, height, with_depth=False)
            self.blur_fbo1 = FrameBuffer(width, height, with_depth=False)
            self.blur_fbo2 = FrameBuffer(width, height, with_depth=False)
            
            # Compilar shaders
            self.brightness_shader = ShaderProgram(VERTEX_SHADER, BRIGHTNESS_SHADER)
            self.blur_h_shader = ShaderProgram(VERTEX_SHADER, BLUR_H_SHADER)
            self.blur_v_shader = ShaderProgram(VERTEX_SHADER, BLUR_V_SHADER)
            self.combine_shader = ShaderProgram(VERTEX_SHADER, COMBINE_SHADER)
            
            # Verificar que todo se creó correctamente
            if (self.scene_fbo.created and self.bright_fbo.created and
                self.blur_fbo1.created and self.blur_fbo2.created and
                self.brightness_shader.compiled and self.blur_h_shader.compiled and
                self.blur_v_shader.compiled and self.combine_shader.compiled):
                
                if self.scene_fbo.with_depth and self.scene_fbo.depth_buffer:
                    print(f"✓ Scene FBO tiene depth buffer (ID: {self.scene_fbo.depth_buffer.value})")
                else:
                    print("✗ WARNING: Scene FBO NO TIENE depth buffer!")
                
                self.enabled = True
                print("✓ Bloom Renderer inicializado correctamente")
                print(f"  Estado inicial: {'ACTIVADO' if self.user_enabled else 'DESACTIVADO'}")
            else:
                print("✗ Bloom Renderer falló al inicializar")
            
        except Exception as e:
            print(f"ERROR inicializando Bloom: {e}")
            self.enabled = False
        
        # Parámetros ajustables
        self.brightness_threshold = BLOOM_THRESHOLD #0.9 default
        self.blur_size = BLOOM_SIZE # 2.0 / width 
        self.bloom_strength = BLOOM_STRENGTH # 1.2
        self.blur_passes = BLOOM_BLUR_PASSES # 2
    
    def render_with_bloom(self, render_scene_func, viewport_width, viewport_height):
        """
        Renderiza la escena con efecto bloom
        
        Args:
            render_scene_func: función que dibuja tu escena 3D
            viewport_width: ancho del viewport actual
            viewport_height: alto del viewport actual
        """
        if not self.enabled or not self.user_enabled:
            render_scene_func()
            return
        
        # CAMBIO: Renderizar escena a textura CON depth test
        self.scene_fbo.bind()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # FORZAR depth test activo
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glDepthMask(GL_TRUE)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        
        render_scene_func()
        
        glFlush()
        self.scene_fbo.unbind()
        
        # Paso 2: Extraer partes brillantes
        self._render_pass(self.scene_fbo, self.bright_fbo, 
                         self.brightness_shader,
                         {'threshold': self.brightness_threshold})
        
        # Paso 3: Blur horizontal y vertical
        src_fbo = self.bright_fbo
        for i in range(self.blur_passes):
            self._render_pass(src_fbo, self.blur_fbo1,
                            self.blur_h_shader,
                            {'blur_size': self.blur_size})
            self._render_pass(self.blur_fbo1, self.blur_fbo2,
                            self.blur_v_shader,
                            {'blur_size': self.blur_size})
            src_fbo = self.blur_fbo2
        
        # Paso 4: Combinar escena + bloom
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, viewport_width, viewport_height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glDisable(GL_DEPTH_TEST)
        
        self.combine_shader.use()
        
        self.scene_fbo.bind_texture(0)
        self.combine_shader.set_uniform_1i('scene', 0)
        
        self.blur_fbo2.bind_texture(1)
        self.combine_shader.set_uniform_1i('bloom', 1)
        
        self.combine_shader.set_uniform_1f('bloom_strength', self.bloom_strength)
        
        self._draw_fullscreen_quad()
        
        glUseProgram(0)
        glBindTexture(GL_TEXTURE_2D, 0)
        glActiveTexture(GL_TEXTURE0)
        
        # CAMBIO: Restaurar depth test
        glEnable(GL_DEPTH_TEST)
    
    def _render_pass(self, input_fbo, output_fbo, shader, uniforms):
        """Renderiza una pasada de post-procesamiento"""
        output_fbo.bind()
        glClear(GL_COLOR_BUFFER_BIT)
        
        glDisable(GL_DEPTH_TEST)
        
        shader.use()
        input_fbo.bind_texture(0)
        shader.set_uniform_1i('texture', 0)
        
        for name, value in uniforms.items():
            shader.set_uniform_1f(name, value)
        
        self._draw_fullscreen_quad()
        
        output_fbo.unbind()
        glUseProgram(0)
    
    def _draw_fullscreen_quad(self):
        """Dibuja un quad que cubre toda la pantalla"""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(-1, -1)
        glTexCoord2f(1, 0); glVertex2f( 1, -1)
        glTexCoord2f(1, 1); glVertex2f( 1,  1)
        glTexCoord2f(0, 1); glVertex2f(-1,  1)
        glEnd()
        
        glEnable(GL_DEPTH_TEST)
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    def toggle(self):
        """Activa/desactiva el bloom (solo si está disponible)"""
        if self.enabled:
            self.user_enabled = not self.user_enabled
            print(f"Bloom: {'ACTIVADO' if self.user_enabled else 'DESACTIVADO'}")
            if self.user_enabled:
                print(f"  (threshold={self.brightness_threshold:.2f}, strength={self.bloom_strength:.2f})")
        else:
            print("Bloom no disponible (falló la inicialización)")
        return self.user_enabled