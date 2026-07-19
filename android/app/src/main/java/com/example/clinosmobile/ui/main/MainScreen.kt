package com.example.clinosmobile.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.clinosmobile.data.DefaultDataRepository
import com.example.clinosmobile.theme.ClinosMobileTheme

@Composable
fun MainScreen(
  onItemClick: (NavKey) -> Unit,
  modifier: Modifier = Modifier,
  viewModel: MainScreenViewModel = viewModel { MainScreenViewModel(DefaultDataRepository()) },
) {
  val state by viewModel.uiState.collectAsStateWithLifecycle()
  when (state) {
    MainScreenUiState.Loading -> {
      Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        CircularProgressIndicator(color = Color(0xFF6366F1))
      }
    }
    is MainScreenUiState.Success -> {
      MainScreen(
        data = (state as MainScreenUiState.Success).data,
        viewModel = viewModel,
        modifier = modifier
      )
    }
    is MainScreenUiState.Error -> {
      Column(
        modifier = modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
      ) {
        Text(
          text = "Error loading telemetry: ${(state as MainScreenUiState.Error).throwable.message}",
          color = MaterialTheme.colorScheme.error,
          fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = { viewModel.refresh() }) {
          Text("Retry")
        }
      }
    }
  }
}

@Composable
internal fun MainScreen(
  data: List<String>,
  viewModel: MainScreenViewModel? = null,
  modifier: Modifier = Modifier
) {
  var consoleLog by remember { mutableStateOf("Ready to receive telemetry triggers.") }
  val scrollState = rememberScrollState()

  // Connection State observation
  val connectionState = viewModel?.connectionState?.collectAsStateWithLifecycle()?.value

  // Connection Inputs
  var isSettingsExpanded by remember { mutableStateOf(false) }
  var serverUrl by remember { mutableStateOf(connectionState?.url ?: "http://10.0.2.2:8000") }
  var username by remember { mutableStateOf(connectionState?.username ?: "") }
  var password by remember { mutableStateOf("") }
  var isConnecting by remember { mutableStateOf(false) }

  // Sync inputs on state change
  LaunchedEffect(connectionState) {
    connectionState?.let {
      serverUrl = it.url
      username = it.username
    }
  }

  Column(
    modifier = modifier
      .fillMaxSize()
      .verticalScroll(scrollState)
      .padding(8.dp),
    verticalArrangement = Arrangement.spacedBy(16.dp)
  ) {
    // ─── Header ───
    Row(
      modifier = Modifier.fillMaxWidth(),
      horizontalArrangement = Arrangement.SpaceBetween,
      verticalAlignment = Alignment.CenterVertically
    ) {
      Column {
        Text(
          text = "AI Healthcare System Mobile",
          fontSize = 24.sp,
          fontWeight = FontWeight.Bold,
          color = Color(0xFF6366F1)
        )
        Text(
          text = "Clinical Telemetry Console",
          fontSize = 12.sp,
          color = Color.Gray,
          fontWeight = FontWeight.Medium
        )
      }

      // Refresh telemetry button
      IconButton(
        onClick = {
          consoleLog = "System: Syncing latest clinical telemetry..."
          viewModel?.refresh()
        }
      ) {
        Text("🔄", fontSize = 18.sp)
      }
    }

    // ─── Server Settings Panel ───
    Card(
      modifier = Modifier.fillMaxWidth(),
      colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B)),
      shape = RoundedCornerShape(12.dp)
    ) {
      Column(modifier = Modifier.padding(12.dp)) {
        Row(
          modifier = Modifier.fillMaxWidth().clickable { isSettingsExpanded = !isSettingsExpanded },
          horizontalArrangement = Arrangement.SpaceBetween,
          verticalAlignment = Alignment.CenterVertically
        ) {
          Row(verticalAlignment = Alignment.CenterVertically) {
            val statusColor = when {
              connectionState?.token != null && connectionState.isOnline -> Color(0xFF10B981) // Green
              connectionState?.token != null -> Color(0xFFF59E0B) // Amber (Offline fallback)
              else -> Color(0xFF94A3B8) // Gray
            }
            Box(
              modifier = Modifier
                .size(8.dp)
                .clip(RoundedCornerShape(4.dp))
                .background(statusColor)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
              text = if (connectionState?.token != null) "API Gateway Connected (${connectionState.username})" else "Offline Mode",
              fontSize = 12.sp,
              fontWeight = FontWeight.SemiBold,
              color = Color.White
            )
          }
          Text(
            text = if (isSettingsExpanded) "Hide Config ▲" else "Configure ▼",
            fontSize = 11.sp,
            color = Color(0xFF38BDF8),
            fontWeight = FontWeight.Bold
          )
        }

        if (isSettingsExpanded) {
          Spacer(modifier = Modifier.height(12.dp))
          OutlinedTextField(
            value = serverUrl,
            onValueChange = { serverUrl = it },
            label = { Text("Server Base URL") },
            placeholder = { Text("http://10.0.2.2:8000") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
              focusedTextColor = Color.White,
              unfocusedTextColor = Color.White,
              focusedBorderColor = Color(0xFF6366F1)
            )
          )
          Spacer(modifier = Modifier.height(8.dp))
          OutlinedTextField(
            value = username,
            onValueChange = { username = it },
            label = { Text("Username") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
              focusedTextColor = Color.White,
              unfocusedTextColor = Color.White,
              focusedBorderColor = Color(0xFF6366F1)
            )
          )
          Spacer(modifier = Modifier.height(8.dp))
          OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Password") },
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
              focusedTextColor = Color.White,
              unfocusedTextColor = Color.White,
              focusedBorderColor = Color(0xFF6366F1)
            )
          )

          connectionState?.lastError?.let { err ->
            Spacer(modifier = Modifier.height(8.dp))
            Text(
              text = err,
              color = Color(0xFFEF4444),
              fontSize = 11.sp,
              fontWeight = FontWeight.Medium
            )
          }

          Spacer(modifier = Modifier.height(12.dp))
          Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
          ) {
            Button(
              onClick = {
                serverUrl = "http://10.0.2.2:8000"
                username = "admin"
                password = "admin_password"
                consoleLog = "System: Loaded local demo connection presets (10.0.2.2:8000). Click 'Connect API' to authenticate."
              },
              modifier = Modifier.weight(1f),
              colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF475569))
            ) {
              Text("Load Demo Presets", fontSize = 11.sp, color = Color.White)
            }
          }

          Spacer(modifier = Modifier.height(8.dp))
          Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
          ) {
            if (connectionState?.token == null) {
              Button(
                onClick = {
                  isConnecting = true
                  viewModel?.connect(serverUrl, username, password) { res ->
                    isConnecting = false
                    password = "" // clear password
                    res.fold(
                      onSuccess = { consoleLog = "System: Authenticated successfully. Token saved." },
                      onFailure = { consoleLog = "System Error: ${it.message}" }
                    )
                  }
                },
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF6366F1)),
                enabled = !isConnecting && serverUrl.isNotBlank() && username.isNotBlank() && password.isNotBlank()
              ) {
                if (isConnecting) {
                  CircularProgressIndicator(modifier = Modifier.size(16.dp), color = Color.White, strokeWidth = 2.dp)
                } else {
                  Text("Connect API")
                }
              }
            } else {
              Button(
                onClick = {
                  viewModel?.disconnect()
                  consoleLog = "System: Disconnected from API. Reverted to secure offline cache."
                },
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEF4444))
              ) {
                Text("Disconnect")
              }
            }
          }
        }
      }
    }

    // ─── Active Beds & Warnings ───
    Card(
      modifier = Modifier.fillMaxWidth(),
      colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)),
      shape = RoundedCornerShape(16.dp)
    ) {
      Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
          text = "ACTIVE EHR BEDS & WARNS",
          fontSize = 11.sp,
          fontWeight = FontWeight.Bold,
          color = Color(0xFF38BDF8),
          letterSpacing = 1.sp
        )

        data.forEach { patient ->
          val isCritical = patient.contains("Critical") || patient.contains("Alert") || patient.contains("Warn")
          val pillColor = if (isCritical) Color(0xFFEF4444) else Color(0xFF10B981)

          Row(
            modifier = Modifier
              .fillMaxWidth()
              .clip(RoundedCornerShape(8.dp))
              .background(Color(0xFF1E293B))
              .padding(10.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
          ) {
            Text(
              text = patient.substringBefore(" ("),
              fontSize = 13.sp,
              fontWeight = FontWeight.SemiBold,
              color = Color.White
            )
            Box(
              modifier = Modifier
                .clip(RoundedCornerShape(6.dp))
                .background(pillColor.copy(alpha = 0.15f))
                .padding(horizontal = 6.dp, vertical = 2.dp)
            ) {
              Text(
                text = if (isCritical) "WARN" else "OK",
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                color = pillColor
              )
            }
          }
        }
      }
    }

    // ─── SOTA AI Agents Controller ───
    Card(
      modifier = Modifier.fillMaxWidth(),
      colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)),
      shape = RoundedCornerShape(16.dp)
    ) {
      Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text(
          text = "CLINICAL AI CONTROLLERS",
          fontSize = 11.sp,
          fontWeight = FontWeight.Bold,
          color = Color(0xFFA855F7),
          letterSpacing = 1.sp
        )

        val firstPatientName = if (data.isNotEmpty()) data.first().substringBefore(" -") else "John Doe"

        Column(
          verticalArrangement = Arrangement.spacedBy(8.dp),
          modifier = Modifier.fillMaxWidth()
        ) {
          // --- Action 1: Audit Notes ---
          Row(
            modifier = Modifier
              .fillMaxWidth()
              .clip(RoundedCornerShape(8.dp))
              .background(Color(0xFF1E293B))
              .padding(10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
          ) {
            Column(modifier = Modifier.weight(1f)) {
              Text("Audit Case Notes", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 13.sp)
              Text("Check clinic SOAP notes for coding issues", color = Color.Gray, fontSize = 11.sp)
            }
            Spacer(modifier = Modifier.width(8.dp))
            Button(
              onClick = {
                consoleLog = "BillingAuditAgent: Invoking CPT code audit on SOAP documentation..."
                viewModel?.triggerSoapAudit(firstPatientName) { res ->
                  consoleLog = res.fold(
                    onSuccess = { it },
                    onFailure = { "Error: ${it.message}" }
                  )
                }
              },
              colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF6366F1)),
              shape = RoundedCornerShape(8.dp)
            ) {
              Text("Run Audit", fontSize = 11.sp, color = Color.White)
            }
          }

          // --- Action 2: Call Doctor ---
          Row(
            modifier = Modifier
              .fillMaxWidth()
              .clip(RoundedCornerShape(8.dp))
              .background(Color(0xFF1E293B))
              .padding(10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
          ) {
            Column(modifier = Modifier.weight(1f)) {
              Text("Call Attending Doctor", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 13.sp)
              Text("Broadcast urgent vitals alert to physician", color = Color.Gray, fontSize = 11.sp)
            }
            Spacer(modifier = Modifier.width(8.dp))
            Button(
              onClick = {
                consoleLog = "TelemetryCallingAgent: Routing emergency alert call to clinician..."
                viewModel?.triggerAutoCall("Critical alert details for $firstPatientName") { res ->
                  consoleLog = res.fold(
                    onSuccess = { it },
                    onFailure = { "Error: ${it.message}" }
                  )
                }
              },
              colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF6366F1)),
              shape = RoundedCornerShape(8.dp)
            ) {
              Text("Call Doc", fontSize = 11.sp, color = Color.White)
            }
          }

          // --- Action 3: Fix System ---
          Row(
            modifier = Modifier
              .fillMaxWidth()
              .clip(RoundedCornerShape(8.dp))
              .background(Color(0xFF1E293B))
              .padding(10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
          ) {
            Column(modifier = Modifier.weight(1f)) {
              Text("Run System Auto-Repair", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 13.sp)
              Text("Detect faults and resolve database locks", color = Color.Gray, fontSize = 11.sp)
            }
            Spacer(modifier = Modifier.width(8.dp))
            Button(
              onClick = {
                consoleLog = "SelfHealingAgent: Performing diagnostic database fix check..."
                viewModel?.triggerSelfHeal { res ->
                  consoleLog = res.fold(
                    onSuccess = { it },
                    onFailure = { "Error: ${it.message}" }
                  )
                }
              },
              colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF6366F1)),
              shape = RoundedCornerShape(8.dp)
            ) {
              Text("Fix App", fontSize = 11.sp, color = Color.White)
            }
          }

          // --- Action 4: Nurse Handoff ---
          Row(
            modifier = Modifier
              .fillMaxWidth()
              .clip(RoundedCornerShape(8.dp))
              .background(Color(0xFF1E293B))
              .padding(10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
          ) {
            Column(modifier = Modifier.weight(1f)) {
              Text("Compile Nurse Handoff", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 13.sp)
              Text("Summarize active shift items for handover", color = Color.Gray, fontSize = 11.sp)
            }
            Spacer(modifier = Modifier.width(8.dp))
            Button(
              onClick = {
                consoleLog = "NursingAgent: Loading triage handoff queue status..."
                viewModel?.triggerHandoff("14C") { res ->
                  consoleLog = res.fold(
                    onSuccess = { it },
                    onFailure = { "Error: ${it.message}" }
                  )
                }
              },
              colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF6366F1)),
              shape = RoundedCornerShape(8.dp)
            ) {
              Text("Handoff", fontSize = 11.sp, color = Color.White)
            }
          }
        }
      }
    }

    // ─── Realtime AI Console Log ───
    Card(
      modifier = Modifier.fillMaxWidth(),
      colors = CardDefaults.cardColors(containerColor = Color.Black),
      shape = RoundedCornerShape(12.dp)
    ) {
      Column(modifier = Modifier.padding(12.dp)) {
        Text(
          text = "CONSOLE MONITOR",
          fontSize = 9.sp,
          fontWeight = FontWeight.Bold,
          color = Color.Green,
          letterSpacing = 0.5.sp
        )
        Spacer(modifier = Modifier.height(6.dp))
        Text(
          text = consoleLog,
          fontSize = 11.sp,
          color = Color.LightGray,
          fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace
        )
      }
    }
  }
}

@Preview(showBackground = true)
@Composable
fun MainScreenPreview() {
  ClinosMobileTheme {
    MainScreen(listOf("John Doe - Bed 14A (Stable)", "Jane Smith - Bed 12B (Alert)"))
  }
}
