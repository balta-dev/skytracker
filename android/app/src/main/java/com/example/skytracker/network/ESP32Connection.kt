package com.example.skytracker.network

import com.example.skytracker.data.models.PointingAngles
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.net.InetSocketAddress
import java.net.Socket

class ESP32Connection(
    private val ipAddress: String,
    private val port: Int = 12345
) {
    private var socket: Socket? = null
    private var reader: java.io.BufferedReader? = null
    private var writer: java.io.BufferedWriter? = null

    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState

    private val _sensorAngles = MutableStateFlow<PointingAngles?>(null)
    val sensorAngles: StateFlow<PointingAngles?> = _sensorAngles

    private var connectionJob: Job? = null

    enum class ConnectionState {
        DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, ERROR
    }

    // ← RECIBIR SCOPE COMO PARÁMETRO (igual que ServerConnection)
    fun connectWithAutoReconnect(scope: CoroutineScope) {
        connectionJob?.cancel()

        connectionJob = scope.launch(Dispatchers.IO) {
            var reconnectDelay = 5000L

            while (isActive) {
                try {
                    _connectionState.value = ConnectionState.CONNECTING

                    socket = Socket()
                    socket?.connect(InetSocketAddress(ipAddress, port), 5000)
                    reader = socket?.getInputStream()?.bufferedReader()
                    writer = socket?.getOutputStream()?.bufferedWriter()

                    withContext(Dispatchers.Main) {
                        _connectionState.value = ConnectionState.CONNECTED
                        reconnectDelay = 5000L
                    }

                    // LEER LÍNEAS (como ServerConnection, más eficiente)
                    while (isActive) {
                        val line = reader?.readLine() ?: break

                        if (line.startsWith("SENS:")) {
                            val parts = line.removePrefix("SENS:").split(",")
                            if (parts.size == 2) {
                                val yaw = parts[0].trim().toDouble()
                                val pitch = parts[1].trim().toDouble()
                                withContext(Dispatchers.Main) {
                                    _sensorAngles.value = PointingAngles(yaw, pitch)
                                }
                            }
                        }
                    }

                } catch (e: Exception) {
                    withContext(Dispatchers.Main) {
                        _connectionState.value = ConnectionState.RECONNECTING
                        _sensorAngles.value = null
                    }
                    delay(reconnectDelay)
                    reconnectDelay = minOf(reconnectDelay * 2, 10000L)
                }
            }
        }
    }

    suspend fun sendAngles(angles: PointingAngles): Boolean = withContext(Dispatchers.IO) {
        if (_connectionState.value != ConnectionState.CONNECTED) return@withContext false
        try {
            writer?.write("CMD:%.2f,%.2f\n".format(angles.yaw, angles.pitch))
            writer?.flush()
            true
        } catch (e: Exception) {
            false
        }
    }

    private fun cleanup() {
        try { socket?.close() } catch (e: Exception) {}
        socket = null
        reader = null
        writer = null
        _sensorAngles.value = null
    }

    fun disconnect() {
        connectionJob?.cancel()
        connectionJob = null
        cleanup()
        _connectionState.value = ConnectionState.DISCONNECTED
    }

}