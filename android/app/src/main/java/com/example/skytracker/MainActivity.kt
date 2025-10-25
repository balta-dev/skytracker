package com.example.skytracker

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.zIndex
import com.example.skytracker.ui.theme.SkyTrackerTheme
import kotlinx.coroutines.*
import java.net.InetSocketAddress
import java.net.Socket

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SkyTrackerTheme {
                SkyTrackerClientScreen()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SkyTrackerClientScreen() {
    var ipAddress by remember { mutableStateOf("192.168.101.6") }
    var port by remember { mutableStateOf("12345") }
    var objectName by remember { mutableStateOf("") }
    var connectionStatus by remember { mutableStateOf("Desconectado") }
    var trackingObject by remember { mutableStateOf("ninguno") }
    var yaw by remember { mutableStateOf("--") }
    var pitch by remember { mutableStateOf("--") }
    var sensorYaw by remember { mutableStateOf("--") }
    var sensorPitch by remember { mutableStateOf("--") }
    var isTracking by remember { mutableStateOf(false) }
    var isConnected by remember { mutableStateOf(false) }

    val focusManager = LocalFocusManager.current
    val scope = rememberCoroutineScope()

    var socketJob by remember { mutableStateOf<Job?>(null) }
    var socket by remember { mutableStateOf<Socket?>(null) }
    var trackingJob by remember { mutableStateOf<Job?>(null) }

    // Animación de pulso para el indicador de conexión
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse"
    )

    fun connect() {
        socketJob?.cancel()
        socket?.close()
        connectionStatus = "Conectando..."

        socketJob = scope.launch(Dispatchers.IO) {
            var reconnectDelay = 2000L
            while (isActive) {
                try {
                    val targetPort = port.toIntOrNull() ?: 12345
                    socket = Socket()
                    socket?.connect(InetSocketAddress(ipAddress, targetPort), 5000)
                    val reader = socket?.getInputStream()?.bufferedReader()

                    withContext(Dispatchers.Main) {
                        connectionStatus = "Conectado"
                        isConnected = true
                        reconnectDelay = 2000L
                    }

                    while (isActive) {
                        val line = reader?.readLine() ?: break
                        withContext(Dispatchers.Main) {
                            when {
                                line.startsWith("OK") -> {
                                    isTracking = true
                                    trackingObject = objectName
                                }
                                line.startsWith("ERROR") -> {
                                    connectionStatus = "Conectado - $line"
                                    isTracking = false
                                }
                                line.startsWith("DATA:") -> {
                                    val parts = line.removePrefix("DATA:").split(",")
                                    if (parts.size == 2) {
                                        yaw = parts[0].trim()
                                        pitch = parts[1].trim()
                                    }
                                }
                                line.startsWith("SENSOR:") -> {
                                    val parts = line.removePrefix("SENSOR:").split(",")
                                    if (parts.size == 2) {
                                        sensorYaw = parts[0].trim()
                                        sensorPitch = parts[1].trim()
                                    }
                                }
                                line.startsWith("STOPPED") -> {
                                    isTracking = false
                                    trackingObject = "ninguno"
                                    yaw = "--"
                                    pitch = "--"
                                }
                            }
                        }
                    }
                } catch (e: Exception) {
                    withContext(Dispatchers.Main) {
                        connectionStatus = "Reconectando en ${reconnectDelay / 1000}s..."
                        isConnected = false
                        isTracking = false
                        yaw = "--"
                        pitch = "--"
                        sensorYaw = "--"
                        sensorPitch = "--"
                    }
                    delay(reconnectDelay)
                    reconnectDelay = minOf(reconnectDelay * 2, 10000L)
                }
            }
        }
    }

    fun disconnect() {
        socketJob?.cancel()
        trackingJob?.cancel()
        socket?.close()
        connectionStatus = "Desconectado"
        isConnected = false
        isTracking = false
        trackingObject = "ninguno"
        yaw = "--"
        pitch = "--"
        sensorYaw = "--"
        sensorPitch = "--"
    }

    fun sendTrackCommand() {
        if (objectName.isNotBlank()) {
            isTracking = true
            trackingObject = objectName
            connectionStatus = "Rastreando $objectName..."
            trackingJob?.cancel()

            trackingJob = scope.launch(Dispatchers.IO) {
                try {
                    val writer = socket?.getOutputStream()?.bufferedWriter()
                    while (isActive && isTracking) {
                        writer?.write("$objectName\n")
                        writer?.flush()
                        delay(2000L)
                    }
                } catch (e: Exception) {
                    withContext(Dispatchers.Main) {
                        connectionStatus = "Error de rastreo: ${e.message}"
                        isTracking = false
                    }
                }
            }
            focusManager.clearFocus()
        }
    }

    fun sendStopCommand() {
        scope.launch(Dispatchers.IO) {
            try {
                val writer = socket?.getOutputStream()?.bufferedWriter()
                writer?.write("STOP\n")
                writer?.flush()
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    connectionStatus = "Error al detener: ${e.message}"
                }
            }
        }
        trackingJob?.cancel()
        trackingJob = null
        isTracking = false
        trackingObject = "ninguno"
        yaw = "--"
        pitch = "--"
        sensorYaw = "--"
        sensorPitch = "--"
        connectionStatus = "Conectado - Esperando comando"
    }

    // UI con gradientes y animaciones
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFF0A0E27),
                        Color(0xFF1A1D3A),
                        Color(0xFF0A0E27)
                    )
                )
            )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {

            Spacer(modifier = Modifier.height(20.dp))

            // TÍTULO CON EFECTO
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.padding(vertical = 8.dp)
            ) {
                Text(
                    text = "SKY",
                    fontSize = 40.sp,
                    fontWeight = FontWeight.Black,
                    color = Color(0xFFFFD700),
                    letterSpacing = 8.sp
                )
                Text(
                    text = "TRACKER",
                    fontSize = 32.sp,
                    fontWeight = FontWeight.Light,
                    color = Color(0xFF00D4FF),
                    letterSpacing = 12.sp
                )

                // Indicador de estado animado
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center,
                    modifier = Modifier.padding(top = 12.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(12.dp)
                            .scale(if (isConnected) pulseScale else 1f)
                            .clip(CircleShape)
                            .background(
                                when {
                                    isConnected -> Color(0xFF00FF88)
                                    connectionStatus.contains("Reconectando") -> Color(0xFFFFAA00)
                                    else -> Color(0xFFFF4444)
                                }
                            )
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = connectionStatus,
                        color = Color.White.copy(alpha = 0.8f),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            // CONTROL DE RASTREO (ahora primero cuando está conectado)
            AnimatedVisibility(
                visible = isConnected,
                enter = expandVertically() + fadeIn(),
                exit = shrinkVertically() + fadeOut()
            ) {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFF1E2239).copy(alpha = 0.8f)
                    ),
                    elevation = CardDefaults.cardElevation(16.dp),
                    shape = RoundedCornerShape(20.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .clip(CircleShape)
                                    .background(if (isTracking) Color(0xFF00FF88) else Color.Gray)
                            )
                            Text(
                                "Control de Rastreo",
                                color = if (isTracking) Color(0xFF00FF88) else Color.Gray,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }

                        AnimatedVisibility(
                            visible = !isTracking,
                            enter = expandVertically() + fadeIn(),
                            exit = shrinkVertically() + fadeOut()
                        ) {
                            OutlinedTextField(
                                value = objectName,
                                onValueChange = { objectName = it },
                                label = { Text("Objeto celestial") },
                                placeholder = { Text("Ej: Sirius, Luna, Marte") },
                                singleLine = true,
                                enabled = isConnected && !isTracking,
                                keyboardActions = KeyboardActions(onDone = { sendTrackCommand() }),
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = Color.White,
                                    unfocusedTextColor = Color.Gray,
                                    focusedBorderColor = Color(0xFF00FF88),
                                    unfocusedBorderColor = Color.Gray,
                                    focusedLabelColor = Color(0xFF00FF88),
                                    unfocusedLabelColor = Color.Gray
                                ),
                                shape = RoundedCornerShape(12.dp),
                                modifier = Modifier.fillMaxWidth()
                            )
                        }

                        if (!isTracking) {
                            Button(
                                onClick = { sendTrackCommand() },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = Color(0xFF00FF88)
                                ),
                                shape = RoundedCornerShape(12.dp),
                                enabled = isConnected && objectName.isNotBlank(),
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(56.dp)
                            ) {
                                Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color.Black)
                                Spacer(Modifier.width(8.dp))
                                Text(
                                    "INICIAR RASTREO",
                                    color = Color.Black,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 16.sp
                                )
                            }
                        } else {
                            Button(
                                onClick = { sendStopCommand() },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = Color(0xFFFF4444)
                                ),
                                shape = RoundedCornerShape(12.dp),
                                enabled = isConnected,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(56.dp)
                            ) {
                                Icon(Icons.Default.Close, contentDescription = null)
                                Spacer(Modifier.width(8.dp))
                                Text(
                                    "DETENER RASTREO",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 16.sp
                                )
                            }
                        }
                    }
                }
            }

            // CONFIGURACIÓN DE SERVIDOR (ahora después cuando está conectado)
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFF1E2239).copy(alpha = 0.8f)
                ),
                elevation = CardDefaults.cardElevation(16.dp),
                shape = RoundedCornerShape(20.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(Color(0xFFFFD700))
                        )
                        Text(
                            "Configuración de Servidor",
                            color = Color(0xFFFFD700),
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp
                        )
                    }

                    AnimatedVisibility(
                        visible = !isConnected,
                        enter = expandVertically() + fadeIn(),
                        exit = shrinkVertically() + fadeOut()
                    ) {
                        Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                OutlinedTextField(
                                    value = ipAddress,
                                    onValueChange = { ipAddress = it },
                                    label = { Text("IP del Servidor") },
                                    singleLine = true,
                                    keyboardOptions = KeyboardOptions(
                                        keyboardType = KeyboardType.Number,
                                        imeAction = ImeAction.Next
                                    ),
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = Color.White,
                                        unfocusedTextColor = Color.Gray,
                                        focusedBorderColor = Color(0xFF00D4FF),
                                        unfocusedBorderColor = Color.Gray,
                                        focusedLabelColor = Color(0xFF00D4FF),
                                        unfocusedLabelColor = Color.Gray
                                    ),
                                    shape = RoundedCornerShape(12.dp),
                                    modifier = Modifier.weight(1f),
                                    enabled = !isConnected
                                )

                                OutlinedTextField(
                                    value = port,
                                    onValueChange = { port = it },
                                    label = { Text("Puerto") },
                                    singleLine = true,
                                    keyboardOptions = KeyboardOptions(
                                        keyboardType = KeyboardType.Number,
                                        imeAction = ImeAction.Done
                                    ),
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = Color.White,
                                        unfocusedTextColor = Color.Gray,
                                        focusedBorderColor = Color(0xFF00D4FF),
                                        unfocusedBorderColor = Color.Gray,
                                        focusedLabelColor = Color(0xFF00D4FF),
                                        unfocusedLabelColor = Color.Gray
                                    ),
                                    shape = RoundedCornerShape(12.dp),
                                    modifier = Modifier.width(110.dp),
                                    enabled = !isConnected
                                )
                            }
                        }
                    }

                    if (!isConnected) {
                        Button(
                            onClick = { connect() },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = Color(0xFF00D4FF)
                            ),
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(56.dp)
                        ) {
                            Icon(Icons.Default.Refresh, contentDescription = null, tint = Color.Black)
                            Spacer(Modifier.width(8.dp))
                            Text(
                                "CONECTAR",
                                color = Color.Black,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }
                    } else {
                        OutlinedButton(
                            onClick = { disconnect() },
                            colors = ButtonDefaults.outlinedButtonColors(
                                contentColor = Color(0xFFFF4444)
                            ),
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(56.dp)
                        ) {
                            Icon(Icons.Default.Close, contentDescription = null)
                            Spacer(Modifier.width(8.dp))
                            Text("DESCONECTAR", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                        }
                    }
                }
            }

            // DATOS DE TELEMETRÍA
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                // TARGET
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFF1E2239).copy(alpha = 0.8f)
                    ),
                    elevation = CardDefaults.cardElevation(16.dp),
                    shape = RoundedCornerShape(20.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            modifier = Modifier.padding(bottom = 12.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .clip(CircleShape)
                                    .background(Color(0xFF00D4FF))
                            )
                            Text(
                                "Vector Comandado",
                                color = Color(0xFF00D4FF),
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }

                        Row(
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            DataCard(
                                label = "YAW",
                                value = yaw,
                                color = Color(0xFF00D4FF),
                                modifier = Modifier.weight(1f)
                            )
                            DataCard(
                                label = "PITCH",
                                value = pitch,
                                color = Color(0xFF00D4FF),
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }

                // SENSOR
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFF1E2239).copy(alpha = 0.8f)
                    ),
                    elevation = CardDefaults.cardElevation(16.dp),
                    shape = RoundedCornerShape(20.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            modifier = Modifier.padding(bottom = 12.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .clip(CircleShape)
                                    .background(Color(0xFFFF6B00))
                            )
                            Text(
                                "Sensor Feedback",
                                color = Color(0xFFFF6B00),
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }

                        Row(
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            DataCard(
                                label = "YAW",
                                value = sensorYaw,
                                color = Color(0xFFFF6B00),
                                modifier = Modifier.weight(1f)
                            )
                            DataCard(
                                label = "PITCH",
                                value = sensorPitch,
                                color = Color(0xFFFF6B00),
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))
        }
    }
}

@Composable
fun DataCard(
    label: String,
    value: String,
    color: Color,
    modifier: Modifier = Modifier
) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF0F1419).copy(alpha = 0.6f)
        ),
        shape = RoundedCornerShape(16.dp),
        modifier = modifier
    ) {
        Column(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = label,
                color = Color.Gray,
                fontSize = 11.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 2.sp
            )
            Spacer(Modifier.height(8.dp))
            Text(
                text = if (value != "--") "$value°" else "--",
                color = if (value != "--") color else Color.White.copy(alpha = 0.3f),
                fontSize = 32.sp,
                fontWeight = FontWeight.Black
            )
        }
    }
}

@Preview(showBackground = true)
@Composable
fun SkyTrackerPreview() {
    SkyTrackerTheme {
        SkyTrackerClientScreen()
    }
}