package com.example.skytracker.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.skytracker.data.models.TelemetryData
import com.example.skytracker.repository.OperationMode
import com.example.skytracker.repository.SkyTrackerRepository
import kotlinx.coroutines.Job
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

    private val _isConnecting = MutableStateFlow(false)
    val isConnecting: StateFlow<Boolean> = _isConnecting

    private var connectionObserverJob: Job? = null


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
        val minutes = repository.getCacheAgeMinutes() // mejor trabajar con minutos
        _cacheAge.value = when {
            minutes < 0 -> "sin datos"
            minutes < 1 -> "actualizado!"
            minutes < 60 -> "hace $minutes minuto${if (minutes == 1L) "" else "s"}"
            minutes < 1440 -> { // menos de 24 horas
                val hours = minutes / 60
                "hace $hours hora${if (hours == 1L) "" else "s"}"
            }
            else -> { // 1 día o más
                val days = minutes / 1440
                "hace $days día${if (days == 1L) "" else "s"}"
            }
        }
    }

    /**
     * Conecta al servidor Python
     */
    fun connectToServer(ipAddress: String, port: String) {
        _isConnecting.value = true
        val portInt = port.toIntOrNull() ?: 12345
        repository.connectToServer(ipAddress, portInt, viewModelScope)
        observeConnection()
    }

    /**
     * Conecta directamente al ESP32
     */
    fun connectToESP32(ipAddress: String, port: String) {
        _isConnecting.value = true
        viewModelScope.launch {
            val portInt = port.toIntOrNull() ?: 12345
            repository.connectToESP32(ipAddress, portInt, viewModelScope)
        }
        observeConnection()
    }

    /**
     * Observa el estado de conexión (evita múltiples collectors)
     */
    private fun observeConnection() {
        connectionObserverJob?.cancel()
        connectionObserverJob = viewModelScope.launch {
            repository.isConnected.collect { connected ->
                if (connected) {
                    _isConnecting.value = false
                }
            }
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

    fun cancelConnection() {
        _isConnecting.value = false
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
        connectionObserverJob?.cancel()
        repository.disconnectAll()
    }
}