package com.example.skytracker.network

import com.example.skytracker.data.models.PointingAngles
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.io.BufferedReader
import java.io.BufferedWriter
import java.net.InetSocketAddress
import java.net.Socket

/**
 * Conexión al servidor Python (modo actual)
 * El servidor Python hace todos los cálculos
 */
class ServerConnection(
    private val ipAddress: String,
    private val port: Int = 12345
) {
    private var socket: Socket? = null
    private var reader: BufferedReader? = null
    private var writer: BufferedWriter? = null

    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState

    private val _targetAngles = MutableStateFlow<PointingAngles?>(null)
    val targetAngles: StateFlow<PointingAngles?> = _targetAngles

    private val _sensorAngles = MutableStateFlow<PointingAngles?>(null)
    val sensorAngles: StateFlow<PointingAngles?> = _sensorAngles

    private val _trackingObject = MutableStateFlow<String?>(null)
    val trackingObject: StateFlow<String?> = _trackingObject

    private val _statusMessage = MutableStateFlow<String>("Desconectado")
    val statusMessage: StateFlow<String> = _statusMessage

    private var connectionJob: Job? = null  // Job de conexión principal
    private var sendJob: Job? = null
    private var currentTrackingObject: String? = null

    enum class ConnectionState {
        DISCONNECTED,
        CONNECTING,
        CONNECTED,
        RECONNECTING,
        ERROR
    }

    /**
     * Conecta al servidor con reconexión automática (RESTAURADO AL ORIGINAL)
     */
    fun connectWithAutoReconnect(scope: CoroutineScope) {
        // Cancelar cualquier conexión previa
        connectionJob?.cancel()

        connectionJob = scope.launch(Dispatchers.IO) {
            var reconnectDelay = 2000L

            while (isActive) {
                try {
                    _connectionState.value = ConnectionState.CONNECTING
                    _statusMessage.value = "Conectando..."

                    // Crear socket y conectar (IGUAL AL ORIGINAL)
                    socket = Socket()
                    socket?.connect(InetSocketAddress(ipAddress, port), 5000)
                    reader = socket?.getInputStream()?.bufferedReader()
                    writer = socket?.getOutputStream()?.bufferedWriter()

                    withContext(Dispatchers.Main) {
                        _connectionState.value = ConnectionState.CONNECTED
                        _statusMessage.value = "Conectado"
                        reconnectDelay = 2000L
                    }

                    // LEER LÍNEAS (IGUAL AL ORIGINAL)
                    while (isActive) {
                        val line = reader?.readLine() ?: break
                        withContext(Dispatchers.Main) {
                            parseMessage(line)
                        }
                    }

                } catch (e: Exception) {
                    withContext(Dispatchers.Main) {
                        _connectionState.value = ConnectionState.RECONNECTING
                        _statusMessage.value = "Reconectando en ${reconnectDelay / 1000}s..."
                        _targetAngles.value = null
                        _sensorAngles.value = null
                    }
                    delay(reconnectDelay)
                    reconnectDelay = minOf(reconnectDelay * 2, 10000L)
                }
            }
        }
    }

    /**
     * Inicia el rastreo de un objeto (RESTAURADO AL ORIGINAL)
     */
    fun startTracking(objectName: String, scope: CoroutineScope) {
        if (_connectionState.value != ConnectionState.CONNECTED) return

        currentTrackingObject = objectName
        _trackingObject.value = objectName
        _statusMessage.value = "Rastreando $objectName..."

        sendJob?.cancel()
        sendJob = scope.launch(Dispatchers.IO) {
            while (isActive && currentTrackingObject == objectName) {
                try {
                    writer?.write("$objectName\n")
                    writer?.flush()
                    delay(2000L)  // Enviar cada 2 segundos
                } catch (e: Exception) {
                    withContext(Dispatchers.Main) {
                        _statusMessage.value = "Error de rastreo: ${e.message}"
                    }
                    break
                }
            }
        }
    }

    /**
     * Detiene el rastreo
     */
    suspend fun stopTracking() = withContext(Dispatchers.IO) {
        try {
            writer?.write("STOP\n")
            writer?.flush()
        } catch (e: Exception) {
            // Ignorar errores
        }

        sendJob?.cancel()
        sendJob = null
        currentTrackingObject = null
        _trackingObject.value = null
        _targetAngles.value = null
        _statusMessage.value = "Conectado - Esperando comando"
    }


    /**
     * Parsea mensajes del servidor (IDÉNTICO AL ORIGINAL)
     */
    private fun parseMessage(line: String) {
        when {
            line.startsWith("OK") -> {
                _trackingObject.value = currentTrackingObject
                _statusMessage.value = "Rastreando ${currentTrackingObject ?: "..."}"
            }

            line.startsWith("ERROR") -> {
                _statusMessage.value = "Conectado - $line"
                _trackingObject.value = null
            }

            line.startsWith("DATA:") -> {
                try {
                    val parts = line.removePrefix("DATA:").split(",")
                    if (parts.size == 2) {
                        val yaw = parts[0].trim().toDouble()
                        val pitch = parts[1].trim().toDouble()
                        _targetAngles.value = PointingAngles(yaw, pitch)
                    }
                } catch (e: Exception) {
                    // Error de parseo
                }
            }

            line.startsWith("SENSOR:") -> {
                try {
                    val parts = line.removePrefix("SENSOR:").split(",")
                    if (parts.size == 2) {
                        val yaw = parts[0].trim().toDouble()
                        val pitch = parts[1].trim().toDouble()
                        _sensorAngles.value = PointingAngles(yaw, pitch)
                    }
                } catch (e: Exception) {
                    // Error de parseo
                }
            }

            line.startsWith("STOPPED") -> {
                _trackingObject.value = null
                _targetAngles.value = null
            }
        }
    }

    /**
     * Desconecta del servidor
     */
    fun disconnect() {
        // CANCELAR EL JOB DE CONEXIÓN (ESTO ES LO IMPORTANTE)
        connectionJob?.cancel()
        connectionJob = null

        sendJob?.cancel()
        sendJob = null

        try {
            socket?.close()
        } catch (e: Exception) {
            // Ignorar errores
        }

        socket = null
        reader = null
        writer = null
        currentTrackingObject = null

        _connectionState.value = ConnectionState.DISCONNECTED
        _trackingObject.value = null
        _targetAngles.value = null
        _sensorAngles.value = null
        _statusMessage.value = "Desconectado"
    }

    fun isConnected(): Boolean {
        return _connectionState.value == ConnectionState.CONNECTED
    }
}