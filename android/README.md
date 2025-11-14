# SkyTracker – Guía rápida para Android

Este directorio contiene **todo lo necesario para utilizar Android como cliente TCP/IP** para el servidor Python o el servidor ESP32.

---

## Descargar APK lista para usar

Si solo querés usar la aplicación, simplemente descargá la **última APK compilada** desde la sección **Releases**: https://github.com/balta-dev/skytracker/releases. 

---

## Modos de operación

Existen 2 modos de operación disponible:

* **DIRECTO**: la app se conecta al ESP32, que procesa todo localmente.  
- **SERVIDOR**: la app se conecta al servidor Python, que realiza los cálculos.

Para el caso directo, simplemente observe la pantalla del SkyTracker físico en busca de **IP** y asegúrese de que ambos números coincidan antes de tocar en "CONECTAR".

Para el caso servidor, observe la pantalla después de abrir ```main.py``` o ```main-cli.py``` en busca de **SERVIDOR TCP** y asegúrese de que ambos números coincidan antes de tocar en "CONECTAR".

¡Y listo! Una vez conectado, solo queda ingresar manualmente el objeto a rastrear.  
Para más detalles, consulte el archivo `README.md` en la carpeta raíz.

---

## Requisitos

>  Nota: Esta sección solo es necesaria si querés modificar la app o compilarla por tu cuenta.

- Android Studio
- SDK de Android instalado
- (Opcional) Cable USB para depuración

---

## Clonar el repositorio

```
git clone https://github.com/balta-dev/skytracker.git
cd android/
```

---

## Abrir el proyecto en Android Studio

1. Abrí **Android Studio**.  
2. Seleccioná **"Open an existing project"**.  
3. Elegí la carpeta:  

```
/android/
```

4. Esperá a que Gradle sincronice el proyecto.

---

## Ubicación del código principal

El archivo principal (`MainActivity.kt`) está en:

```
/android/app/src/main/java/com/example/skytracker/MainActivity.kt
```

---

## Compilar una APK (modo debug)

1. En Android Studio, abrí **Build**.  
2. Seleccioná:  
   **Build > Build Bundle(s) / APK(s) > Build APK(s)**  
3. La APK generada se guarda en:

```
/android/app/build/outputs/apk/debug/app-debug.apk
```

---

## Instalar la APK en tu teléfono

### **A) Instalación manual**
1. Copiá `app-debug.apk` al teléfono.  
2. Abrilo desde el explorador de archivos.  
3. Permití la instalación desde **"orígenes desconocidos"** si te lo pide.

---

### **B) Instalación mediante depuración USB**
1. Activá **Depuración USB** en tu teléfono.  
2. Conectalo a la PC por USB.  
3. En Android Studio, seleccioná tu dispositivo en la barra superior.  
4. Presioná **Run ▶** para instalar y ejecutar la app automáticamente.
