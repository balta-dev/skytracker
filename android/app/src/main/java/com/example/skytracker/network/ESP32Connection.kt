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
    private var listenJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    enum class ConnectionState {
        DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, ERROR
    }

    fun connectWithAutoReconnect() {
        connectionJob?.cancel()
        connectionJob = scope.launch {
            var delayMs = 1000L
            while (isActive) {
                try {
                    _connectionState.value = ConnectionState.CONNECTING

                    socket = Socket()
                    socket?.connect(InetSocketAddress(ipAddress, port), 5000)
                    reader = socket?.getInputStream()?.bufferedReader()
                    writer = socket?.getOutputStream()?.bufferedWriter()

                    _connectionState.value = ConnectionState.CONNECTED
                    delayMs = 1000L
                    startListening()

                    while (isActive && socket?.isConnected == true) {
                        delay(100)
                    }
                } catch (e: Exception) {
                    cleanup()
                    _connectionState.value = ConnectionState.RECONNECTING
                    delay(delayMs)
                    delayMs = (delayMs * 2).coerceAtMost(10000L)
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

    private fun startListening() {
        listenJob?.cancel()
        listenJob = scope.launch {
            while (isActive && _connectionState.value == ConnectionState.CONNECTED) {
                try {
                    val line = reader?.readLine() ?: break
                    if (line.isNotBlank() && line.startsWith("SENS:")) {
                        val parts = line.removePrefix("SENS:").split(",")
                        if (parts.size == 2) {
                            val yaw = parts[0].trim().toDouble()
                            val pitch = parts[1].trim().toDouble()
                            withContext(Dispatchers.Main) {
                                _sensorAngles.value = PointingAngles(yaw, pitch)
                            }
                        }
                    }
                } catch (e: Exception) {
                    delay(100)
                }
            }
        }
    }

    private fun cleanup() {
        listenJob?.cancel()
        try { socket?.close() } catch (e: Exception) {}
        socket = null
        reader = null
        writer = null
        _sensorAngles.value = null
    }

    fun disconnect() {
        connectionJob?.cancel()
        cleanup()
        _connectionState.value = ConnectionState.DISCONNECTED
    }

    fun isConnected() = _connectionState.value == ConnectionState.CONNECTED
}