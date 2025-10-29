package com.example.skytracker.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.skytracker.data.models.TelemetryData
import com.example.skytracker.repository.OperationMode
import com.example.skytracker.repository.SkyTrackerRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel para la pantalla principal
 */
class SkyTrackerViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = SkyTrackerRepository(application.applicationContext)

    // Estados de UI
    val telemetryData: StateFlow<TelemetryData> = repository.telemetryData
    val connectionStatus: StateFlow<String> = repository.connectionStatus
    val isConnected: StateFlow<Boolean> = repository.isConnected
    val operationMode: StateFlow<OperationMode> = repository.operationMode
    val isRefreshing: StateFlow<Boolean> = repository.isRefreshing

    private val _availableObjects = MutableStateFlow<List<String>>(emptyList())
    val availableObjects: StateFlow<List<String>> = _availableObjects

    private val _cacheAge = MutableStateFlow<String>("--")
    val cacheAge: StateFlow<String> = _cacheAge

    private val _updateMessage = MutableStateFlow<String?>(null)
    val updateMessage: StateFlow<String?> = _updateMessage

    private val _showCacheAge = MutableStateFlow(false)
    val showCacheAge: StateFlow<Boolean> = _showCacheAge


    init {
        // Cargar objetos disponibles
        _availableObjects.value = repository.getAvailableObjects()
        updateCacheAge()

        // Mostrar cache al inicio por 4 segundos
        viewModelScope.launch {
            _showCacheAge.value = true
            delay(4000)
            _showCacheAge.value = shouldShowCacheWarning()
        }
    }

    private fun shouldShowCacheWarning(): Boolean {
        val hours = repository.getCacheAgeHours()
        return hours > 24 // Mostrar permanente si es viejo
    }

    /**
     * Actualiza las efemérides (pull-to-refresh)
     */
    fun refreshEphemeris() {
        viewModelScope.launch {
            _updateMessage.value = "Actualizando..."
            val success = repository.refreshEphemeris()
            if (success) {
                // Recargar lista de objetos con nuevas coordenadas
                _availableObjects.value = repository.getAvailableObjects()
                updateCacheAge()
                _updateMessage.value = "✓ Datos actualizados correctamente"
                _showCacheAge.value = true
                delay(4000)
                _showCacheAge.value = shouldShowCacheWarning()
            } else {
                _updateMessage.value = "✗ Error al actualizar datos"
            }

            // Limpiar mensaje después de 3 segundos
            delay(3000)
            _updateMessage.value = null
        }
    }

    /**
     * Actualiza la edad del cache
     */
    private fun updateCacheAge() {
        val hours = repository.getCacheAgeHours()
        _cacheAge.value = when {
            hours < 0 -> "Sin cache"
            hours == 0L -> "Recién actualizado"
            hours < 24 -> "$hours horas"
            else -> "${hours / 24} días"
        }
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
        viewModelScope.launch {
            val portInt = port.toIntOrNull() ?: 12345
            repository.connectToESP32(ipAddress, portInt, viewModelScope)
        }
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