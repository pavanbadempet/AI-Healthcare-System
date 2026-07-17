package com.example.clinosmobile.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

data class ConnectionState(
  val url: String = "http://10.0.2.2:8000",
  val username: String = "",
  val token: String? = null,
  val isOnline: Boolean = false,
  val lastError: String? = null
)

interface DataRepository {
  val data: Flow<List<String>>
  val connectionState: StateFlow<ConnectionState>

  suspend fun connectAndLogin(url: String, username: String, password: String): Result<String>
  fun disconnect()
  suspend fun triggerSoapAudit(patientName: String): Result<String>
  suspend fun triggerAutoCall(alertDetails: String): Result<String>
  suspend fun triggerSelfHeal(): Result<String>
  suspend fun triggerHandoff(bed: String): Result<String>
  suspend fun refreshTelemetry()
}

class DefaultDataRepository : DataRepository {
  private val _connectionState = MutableStateFlow(ConnectionState())
  override val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

  private val _telemetryData = MutableStateFlow<List<String>>(getMockData())
  override val data: Flow<List<String>> = _telemetryData

  private fun getMockData(): List<String> {
    return listOf(
      "John Doe - Bed 14A (Stable)",
      "Jane Smith - Bed 12B (Alert: SpO2 88%)",
      "Robert Green - Bed 9C (Stable)",
      "Alice Watson - Bed 4D (Stable)",
      "Marcus Thorne - Bed 14C (Critical: HR 118)"
    )
  }

  private suspend fun makePostRequest(
    urlString: String,
    params: Map<String, String>,
    token: String? = null
  ): Result<String> = withContext(Dispatchers.IO) {
    try {
      val url = URL(urlString)
      val conn = url.openConnection() as HttpURLConnection
      conn.requestMethod = "POST"
      conn.doOutput = true
      conn.connectTimeout = 5000
      conn.readTimeout = 5000

      if (token != null) {
        conn.setRequestProperty("Authorization", "Bearer $token")
      }

      val postData = params.map { (k, v) ->
        "${URLEncoder.encode(k, "UTF-8")}=${URLEncoder.encode(v, "UTF-8")}"
      }.joinToString("&")

      conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
      conn.setRequestProperty("Content-Length", postData.length.toString())

      OutputStreamWriter(conn.outputStream).use { writer ->
        writer.write(postData)
        writer.flush()
      }

      val responseCode = conn.responseCode
      if (responseCode in 200..299) {
        val response = conn.inputStream.bufferedReader().use { it.readText() }
        Result.success(response)
      } else {
        val errorResponse = conn.errorStream?.bufferedReader()?.use { it.readText() }
          ?: "HTTP error code: $responseCode"
        Result.failure(Exception(errorResponse))
      }
    } catch (e: Exception) {
      Result.failure(e)
    }
  }

  private suspend fun makeGetRequest(
    urlString: String,
    token: String? = null
  ): Result<String> = withContext(Dispatchers.IO) {
    try {
      val url = URL(urlString)
      val conn = url.openConnection() as HttpURLConnection
      conn.requestMethod = "GET"
      conn.connectTimeout = 5000
      conn.readTimeout = 5000

      if (token != null) {
        conn.setRequestProperty("Authorization", "Bearer $token")
      }

      val responseCode = conn.responseCode
      if (responseCode in 200..299) {
        val response = conn.inputStream.bufferedReader().use { it.readText() }
        Result.success(response)
      } else {
        val errorResponse = conn.errorStream?.bufferedReader()?.use { it.readText() }
          ?: "HTTP error code: $responseCode"
        Result.failure(Exception(errorResponse))
      }
    } catch (e: Exception) {
      Result.failure(e)
    }
  }

  private suspend fun makePostQueryRequest(
    urlString: String,
    token: String? = null
  ): Result<String> = withContext(Dispatchers.IO) {
    try {
      val url = URL(urlString)
      val conn = url.openConnection() as HttpURLConnection
      conn.requestMethod = "POST"
      conn.connectTimeout = 8000
      conn.readTimeout = 8000

      if (token != null) {
        conn.setRequestProperty("Authorization", "Bearer $token")
      }

      val responseCode = conn.responseCode
      if (responseCode in 200..299) {
        val response = conn.inputStream.bufferedReader().use { it.readText() }
        Result.success(response)
      } else {
        val errorResponse = conn.errorStream?.bufferedReader()?.use { it.readText() }
          ?: "HTTP error code: $responseCode"
        Result.failure(Exception(errorResponse))
      }
    } catch (e: Exception) {
      Result.failure(e)
    }
  }

  override suspend fun connectAndLogin(url: String, username: String, password: String): Result<String> {
    val baseUrl = if (url.endsWith("/")) url.substring(0, url.length - 1) else url
    val tokenUrl = "$baseUrl/v1/token"

    val params = mapOf("username" to username, "password" to password)
    val result = makePostRequest(tokenUrl, params)

    return result.fold(
      onSuccess = { response ->
        val tokenRegex = """\"access_token\"\s*:\s*\"([^\"]+)\"""".toRegex()
        val match = tokenRegex.find(response)
        val token = match?.groupValues?.get(1)

        if (token != null) {
          _connectionState.value = ConnectionState(
            url = baseUrl,
            username = username,
            token = token,
            isOnline = true,
            lastError = null
          )
          refreshTelemetry()
          Result.success(token)
        } else {
          val err = "Could not parse access token from login response"
          _connectionState.value = _connectionState.value.copy(lastError = err)
          Result.failure(Exception(err))
        }
      },
      onFailure = { error ->
        val err = "Login failed: ${error.message}"
        _connectionState.value = _connectionState.value.copy(lastError = err)
        Result.failure(error)
      }
    )
  }

  override suspend fun refreshTelemetry() {
    val state = _connectionState.value
    if (state.token == null) {
      _telemetryData.value = getMockData()
      return
    }

    val patientsUrl = "${state.url}/v1/hospital/doctor/patients"
    val result = makeGetRequest(patientsUrl, state.token)

    result.fold(
      onSuccess = { json ->
        val patients = parsePatientsJson(json)
        if (patients.isNotEmpty()) {
          _telemetryData.value = patients
          _connectionState.value = _connectionState.value.copy(isOnline = true, lastError = null)
        } else {
          _telemetryData.value = getMockData().map { "$it (Mock Fallback)" }
        }
      },
      onFailure = { error ->
        _telemetryData.value = getMockData().map { "$it (Offline)" }
        _connectionState.value = _connectionState.value.copy(isOnline = false, lastError = error.message)
      }
    )
  }

  private fun parsePatientsJson(json: String): List<String> {
    val list = mutableListOf<String>()
    val regex = """\{[^{}]+\}""".toRegex()
    val matches = regex.findAll(json)
    for (match in matches) {
      val block = match.value
      val name = """\"full_name\"\s*:\s*\"([^\"]+)\"""".toRegex().find(block)?.groupValues?.get(1) ?: "Unknown Patient"
      val id = """\"patient_id\"\s*:\s*(\d+)""".toRegex().find(block)?.groupValues?.get(1) ?: "0"
      val status = """\"latest_status\"\s*:\s*\"([^\"]+)\"""".toRegex().find(block)?.groupValues?.get(1) ?: "Stable"
      val encType = """\"latest_encounter_type\"\s*:\s*\"([^\"]+)\"""".toRegex().find(block)?.groupValues?.get(1) ?: "Encounter"
      list.add("$name - Bed $id ($status: $encType)")
    }
    return list
  }

  override suspend fun triggerSoapAudit(patientName: String): Result<String> {
    val state = _connectionState.value
    if (state.token == null) {
      return Result.success("Mock SOAP Audit on $patientName completed. Score: 95%. ICD-10: I10.")
    }

    val soapNote = "Patient $patientName presents with blood pressure of 145/95. Attending diagnosed essential hypertension."
    val url = "${state.url}/v1/admin/agents/soap-audit?soap_note=${URLEncoder.encode(soapNote, "UTF-8")}"

    return makePostQueryRequest(url, state.token).fold(
      onSuccess = { response -> Result.success("Real SOAP Audit: $response") },
      onFailure = { error -> Result.failure(error) }
    )
  }

  override suspend fun triggerAutoCall(alertDetails: String): Result<String> {
    val state = _connectionState.value
    if (state.token == null) {
      return Result.success("Mock CallingAgent: Routing alert '$alertDetails' to Dr. Sarah Jenkins (+1-555-0199)...")
    }

    val url = "${state.url}/v1/admin/agents/auto-call?alert_details=${URLEncoder.encode(alertDetails, "UTF-8")}"

    return makePostQueryRequest(url, state.token).fold(
      onSuccess = { response -> Result.success("Real Auto Call: $response") },
      onFailure = { error -> Result.failure(error) }
    )
  }

  override suspend fun triggerSelfHeal(): Result<String> {
    val state = _connectionState.value
    if (state.token == null) {
      return Result.success("Mock SelfHealingAgent: Rebuilding B-Tree and vacuuming sqlite... Success.")
    }

    val errorLogs = "OperationalError: database is locked"
    val healthSignals = "CPU: 92%, Memory: 85%"
    val url = "${state.url}/v1/admin/agents/auto-fix?error_logs=${URLEncoder.encode(errorLogs, "UTF-8")}&health_signals=${URLEncoder.encode(healthSignals, "UTF-8")}"

    return makePostQueryRequest(url, state.token).fold(
      onSuccess = { response -> Result.success("Real Self Heal: $response") },
      onFailure = { error -> Result.failure(error) }
    )
  }

  override suspend fun triggerHandoff(bed: String): Result<String> {
    val state = _connectionState.value
    if (state.token == null) {
      return Result.success("Mock NursingAgent: Compiled shift card for Bed $bed. Priority: Stable Q2h checks.")
    }

    val url = "${state.url}/v1/hospital/triage-queue"
    return makeGetRequest(url, state.token).fold(
      onSuccess = { response -> Result.success("Real Triage Handoff Queue: $response") },
      onFailure = { error -> Result.failure(error) }
    )
  }

  override fun disconnect() {
    _connectionState.value = ConnectionState()
    _telemetryData.value = getMockData()
  }
}
