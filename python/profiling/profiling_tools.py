"""
Herramientas de profiling para identificar cuellos de botella
"""
import time
import functools
from collections import defaultdict


class PerformanceProfiler:
    """Profiler simple para medir tiempos de ejecución"""
    
    def __init__(self):
        self.timings = defaultdict(list)
        self.frame_count = 0
        self.report_interval = 60  # Reportar cada 60 frames
    
    def measure(self, name):
        """Decorador para medir tiempo de ejecución de una función"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000  # ms
                self.timings[name].append(elapsed)
                return result
            return wrapper
        return decorator
    
    def start(self, name):
        """Inicia medición manual"""
        return time.perf_counter()
    
    def end(self, name, start_time):
        """Finaliza medición manual"""
        elapsed = (time.perf_counter() - start_time) * 1000  # ms
        self.timings[name].append(elapsed)
    
    def frame_tick(self):
        """Llamar al final de cada frame"""
        self.frame_count += 1
        
        if self.frame_count % self.report_interval == 0:
            self.print_report()
            self.reset()
    
    def print_report(self):
        """Imprime reporte de performance"""
        print("\n" + "="*60)
        print(f"PERFORMANCE REPORT - {self.frame_count} frames")
        print("="*60)
        
        total_time = 0
        items = []
        
        for name, times in self.timings.items():
            if not times:
                continue
                
            avg = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            total = sum(times)
            
            items.append((name, avg, max_time, min_time, total))
            total_time += total
        
        # Ordenar por tiempo total descendente
        items.sort(key=lambda x: x[4], reverse=True)
        
        print(f"{'Function':<30} {'Avg (ms)':<12} {'Max (ms)':<12} {'Min (ms)':<12} {'% Total':<10}")
        print("-"*60)
        
        for name, avg, max_time, min_time, total in items:
            percentage = (total / total_time * 100) if total_time > 0 else 0
            print(f"{name:<30} {avg:>10.3f}  {max_time:>10.3f}  {min_time:>10.3f}  {percentage:>8.1f}%")
        
        print("-"*60)
        print(f"Total frame time: {total_time/self.report_interval:.3f} ms/frame")
        print(f"Estimated FPS: {1000/(total_time/self.report_interval):.1f}")
        print("="*60 + "\n")
    
    def reset(self):
        """Resetea estadísticas"""
        self.timings.clear()


# Instancia global del profiler
profiler = PerformanceProfiler()


class GPUProfiler:
    """Profiler para OpenGL draw calls y cambios de estado"""
    
    def __init__(self):
        self.draw_calls = 0
        self.state_changes = 0
        self.vertices_rendered = 0
        self.frame_count = 0
        self.report_interval = 60
    
    def count_draw_call(self, vertex_count=0):
        """Cuenta una draw call"""
        self.draw_calls += 1
        self.vertices_rendered += vertex_count
    
    def count_state_change(self):
        """Cuenta un cambio de estado OpenGL"""
        self.state_changes += 1
    
    def frame_tick(self):
        """Llamar al final de cada frame"""
        self.frame_count += 1
        
        if self.frame_count % self.report_interval == 0:
            self.print_report()
            self.reset()
    
    def print_report(self):
        """Imprime reporte de GPU"""
        avg_draws = self.draw_calls / self.report_interval
        avg_states = self.state_changes / self.report_interval
        avg_vertices = self.vertices_rendered / self.report_interval
        
        print("\n" + "="*60)
        print(f"GPU REPORT - {self.frame_count} frames")
        print("="*60)
        print(f"Draw calls per frame: {avg_draws:.1f}")
        print(f"State changes per frame: {avg_states:.1f}")
        print(f"Vertices per frame: {avg_vertices:.0f}")
        print("="*60 + "\n")
    
    def reset(self):
        """Resetea estadísticas"""
        self.draw_calls = 0
        self.state_changes = 0
        self.vertices_rendered = 0


# Instancia global del GPU profiler
gpu_profiler = GPUProfiler()


def enable_profiling(main_file):
    """
    Función helper para activar profiling en main.py
    
    Uso en main.py:
    
    from profiling_tools import profiler, gpu_profiler, enable_profiling
    
    # En el método update():
    def update(self, dt):
        t = profiler.start('update_total')
        # ... código ...
        profiler.end('update_total', t)
    
    # En el método on_draw():
    def on_draw(self):
        t = profiler.start('draw_total')
        # ... código ...
        profiler.end('draw_total', t)
        
        profiler.frame_tick()
        gpu_profiler.frame_tick()
    
    # Para medir funciones específicas:
    @profiler.measure('calculate_coordinates')
    def some_function():
        pass
    """
    pass


# Ejemplo de uso integrado en código existente
class ProfiledRenderer:
    """Wrapper para medir performance de renderizado"""
    
    @staticmethod
    def draw_with_profiling(draw_func, name):
        """Ejecuta función de dibujado con profiling"""
        t = profiler.start(name)
        result = draw_func()
        profiler.end(name, t)
        return result


# Función para analizar memory leaks
class MemoryTracker:
    """Rastrea uso de memoria para detectar leaks"""
    
    def __init__(self):
        self.snapshots = []
        self.interval = 120  # frames
        self.frame_count = 0
    
    def track(self):
        """Toma snapshot de memoria"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        self.snapshots.append({
            'frame': self.frame_count,
            'rss_mb': mem_info.rss / 1024 / 1024,
            'vms_mb': mem_info.vms / 1024 / 1024
        })
        
        self.frame_count += 1
        
        if len(self.snapshots) > 10:
            self.snapshots.pop(0)
    
    def frame_tick(self):
        """Llamar cada frame"""
        self.frame_count += 1
        
        if self.frame_count % self.interval == 0:
            self.track()
            self.print_report()
    
    def print_report(self):
        """Imprime reporte de memoria"""
        if len(self.snapshots) < 2:
            return
        
        first = self.snapshots[0]
        last = self.snapshots[-1]
        
        rss_diff = last['rss_mb'] - first['rss_mb']
        vms_diff = last['vms_mb'] - first['vms_mb']
        
        print("\n" + "="*60)
        print("MEMORY REPORT")
        print("="*60)
        print(f"Current RSS: {last['rss_mb']:.2f} MB")
        print(f"Current VMS: {last['vms_mb']:.2f} MB")
        print(f"RSS change: {rss_diff:+.2f} MB")
        print(f"VMS change: {vms_diff:+.2f} MB")
        
        if abs(rss_diff) > 10:  # More than 10MB change
            print("⚠️  WARNING: Significant memory change detected!")
        
        print("="*60 + "\n")


# Instancia global del memory tracker
memory_tracker = MemoryTracker()


if __name__ == "__main__":
    print("""
    === PROFILING TOOLS ===
    
    Para usar estas herramientas en tu código:
    
    1. Importar al inicio de main.py:
       from profiling_tools import profiler, gpu_profiler, memory_tracker
    
    2. En el método update():
       def update(self, dt):
           t = profiler.start('update')
           # ... tu código ...
           profiler.end('update', t)
    
    3. En el método on_draw():
       def on_draw(self):
           t = profiler.start('draw')
           # ... tu código ...
           profiler.end('draw', t)
           
           # Al final del on_draw:
           profiler.frame_tick()
           gpu_profiler.frame_tick()
           memory_tracker.frame_tick()
    
    4. Para medir secciones específicas:
       t1 = profiler.start('celestial_projection')
       # ... calcular proyecciones ...
       profiler.end('celestial_projection', t1)
       
       t2 = profiler.start('bloom_render')
       # ... renderizar bloom ...
       profiler.end('bloom_render', t2)
    
    5. Los reportes se imprimirán automáticamente en consola cada 60 frames
    """)