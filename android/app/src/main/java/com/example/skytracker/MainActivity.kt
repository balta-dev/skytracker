package com.example.skytracker

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
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
import androidx.compose.material.icons.filled.*
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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.skytracker.repository.OperationMode
import com.example.skytracker.ui.theme.SkyTrackerTheme
import com.example.skytracker.ui.viewmodel.SkyTrackerViewModel

class MainActivity : ComponentActivity() {
    private val viewModel: SkyTrackerViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SkyTrackerTheme {
                SkyTrackerScreen(viewModel)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SkyTrackerScreen(viewModel: SkyTrackerViewModel) {
    // Estados de configuración
    var serverIp by remember { mutableStateOf("192.168.101.6") }
    var serverPort by remember { mutableStateOf("12345") }
    var esp32Ip by remember { mutableStateOf("192.168.101.100") }
    var esp32Port by remember { mutableStateOf("80") }
    var objectName by remember { mutableStateOf("") }
    var selectedMode by remember { mutableStateOf(OperationMode.SERVER) }

    // Estados del ViewModel
    val telemetryData by viewModel.telemetryData.collectAsState()
    val connectionStatus by viewModel.connectionStatus.collectAsState()
    val isConnected by viewModel.isConnected.collectAsState()
    val operationMode by viewModel.operationMode.collectAsState()

    val focusManager = LocalFocusManager.current

    // Animación de pulso
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

    // Funciones de control
    fun connect() {
        when (selectedMode) {
            OperationMode.SERVER -> {
                viewModel.connectToServer(serverIp, serverPort)
            }
            OperationMode.DIRECT -> {
                viewModel.connectToESP32(esp32Ip, esp32Port)
            }
        }
    }

    fun disconnect() {
        viewModel.disconnect()
    }

    fun startTracking() {
        if (objectName.isNotBlank()) {
            viewModel.startTracking(objectName)
            focusManager.clearFocus()
        }
    }

    fun stopTracking() {
        viewModel.stopTracking()
    }

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

            // TÍTULO Y ESTADO
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

                // Badge de modo
                Surface(
                    color = when(operationMode) {
                        OperationMode.SERVER -> Color(0xFF00D4FF)
                        OperationMode.DIRECT -> Color(0xFFFF6B00)
                    }.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(20.dp),
                    modifier = Modifier.padding(top = 8.dp)
                ) {
                    Text(
                        text = when(operationMode) {
                            OperationMode.SERVER -> "MODO SERVIDOR"
                            OperationMode.DIRECT -> "MODO DIRECTO"
                        },
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 6.dp),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = when(operationMode) {
                            OperationMode.SERVER -> Color(0xFF00D4FF)
                            OperationMode.DIRECT -> Color(0xFFFF6B00)
                        }
                    )
                }

                // Indicador de estado
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

            // CONTROL DE RASTREO (cuando está conectado)
            AnimatedVisibility(
                visible = isConnected,
                enter = expandVertically() + fadeIn(),
                exit = shrinkVertically() + fadeOut()
            ) {
                TrackingControl(
                    objectName = objectName,
                    onObjectNameChange = { objectName = it },
                    isTracking = telemetryData.isTracking,
                    onStartTracking = { startTracking() },
                    onStopTracking = { stopTracking() }
                )
            }

            // SELECTOR DE MODO (solo cuando no está conectado)
            AnimatedVisibility(
                visible = !isConnected,
                enter = expandVertically() + fadeIn(),
                exit = shrinkVertically() + fadeOut()
            ) {
                ModeSelector(
                    selectedMode = selectedMode,
                    onModeSelected = { selectedMode = it }
                )
            }

            // CONFIGURACIÓN DE CONEXIÓN
            ConnectionConfig(
                isConnected = isConnected,
                selectedMode = selectedMode,
                serverIp = serverIp,
                serverPort = serverPort,
                esp32Ip = esp32Ip,
                esp32Port = esp32Port,
                onServerIpChange = { serverIp = it },
                onServerPortChange = { serverPort = it },
                onEsp32IpChange = { esp32Ip = it },
                onEsp32PortChange = { esp32Port = it },
                onConnect = { connect() },
                onDisconnect = { disconnect() }
            )

            // TELEMETRÍA
            TelemetryDisplay(
                targetYaw = telemetryData.targetAngles?.yaw?.let { "%.2f".format(it) } ?: "--",
                targetPitch = telemetryData.targetAngles?.pitch?.let { "%.2f".format(it) } ?: "--",
                sensorYaw = telemetryData.sensorAngles?.yaw?.let { "%.2f".format(it) } ?: "--",
                sensorPitch = telemetryData.sensorAngles?.pitch?.let { "%.2f".format(it) } ?: "--"
            )

            Spacer(modifier = Modifier.height(20.dp))
        }
    }
}

@Composable
fun ModeSelector(
    selectedMode: OperationMode,
    onModeSelected: (OperationMode) -> Unit
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
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                "Modo de Operación",
                color = Color(0xFFFFD700),
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp
            )

            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                ModeButton(
                    title = "SERVIDOR",
                    description = "Conectar a Python\nCálculos en servidor",
                    icon = Icons.Default.Info,
                    color = Color(0xFF00D4FF),
                    isSelected = selectedMode == OperationMode.SERVER,
                    onClick = { onModeSelected(OperationMode.SERVER) },
                    modifier = Modifier.weight(1f)
                )

                ModeButton(
                    title = "DIRECTO",
                    description = "Conectar al ESP32\nCálculos locales",
                    icon = Icons.Default.Star,
                    color = Color(0xFFFF6B00),
                    isSelected = selectedMode == OperationMode.DIRECT,
                    onClick = { onModeSelected(OperationMode.DIRECT) },
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
fun ModeButton(
    title: String,
    description: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    color: Color,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Button(
        onClick = onClick,
        colors = ButtonDefaults.buttonColors(
            containerColor = if (isSelected) color else Color(0xFF0F1419).copy(alpha = 0.6f),
            contentColor = if (isSelected) Color.Black else color
        ),
        shape = RoundedCornerShape(16.dp),
        modifier = modifier.height(100.dp)
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                icon,
                contentDescription = null,
                modifier = Modifier.size(24.dp)
            )
            Spacer(Modifier.height(8.dp))
            Text(
                title,
                fontWeight = FontWeight.Bold,
                fontSize = 12.sp
            )
            Text(
                description,
                fontSize = 9.sp,
                modifier = Modifier.padding(top = 4.dp),
                lineHeight = 11.sp
            )
        }
    }
}

@Composable
fun TrackingControl(
    objectName: String,
    onObjectNameChange: (String) -> Unit,
    isTracking: Boolean,
    onStartTracking: () -> Unit,
    onStopTracking: () -> Unit
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

            AnimatedVisibility(visible = !isTracking) {
                OutlinedTextField(
                    value = objectName,
                    onValueChange = onObjectNameChange,
                    label = { Text("Objeto celestial") },
                    placeholder = { Text("Ej: Sirius, Luna, Marte") },
                    singleLine = true,
                    keyboardActions = KeyboardActions(onDone = { onStartTracking() }),
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
                    onClick = onStartTracking,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF00FF88)),
                    shape = RoundedCornerShape(12.dp),
                    enabled = objectName.isNotBlank(),
                    modifier = Modifier.fillMaxWidth().height(56.dp)
                ) {
                    Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color.Black)
                    Spacer(Modifier.width(8.dp))
                    Text("INICIAR RASTREO", color = Color.Black, fontWeight = FontWeight.Bold)
                }
            } else {
                Button(
                    onClick = onStopTracking,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF4444)),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth().height(56.dp)
                ) {
                    Icon(Icons.Default.Close, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("DETENER RASTREO", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun ConnectionConfig(
    isConnected: Boolean,
    selectedMode: OperationMode,
    serverIp: String,
    serverPort: String,
    esp32Ip: String,
    esp32Port: String,
    onServerIpChange: (String) -> Unit,
    onServerPortChange: (String) -> Unit,
    onEsp32IpChange: (String) -> Unit,
    onEsp32PortChange: (String) -> Unit,
    onConnect: () -> Unit,
    onDisconnect: () -> Unit
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
                        .background(Color(0xFFFFD700))
                )
                Text(
                    "Configuración de Conexión",
                    color = Color(0xFFFFD700),
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp
                )
            }

            AnimatedVisibility(visible = !isConnected) {
                Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    when (selectedMode) {
                        OperationMode.SERVER -> {
                            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                OutlinedTextField(
                                    value = serverIp,
                                    onValueChange = onServerIpChange,
                                    label = { Text("IP del Servidor") },
                                    singleLine = true,
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = Color.White,
                                        unfocusedTextColor = Color.Gray,
                                        focusedBorderColor = Color(0xFF00D4FF),
                                        unfocusedBorderColor = Color.Gray
                                    ),
                                    shape = RoundedCornerShape(12.dp),
                                    modifier = Modifier.weight(1f)
                                )
                                OutlinedTextField(
                                    value = serverPort,
                                    onValueChange = onServerPortChange,
                                    label = { Text("Puerto") },
                                    singleLine = true,
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = Color.White,
                                        unfocusedTextColor = Color.Gray,
                                        focusedBorderColor = Color(0xFF00D4FF),
                                        unfocusedBorderColor = Color.Gray
                                    ),
                                    shape = RoundedCornerShape(12.dp),
                                    modifier = Modifier.width(110.dp)
                                )
                            }
                        }
                        OperationMode.DIRECT -> {
                            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                OutlinedTextField(
                                    value = esp32Ip,
                                    onValueChange = onEsp32IpChange,
                                    label = { Text("IP del ESP32") },
                                    singleLine = true,
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = Color.White,
                                        unfocusedTextColor = Color.Gray,
                                        focusedBorderColor = Color(0xFFFF6B00),
                                        unfocusedBorderColor = Color.Gray
                                    ),
                                    shape = RoundedCornerShape(12.dp),
                                    modifier = Modifier.weight(1f)
                                )
                                OutlinedTextField(
                                    value = esp32Port,
                                    onValueChange = onEsp32PortChange,
                                    label = { Text("Puerto") },
                                    singleLine = true,
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                    colors = OutlinedTextFieldDefaults.colors(
                                        focusedTextColor = Color.White,
                                        unfocusedTextColor = Color.Gray,
                                        focusedBorderColor = Color(0xFFFF6B00),
                                        unfocusedBorderColor = Color.Gray
                                    ),
                                    shape = RoundedCornerShape(12.dp),
                                    modifier = Modifier.width(110.dp)
                                )
                            }
                        }
                    }
                }
            }

            if (!isConnected) {
                Button(
                    onClick = onConnect,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = when(selectedMode) {
                            OperationMode.SERVER -> Color(0xFF00D4FF)
                            OperationMode.DIRECT -> Color(0xFFFF6B00)
                        }
                    ),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth().height(56.dp)
                ) {
                    Icon(Icons.Default.Refresh, contentDescription = null, tint = Color.Black)
                    Spacer(Modifier.width(8.dp))
                    Text("CONECTAR", color = Color.Black, fontWeight = FontWeight.Bold)
                }
            } else {
                OutlinedButton(
                    onClick = onDisconnect,
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFFFF4444)),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth().height(56.dp)
                ) {
                    Icon(Icons.Default.Close, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("DESCONECTAR", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun TelemetryDisplay(
    targetYaw: String,
    targetPitch: String,
    sensorYaw: String,
    sensorPitch: String
) {
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        TelemetryCard(
            title = "Vector Comandado",
            color = Color(0xFF00D4FF),
            yaw = targetYaw,
            pitch = targetPitch
        )

        TelemetryCard(
            title = "Sensor Feedback",
            color = Color(0xFFFF6B00),
            yaw = sensorYaw,
            pitch = sensorPitch
        )
    }
}

@Composable
fun TelemetryCard(
    title: String,
    color: Color,
    yaw: String,
    pitch: String
) {
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
                        .background(color)
                )
                Text(title, color = color, fontSize = 14.sp, fontWeight = FontWeight.Bold)
            }

            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                DataCard(label = "YAW", value = yaw, color = color, modifier = Modifier.weight(1f))
                DataCard(label = "PITCH", value = pitch, color = color, modifier = Modifier.weight(1f))
            }
        }
    }
}

@Composable
fun DataCard(label: String, value: String, color: Color, modifier: Modifier = Modifier) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF0F1419).copy(alpha = 0.6f)
        ),
        shape = RoundedCornerShape(16.dp),
        modifier = modifier
    ) {
        Column(
            modifier = Modifier.padding(16.dp).fillMaxWidth(),
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