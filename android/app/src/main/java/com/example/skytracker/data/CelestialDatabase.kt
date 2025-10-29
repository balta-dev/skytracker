package com.example.skytracker.data

import android.content.Context
import android.content.SharedPreferences
import com.example.skytracker.data.models.CelestialData
import com.example.skytracker.data.models.CelestialObject
import com.example.skytracker.data.models.ObjectType
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

/**
 * Base de datos de objetos celestiales con caché de efemérides
 */
class CelestialDatabase private constructor(context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences("ephemeris_cache", Context.MODE_PRIVATE)
    private val calculator = EphemerisCalculator(context)

    companion object {
        @Volatile
        private var INSTANCE: CelestialDatabase? = null

        fun getInstance(context: Context): CelestialDatabase {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: CelestialDatabase(context.applicationContext).also { INSTANCE = it }
            }
        }

        private const val CACHE_KEY = "cached_objects"
        private const val CACHE_TIMESTAMP_KEY = "cache_timestamp"
    }

    /**
     * Obtiene datos celestiales (desde caché o defaults)
     */
    fun getCelestialData(): CelestialData {
        // Intentar cargar desde caché
        val cachedJson = prefs.getString(CACHE_KEY, null)
        println("CelestialDatabase: getCelestialData - Caché encontrado: ${cachedJson != null}")

        if (cachedJson != null) {
            try {
                println("CelestialDatabase: Cargando desde caché (${cachedJson.length} chars)")
                val data = parseCachedData(cachedJson)
                println("CelestialDatabase: ✓ Caché cargado: ${data.planets.size} planetas, Luna: ${data.moon.name}")
                return data
            } catch (e: Exception) {
                println("CelestialDatabase: ✗ Error parseando caché: ${e.message}")
                e.printStackTrace()
            }
        }

        // Fallback a datos por defecto
        println("CelestialDatabase: Usando datos por defecto")
        return getDefaultCelestialData()
    }

    /**
     * Actualiza efemérides desde JPL Horizons
     */
    suspend fun updateEphemeris(): Boolean = withContext(Dispatchers.IO) {
        try {
            println("CelestialDatabase: Iniciando actualización de efemérides...")
            val updatedObjects = mutableListOf<CelestialObject>()

            // Actualizar planetas - USAR getRaDec() en lugar de getTopocentric()
            val planetIds = mapOf(
                "Mercurio" to "199",
                "Venus" to "299",
                "Marte" to "499",
                "Jupiter" to "599",
                "Saturno" to "699"
            )

            for ((name, id) in planetIds) {
                println("CelestialDatabase: Obteniendo coordenadas de $name (ID: $id)")
                val coords = calculator.getRaDec(id)
                if (coords != null) {
                    println("CelestialDatabase: $name - RA=${coords.raHours}h, Dec=${coords.decDegrees}°")
                    updatedObjects.add(
                        CelestialObject(name, coords.raHours, coords.decDegrees, 0.5, ObjectType.PLANET)
                    )
                } else {
                    println("CelestialDatabase: ERROR - No se obtuvieron coordenadas para $name")
                }
            }

            // Actualizar Luna
            println("CelestialDatabase: Obteniendo coordenadas de Luna (ID: 301)")
            val moonCoords = calculator.getRaDec("301")
            if (moonCoords != null) {
                println("CelestialDatabase: Luna - RA=${moonCoords.raHours}h, Dec=${moonCoords.decDegrees}°")
                updatedObjects.add(
                    CelestialObject("Luna", moonCoords.raHours, moonCoords.decDegrees, 1.2, ObjectType.MOON)
                )
            } else {
                println("CelestialDatabase: ERROR - No se obtuvieron coordenadas para Luna")
            }

            // Si obtuvimos datos, guardar en caché
            if (updatedObjects.isNotEmpty()) {
                println("CelestialDatabase: Se obtuvieron ${updatedObjects.size} objetos, guardando en caché...")
                val defaultData = getDefaultCelestialData()
                val updatedData = CelestialData(
                    stars = defaultData.stars,
                    galaxies = defaultData.galaxies,
                    planets = updatedObjects.filter { it.type == ObjectType.PLANET },
                    moon = updatedObjects.firstOrNull { it.type == ObjectType.MOON }
                        ?: defaultData.moon
                )

                saveCachedData(updatedData)
                println("CelestialDatabase: ✓ Actualización completada exitosamente")
                return@withContext true
            } else {
                println("CelestialDatabase: ERROR - No se obtuvo ningún objeto")
            }

            false
        } catch (e: Exception) {
            println("CelestialDatabase: Exception en updateEphemeris: ${e.message}")
            e.printStackTrace()
            false
        }
    }

    /**
     * Obtiene la edad del caché en horas
     */
    fun getCacheAge(): Long {
        val timestamp = prefs.getLong(CACHE_TIMESTAMP_KEY, -1)
        println("CelestialDatabase: getCacheAge - Timestamp: $timestamp")

        if (timestamp < 0) {
            println("CelestialDatabase: No hay timestamp guardado")
            return -1
        }

        val ageMillis = System.currentTimeMillis() - timestamp
        val ageHours = ageMillis / (1000 * 60 * 60)

        println("CelestialDatabase: Edad del caché: $ageHours horas")
        return ageHours
    }

    /**
     * Obtiene la edad del caché en minutos
     */
    fun getCacheAgeMinutes(): Long {
        val timestamp = prefs.getLong(CACHE_TIMESTAMP_KEY, -1)
        println("CelestialDatabase: getCacheAgeMinutes - Timestamp: $timestamp")

        if (timestamp < 0) {
            println("CelestialDatabase: No hay timestamp guardado")
            return -1
        }

        val ageMillis = System.currentTimeMillis() - timestamp
        val ageMinutes = ageMillis / (1000 * 60) // milisegundos → minutos

        println("CelestialDatabase: Edad del caché: $ageMinutes minutos")
        return ageMinutes
    }


    /**
     * Guarda datos en caché
     */
    private fun saveCachedData(data: CelestialData) {
        try {
            println("CelestialDatabase: Guardando caché...")
            println("CelestialDatabase: - ${data.planets.size} planetas")
            println("CelestialDatabase: - Luna: ${data.moon.name}")

            val json = JSONObject().apply {
                put("stars", objectsToJson(data.stars))
                put("galaxies", objectsToJson(data.galaxies))
                put("planets", objectsToJson(data.planets))
                put("moon", objectToJson(data.moon))
            }

            val timestamp = System.currentTimeMillis()
            val success = prefs.edit()
                .putString(CACHE_KEY, json.toString())
                .putLong(CACHE_TIMESTAMP_KEY, timestamp)
                .commit() // Usar commit() en lugar de apply() para saber si fue exitoso

            if (success) {
                println("CelestialDatabase: ✓ Caché guardado exitosamente")
                println("CelestialDatabase: Timestamp: $timestamp")

                // Verificar que se guardó
                val saved = prefs.getString(CACHE_KEY, null)
                val savedTimestamp = prefs.getLong(CACHE_TIMESTAMP_KEY, -1)
                println("CelestialDatabase: Verificación - JSON length: ${saved?.length}, Timestamp: $savedTimestamp")
            } else {
                println("CelestialDatabase: ✗ ERROR - No se pudo guardar el caché")
            }
        } catch (e: Exception) {
            println("CelestialDatabase: Exception guardando caché: ${e.message}")
            e.printStackTrace()
        }
    }

    /**
     * Parsea datos desde JSON
     */
    private fun parseCachedData(json: String): CelestialData {
        val obj = JSONObject(json)
        return CelestialData(
            stars = jsonToObjects(obj.getJSONArray("stars")),
            galaxies = jsonToObjects(obj.getJSONArray("galaxies")),
            planets = jsonToObjects(obj.getJSONArray("planets")),
            moon = jsonToObject(obj.getJSONObject("moon"))
        )
    }

    private fun objectsToJson(objects: List<CelestialObject>): JSONArray {
        return JSONArray().apply {
            objects.forEach {
                put(objectToJson(it))
                println("CelestialDatabase: Serializando ${it.name}: RA=${it.raHours}h, Dec=${it.decDegrees}°")
            }
        }
    }

    private fun objectToJson(obj: CelestialObject): JSONObject {
        return JSONObject().apply {
            put("name", obj.name)
            put("raHours", obj.raHours)
            put("decDegrees", obj.decDegrees)
            put("size", obj.size)
            put("type", obj.type.name)
        }
    }

    private fun jsonToObjects(array: JSONArray): List<CelestialObject> {
        return (0 until array.length()).map { i ->
            jsonToObject(array.getJSONObject(i))
        }
    }

    private fun jsonToObject(obj: JSONObject): CelestialObject {
        return CelestialObject(
            name = obj.getString("name"),
            raHours = obj.getDouble("raHours"),
            decDegrees = obj.getDouble("decDegrees"),
            size = obj.optDouble("size", 1.0),
            type = ObjectType.valueOf(obj.getString("type"))
        )
    }

    /**
     * Datos por defecto (estrellas fijas y posiciones aproximadas de planetas)
     */
    private fun getDefaultCelestialData(): CelestialData {
        return CelestialData(
            stars = getStars(),
            galaxies = getGalaxies(),
            planets = getPlanets(),
            moon = getMoon()
        )
    }

    private fun getStars(): List<CelestialObject> = listOf(
        // Hemisferio Sur primero
        CelestialObject("Canopus", 6.409528, -52.702861, 8.0, ObjectType.STAR),
        CelestialObject("Achernar", 1.645444, -57.104222, 6.0, ObjectType.STAR),
        CelestialObject("Alpha Centauri", 14.68875, -60.942194, 6.0, ObjectType.STAR), // Alpha Centauri
        CelestialObject("Antares", 16.51625, -26.489222, 7.0, ObjectType.STAR),
        CelestialObject("Fomalhaut", 22.984944, -29.485417, 6.0, ObjectType.STAR),
        CelestialObject("Betelgeuse", 5.9429722, 7.4137222, 7.0, ObjectType.STAR),
        CelestialObject("Rigel", 5.26325, -8.1685, 7.0, ObjectType.STAR),
        CelestialObject("Sirius", 6.7715556, -16.7474167, 9.0, ObjectType.STAR),
        CelestialObject("Vega", 18.630056, 38.811306, 8.0, ObjectType.STAR),
        CelestialObject("Polaris", 3.116, 89.371111, 6.0, ObjectType.STAR),
        CelestialObject("Altair", 19.867389, 8.938889, 6.0, ObjectType.STAR),
        CelestialObject("Deneb", 20.705222, 45.376972, 6.0, ObjectType.STAR),
        CelestialObject("Spica", 13.44225, -11.294333, 6.0, ObjectType.STAR),
        CelestialObject("Arcturus", 14.280361, 19.049444, 6.0, ObjectType.STAR),
        // Pléyades y cinturón de Orión
        CelestialObject("Mintaka", 5.555694, -0.277361, 4.0, ObjectType.STAR),
        CelestialObject("Alnilam", 5.625639, -1.182722, 4.0, ObjectType.STAR),
        CelestialObject("Alnitak", 5.701278, -1.926139, 4.0, ObjectType.STAR),
        CelestialObject("Electra", 3.773917, 24.195583, 3.0, ObjectType.STAR),
        CelestialObject("Merope", 3.798083, 24.029861, 3.0, ObjectType.STAR),
        CelestialObject("Alcyone", 3.817417, 24.186028, 3.0, ObjectType.STAR),
        CelestialObject("Atlas", 3.845389, 24.133444, 3.0, ObjectType.STAR),
        CelestialObject("Pleione", 3.845806, 24.216694, 3.0, ObjectType.STAR),
        CelestialObject("Taygeta", 3.779528, 24.549417, 3.0, ObjectType.STAR),
        CelestialObject("Maia", 3.789806, 24.4495, 3.0, ObjectType.STAR),
        CelestialObject("Diphda", 0.748528, -17.843167, 6.0, ObjectType.STAR)
    )

    private fun getGalaxies(): List<CelestialObject> = listOf(
        // Prioridad sur
        CelestialObject("LMC", 5.400, -69.756, 10.0, ObjectType.GALAXY),
        CelestialObject("SMC", 0.875, -72.800, 8.0, ObjectType.GALAXY),
        // Resto
        CelestialObject("M31", 0.736306, 41.413222, 8.0, ObjectType.GALAXY),
        CelestialObject("M33", 1.564, 30.660, 8.0, ObjectType.GALAXY),
        CelestialObject("M81", 9.960667, 68.939444, 8.0, ObjectType.GALAXY),
        CelestialObject("M51", 13.515722, 47.062389, 8.0, ObjectType.GALAXY)
    )

    private fun getPlanets(): List<CelestialObject> = listOf(
        CelestialObject("Mercurio", 17.5, -23.0, 0.3, ObjectType.PLANET),
        CelestialObject("Venus", 14.2, -10.5, 0.5, ObjectType.PLANET),
        CelestialObject("Marte", 8.5, 22.0, 0.4, ObjectType.PLANET),
        CelestialObject("Jupiter", 3.2, 15.8, 0.8, ObjectType.PLANET),
        CelestialObject("Saturno", 22.8, -12.3, 0.6, ObjectType.PLANET)
    )

    private fun getMoon(): CelestialObject {
        return CelestialObject("Luna", 12.5, -5.0, 1.2, ObjectType.MOON)
    }
}