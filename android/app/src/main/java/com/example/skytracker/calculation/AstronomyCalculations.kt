package com.example.skytracker.calculation

import com.example.skytracker.data.models.PointingAngles
import com.example.skytracker.data.models.Vector3D
import java.util.*
import kotlin.math.*

/**
 * Configuración del observador
 */
object ObserverConfig {
    const val LOCATION_LONGITUDE = -58.229712  // Concepción del Uruguay
    const val LOCATION_LATITUDE = -32.495417
    const val WORLD_SCALE = 30.0
}

/**
 * Cálculos astronómicos portados desde Python
 */
object AstronomyCalculations {

    /**
     * Calcula el Local Sidereal Time (LST)
     * Portado de astronomy.py
     */
    fun calculateLST(dateTime: Calendar, longitudeDeg: Double): Pair<Double, Double> {
        val year = dateTime.get(Calendar.YEAR)
        var month = dateTime.get(Calendar.MONTH) + 1  // Calendar.MONTH es 0-based
        var day = dateTime.get(Calendar.DAY_OF_MONTH)
        val hour = dateTime.get(Calendar.HOUR_OF_DAY)
        val minute = dateTime.get(Calendar.MINUTE)
        val second = dateTime.get(Calendar.SECOND)
        val millisecond = dateTime.get(Calendar.MILLISECOND)

        var y = year
        var m = month

        // Ajuste para enero/febrero
        if (m <= 2) {
            y -= 1
            m += 12
        }

        val a = (y / 100).toInt()
        val b = 2 - a + (a / 4).toInt()

        // Julian Date
        var jd = floor(365.25 * (y + 4716)).toInt() +
                floor(30.6001 * (m + 1)).toInt() +
                day + b - 1524.5

        val fracDay = (hour + minute/60.0 + (second + millisecond/1000.0)/3600.0) / 24.0
        jd += fracDay

        // Siglos desde J2000.0
        val t = (jd - 2451545.0) / 36525.0

        // Greenwich Mean Sidereal Time
        var gmst = 280.46061837 +
                360.98564736629 * (jd - 2451545.0) +
                0.000387933 * t.pow(2) -
                t.pow(3) / 38710000.0

        gmst = gmst % 360.0

        // Local Sidereal Time
        val lstDeg = (gmst + longitudeDeg) % 360.0
        val lstH = lstDeg / 15.0

        return Pair(lstDeg, lstH)
    }

    /**
     * Convierte RA/DEC a coordenadas XYZ cartesianas
     * Portado de astronomy.py
     */
    fun raDecToXYZ(
        raHours: Double,
        decDegrees: Double,
        lstHours: Double,
        latDegrees: Double = ObserverConfig.LOCATION_LATITUDE
    ): Vector3D {
        // Hour Angle
        val haH = lstHours - raHours
        val haDeg = haH * 15.0
        val haRad = Math.toRadians(haDeg)
        val decRad = Math.toRadians(decDegrees)
        val latRad = Math.toRadians(latDegrees)

        // Altura (elevación)
        val sinAlt = sin(decRad) * sin(latRad) +
                cos(decRad) * cos(latRad) * cos(haRad)
        val altRad = asin(sinAlt)

        // Azimut
        val cosAz = (sin(decRad) - sin(altRad) * sin(latRad)) /
                (cos(altRad) * cos(latRad))
        var azRad = acos(cosAz.coerceIn(-1.0, 1.0))  // Proteger de errores numéricos

        // Ajuste de azimut según el signo del seno del HA
        if (sin(haRad) > 0) {
            azRad = 2 * PI - azRad
        }

        // Proyección a 3D
        var x = cos(altRad) * sin(azRad)
        var y = sin(altRad)
        var z = -cos(altRad) * cos(azRad)

        // Escalar para que llegue a ±WORLD_SCALE
        val factor = ObserverConfig.WORLD_SCALE / maxOf(abs(x), abs(y), abs(z))
        x *= factor
        y *= factor
        z *= factor

        return Vector3D(x, y, z)
    }

    /**
     * Calcula los ángulos yaw y pitch para apuntar a un objetivo
     * Portado de astronomy.py
     */
    fun calculateVectorAngles(
        targetX: Double, targetY: Double, targetZ: Double,
        baseX: Double = 0.0, baseY: Double = 0.0, baseZ: Double = 0.0
    ): PointingAngles {
        val dx = targetX - baseX
        val dy = targetY - baseY
        val dz = targetZ - baseZ

        // Calcular pitch (elevación)
        val horizontalDist = sqrt(dx.pow(2) + dz.pow(2))
        val pitch = Math.toDegrees(atan2(dy, horizontalDist))

        // Calcular yaw (azimut)
        val yaw = Math.toDegrees(atan2(dx, -dz)) % 360.0

        return PointingAngles(
            yaw = if (yaw < 0) yaw + 360.0 else yaw,
            pitch = pitch
        )
    }
}

/**
 * Tracker de objetos celestiales
 */
class CelestialTracker {

    /**
     * Calcula los ángulos necesarios para apuntar a un objeto celestial
     */
    fun calculateTrackingAngles(
        raHours: Double,
        decDegrees: Double,
        longitudeDeg: Double = ObserverConfig.LOCATION_LONGITUDE,
        baseX: Double = 0.0,
        baseY: Double = 0.0,
        baseZ: Double = 0.0
    ): PointingAngles {
        // Obtener tiempo actual en UTC
        val now = Calendar.getInstance(TimeZone.getTimeZone("UTC"))

        // Calcular LST
        val (_, lstH) = AstronomyCalculations.calculateLST(now, longitudeDeg)

        // Convertir a coordenadas 3D
        val target = AstronomyCalculations.raDecToXYZ(raHours, decDegrees, lstH)

        // Calcular ángulos
        return AstronomyCalculations.calculateVectorAngles(
            target.x, target.y, target.z,
            baseX, baseY, baseZ
        )
    }
}