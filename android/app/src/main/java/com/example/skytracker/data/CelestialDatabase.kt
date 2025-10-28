package com.example.skytracker.data

import com.example.skytracker.data.models.CelestialData
import com.example.skytracker.data.models.CelestialObject
import com.example.skytracker.data.models.ObjectType

/**
 * Base de datos hardcodeada de objetos celestiales
 * Estos datos deben actualizarse periódicamente para planetas y la Luna
 */
object CelestialDatabase {

    /**
     * Datos celestiales principales
     * NOTA: Los datos de planetas y Luna están desactualizados,
     * idealmente deberían calcularse con efemérides
     */
    fun getCelestialData(): CelestialData {
        return CelestialData(
            stars = getStars(),
            galaxies = getGalaxies(),
            planets = getPlanets(),
            moon = getMoon()
        )
    }

    private fun getStars(): List<CelestialObject> = listOf(
        CelestialObject("Sirius", 6.752, -16.716, 8.0, ObjectType.STAR),
        CelestialObject("Canopus", 6.399, -52.696, 7.0, ObjectType.STAR),
        CelestialObject("Rigil Kentaurus", 14.661, -60.834, 6.5, ObjectType.STAR),
        CelestialObject("Arcturus", 14.261, 19.182, 6.5, ObjectType.STAR),
        CelestialObject("Vega", 18.615, 38.783, 6.5, ObjectType.STAR),
        CelestialObject("Capella", 5.278, 45.998, 6.5, ObjectType.STAR),
        CelestialObject("Rigel", 5.242, -8.202, 6.5, ObjectType.STAR),
        CelestialObject("Procyon", 7.655, 5.225, 6.5, ObjectType.STAR),
        CelestialObject("Achernar", 1.628, -57.237, 6.5, ObjectType.STAR),
        CelestialObject("Betelgeuse", 5.919, 7.407, 7.0, ObjectType.STAR),
        CelestialObject("Hadar", 14.063, -60.373, 6.5, ObjectType.STAR),
        CelestialObject("Altair", 19.846, 8.868, 6.0, ObjectType.STAR),
        CelestialObject("Acrux", 12.444, -63.099, 6.5, ObjectType.STAR),
        CelestialObject("Aldebaran", 4.598, 16.509, 6.5, ObjectType.STAR),
        CelestialObject("Antares", 16.490, -26.432, 6.5, ObjectType.STAR),
        CelestialObject("Spica", 13.420, -11.161, 6.0, ObjectType.STAR),
        CelestialObject("Pollux", 7.755, 28.026, 6.0, ObjectType.STAR),
        CelestialObject("Fomalhaut", 22.961, -29.622, 6.0, ObjectType.STAR),
        CelestialObject("Deneb", 20.690, 45.280, 6.0, ObjectType.STAR),
        CelestialObject("Mimosa", 12.795, -59.689, 6.0, ObjectType.STAR),
        CelestialObject("Regulus", 10.139, 11.967, 6.0, ObjectType.STAR),
        CelestialObject("Adhara", 6.977, -28.972, 6.0, ObjectType.STAR),
        CelestialObject("Castor", 7.576, 31.888, 6.0, ObjectType.STAR),
        CelestialObject("Gacrux", 12.519, -57.113, 6.0, ObjectType.STAR),
        CelestialObject("Bellatrix", 5.418, 6.350, 6.0, ObjectType.STAR),
        CelestialObject("Elnath", 5.438, 28.608, 6.0, ObjectType.STAR),
        CelestialObject("Alnilam", 5.603, -1.202, 6.0, ObjectType.STAR),
        CelestialObject("Alnitak", 5.679, -1.943, 6.0, ObjectType.STAR),
        CelestialObject("Saiph", 5.796, -9.669, 6.0, ObjectType.STAR),
        CelestialObject("Mintaka", 5.533, -0.299, 6.0, ObjectType.STAR)
    )

    private fun getGalaxies(): List<CelestialObject> = listOf(
        CelestialObject("M31", 0.712, 41.269, 8.0, ObjectType.GALAXY),
        CelestialObject("M33", 1.564, 30.660, 8.0, ObjectType.GALAXY),
        CelestialObject("LMC", 5.400, -69.756, 10.0, ObjectType.GALAXY),
        CelestialObject("SMC", 0.875, -72.800, 8.0, ObjectType.GALAXY)
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