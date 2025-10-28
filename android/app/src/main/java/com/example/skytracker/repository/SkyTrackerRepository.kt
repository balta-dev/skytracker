package com.example.skytracker.repository

import com.example.skytracker.calculation.CelestialTracker
import com.example.skytracker.data.CelestialDatabase
import com.example.skytracker.data.models.CelestialData
import com.example.skytracker.data.models.CelestialObject
import com.example.skytracker.data.models.PointingAngles
import com.example.skytracker.data.models.TelemetryData
import com.example.skytracker.network.ESP32Connection
import com.example.skytracker.network.ServerConnection
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

/**
 * Modos de operación
 */
enum class OperationMode {
    SERVER,  // Conectado al servidor Python
    DIRECT   // Conexión directa al ESP32 con cálculos locales
}

/**
 * Repositorio principal que abstrae la fuente de datos
 */
class SkyTrackerRepository {

    private val celestialData: CelestialData = CelestialDatabase.getCelestialData()
    private val tracker = CelestialTracker()

    // Conexiones
    private var serverConnection: ServerConnection? = null
    private var esp32Connection: ESP32Connection? = null

    // Estado actual
    private val _operationMode = MutableStateFlow(OperationMode.SERVER)
    val operationMode: StateFlow<OperationMode> = _operationMode

    private val _telemetryData = MutableStateFlow(
        TelemetryData(null, null, null, false)
    )
    val telemetryData: StateFlow<TelemetryData> = _telemetryData

    private val _connectionStatus = MutableStateFlow("Desconectado")
    val connectionStatus: StateFlow<String> = _connectionStatus

    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected

    private var trackingJob: Job? = null
    private var currentTrackedObject: CelestialObject? = null

    /**
     * Conecta en modo servidor Python
     */
    fun connectToServer(ipAddress: String, port: Int, scope: CoroutineScope) {
        disconnectAll()

        _operationMode.value = OperationMode.SERVER
        serverConnection = ServerConnection(ipAddress, port)

        serverConnection?.connectWithAutoReconnect(scope)

        // Observar estado del servidor
        scope.launch {
            serverConnection?.connectionState?.collect { state ->
                _isConnected.value = (state == ServerConnection.ConnectionState.CONNECTED)
            }
        }

        scope.launch {
            serverConnection?.statusMessage?.collect { status ->
                _connectionStatus.value = status
            }
        }

        scope.launch {
            combine(
                serverConnection?.targetAngles ?: flowOf(null),
                serverConnection?.sensorAngles ?: flowOf(null),
                serverConnection?.trackingObject ?: flowOf(null)
            ) { target, sensor, tracking ->
                TelemetryData(
                    targetAngles = target,
                    sensorAngles = sensor,
                    trackingObject = tracking,
                    isTracking = tracking != null
                )
            }.collect { data ->
                _telemetryData.value = data
            }
        }
    }

    /**
     * Conecta en modo directo al ESP32
     */
    fun connectToESP32(ipAddress: String, port: Int, scope: CoroutineScope) {
        disconnectAll()
        _operationMode.value = OperationMode.DIRECT
        esp32Connection = ESP32Connection(ipAddress, port)
        esp32Connection?.connectWithAutoReconnect()

        // OBSERVAR ESTADO
        scope.launch {
            esp32Connection?.connectionState?.collect { state ->
                _isConnected.value = state == ESP32Connection.ConnectionState.CONNECTED
                _connectionStatus.value = when (state) {
                    ESP32Connection.ConnectionState.CONNECTED -> "Conectado al ESP32"
                    ESP32Connection.ConnectionState.CONNECTING -> "Conectando al ESP32..."
                    ESP32Connection.ConnectionState.RECONNECTING -> "Reconectando al ESP32..."
                    ESP32Connection.ConnectionState.DISCONNECTED, ESP32Connection.ConnectionState.ERROR -> "Desconectado"
                }
            }
        }

        // OBSERVAR SENSOR
        scope.launch {
            esp32Connection?.sensorAngles?.collect { angles ->
                _telemetryData.value = _telemetryData.value.copy(sensorAngles = angles)
            }
        }
    }

    /**
     * Inicia el rastreo de un objeto
     */
    fun startTracking(objectName: String, scope: CoroutineScope): Boolean {
        val obj = celestialData.findObject(objectName)
        if (obj == null) {
            _connectionStatus.value = "Objeto no encontrado: $objectName"
            return false
        }

        currentTrackedObject = obj

        when (_operationMode.value) {
            OperationMode.SERVER -> {
                serverConnection?.startTracking(objectName, scope)
            }

            OperationMode.DIRECT -> {
                startDirectTracking(obj, scope)
            }
        }

        return true
    }

    /**
     * Rastreo directo (modo ESP32)
     */
    private fun startDirectTracking(obj: CelestialObject, scope: CoroutineScope) {
        trackingJob?.cancel()

        _telemetryData.value = _telemetryData.value.copy(
            trackingObject = obj.name,
            isTracking = true
        )
        _connectionStatus.value = "Rastreando ${obj.name}"

        trackingJob = scope.launch {
            while (isActive) {
                try {
                    // Calcular ángulos para el objeto
                    val angles = tracker.calculateTrackingAngles(
                        obj.raHours,
                        obj.decDegrees
                    )

                    // Actualizar telemetría
                    _telemetryData.value = _telemetryData.value.copy(
                        targetAngles = angles
                    )

                    // Enviar al ESP32
                    esp32Connection?.sendAngles(angles)

                    // Actualizar cada 1 segundo (el ESP32 se mueve lentamente)
                    delay(1000)

                } catch (e: Exception) {
                    _connectionStatus.value = "Error en rastreo: ${e.message}"
                    break
                }
            }
        }
    }

    /**
     * Detiene el rastreo
     */
    suspend fun stopTracking() {
        trackingJob?.cancel()
        trackingJob = null
        currentTrackedObject = null

        when (_operationMode.value) {
            OperationMode.SERVER -> {
                serverConnection?.stopTracking()
            }

            OperationMode.DIRECT -> {
                _telemetryData.value = TelemetryData(
                    targetAngles = null,
                    sensorAngles = _telemetryData.value.sensorAngles,
                    trackingObject = null,
                    isTracking = false
                )
                _connectionStatus.value = "Conectado al ESP32"
            }
        }
    }

    /**
     * Obtiene la lista de objetos disponibles
     */
    fun getAvailableObjects(): List<String> {
        return celestialData.getAllNames()
    }

    /**
     * Busca un objeto por nombre
     */
    fun findObject(name: String): CelestialObject? {
        return celestialData.findObject(name)
    }

    /**
     * Desconecta todo
     */
    fun disconnectAll() {
        trackingJob?.cancel()
        serverConnection?.disconnect()
        esp32Connection?.disconnect()

        serverConnection = null
        esp32Connection = null
        currentTrackedObject = null

        _isConnected.value = false
        _connectionStatus.value = "Desconectado"
        _telemetryData.value = TelemetryData(null, null, null, false)
    }

    /**
     * Verifica si está rastreando
     */
    fun isTracking(): Boolean {
        return _telemetryData.value.isTracking
    }
}