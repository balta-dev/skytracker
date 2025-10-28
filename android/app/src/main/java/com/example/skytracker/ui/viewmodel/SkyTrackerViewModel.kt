package com.example.skytracker.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.skytracker.data.models.TelemetryData
import com.example.skytracker.repository.OperationMode
import com.example.skytracker.repository.SkyTrackerRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel para la pantalla principal
 */
class SkyTrackerViewModel : ViewModel() {

    private val repository = SkyTrackerRepository()

    // Estados de UI
    val telemetryData: StateFlow<TelemetryData> = repository.telemetryData
    val connectionStatus: StateFlow<String> = repository.connectionStatus
    val isConnected: StateFlow<Boolean> = repository.isConnected
    val operationMode: StateFlow<OperationMode> = repository.operationMode

    private val _availableObjects = MutableStateFlow<List<String>>(emptyList())
    val availableObjects: StateFlow<List<String>> = _availableObjects

    init {
        // Cargar objetos disponibles
        _availableObjects.value = repository.getAvailableObjects()
    }

    /**
     * Conecta al servidor Python
     */
    fun connectToServer(ipAddress: String, port: String) {
        val portInt = port.toIntOrNull() ?: 12345
        repository.connectToServer(ipAddress, portInt, viewModelScope)
    }

    /**
     * Conecta directamente al ESP32
     */
    fun connectToESP32(ipAddress: String, port: String) {
        val portInt = port.toIntOrNull() ?: 80
        // PASAR viewModelScope como tercer parámetro
        repository.connectToESP32(ipAddress, portInt, viewModelScope)
    }

    /**
     * Inicia el rastreo de un objeto
     */
    fun startTracking(objectName: String) {
        repository.startTracking(objectName, viewModelScope)
    }

    /**
     * Detiene el rastreo
     */
    fun stopTracking() {
        viewModelScope.launch {
            repository.stopTracking()
        }
    }

    /**
     * Desconecta todo
     */
    fun disconnect() {
        repository.disconnectAll()
    }

    /**
     * Verifica si un objeto existe
     */
    fun isValidObject(name: String): Boolean {
        return repository.findObject(name) != null
    }

    override fun onCleared() {
        super.onCleared()
        repository.disconnectAll()
    }
}