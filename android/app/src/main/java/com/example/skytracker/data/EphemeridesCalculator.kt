package com.example.skytracker.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.CertificatePinner
import java.net.HttpURLConnection
import java.net.URL
import java.util.*
import kotlin.math.*
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.IOException
import java.io.InputStream
import java.security.KeyStore
import java.security.SecureRandom
import java.security.cert.CertificateFactory
import java.security.cert.X509Certificate
import java.util.concurrent.TimeUnit
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManager
import javax.net.ssl.TrustManagerFactory
import javax.net.ssl.X509TrustManager

/**
 * Calculador de efemérides usando JPL Horizons API
 */
class EphemerisCalculator(private val context: Context) {

    // Ubicación del observador
    private val observerLon = -58.229712  // Concepción del Uruguay
    private val observerLat = -32.495417
    private val observerAlt = 3.0         // metros

    /**
     * Obtiene RA/Dec desde JPL Horizons
     * Usa OBSERVER mode con QUANTITIES='1' para obtener RA/Dec aparente
     */
    suspend fun getRaDec(objectId: String): RaDecCoordinates? = withContext(Dispatchers.IO) {
        try {
            val nowUtc = Calendar.getInstance(TimeZone.getTimeZone("UTC"))
            val jd = calculateJulianDate(nowUtc)

            val jdStart = String.format(Locale.US, "JD%.3f", jd)
            val jdStop = String.format(Locale.US, "JD%.3f", jd + 0.001)

            val url = "https://ssd.jpl.nasa.gov/api/horizons.api" +
                    "?format=text" +
                    "&COMMAND=$objectId" +
                    "&MAKE_EPHEM=YES" +
                    "&EPHEM_TYPE=OBSERVER" +
                    "&CENTER=500@399" +
                    "&START_TIME=$jdStart" +
                    "&STOP_TIME=$jdStop" +
                    "&STEP_SIZE=1m" +
                    "&QUANTITIES=1" +
                    "&ANG_FORMAT=DEG"

            val response = fetchFromHorizons(url)
            if (response != null) {
                return@withContext parseRaDecResponse(response)
            }

            null
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * Crear cliente OkHttp seguro
     */
    private fun createSecureOkHttpClient(): OkHttpClient {
        return OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    /**
     * Realiza la petición HTTP a Horizons
     */
    private fun fetchFromHorizons(urlString: String): String? {
        return try {
            println("EphemerisCalculator: Fetching URL: $urlString")

            val client = createSecureOkHttpClient()
            val request = okhttp3.Request.Builder()
                .url(urlString)
                .get()
                .header("User-Agent", "SkyTracker/1.0")
                .build()

            val response = client.newCall(request).execute()
            println("EphemerisCalculator: Response code: ${response.code}")

            if (response.isSuccessful) {
                val body = response.body?.string()
                println("EphemerisCalculator: Response length: ${body?.length ?: 0} chars")
                if (body != null && body.length > 500) {
                    println("EphemerisCalculator: Response preview: ${body.substring(0, 500)}")
                }
                body
            } else {
                println("EphemerisCalculator: Error response: ${response.body?.string()}")
                null
            }
        } catch (e: Exception) {
            println("EphemerisCalculator: Exception fetching: ${e.message}")
            e.printStackTrace()
            null
        }
    }
    /**
     * Parsea la respuesta OBSERVER mode para extraer RA/Dec
     * Busca líneas de datos después del encabezado
     */
    private fun parseRaDecResponse(response: String): RaDecCoordinates? {
        try {
            // Buscar sección de datos
            val soeIndex = response.indexOf("\$\$SOE")
            val eoeIndex = response.indexOf("\$\$EOE")

            if (soeIndex < 0 || eoeIndex < 0) {
                println("EphemerisCalculator: No se encontró SOE o EOE")
                return null
            }

            val dataSection = response.substring(soeIndex + 6, eoeIndex).trim()
            val lines = dataSection.lines().filter { it.trim().isNotBlank() }

            if (lines.isEmpty()) {
                println("EphemerisCalculator: No hay líneas de datos")
                return null
            }

            // La primera línea con datos numéricos
            for (line in lines) {
                val trimmed = line.trim()
                // Buscar línea que empiece con fecha/JD y tenga números
                if (trimmed.matches(Regex("^[\\d\\s.]+.*"))) {
                    val parts = trimmed.split(Regex("\\s+"))

                    // Necesitamos al menos: fecha + RA + Dec
                    if (parts.size >= 3) {
                        // Intentar parsear RA y Dec (pueden estar en posiciones 1 y 2, o más adelante)
                        for (i in 1 until parts.size - 1) {
                            val ra = parts[i].toDoubleOrNull()
                            val dec = parts[i + 1].toDoubleOrNull()

                            if (ra != null && dec != null) {
                                // RA viene en grados, convertir a horas
                                val raHours = ra / 15.0
                                println("EphemerisCalculator: Parseado RA=$raHours h, Dec=$dec°")
                                return RaDecCoordinates(raHours, dec)
                            }
                        }
                    }
                }
            }

            println("EphemerisCalculator: No se pudo parsear RA/Dec de la respuesta")
            null
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
        return null
    }

    /**
     * Parsea la respuesta OBSERVER mode para extraer Az/Alt
     * Busca líneas de datos después del encabezado
     */
    private fun parseAzAltResponse(response: String): CelestialCoordinates? {
        try {
            val soeIndex = response.indexOf("\$\$SOE")
            val eoeIndex = response.indexOf("\$\$EOE")

            if (soeIndex < 0 || eoeIndex < 0) {
                println("EphemerisCalculator: No se encontró SOE o EOE en Az/Alt")
                return null
            }

            val dataSection = response.substring(soeIndex + 6, eoeIndex).trim()
            val lines = dataSection.lines().filter { it.trim().isNotBlank() }

            if (lines.isEmpty()) {
                println("EphemerisCalculator: No hay líneas de datos en Az/Alt")
                return null
            }

            // La primera línea con datos numéricos
            for (line in lines) {
                val trimmed = line.trim()
                if (trimmed.matches(Regex("^[\\d\\s.]+.*"))) {
                    val parts = trimmed.split(Regex("\\s+"))

                    if (parts.size >= 3) {
                        for (i in 1 until parts.size - 1) {
                            val az = parts[i].toDoubleOrNull()
                            val alt = parts[i + 1].toDoubleOrNull()

                            if (az != null && alt != null) {
                                println("EphemerisCalculator: Parseado Az=$az°, Alt=$alt°")
                                return CelestialCoordinates(az, alt)
                            }
                        }
                    }
                }
            }

            println("EphemerisCalculator: No se pudo parsear Az/Alt de la respuesta")
            null
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
        return null
    }

    /**
     * Calcula Julian Date desde Calendar
     */
    private fun calculateJulianDate(date: Calendar): Double {
        var year = date.get(Calendar.YEAR)
        var month = date.get(Calendar.MONTH) + 1
        val day = date.get(Calendar.DAY_OF_MONTH)

        if (month <= 2) {
            year -= 1
            month += 12
        }

        val a = (year / 100).toInt()
        val b = 2 - a + (a / 4).toInt()

        val jd0 = floor(365.25 * (year + 4716.0)) +
                floor(30.6001 * (month + 1.0)) +
                day + b - 1524.5

        val hour = date.get(Calendar.HOUR_OF_DAY)
        val minute = date.get(Calendar.MINUTE)
        val second = date.get(Calendar.SECOND)

        return jd0 + (hour + minute/60.0 + second/3600.0) / 24.0
    }
}

/**
 * Coordenadas celestiales en Az/Alt
 */
data class CelestialCoordinates(
    val yawDegrees: Double,   // Azimut
    val pitchDegrees: Double  // Elevación
)

/**
 * Coordenadas en RA/Dec
 */
data class RaDecCoordinates(
    val raHours: Double,      // Ascensión Recta en horas
    val decDegrees: Double    // Declinación en grados
)