package com.example.skytracker.data.models

/**
 * Modelo para objetos celestiales
 */
data class CelestialObject(
    val name: String,
    val raHours: Double,        // Ascensión Recta en horas
    val decDegrees: Double,     // Declinación en grados
    val size: Double = 1.0,
    val type: ObjectType = ObjectType.STAR
)

enum class ObjectType {
    STAR,
    GALAXY,
    PLANET,
    MOON
}

/**
 * Datos celestiales completos
 */
data class CelestialData(
    val stars: List<CelestialObject>,
    val galaxies: List<CelestialObject>,
    val planets: List<CelestialObject>,
    val moon: CelestialObject
) {
    /**
     * Busca un objeto por nombre (case-insensitive)
     */
    fun findObject(name: String): CelestialObject? {
        val searchName = name.lowercase().trim()

        // Buscar en todas las categorías
        val allObjects = stars + galaxies + planets + listOf(moon)

        return allObjects.find {
            it.name.lowercase() == searchName
        }
    }

    /**
     * Lista de todos los nombres disponibles
     */
    fun getAllNames(): List<String> {
        return (stars + galaxies + planets + listOf(moon)).map { it.name }
    }
}

/**
 * Coordenadas 3D en el espacio
 */
data class Vector3D(
    val x: Double,
    val y: Double,
    val z: Double
)

/**
 * Ángulos de apuntamiento
 */
data class PointingAngles(
    val yaw: Double,    // 0-360°
    val pitch: Double   // -90 a +90°
) {
    fun format(): String = "Yaw: %.2f° Pitch: %.2f°".format(yaw, pitch)
}

/**
 * Datos de telemetría
 */
data class TelemetryData(
    val targetAngles: PointingAngles?,
    val sensorAngles: PointingAngles?,
    val trackingObject: String?,
    val isTracking: Boolean
)